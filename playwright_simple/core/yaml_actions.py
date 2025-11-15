#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core action mappings for YAML parser.

Maps YAML action names to test methods.
Uses PlaywrightCommands for click, type, submit to reuse the same code from recording.
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Optional

from .base import SimpleTestBase

logger = logging.getLogger(__name__)

# Try to import PlaywrightCommands
try:
    from .playwright_commands import PlaywrightCommands
    PLAYWRIGHT_COMMANDS_AVAILABLE = True
    logger.debug("PlaywrightCommands importado com sucesso")
except ImportError as e:
    PlaywrightCommands = None
    PLAYWRIGHT_COMMANDS_AVAILABLE = False
    logger.warning(f"PlaywrightCommands não disponível: {e}")


class ActionMapper:
    """Maps YAML actions to test methods."""
    
    @staticmethod
    def _get_playwright_commands(test: SimpleTestBase) -> Optional['PlaywrightCommands']:
        """Get or create PlaywrightCommands instance using unified function."""
        from .playwright_commands.unified import get_playwright_commands
        
        if not hasattr(test, 'page') or test.page is None:
            logger.warning("Test não tem page disponível")
            return None
        
        # Get fast_mode from test config
        fast_mode = False
        if hasattr(test, 'config') and hasattr(test.config, 'step'):
            fast_mode = getattr(test.config.step, 'fast_mode', False)
        
        # Initialize cache if not exists
        if not hasattr(test, '_playwright_commands_cache'):
            test._playwright_commands_cache = {}
        
        # Use unified function
        commands = get_playwright_commands(
            page=test.page,
            fast_mode=fast_mode,
            cache_key=test,
            cache=test._playwright_commands_cache
        )
        
        logger.debug(f"_get_playwright_commands retornou: {commands is not None}")
        return commands
    
    @staticmethod
    def get_core_actions(step: Dict[str, Any], test: SimpleTestBase) -> Dict[str, Callable]:
        """
        Get dictionary of core actions mapped to test methods.
        
        Uses PlaywrightCommands for click, type, submit to reuse recording code.
        
        Args:
            step: Step dictionary
            test: Test base instance
            
        Returns:
            Dictionary mapping action names to callable functions
        """
        logger.debug(f"Obtendo ações core para step: {step}")
        
        # Get PlaywrightCommands instance (reuses recording code)
        commands = ActionMapper._get_playwright_commands(test)
        
        actions = {
            'go_to': lambda: test.go_to(step.get('url', '/')),
            'click': lambda: ActionMapper._execute_click(step, test, commands),
            'type': lambda: ActionMapper._execute_type(step, test, commands),
            'select': lambda: test.select(
                step.get('selector', ''),
                step.get('option', ''),
                step.get('description', '')
            ),
            'hover': lambda: test.hover(
                step.get('text') or step.get('selector', ''),
                step.get('description', '')
            ),
            'drag': lambda: test.drag(
                step.get('source', ''),
                step.get('target', ''),
                step.get('description', '')
            ),
            'scroll': lambda: test.scroll(
                step.get('selector'),
                step.get('direction', 'down'),
                step.get('amount', 500)
            ),
            'wait': lambda: ActionMapper._execute_wait(step, test),
            'press': lambda: test.press(step.get('key', 'Enter'), step.get('description', '')),
            'keypress': lambda: test.keypress(step.get('key', 'Enter'), step.get('description', '')),
            'keydown': lambda: test.keydown(step.get('key', ''), step.get('description', '')),
            'keyup': lambda: test.keyup(step.get('key', ''), step.get('description', '')),
            'insert_text': lambda: test.insert_text(step.get('text', ''), step.get('description', '')),
            'focus': lambda: test.focus(
                step.get('text') or step.get('selector', ''),
                step.get('description', '')
            ),
            'blur': lambda: test.blur(
                step.get('text') or step.get('selector', ''),
                step.get('description', '')
            ),
            'double_click': lambda: test.double_click(
                step.get('text') or step.get('selector', ''),
                step.get('description', '')
            ),
            'right_click': lambda: test.right_click(
                step.get('text') or step.get('selector', ''),
                step.get('description', '')
            ),
            'middle_click': lambda: test.middle_click(
                step.get('text') or step.get('selector', ''),
                step.get('description', '')
            ),
            'select_all': lambda: test.select_all(step.get('description', '')),
            'copy': lambda: test.copy(step.get('description', '')),
            'paste': lambda: test.paste(step.get('description', '')),
            'clear': lambda: test.clear(
                step.get('text') or step.get('selector', ''),
                step.get('description', '')
            ),
            'wait_for': lambda: test.wait_for(
                step.get('selector', ''),
                step.get('state', 'visible'),
                step.get('timeout'),
                step.get('description', '')
            ),
            'wait_for_url': lambda: test.wait_for_url(
                step.get('url_pattern', ''),
                step.get('timeout')
            ),
            'wait_for_text': lambda: test.wait_for_text(
                step.get('selector', ''),
                step.get('text', ''),
                step.get('timeout'),
                step.get('description', '')
            ),
            'assert_text': lambda: test.assert_text(
                step.get('selector', ''),
                step.get('expected', ''),
                step.get('description', '')
            ),
            'assert_visible': lambda: test.assert_visible(
                step.get('selector', ''),
                step.get('description', '')
            ),
            'assert_url': lambda: test.assert_url(step.get('pattern', '')),
            'assert_count': lambda: test.assert_count(
                step.get('selector', ''),
                step.get('expected_count', 0),
                step.get('description', '')
            ),
            'assert_attr': lambda: test.assert_attr(
                step.get('selector', ''),
                step.get('attribute', ''),
                step.get('expected', ''),
                step.get('description', '')
            ),
            'fill_form': lambda: test.fill_form(step.get('fields', {})),
            'submit': lambda: ActionMapper._execute_submit(step, test, commands),
            'screenshot': lambda: test.screenshot(
                step.get('name'),
                step.get('full_page'),
                step.get('element')
            ),
        }
        logger.debug(f"Ações core mapeadas: {list(actions.keys())}")
        return actions
    
    @staticmethod
    async def _execute_click(step: Dict[str, Any], test: SimpleTestBase, commands: Optional['PlaywrightCommands']) -> None:
        """Execute click action using CursorController (same code as recording)."""
        text = step.get('text')
        selector = step.get('selector')
        role = step.get('role')
        index = step.get('index', 0)
        description = step.get('description', '')
        
        logger.info(f"[DEBUG] [ACTION] ===== INÍCIO _execute_click =====")
        logger.info(f"[DEBUG] [ACTION] Executando click: text='{text}', selector='{selector}', role='{role}', description='{description}'")
        
        if not test.page:
            raise ValueError("Page not available for click action")
        
        # Get CursorController from test
        cursor_controller = test._get_cursor_controller()
        if not cursor_controller:
            raise ValueError("CursorController not available for click action")
        
        logger.info(f"[DEBUG] [ACTION] CursorController obtido: is_active={cursor_controller.is_active}")
        
        # Ensure cursor controller is started and visible
        if not cursor_controller.is_active:
            logger.info(f"[DEBUG] [ACTION] Iniciando CursorController...")
            await cursor_controller.start()
        logger.info(f"[DEBUG] [ACTION] Mostrando cursor...")
        await cursor_controller.show()  # Ensure cursor is visible
        
        # Wait for page to be ready
        try:
            logger.info(f"[DEBUG] [ACTION] Aguardando domcontentloaded...")
            await test.page.wait_for_load_state('domcontentloaded', timeout=2000)
            logger.info(f"[DEBUG] [ACTION] domcontentloaded OK")
        except Exception as e:
            logger.info(f"[DEBUG] [ACTION] domcontentloaded timeout (normal): {e}")
        
        # Capture URL BEFORE click to detect navigation
        url_before = test.page.url
        logger.info(f"[DEBUG] [ACTION] URL ANTES do clique: {url_before}")
        
        try:
            # Execute click using CursorController
            logger.info(f"[DEBUG] [ACTION] Executando clique via CursorController...")
            success = False
            if text:
                logger.info(f"[DEBUG] [ACTION] Chamando click_by_text('{text}')...")
                success = await cursor_controller.click_by_text(text)
                logger.info(f"[DEBUG] [ACTION] click_by_text retornou: {success}")
            elif selector:
                logger.info(f"[DEBUG] [ACTION] Chamando click_by_selector('{selector}')...")
                success = await cursor_controller.click_by_selector(selector)
                logger.info(f"[DEBUG] [ACTION] click_by_selector retornou: {success}")
            elif role:
                logger.info(f"[DEBUG] [ACTION] Chamando click_by_role('{role}', {index})...")
                success = await cursor_controller.click_by_role(role, index)
                logger.info(f"[DEBUG] [ACTION] click_by_role retornou: {success}")
            else:
                raise ValueError("Click action requires 'text', 'selector', or 'role'")
            
            if not success:
                error_msg = f"Failed to click: {description or text or selector or role}"
                logger.error(f"[DEBUG] [ACTION] {error_msg}")
                raise Exception(error_msg)
            
            logger.info(f"[DEBUG] [ACTION] Clique executado com sucesso! Aguardando navegação...")
            
            # Wait for navigation after click (using same logic as EventCapture._handle_navigation)
            logger.info(f"[DEBUG] [ACTION] Chamando wait_for_navigation_after_action(timeout=5.0)...")
            navigation_occurred = await cursor_controller.wait_for_navigation_after_action(timeout=5.0)
            logger.info(f"[DEBUG] [ACTION] wait_for_navigation_after_action retornou: {navigation_occurred}")
            
            # Check URL after click (even if no event was detected)
            logger.info(f"[DEBUG] [ACTION] Aguardando 0.2s para URL atualizar...")
            await asyncio.sleep(0.2)  # Small delay to allow URL to update
            url_after = test.page.url
            logger.info(f"[DEBUG] [ACTION] URL APÓS clique: {url_after}")
            logger.info(f"[DEBUG] [ACTION] URL mudou? {url_before != url_after}, navigation_occurred={navigation_occurred}")
            
            # Check if navigation occurred (either event fired or URL changed)
            if url_before != url_after or navigation_occurred:
                # Navigation happened, wait for it to complete (additional wait for networkidle)
                logger.info(f"[DEBUG] [ACTION] ✓ Navegação detectada: {url_before} -> {url_after} (event={navigation_occurred})")
                try:
                    logger.info(f"[DEBUG] [ACTION] Aguardando networkidle (timeout=15s)...")
                    # Wait for navigation to complete
                    await test.page.wait_for_load_state('networkidle', timeout=15000)
                    logger.info(f"[DEBUG] [ACTION] ✓ networkidle completado")
                except Exception as e:
                    logger.warning(f"[DEBUG] [ACTION] ⚠ Timeout esperando networkidle: {e}")
                    # Fallback: wait for domcontentloaded
                    try:
                        logger.info(f"[DEBUG] [ACTION] Tentando domcontentloaded (timeout=8s)...")
                        await test.page.wait_for_load_state('domcontentloaded', timeout=8000)
                        logger.info(f"[DEBUG] [ACTION] ✓ domcontentloaded completado")
                    except Exception as e2:
                        logger.warning(f"[DEBUG] [ACTION] ⚠ Timeout esperando domcontentloaded: {e2}")
                        # Last resort: wait a bit and check if page is interactive
                        logger.info(f"[DEBUG] [ACTION] Último recurso: aguardando 2s...")
                        await asyncio.sleep(2)
                
                # Additional wait to ensure page is fully interactive (same as EventCapture does)
                logger.info(f"[DEBUG] [ACTION] Aguardando página estar totalmente interativa...")
                try:
                    # Wait for body to be ready and interactive
                    await test.page.wait_for_function(
                        "document.readyState === 'complete' && document.body !== null",
                        timeout=5000
                    )
                    logger.info(f"[DEBUG] [ACTION] ✓ Página totalmente interativa")
                except Exception as e:
                    logger.info(f"[DEBUG] [ACTION] ⚠ Timeout aguardando página interativa: {e}")
                    # Small delay as fallback
                    await asyncio.sleep(0.5)
            else:
                # No URL change, but might be SPA navigation or form submission
                # Wait a bit for any async operations
                logger.info(f"[DEBUG] [ACTION] Sem mudança de URL, aguardando operações assíncronas...")
                try:
                    # Wait for network to be idle (might be form submission, AJAX, etc.)
                    logger.info(f"[DEBUG] [ACTION] Aguardando networkidle (timeout=5s)...")
                    await test.page.wait_for_load_state('networkidle', timeout=5000)
                    logger.info(f"[DEBUG] [ACTION] ✓ Network idle após clique")
                except Exception as e:
                    logger.info(f"[DEBUG] [ACTION] Networkidle timeout (normal para alguns cliques): {e}")
                    # If networkidle times out, wait a bit for any async operations
                    logger.info(f"[DEBUG] [ACTION] Aguardando 0.5s...")
                    await asyncio.sleep(0.5)
            
            logger.info(f"[DEBUG] [ACTION] ===== FIM _execute_click (sucesso) =====")
        except Exception as e:
            logger.error(f"[DEBUG] [ACTION] ===== ERRO em _execute_click: {e} =====", exc_info=True)
            # Don't fail if wait fails - the click might have succeeded
            raise
    
    @staticmethod
    async def _execute_type(step: Dict[str, Any], test: SimpleTestBase, commands: Optional['PlaywrightCommands']) -> None:
        """Execute type action using CursorController (same code as recording)."""
        text = step.get('text', '')
        selector = step.get('selector')
        description = step.get('description', '')
        
        logger.debug(f"[ACTION] Executando type: text='{text}', selector='{selector}'")
        
        if not test.page:
            raise ValueError("Page not available for type action")
        
        if not text:
            raise ValueError("Text is required for type action")
        
        # Get CursorController from test
        cursor_controller = test._get_cursor_controller()
        if not cursor_controller:
            raise ValueError("CursorController not available for type action")
        
        # Ensure cursor controller is started and visible
        if not cursor_controller.is_active:
            await cursor_controller.start()
        await cursor_controller.show()  # Ensure cursor is visible
        
        # Determine field selector (use selector, description, or None for auto-detect)
        field_selector = selector or description or None
        
        # Execute type using CursorController
        success = await cursor_controller.type_text(text, field_selector)
        
        if not success:
            field = selector or description or 'field'
            raise Exception(f"Failed to type '{text}' into {field}")
    
    @staticmethod
    async def _execute_submit(step: Dict[str, Any], test: SimpleTestBase, commands: Optional['PlaywrightCommands']) -> None:
        """Execute submit action using CursorController (same code as recording)."""
        button_text = step.get('button_text') or step.get('text')
        description = step.get('description', '')
        
        logger.debug(f"[ACTION] Executando submit: button_text='{button_text}'")
        
        if not test.page:
            raise ValueError("Page not available for submit action")
        
        # Get CursorController from test
        cursor_controller = test._get_cursor_controller()
        if not cursor_controller:
            raise ValueError("CursorController not available for submit action")
        
        # Ensure cursor controller is started and visible
        if not cursor_controller.is_active:
            await cursor_controller.start()
        await cursor_controller.show()  # Ensure cursor is visible
        
        # Execute submit using CursorController
        success = await cursor_controller.submit_form(button_text)
        
        if not success:
            raise Exception(f"Failed to submit form: {description or button_text or 'form'}")
    
    @staticmethod
    async def _execute_wait(step: Dict[str, Any], test: SimpleTestBase) -> None:
        """Execute wait action, handling static waits based on fast_mode."""
        is_static = step.get('static', False)
        seconds = step.get('seconds')
        
        logger.debug(f"[ACTION] Executando wait: static={is_static}, seconds={seconds}")
        
        if is_static:
            # Static wait: duration determined by fast_mode configuration
            fast_mode = getattr(test.config.step, 'fast_mode', False) if hasattr(test, 'config') else False
            # Use static_min_duration from config, or default values
            if hasattr(test.config, 'step') and hasattr(test.config.step, 'static_min_duration'):
                duration = test.config.step.static_min_duration
            else:
                # Default: 0.1s in fast mode, 2.0s in normal mode
                duration = 0.1 if fast_mode else 2.0
            logger.debug(f"[ACTION] Wait estático: {duration}s (fast_mode={fast_mode})")
            await test.wait(duration)
        else:
            # Regular wait: use specified seconds or default
            wait_seconds = seconds if seconds is not None else 1.0
            logger.debug(f"[ACTION] Wait normal: {wait_seconds}s")
            await test.wait(wait_seconds)
    
    @staticmethod
    def is_deprecated(action: str) -> bool:
        """Check if action is deprecated."""
        return action in ['go_to', 'navigate']
    
    @staticmethod
    def get_deprecation_warning(action: str) -> str:
        """Get deprecation warning message for action."""
        warnings = {
            'go_to': "DEPRECATED: action 'go_to' será removido em versão futura. Use 'click' em links/menus para navegação.",
            'navigate': "DEPRECATED: action 'navigate' será removido em versão futura. Use múltiplos 'click' para navegar por menus.",
        }
        return warnings.get(action, '')

