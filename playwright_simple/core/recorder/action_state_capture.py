#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Action State Capture module.

Captures and compares page state before/after actions to validate if actions worked.
"""

import hashlib
import logging
from typing import Dict, Any, Optional, List
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class ActionStateCapture:
    """Captures and compares page state for action validation."""
    
    @staticmethod
    async def capture_state(page: Page) -> Dict[str, Any]:
        """
        Capture current page state.
        
        Args:
            page: Playwright Page instance
            
        Returns:
            Dictionary with state information:
            - url: Current page URL
            - title: Page title
            - html_hash: Hash of page HTML (for quick comparison)
            - visible_elements: List of visible interactive elements
            - load_state: Current load state
        """
        state = {}
        try:
            state['url'] = page.url
            state['title'] = await page.title()
            
            # Get HTML hash for quick comparison
            try:
                html_content = await page.content()
                state['html_hash'] = hashlib.md5(html_content.encode()).hexdigest()[:16]
            except:
                state['html_hash'] = None
            
            # Get visible interactive elements (buttons, links, inputs)
            try:
                visible_elements = await page.evaluate("""
                    () => {
                        const elements = [];
                        const selectors = [
                            'button:visible',
                            'a:visible',
                            'input:visible',
                            '[role="button"]:visible',
                            '[onclick]:visible'
                        ];
                        
                        selectors.forEach(selector => {
                            document.querySelectorAll(selector).forEach(el => {
                                const text = (el.textContent || el.innerText || el.value || '').trim();
                                if (text) {
                                    elements.push({
                                        tag: el.tagName.toLowerCase(),
                                        text: text.substring(0, 50),
                                        id: el.id || '',
                                        className: el.className || ''
                                    });
                                }
                            });
                        });
                        
                        return elements;
                    }
                """)
                state['visible_elements'] = visible_elements
                state['element_count'] = len(visible_elements)
            except Exception as e:
                logger.debug(f"Error capturing visible elements: {e}")
                state['visible_elements'] = []
                state['element_count'] = 0
            
            # Get load state
            try:
                load_state = await page.evaluate("document.readyState")
                state['load_state'] = load_state
            except:
                state['load_state'] = 'unknown'
                
        except Exception as e:
            logger.error(f"Error capturing state: {e}")
            state['error'] = str(e)
        
        return state
    
    @staticmethod
    def compare_states(state_before: Dict[str, Any], state_after: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two states and return detected changes.
        
        Args:
            state_before: State before action
            state_after: State after action
            
        Returns:
            Dictionary with detected changes:
            - url_changed: Whether URL changed
            - title_changed: Whether title changed
            - html_changed: Whether HTML hash changed
            - element_count_changed: Whether number of elements changed
            - new_elements: Elements that appeared
            - removed_elements: Elements that disappeared
        """
        changes = {
            'url_changed': False,
            'title_changed': False,
            'html_changed': False,
            'element_count_changed': False,
            'new_elements': [],
            'removed_elements': []
        }
        
        try:
            # Compare URL
            url_before = state_before.get('url', '')
            url_after = state_after.get('url', '')
            changes['url_changed'] = url_before != url_after
            if changes['url_changed']:
                changes['url_before'] = url_before
                changes['url_after'] = url_after
            
            # Compare title
            title_before = state_before.get('title', '')
            title_after = state_after.get('title', '')
            changes['title_changed'] = title_before != title_after
            if changes['title_changed']:
                changes['title_before'] = title_before
                changes['title_after'] = title_after
            
            # Compare HTML hash
            html_before = state_before.get('html_hash')
            html_after = state_after.get('html_hash')
            if html_before and html_after:
                changes['html_changed'] = html_before != html_after
            
            # Compare element count
            count_before = state_before.get('element_count', 0)
            count_after = state_after.get('element_count', 0)
            changes['element_count_changed'] = count_before != count_after
            
            # Find new and removed elements
            elements_before = {e.get('text', '') for e in state_before.get('visible_elements', [])}
            elements_after = {e.get('text', '') for e in state_after.get('visible_elements', [])}
            
            changes['new_elements'] = list(elements_after - elements_before)
            changes['removed_elements'] = list(elements_before - elements_after)
            
        except Exception as e:
            logger.error(f"Error comparing states: {e}")
            changes['error'] = str(e)
        
        return changes
    
    @staticmethod
    def validate_expected_changes(
        action_type: str,
        state_before: Dict[str, Any],
        state_after: Dict[str, Any],
        expected_changes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate if expected changes occurred after an action.
        
        Args:
            action_type: Type of action ('click', 'type', 'submit')
            state_before: State before action
            state_after: State after action
            expected_changes: Optional dict with expected changes
            
        Returns:
            Dictionary with validation result:
            - action_worked: Whether action actually worked
            - expected_changes_met: Whether expected changes occurred
            - validation_details: Details about what was validated
        """
        changes = ActionStateCapture.compare_states(state_before, state_after)
        
        validation = {
            'action_worked': False,
            'expected_changes_met': False,
            'validation_details': {}
        }
        
        try:
            if action_type == 'click':
                # For click, action worked if:
                # - URL changed, OR
                # - HTML changed (DOM updated), OR
                # - Elements changed (new elements appeared or old disappeared)
                validation['action_worked'] = (
                    changes.get('url_changed', False) or
                    changes.get('html_changed', False) or
                    changes.get('element_count_changed', False) or
                    len(changes.get('new_elements', [])) > 0 or
                    len(changes.get('removed_elements', [])) > 0
                )
                validation['validation_details'] = {
                    'url_changed': changes.get('url_changed', False),
                    'html_changed': changes.get('html_changed', False),
                    'elements_changed': changes.get('element_count_changed', False)
                }
                
            elif action_type == 'type':
                # For type, we validate separately by checking field value
                # This is handled in the handler itself
                validation['action_worked'] = True  # Will be overridden by handler
                validation['validation_details'] = {'type_validation': 'handled_in_handler'}
                
            elif action_type == 'submit':
                # For submit, action worked if:
                # - URL changed (navigation occurred), OR
                # - HTML changed significantly (form disappeared, new content appeared)
                validation['action_worked'] = (
                    changes.get('url_changed', False) or
                    changes.get('html_changed', False) or
                    len(changes.get('removed_elements', [])) > 3  # Form elements disappeared
                )
                validation['validation_details'] = {
                    'url_changed': changes.get('url_changed', False),
                    'html_changed': changes.get('html_changed', False),
                    'form_elements_removed': len(changes.get('removed_elements', []))
                }
            
            # Check if expected changes were met
            if expected_changes:
                validation['expected_changes_met'] = all(
                    changes.get(key) == value
                    for key, value in expected_changes.items()
                )
            else:
                validation['expected_changes_met'] = validation['action_worked']
                
        except Exception as e:
            logger.error(f"Error validating expected changes: {e}")
            validation['error'] = str(e)
        
        return validation

