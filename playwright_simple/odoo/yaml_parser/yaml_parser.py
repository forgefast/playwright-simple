#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main OdooYAMLParser class that composes parsing and execution modules.
"""

import asyncio
import logging
from typing import Dict, Any, Callable, TYPE_CHECKING, Optional, List
from datetime import datetime
from pathlib import Path
from playwright.async_api import Page

from ...core.yaml_resolver import parse_yaml_file
from ...core.step import TestStep
from ...core.cursor_transition import CursorTransitionManager
from .action_parser import ActionParser
from .action_validator import ActionValidator
from .step_executor import StepExecutor
from ...core.debug import DebugManager, QuitTestException

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..base import OdooTestBase


class OdooYAMLParser:
    """YAML parser with Odoo-specific actions - User-friendly syntax."""
    
    def __init__(self):
        """Initialize Odoo YAML parser with composed modules."""
        self.action_parser = ActionParser()
        self.action_validator = ActionValidator()
    
    @classmethod
    def to_python_function(cls, yaml_data: Dict[str, Any]) -> Callable:
        """
        Convert YAML test definition to Python function with Odoo support.
        
        Supports user-friendly YAML format with inheritance, composition, setup/teardown:
        ```yaml
        extends: common_login.yaml
        setup:
          - login: admin
            password: admin
        steps:
          - go_to: "Vendas > Pedidos"
          - click: "Criar"
          - fill: "Cliente = João Silva"
        teardown:
          - logout:
        save_session: true
        ```
        
        Args:
            yaml_data: YAML test data (already resolved for inheritance/includes)
            
        Returns:
            Python test function
        """
        # Import here to avoid circular dependency
        from ..base import OdooTestBase
        
        # Get setup, steps, and teardown
        setup_steps = yaml_data.get("setup", [])
        steps = yaml_data.get("steps", [])
        teardown_steps = yaml_data.get("teardown", [])
        config_data = yaml_data.get("config", {})
        save_session = yaml_data.get("save_session", False)
        load_session = yaml_data.get("load_session")
        
        async def test_function(page: Page, test: 'OdooTestBase', test_steps: Optional[List[Dict[str, Any]]] = None, video_start_time: Optional[datetime] = None):
            """Generated test function from user-friendly YAML."""
            # Initialize test_steps if not provided
            if test_steps is None:
                test_steps = []
            
            # Store step count for duration estimation
            total_steps = len(setup_steps) + len(steps) + len(teardown_steps)
            test_function.yaml_steps_count = total_steps
            test_function.yaml_main_steps_count = len(steps)
            
            # Use video_start_time if provided
            test_start_time = video_start_time if video_start_time else datetime.now()
            
            # Apply configuration from YAML if provided
            if config_data:
                if 'cursor' in config_data:
                    cursor_data = config_data['cursor']
                    if 'style' in cursor_data:
                        test.config.cursor.style = cursor_data['style']
                    if 'color' in cursor_data:
                        test.config.cursor.color = cursor_data['color']
                    if 'size' in cursor_data:
                        test.config.cursor.size = cursor_data['size']
                    if 'click_effect' in cursor_data:
                        test.config.cursor.click_effect = cursor_data['click_effect']
                    if 'animation_speed' in cursor_data:
                        test.config.cursor.animation_speed = cursor_data['animation_speed']
                
                if 'video' in config_data:
                    video_data = config_data['video']
                    if 'enabled' in video_data:
                        test.config.video.enabled = video_data['enabled']
                    if 'quality' in video_data:
                        test.config.video.quality = video_data['quality']
                    if 'codec' in video_data:
                        test.config.video.codec = video_data['codec']
                    if 'speed' in video_data:
                        test.config.video.speed = float(video_data['speed'])
                    if 'subtitles' in video_data:
                        test.config.video.subtitles = bool(video_data['subtitles'])
                    if 'hard_subtitles' in video_data:
                        test.config.video.hard_subtitles = bool(video_data['hard_subtitles'])
                    if 'audio' in video_data:
                        test.config.video.audio = bool(video_data['audio'])
                    if 'audio_engine' in video_data:
                        test.config.video.audio_engine = video_data['audio_engine']
                    if 'audio_lang' in video_data:
                        test.config.video.audio_lang = video_data['audio_lang']
                    if 'audio_voice' in video_data:
                        test.config.video.audio_voice = video_data['audio_voice']
                    if 'audio_rate' in video_data:
                        test.config.video.audio_rate = video_data['audio_rate']
                    if 'audio_pitch' in video_data:
                        test.config.video.audio_pitch = video_data['audio_pitch']
                    if 'audio_volume' in video_data:
                        test.config.video.audio_volume = video_data['audio_volume']
                    if 'narration' in video_data:
                        test.config.video.narration = bool(video_data['narration'])
                    if 'narration_lang' in video_data:
                        test.config.video.narration_lang = video_data['narration_lang']
                    if 'narration_engine' in video_data:
                        test.config.video.narration_engine = video_data['narration_engine']
                    if 'narration_slow' in video_data:
                        test.config.video.narration_slow = bool(video_data['narration_slow'])
                
                if 'browser' in config_data:
                    browser_data = config_data['browser']
                    if 'headless' in browser_data:
                        test.config.browser.headless = browser_data['headless']
                    if 'slow_mo' in browser_data:
                        test.config.browser.slow_mo = browser_data['slow_mo']
            
            # Initialize debug manager (always create it, even if disabled, to support breakpoints)
            debug_manager = None
            debug_enabled = False
            pause_on_actions = []
            
            if config_data and 'debug' in config_data:
                debug_data = config_data['debug']
                debug_enabled = debug_data.get('enabled', False)
                pause_on_actions = debug_data.get('pause_on_actions', [])
                fast_mode = debug_data.get('fast_mode', False)
                # Set fast_mode on test config for easy access
                test.config.fast_mode = fast_mode
                if fast_mode:
                    print("  ⚡ Modo RÁPIDO ativado - delays em passos static serão ignorados")
            
            # Check if there are any breakpoints in steps
            has_breakpoints = False
            if steps:
                for step_dict in steps:
                    if step_dict.get('debug', False) is True or step_dict.get('breakpoint', False) is True:
                        has_breakpoints = True
                        break
            
            # Create debug manager if debug is enabled OR if there are breakpoints
            if debug_enabled or has_breakpoints:
                debug_manager = DebugManager(
                    enabled=debug_enabled,  # May be False, but breakpoints will still work via force=True
                    pause_on_actions=pause_on_actions if pause_on_actions else None
                )
                # Force headless=False when debug is enabled or breakpoints exist (so user can see browser)
                if debug_enabled or has_breakpoints:
                    test.config.browser.headless = False
                
                if debug_enabled:
                    print("  🔍 Modo DEBUG ativado - o teste pausará antes de cada ação")
                    if pause_on_actions:
                        print(f"  🔍 Pausando apenas em: {', '.join(pause_on_actions)}")
                    else:
                        print("  🔍 Pausando em todas as ações")
                
                if has_breakpoints:
                    print("  🛑 Breakpoints detectados nos passos - o teste pausará nos breakpoints")
            
            # Execute setup steps first
            if setup_steps:
                print(f"  🔧 Executando {len(setup_steps)} passo(s) de setup...")
                for i, step in enumerate(setup_steps, 1):
                    try:
                        print(f"    [{i}/{len(setup_steps)}] Setup: {str(step)[:80]}")
                        action_func = ActionParser.parse_odoo_action(step, test, None)
                        await action_func()
                        
                        # Automatically wait for Odoo to be ready after each setup action
                        if "wait" not in step and "screenshot" not in step:
                            await test.wait_until_ready()
                        
                        print(f"    ✅ Setup passo {i} concluído")
                    except Exception as e:
                        step_str = str(step)[:100]
                        error_msg = str(e)
                        
                        # Log structured error
                        logger.error(
                            f"Setup step {i} failed",
                            extra={
                                "step_number": i,
                                "step_type": "setup",
                                "step_action": step_str,
                                "error_type": type(e).__name__,
                                "error_message": error_msg,
                                "test_name": getattr(test, 'test_name', 'unknown')
                            }
                        )
                        
                        print(f"    ❌ Erro no setup passo {i}: {error_msg}")
                        
                        # Save HTML content of the page (more useful for debugging)
                        try:
                            debug_html = test.screenshot_manager.test_dir / f"debug_error_setup_step_{i}.html"
                            debug_html.parent.mkdir(parents=True, exist_ok=True)
                            html_content = await test.page.content()
                            debug_html.write_text(html_content, encoding='utf-8')
                            print(f"    📄 HTML da página de erro (setup) salvo: {debug_html}")
                            logger.error(
                                f"Setup error HTML captured",
                                extra={
                                    "step_number": i,
                                    "html_path": str(debug_html)
                                }
                            )
                        except Exception as html_error:
                            logger.warning(f"Failed to capture setup error HTML: {html_error}")
                            print(f"    ⚠️  Erro ao capturar HTML: {html_error}")
                        
                        raise RuntimeError(
                            f"Erro ao executar setup passo {i}: {step_str}\n"
                            f"Erro: {error_msg}"
                        ) from e
            
            # Initialize cursor transition manager
            cursor_transition = CursorTransitionManager(
                transition_delay=test.config.cursor.transition_delay
            )
            if hasattr(test, 'cursor_manager'):
                cursor_transition.set_cursor_manager(test.cursor_manager)
            
            # Initialize step executor (with debug manager if enabled)
            step_executor = StepExecutor(test, cursor_transition, debug_manager=debug_manager)
            
            # Process shared subtitles: subtitle in first step applies to following steps
            current_subtitle: Optional[str] = None
            # Process shared audio: audio in first step applies to following steps (until next audio is specified)
            current_audio: Optional[str] = None
            
            # Execute main steps
            try:
                print(f"  ▶️  Executando {len(steps)} passo(s) principal(is)...")
                
                for i, step_dict in enumerate(steps, 1):
                    try:
                        # Debug: Check for breakpoint in step_dict
                        if step_dict.get('breakpoint', False) is True or step_dict.get('debug', False) is True:
                            logger.info(f"YAML Parser: Breakpoint found in step {i}, step_dict: {step_dict}")
                            print(f"  🛑 YAML Parser detectou breakpoint no passo {i}")
                        
                        # Process shared subtitles (inherited from previous step if not specified)
                        if 'subtitle' in step_dict or 'legend' in step_dict:
                            current_subtitle = step_dict.get('subtitle') or step_dict.get('legend')
                        
                        # Process shared audio (inherited from previous step if not specified)
                        if 'audio' in step_dict or 'speech' in step_dict:
                            current_audio = step_dict.get('audio') or step_dict.get('speech')
                        
                        # Create TestStep object
                        step = TestStep(
                            step_number=i,
                            action=step_dict,
                            subtitle=current_subtitle,
                            description=step_dict.get('description', current_subtitle),
                            video_start_time=test_start_time,
                            audio=current_audio
                        )
                        
                        # Parse action function
                        action_func = ActionParser.parse_odoo_action(step_dict, test, step)
                        
                        # Execute step with validation
                        await step_executor.execute_step(
                            step_dict=step_dict,
                            step=step,
                            i=i,
                            total_steps=len(steps),
                            action_func=action_func,
                            validate_element_func=ActionValidator.validate_element_before_action,
                            capture_state_func=ActionValidator.capture_action_state,
                            validate_action_func=ActionValidator.validate_action_succeeded
                        )
                        
                        # Add step to test_steps list
                        test_steps.append(step)
                        
                    except QuitTestException:
                        # User requested to quit test
                        print("  🛑 Teste interrompido pelo usuário")
                        logger.info("Test quit by user via debug interface")
                        break  # Exit the loop
                    except Exception as e:
                        # Mark step as failed if it exists
                        step_obj = None
                        if 'step' in locals() and isinstance(step, TestStep):
                            step_obj = step
                            step_obj.fail_with_error(e)
                            test_steps.append(step_obj)
                        
                        # Provide helpful error message
                        step_str = str(step_dict)[:100]
                        error_msg = str(e)
                        
                        # Log structured error
                        logger.error(
                            f"Step {i} failed",
                            extra={
                                "step_number": i,
                                "step_action": step_str,
                                "error_type": type(e).__name__,
                                "error_message": error_msg,
                                "test_name": getattr(test, 'test_name', 'unknown')
                            }
                        )
                        
                        print(f"    ❌ Erro no passo {i}: {error_msg}")
                        
                        # Save HTML content of the page (more useful for debugging than screenshots)
                        try:
                            debug_html = test.screenshot_manager.test_dir / f"debug_error_step_{i}.html"
                            debug_html.parent.mkdir(parents=True, exist_ok=True)
                            html_content = await test.page.content()
                            debug_html.write_text(html_content, encoding='utf-8')
                            print(f"    📄 HTML da página de erro salvo: {debug_html}")
                            
                            logger.error(
                                f"Error HTML captured for step {i}",
                                extra={
                                    "step_number": i,
                                    "html_path": str(debug_html),
                                    "error_type": type(e).__name__
                                }
                            )
                        except Exception as html_error:
                            logger.warning(f"Failed to capture error HTML: {html_error}")
                            print(f"    ⚠️  Erro ao capturar HTML: {html_error}")
                        
                        # Try to capture page state info for debugging
                        try:
                            current_url = test.page.url
                            page_title = await test.page.title()
                            logger.error(
                                f"Page state at error",
                                extra={
                                    "step_number": i,
                                    "url": current_url,
                                    "title": page_title
                                }
                            )
                        except Exception:
                            pass
                        
                        raise RuntimeError(
                            f"Erro ao executar passo {i}: {step_str}\n"
                            f"Erro: {error_msg}"
                        ) from e
            finally:
                # Execute teardown steps (always, even on error)
                if teardown_steps:
                    for step in teardown_steps:
                        try:
                            action_func = ActionParser.parse_odoo_action(step, test, None)
                            await action_func()
                        except Exception as e:
                            # Log but don't fail on teardown errors
                            print(f"  ⚠️  Teardown step failed: {e}")
        
        # Set function attributes for session management
        test_function.save_session = save_session if save_session else None
        test_function.load_session = load_session if load_session else None
        
        return test_function

    @staticmethod
    def parse_file(yaml_path: Path) -> Dict[str, Any]:
        """
        Parse YAML test file with support for inheritance and composition.
        
        This method uses the core YAMLResolver to parse files, replacing
        the old YAMLParser dependency.
        """
        return parse_yaml_file(yaml_path)

