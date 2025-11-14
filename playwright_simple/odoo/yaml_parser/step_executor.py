#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step executor for Odoo YAML tests.

Handles execution of test steps with validation and state management.
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from playwright.async_api import Page

from ...core.step import TestStep
from ...core.cursor_transition import CursorTransitionManager
from ...core.debug import DebugManager, SkipStepException, QuitTestException

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executor for test steps with validation and state management."""
    
    def __init__(self, test, cursor_transition: CursorTransitionManager, debug_manager: Optional[DebugManager] = None):
        """
        Initialize step executor.
        
        Args:
            test: OdooTestBase instance
            cursor_transition: CursorTransitionManager instance
            debug_manager: Optional DebugManager for interactive debugging
        """
        self.test = test
        self.cursor_transition = cursor_transition
        self.debug_manager = debug_manager
    
    async def execute_step(
        self,
        step_dict: Dict[str, Any],
        step: TestStep,
        i: int,
        total_steps: int,
        action_func,
        validate_element_func,
        capture_state_func,
        validate_action_func
    ) -> None:
        """
        Execute a single test step with full validation.
        
        Args:
            step_dict: Step dictionary from YAML
            step: TestStep instance
            i: Step number (1-based)
            total_steps: Total number of steps
            action_func: Function to execute the action
            validate_element_func: Function to validate element before action
            capture_state_func: Function to capture state before action
            validate_action_func: Function to validate action after execution
        """
        print(f"    [{i}/{total_steps}] Passo: {str(step_dict)[:80]}")
        logger.info(f"Step {i}: Created TestStep object with subtitle='{step.subtitle}'")
        
        # Wait for cursor transition before starting (except first step)
        if i > 1:
            await self.cursor_transition.wait_before_step_start(i)
        
        # STATE: STARTING - Transition to starting state
        step.start()
        
        # STATE: EXECUTING - Mark as executing RIGHT BEFORE action runs
        step.execute()
        
        # DEBUG: Pause BEFORE validation (if debug mode enabled or breakpoint in step)
        # This allows user to inspect the page state before validation fails
        if self.debug_manager:
            try:
                # Check if this step has a breakpoint (debug: true or breakpoint: true)
                has_breakpoint = (
                    step_dict.get('debug', False) is True or
                    step_dict.get('breakpoint', False) is True
                )
                
                # Debug log to verify breakpoint detection
                if has_breakpoint:
                    logger.info(f"Step {i}: Breakpoint detected! step_dict keys: {list(step_dict.keys())}, breakpoint value: {step_dict.get('breakpoint')}, debug value: {step_dict.get('debug')}")
                    print(f"  🛑 Breakpoint detectado no passo {i}")
                
                # Determine action type
                action_type = 'unknown'
                if 'go_to' in step_dict:
                    action_type = 'go_to'
                elif 'open_filters' in step_dict:
                    action_type = 'open_filters'
                elif 'click' in step_dict:
                    action_type = 'click'
                elif 'fill' in step_dict:
                    action_type = 'fill'
                elif 'hover' in step_dict:
                    action_type = 'hover'
                elif 'login' in step_dict:
                    action_type = 'login'
                elif 'open_record' in step_dict:
                    action_type = 'open_record'
                
                await self.debug_manager.pause(
                    step_number=i,
                    action_type=action_type,
                    action_details=step_dict,
                    page_url=self.test.page.url if hasattr(self.test, 'page') else '',
                    page_title=await self.test.page.title() if hasattr(self.test, 'page') else '',
                    force=has_breakpoint,  # Force pause if breakpoint is set in step
                    page=self.test.page if hasattr(self.test, 'page') else None  # Pass page to bring window to front
                )
            except SkipStepException:
                logger.info(f"Step {i} skipped by user")
                return
            except QuitTestException:
                logger.info("Test quit by user")
                raise
        
        # Capture state BEFORE action (for validation after)
        state_before = await capture_state_func(step_dict, self.test)
        step.action_details['state_before'] = state_before
        
        # Validate element exists BEFORE executing action
        await validate_element_func(step_dict, self.test, step)
        
        # NOW execute the action
        await action_func()
        
        # Validate action succeeded AFTER execution
        await validate_action_func(step_dict, self.test, step, state_before)
        
        # STATE: WAITING_FOR_LOAD - Wait for page to load
        step.wait_load()
        if "wait" not in step_dict:
            # Wait until ready with appropriate timeout
            if "go_to" in step_dict or "login" in step_dict or "logout" in step_dict:
                await self.test.wait_until_ready(timeout=5000)  # Longer for navigation
            elif "open_record" in step_dict or "click" in step_dict:
                await self.test.wait_until_ready(timeout=3000)  # Medium for interactions
            else:
                await self.test.wait_until_ready(timeout=2000)  # Shorter for other actions
        
        # Wait after screen loads (proportional to action type)
        await self._apply_post_load_delay(step_dict, step)
        
        # STATE: COMPLETED - Mark step as completed
        step.complete()
        
        # Capture debug screenshot after step completes
        await self._capture_debug_screenshot(step_dict, step, i)
        
        # Wait for cursor transition after completing
        await self.cursor_transition.wait_after_step_complete(i)
        
        # Print completion message with validation status
        self._print_completion_message(step, i)
        
        # Fail test if critical actions failed
        self._check_critical_failure(step_dict, step, i)
    
    async def _apply_post_load_delay(self, step_dict: Dict[str, Any], step: TestStep) -> None:
        """Apply post-load delay based on action type and step configuration."""
        # Check if fast mode is enabled (skip delays for static steps)
        fast_mode = getattr(self.test.config, 'fast_mode', False)
        if hasattr(self.test.config, 'debug') and hasattr(self.test.config.debug, 'fast_mode'):
            fast_mode = self.test.config.debug.fast_mode
        
        post_load_delay = self.test.config.video.post_load_delay
        static_step_duration = self.test.config.video.static_step_duration
        
        # Check if this is a "static step"
        subtitle_text = step.subtitle or step_dict.get('subtitle', '') or step_dict.get('description', '')
        is_static_step = (
            step_dict.get('static', False) or
            subtitle_text.lower().startswith('visualizando') or
            subtitle_text.lower().startswith('mostrando') or
            subtitle_text.lower().startswith('exibindo') or
            "screenshot" in step_dict or
            (not any(key in step_dict for key in ['go_to', 'click', 'fill', 'open_record', 'search', 'filter_by', 'login', 'logout', 'add_line']) and 'description' in step_dict)
        )
        
        # In fast mode, skip delays for static steps
        if fast_mode and is_static_step:
            logger.debug(f"Fast mode: skipping delay for static step")
            return
        
        if is_static_step:
            await asyncio.sleep(static_step_duration)
        elif "screenshot" in step_dict:
            await asyncio.sleep(post_load_delay * 0.8)
        elif "go_to" in step_dict or "login" in step_dict:
            await asyncio.sleep(post_load_delay * 1.3)
        elif "open_record" in step_dict or "click" in step_dict:
            await asyncio.sleep(post_load_delay)
        else:
            await asyncio.sleep(post_load_delay * 0.7)
    
    def _print_completion_message(self, step: TestStep, i: int) -> None:
        """Print completion message with validation status."""
        status_parts = []
        if step.element_found is not None:
            status_parts.append(f"Elemento: {'✅' if step.element_found else '❌'}")
        if step.action_succeeded is not None:
            status_parts.append(f"Ação: {'✅' if step.action_succeeded else '❌'}")
        if step.warnings:
            status_parts.append(f"⚠️ {len(step.warnings)} aviso(s)")
        
        status_str = " | ".join(status_parts) if status_parts else ""
        completion_msg = f"    ✅ Passo {i} concluído (estado: {step.current_state.id})"
        if status_str:
            completion_msg += f" | {status_str}"
        print(completion_msg)
        
        # Print warnings if any
        if step.warnings:
            for warning in step.warnings:
                print(f"      ⚠️  {warning}")
    
    def _check_critical_failure(self, step_dict: Dict[str, Any], step: TestStep, i: int) -> None:
        """Check if step failed critically and raise error if needed."""
        if step.element_found is False and step.action_succeeded is False:
            # Both element not found AND action failed - this is critical
            critical_actions = ["click", "fill", "open_record"]
            if any(key in step_dict for key in critical_actions):
                error_msg = (
                    f"Passo {i} falhou: elemento não encontrado E ação não surtiu efeito. "
                    f"Warnings: {', '.join(step.warnings)}"
                )
                logger.error(f"Step {i}: Critical failure - {error_msg}")
                # HTML will be saved by ActionValidator or in exception handler
                raise RuntimeError(error_msg)
    
    async def _save_error_html(
        self,
        step_dict: Dict[str, Any],
        step: TestStep,
        i: int,
        reason: str = ""
    ) -> None:
        """
        Save HTML content when an error occurs.
        
        Args:
            step_dict: Step dictionary from YAML
            step: TestStep instance
            i: Step number (1-based)
            reason: Reason for saving HTML
        """
        try:
            # Get test name
            test_name = getattr(self.test, 'test_name', 'unknown')
            
            # Create error directory
            project_root = Path(__file__).parent.parent.parent.parent.parent
            error_dir = project_root / "presentation" / "playwright" / "screenshots" / test_name
            error_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate HTML filename
            action_type = self._get_action_type(step_dict)
            html_path = error_dir / f"debug_error_step_{i}_{action_type}.html"
            
            # Save HTML
            html_content = await self.test.page.content()
            html_path.write_text(html_content, encoding='utf-8')
            
            logger.error(f"HTML de erro salvo em {html_path} - Razão: {reason}")
            print(f"    📄 HTML de erro salvo: {html_path}")
        except Exception as e:
            logger.warning(f"Erro ao salvar HTML: {e}")
    
    def _generate_debug_screenshot_name(self, step_dict: Dict[str, Any], i: int) -> str:
        """
        Generate descriptive screenshot name based on action type and step number.
        
        Args:
            step_dict: Step dictionary from YAML
            i: Step number (1-based)
            
        Returns:
            Sanitized filename without extension
        """
        # Extract action type and value
        action_type = None
        action_value = None
        
        # Check for common action types
        if "login" in step_dict:
            action_type = "login"
            action_value = str(step_dict.get("login", ""))
        elif "go_to" in step_dict:
            action_type = "go_to"
            action_value = str(step_dict.get("go_to", ""))
        elif "screenshot" in step_dict:
            action_type = "screenshot"
            action_value = str(step_dict.get("screenshot", ""))
        elif "click" in step_dict:
            action_type = "click"
            action_value = str(step_dict.get("click", ""))
        elif "fill" in step_dict:
            action_type = "fill"
            action_value = str(step_dict.get("fill", ""))
        elif "open_record" in step_dict:
            action_type = "open_record"
            action_value = str(step_dict.get("open_record", ""))
        elif "search" in step_dict:
            action_type = "search"
            action_value = str(step_dict.get("search", ""))
        elif "filter_by" in step_dict:
            action_type = "filter_by"
            action_value = str(step_dict.get("filter_by", ""))
        elif "logout" in step_dict:
            action_type = "logout"
            action_value = ""
        elif "add_line" in step_dict:
            action_type = "add_line"
            action_value = str(step_dict.get("add_line", ""))
        else:
            # Generic step without specific action
            action_type = "step"
            action_value = ""
        
        # Sanitize action_value for filename
        # Remove/replace invalid characters: /, \, :, *, ?, ", <, >, |
        sanitized_value = re.sub(r'[/\\:*?"<>|]', '_', action_value)
        # Replace spaces with underscores
        sanitized_value = sanitized_value.replace(' ', '_')
        # Remove multiple consecutive underscores
        sanitized_value = re.sub(r'_+', '_', sanitized_value)
        # Remove leading/trailing underscores
        sanitized_value = sanitized_value.strip('_')
        # Limit length to 80 characters
        if len(sanitized_value) > 80:
            sanitized_value = sanitized_value[:80]
        
        # Build filename
        if sanitized_value:
            filename = f"step_{i:02d}_{action_type}_{sanitized_value}"
        else:
            filename = f"step_{i:02d}_{action_type}"
        
        # Final sanitization: ensure no invalid characters remain
        filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('_')
        
        return filename
    
    async def _save_debug_metadata(
        self,
        metadata_path: Path,
        step_dict: Dict[str, Any],
        step: TestStep,
        i: int
    ) -> None:
        """
        Save debug metadata to file.
        
        Args:
            metadata_path: Path to save metadata file
            step_dict: Step dictionary from YAML
            step: TestStep instance
            i: Step number (1-based)
        """
        try:
            # Get current page info
            current_url = self.test.page.url
            page_title = await self.test.page.title()
        except Exception as e:
            logger.warning(f"Could not get page info for metadata: {e}")
            current_url = "unknown"
            page_title = "unknown"
        
        # Build metadata content
        metadata_lines = [
            f"Step: {i}",
            f"Action Type: {self._get_action_type(step_dict)}",
            f"Action Details: {step_dict}",
            f"Expected Description: {step.description or 'N/A'}",
            f"Subtitle: {step.subtitle or 'N/A'}",
            f"URL: {current_url}",
            f"Page Title: {page_title}",
            f"Timestamp: {datetime.now().isoformat()}",
        ]
        
        # Add step state info if available
        if hasattr(step, 'current_state'):
            metadata_lines.append(f"Step State: {step.current_state.id}")
        
        # Add validation info if available
        if step.element_found is not None:
            metadata_lines.append(f"Element Found: {step.element_found}")
        if step.action_succeeded is not None:
            metadata_lines.append(f"Action Succeeded: {step.action_succeeded}")
        if step.warnings:
            metadata_lines.append(f"Warnings: {', '.join(step.warnings)}")
        
        # Write metadata file
        try:
            metadata_path.write_text('\n'.join(metadata_lines), encoding='utf-8')
            logger.debug(f"Debug metadata saved: {metadata_path}")
        except Exception as e:
            logger.warning(f"Failed to save debug metadata: {e}")
    
    def _get_action_type(self, step_dict: Dict[str, Any]) -> str:
        """Get action type from step dictionary."""
        action_keys = ["login", "go_to", "screenshot", "click", "fill", "open_record", 
                      "search", "filter_by", "logout", "add_line"]
        for key in action_keys:
            if key in step_dict:
                return key
        return "unknown"
    
    async def _capture_debug_screenshot(
        self,
        step_dict: Dict[str, Any],
        step: TestStep,
        i: int
    ) -> None:
        """
        Capture debug screenshot after step completes.
        
        Args:
            step_dict: Step dictionary from YAML
            step: TestStep instance
            i: Step number (1-based)
        """
        try:
            # Get test name
            test_name = getattr(self.test, 'test_name', 'unknown')
            
            # Create debug screenshots directory
            # Use presentation/playwright/screenshots_debug as base (relative to project root)
            # We need to find the project root first
            project_root = Path(__file__).parent.parent.parent.parent.parent
            debug_dir = project_root / "presentation" / "playwright" / "screenshots_debug" / test_name
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate screenshot name
            screenshot_name = self._generate_debug_screenshot_name(step_dict, i)
            screenshot_path = debug_dir / f"{screenshot_name}.png"
            metadata_path = debug_dir / f"{screenshot_name}.txt"
            
            # Capture screenshot
            await self.test.page.screenshot(
                path=str(screenshot_path),
                full_page=True
            )
            
            # Save metadata
            await self._save_debug_metadata(metadata_path, step_dict, step, i)
            
            logger.debug(f"Debug screenshot captured: {screenshot_path}")
            
        except Exception as e:
            # Don't interrupt test execution if screenshot capture fails
            logger.warning(f"Failed to capture debug screenshot for step {i}: {e}", exc_info=True)

