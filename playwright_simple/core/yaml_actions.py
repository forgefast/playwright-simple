#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core action mappings for YAML parser.

Maps YAML action names to test methods.
Uses PlaywrightCommands for click, type, submit to reuse the same code from recording.
"""

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
        """Execute click action using unified function (same code as recording)."""
        from .playwright_commands.unified import unified_click, parse_click_args
        
        text = step.get('text')
        selector = step.get('selector')
        description = step.get('description', '')
        
        logger.debug(f"[ACTION] Executando click: text='{text}', selector='{selector}', description='{description}'")
        
        if not test.page:
            raise ValueError("Page not available for click action")
        
        # Get fast_mode from test config
        fast_mode = False
        if hasattr(test, 'config') and hasattr(test.config, 'step'):
            fast_mode = getattr(test.config.step, 'fast_mode', False)
        
        # Get cursor_manager from test if available (for visual feedback)
        # CursorManager can be used directly with visual_feedback (it has move_to method)
        cursor_controller = None
        if hasattr(test, 'cursor_manager') and test.cursor_manager:
            cursor_controller = test.cursor_manager
        
        # Build args string for unified parser (same format as CLI)
        args_str = ''
        if text:
            args_str = text
        elif selector:
            args_str = f'selector {selector}'
        else:
            raise ValueError("Click action requires either 'text' or 'selector'")
        
        # Parse arguments using unified parser
        parsed = parse_click_args(args_str)
        
        # Wait for page to be ready (same as before)
        try:
            await test.page.wait_for_load_state('domcontentloaded', timeout=2000)
        except:
            pass
        
        # Initialize cache if not exists
        if not hasattr(test, '_playwright_commands_cache'):
            test._playwright_commands_cache = {}
        
        # Debug: Check if element exists before clicking
        logger.debug(f"[ACTION] Verificando se elemento existe antes do click...")
        element_found = False
        try:
            if parsed['text']:
                # Try to find element by text
                result = await test.page.evaluate("""
                    (text) => {
                        const textLower = text.toLowerCase();
                        const elements = Array.from(document.querySelectorAll('*'));
                        for (const el of elements) {
                            if (el.offsetParent === null) continue;
                            const elText = (el.textContent || el.innerText || '').trim().toLowerCase();
                            if (elText.includes(textLower)) {
                                const rect = el.getBoundingClientRect();
                                return {
                                    found: true,
                                    tag: el.tagName,
                                    text: elText.substring(0, 50),
                                    visible: rect.width > 0 && rect.height > 0,
                                    x: rect.left,
                                    y: rect.top
                                };
                            }
                        }
                        return {found: false};
                    }
                """, parsed['text'])
                element_found = result.get('found', False)
                if element_found:
                    logger.debug(f"[ACTION] Elemento encontrado: {result}")
                    print(f"✅ [DIAGNÓSTICO] Elemento '{parsed['text']}' encontrado: {result.get('tag')} - visível={result.get('visible')}")
                else:
                    logger.warning(f"[ACTION] Elemento '{parsed['text']}' NÃO encontrado na página")
                    print(f"⚠️  [DIAGNÓSTICO] Elemento '{parsed['text']}' NÃO encontrado na página")
                    print(f"💡 [DIAGNÓSTICO] Use comandos CLI para investigar:")
                    print(f"   playwright-simple find \"{parsed['text']}\"")
                    print(f"   playwright-simple info")
                    print(f"   playwright-simple html --max-length 500")
            elif parsed['selector']:
                # Try to find element by selector
                try:
                    element = await test.page.query_selector(parsed['selector'])
                    if element:
                        box = await element.bounding_box()
                        element_found = True
                        logger.debug(f"[ACTION] Elemento encontrado por selector: {parsed['selector']}, box={box}")
                        print(f"✅ [DIAGNÓSTICO] Elemento '{parsed['selector']}' encontrado: visível={box is not None}")
                    else:
                        logger.warning(f"[ACTION] Elemento '{parsed['selector']}' NÃO encontrado na página")
                        print(f"⚠️  [DIAGNÓSTICO] Elemento '{parsed['selector']}' NÃO encontrado na página")
                except Exception as e:
                    logger.warning(f"[ACTION] Erro ao buscar elemento por selector: {e}")
                    print(f"⚠️  [DIAGNÓSTICO] Erro ao buscar '{parsed['selector']}': {e}")
        except Exception as e:
            logger.debug(f"[ACTION] Erro no diagnóstico: {e}")
        
        # Use unified click function
        success = await unified_click(
            page=test.page,
            text=parsed['text'],
            selector=parsed['selector'],
            role=parsed['role'],
            index=parsed['index'],
            cursor_controller=cursor_controller,
            fast_mode=fast_mode,
            description=description,
            cache_key=test,
            cache=test._playwright_commands_cache
        )
        
        if not success:
            error_msg = f"Failed to click: {description or text or selector}"
            logger.error(f"[ACTION] {error_msg}")
            print(f"❌ [DIAGNÓSTICO] Falha no click. Use comandos CLI para investigar:")
            print(f"   playwright-simple find \"{text or selector}\"")
            print(f"   playwright-simple info")
            raise Exception(error_msg)
    
    @staticmethod
    async def _execute_type(step: Dict[str, Any], test: SimpleTestBase, commands: Optional['PlaywrightCommands']) -> None:
        """Execute type action using unified function (same code as recording)."""
        from .playwright_commands.unified import unified_type, parse_type_args
        
        text = step.get('text', '')
        selector = step.get('selector')
        description = step.get('description', '')
        
        logger.debug(f"[ACTION] Executando type: text='{text}', selector='{selector}'")
        
        if not test.page:
            raise ValueError("Page not available for type action")
        
        if not text:
            raise ValueError("Text is required for type action")
        
        # Get fast_mode from test config
        fast_mode = False
        if hasattr(test, 'config') and hasattr(test.config, 'step'):
            fast_mode = getattr(test.config.step, 'fast_mode', False)
        
        # Get cursor_manager from test if available (for visual feedback)
        # CursorManager can be used directly with visual_feedback (it has move_to method)
        cursor_controller = None
        if hasattr(test, 'cursor_manager') and test.cursor_manager:
            cursor_controller = test.cursor_manager
        
        # Build args string for unified parser (same format as CLI)
        if selector:
            args_str = f'{text} into selector {selector}'
        elif description:
            args_str = f'{text} into {description}'
        else:
            # Try to find field by common patterns (email, password, etc)
            args_str = f'{text} into input'
        
        # Parse arguments using unified parser
        parsed = parse_type_args(args_str)
        
        # Initialize cache if not exists
        if not hasattr(test, '_playwright_commands_cache'):
            test._playwright_commands_cache = {}
        
        # Use unified type function
        success = await unified_type(
            page=test.page,
            text=parsed['text'],
            into=parsed['into'],
            selector=parsed['selector'],
            cursor_controller=cursor_controller,
            fast_mode=fast_mode,
            cache_key=test,
            cache=test._playwright_commands_cache
        )
        
        if not success:
            field = parsed['selector'] or parsed['into'] or description or 'field'
            raise Exception(f"Failed to type '{text}' into {field}")
    
    @staticmethod
    async def _execute_submit(step: Dict[str, Any], test: SimpleTestBase, commands: Optional['PlaywrightCommands']) -> None:
        """Execute submit action using unified function (same code as recording)."""
        from .playwright_commands.unified import unified_submit
        
        button_text = step.get('button_text') or step.get('text')
        description = step.get('description', '')
        
        logger.debug(f"[ACTION] Executando submit: button_text='{button_text}'")
        
        if not test.page:
            raise ValueError("Page not available for submit action")
        
        # Get fast_mode from test config
        fast_mode = False
        if hasattr(test, 'config') and hasattr(test.config, 'step'):
            fast_mode = getattr(test.config.step, 'fast_mode', False)
        
        # Get cursor_manager from test if available (for visual feedback)
        # CursorManager can be used directly with visual_feedback (it has move_to method)
        cursor_controller = None
        if hasattr(test, 'cursor_manager') and test.cursor_manager:
            cursor_controller = test.cursor_manager
        
        # Initialize cache if not exists
        if not hasattr(test, '_playwright_commands_cache'):
            test._playwright_commands_cache = {}
        
        # Use unified submit function
        success = await unified_submit(
            page=test.page,
            button_text=button_text,
            cursor_controller=cursor_controller,
            fast_mode=fast_mode,
            cache_key=test,
            cache=test._playwright_commands_cache
        )
        
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

