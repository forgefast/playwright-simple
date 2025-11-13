#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step executor for Odoo YAML tests.

Handles execution of test steps with validation and state management.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from playwright.async_api import Page

from ...core.step import TestStep
from ...core.cursor_transition import CursorTransitionManager

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executor for test steps with validation and state management."""
    
    def __init__(self, test, cursor_transition: CursorTransitionManager):
        """
        Initialize step executor.
        
        Args:
            test: OdooTestBase instance
            cursor_transition: CursorTransitionManager instance
        """
        self.test = test
        self.cursor_transition = cursor_transition
    
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
        
        # Validate element exists BEFORE executing action
        await validate_element_func(step_dict, self.test, step)
        
        # Capture state BEFORE action (for validation after)
        state_before = await capture_state_func(step_dict, self.test)
        step.action_details['state_before'] = state_before
        
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
        
        # Wait for cursor transition after completing
        await self.cursor_transition.wait_after_step_complete(i)
        
        # Print completion message with validation status
        self._print_completion_message(step, i)
        
        # Fail test if critical actions failed
        self._check_critical_failure(step_dict, step, i)
    
    async def _apply_post_load_delay(self, step_dict: Dict[str, Any], step: TestStep) -> None:
        """Apply post-load delay based on action type and step configuration."""
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
                raise RuntimeError(error_msg)

