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
        """Get or create PlaywrightCommands instance for the test."""
        logger.debug(f"_get_playwright_commands: PLAYWRIGHT_COMMANDS_AVAILABLE={PLAYWRIGHT_COMMANDS_AVAILABLE}")
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            logger.warning("PlaywrightCommands não disponível (PLAYWRIGHT_COMMANDS_AVAILABLE=False)")
            return None
        
        # Check if test has page
        if not hasattr(test, 'page') or test.page is None:
            logger.warning("Test não tem page disponível")
            return None
        
        # Check if test already has a PlaywrightCommands instance
        if hasattr(test, '_playwright_commands'):
            logger.debug("Reutilizando instância existente de PlaywrightCommands")
            return test._playwright_commands
        
        # Create new instance
        fast_mode = getattr(test.config.step, 'fast_mode', False) if hasattr(test, 'config') else False
        logger.debug(f"Criando nova instância de PlaywrightCommands (fast_mode={fast_mode})")
        try:
            commands = PlaywrightCommands(test.page, fast_mode=fast_mode)
            test._playwright_commands = commands  # Cache for reuse
            logger.debug("PlaywrightCommands criado com sucesso")
            return commands
        except Exception as e:
            logger.error(f"Erro ao criar PlaywrightCommands: {e}", exc_info=True)
            return None
    
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
        """Execute click action using PlaywrightCommands (same code as recording)."""
        text = step.get('text')
        selector = step.get('selector')
        description = step.get('description', '')
        
        logger.debug(f"[ACTION] Executando click: text='{text}', selector='{selector}', description='{description}'")
        print(f"🔍 [ACTION] Executando click: text='{text}', selector='{selector}'")
        
        if commands:
            # Use PlaywrightCommands (same code as recording)
            logger.debug(f"[ACTION] PlaywrightCommands disponível, executando click...")
            print(f"🔍 [ACTION] PlaywrightCommands disponível, executando click...")
            try:
                # Get cursor_controller from test if available (for visual feedback)
                # Same logic as in command_server and command_handlers
                cursor_controller = None
                if hasattr(test, 'cursor_manager') and hasattr(test.cursor_manager, 'controller'):
                    cursor_controller = test.cursor_manager.controller
                
                # Parse index if needed (same as command_server)
                index = 0
                if text and '[' in text and ']' in text:
                    try:
                        index_part = text[text.index('[')+1:text.index(']')]
                        index = int(index_part)
                        text = text[:text.index('[')].strip()
                    except:
                        pass
                
                if text:
                    logger.debug(f"[ACTION] Chamando commands.click(text='{text}', index={index})...")
                    print(f"🔍 [ACTION] Chamando commands.click(text='{text}', index={index})...")
                    success = await commands.click(text=text, index=index, cursor_controller=cursor_controller, description=description)
                    logger.debug(f"[ACTION] commands.click retornou: {success}")
                    print(f"🔍 [ACTION] commands.click retornou: {success}")
                elif selector:
                    logger.debug(f"[ACTION] Chamando commands.click(selector='{selector}')...")
                    print(f"🔍 [ACTION] Chamando commands.click(selector='{selector}')...")
                    success = await commands.click(selector=selector, cursor_controller=cursor_controller, description=description)
                    logger.debug(f"[ACTION] commands.click retornou: {success}")
                    print(f"🔍 [ACTION] commands.click retornou: {success}")
                else:
                    raise ValueError("Click action requires either 'text' or 'selector'")
                
                if not success:
                    error_msg = f"Failed to click: {description or text or selector}"
                    logger.error(f"[ACTION] {error_msg}")
                    print(f"❌ [ACTION] {error_msg}")
                    raise Exception(error_msg)
                else:
                    logger.debug(f"[ACTION] Click executado com sucesso!")
                    print(f"✅ [ACTION] Click executado com sucesso!")
            except Exception as e:
                logger.error(f"[ACTION] Erro ao executar click: {e}", exc_info=True)
                print(f"❌ [ACTION] Erro ao executar click: {e}")
                raise
        else:
            # Fallback to SimpleTestBase if PlaywrightCommands not available
            logger.warning("PlaywrightCommands not available, using SimpleTestBase.click")
            print("⚠️  [ACTION] PlaywrightCommands não disponível, usando SimpleTestBase.click")
            await test.click(
                text or selector or '',
                description
            )
    
    @staticmethod
    async def _execute_type(step: Dict[str, Any], test: SimpleTestBase, commands: Optional['PlaywrightCommands']) -> None:
        """Execute type action using PlaywrightCommands (same code as recording)."""
        text = step.get('text', '')
        selector = step.get('selector')
        description = step.get('description', '')
        
        logger.debug(f"[ACTION] Executando type: text='{text}', selector='{selector}'")
        
        if commands:
            # Use PlaywrightCommands (same code as recording)
            if selector:
                success = await commands.type_text(text, selector=selector)
            else:
                # Try to find field by common patterns (email, password, etc)
                success = await commands.type_text(text, into=description or 'input')
            
            if not success:
                raise Exception(f"Failed to type '{text}' into {description or selector or 'field'}")
        else:
            # Fallback to SimpleTestBase if PlaywrightCommands not available
            logger.warning("PlaywrightCommands not available, using SimpleTestBase.type")
            await test.type(
                selector or '',
                text,
                description
            )
    
    @staticmethod
    async def _execute_submit(step: Dict[str, Any], test: SimpleTestBase, commands: Optional['PlaywrightCommands']) -> None:
        """Execute submit action using PlaywrightCommands (same code as recording)."""
        button_text = step.get('button_text') or step.get('text')
        description = step.get('description', '')
        
        logger.debug(f"[ACTION] Executando submit: button_text='{button_text}'")
        
        if commands:
            # Use PlaywrightCommands (same code as recording)
            success = await commands.submit_form(button_text=button_text)
            if not success:
                raise Exception(f"Failed to submit form: {description or button_text or 'form'}")
        else:
            # Fallback to SimpleTestBase if PlaywrightCommands not available
            logger.warning("PlaywrightCommands not available, using SimpleTestBase.submit")
            await test.submit(button_text, description)
    
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

