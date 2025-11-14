#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core action mappings for YAML parser.

Maps YAML action names to SimpleTestBase methods.
"""

import logging
from typing import Dict, Any, Callable

from .base import SimpleTestBase

logger = logging.getLogger(__name__)


class ActionMapper:
    """Maps YAML actions to test methods."""
    
    @staticmethod
    def get_core_actions(step: Dict[str, Any], test: SimpleTestBase) -> Dict[str, Callable]:
        """
        Get dictionary of core actions mapped to test methods.
        
        Args:
            step: Step dictionary
            test: Test base instance
            
        Returns:
            Dictionary mapping action names to callable functions
        """
        logger.debug(f"Obtendo ações core para step: {step}")
        actions = {
            'go_to': lambda: test.go_to(step.get('url', '/')),
            'click': lambda: test.click(
                step.get('text') or step.get('selector', ''),
                step.get('description', '')
            ),
            'type': lambda: test.type(
                step.get('text', ''),
                step.get('selector'),  # Optional
                step.get('description', '')
            ),
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
            'wait': lambda: test.wait(step.get('seconds', 1.0)),
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
            'submit': lambda: test.submit(
                step.get('button_text') or step.get('text'),
                step.get('description', '')
            ),
            'screenshot': lambda: test.screenshot(
                step.get('name'),
                step.get('full_page'),
                step.get('element')
            ),
        }
        logger.debug(f"Ações core mapeadas: {list(actions.keys())}")
        return actions
    
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

