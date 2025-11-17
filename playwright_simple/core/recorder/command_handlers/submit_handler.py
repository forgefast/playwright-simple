#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Submit handler for Playwright commands.
"""

import logging
from typing import Dict, Any

from .base_handler import BaseHandler
from ..action_converter import ActionConverter
from ..action_state_capture import ActionStateCapture
from ..page_stability import wait_for_navigation_after_click

logger = logging.getLogger(__name__)


class SubmitHandler(BaseHandler):
    """Handles submit commands."""
    
    async def handle_submit(self, args: str) -> Dict[str, Any]:
        """Handle submit command."""
        result = {
            'success': False,
            'element_found': False,
            'action_worked': False,
            'state_before': {},
            'state_after': {},
            'changes': {},
            'error': None,
            'warnings': []
        }
        
        page = self._get_page()
        if not page:
            result['error'] = "Page not available"
            return result
        
        action_id = f"submit_{args}"
        if self.recorder_logger:
            self.recorder_logger.start_action_timer(action_id)
        
        state_before = await ActionStateCapture.capture_state(page)
        result['state_before'] = state_before
        
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_before.get('url', ''),
                'title': state_before.get('title', ''),
                'element_count': state_before.get('element_count', 0)
            })
        
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            result['error'] = "CursorController not available"
            return result
        
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Garantir que cursor esteja visível antes de executar ação
        await cursor_controller.show()
        
        button_text = args.strip().strip('"\'') if args.strip() else None
        
        # Get submit element info
        submit_element_info = None
        try:
            if button_text:
                submit_element_info = await page.evaluate("""
                    (buttonText) => {
                        const textLower = buttonText.toLowerCase();
                        const submitSelectors = ['input[type="submit"]', 'button[type="submit"]', 'button:not([type])'];
                        for (const selector of submitSelectors) {
                            const elements = Array.from(document.querySelectorAll(selector));
                            for (const el of elements) {
                                if (el.offsetParent === null || el.style.display === 'none') continue;
                                const elText = (el.textContent || el.innerText || el.value || '').trim().toLowerCase();
                                if (elText === textLower || elText.includes(textLower)) {
                                    const isSubmit = el.type === 'submit' || 
                                                    (el.tagName?.toUpperCase() === 'BUTTON' && 
                                                     (el.type === 'submit' || el.type === ''));
                                    if (isSubmit) {
                                        return {
                                            tagName: el.tagName || '',
                                            text: (el.textContent || el.innerText || el.value || '').trim(),
                                            id: el.id || '',
                                            type: el.type || 'submit',
                                            name: el.name || ''
                                        };
                                    }
                                }
                            }
                        }
                        return null;
                    }
                """, button_text)
            else:
                submit_element_info = await page.evaluate("""
                    () => {
                        const submitSelectors = ['input[type="submit"]', 'button[type="submit"]'];
                        for (const selector of submitSelectors) {
                            const el = document.querySelector(selector);
                            if (el && el.offsetParent !== null && el.style.display !== 'none') {
                                return {
                                    tagName: el.tagName || '',
                                    text: (el.textContent || el.innerText || el.value || '').trim(),
                                    id: el.id || '',
                                    type: el.type || 'submit',
                                    name: el.name || ''
                                };
                            }
                        }
                        return null;
                    }
                """)
        except Exception as e:
            logger.debug(f"Error getting submit element info: {e}")
        
        # Finalize pending inputs
        if self.yaml_writer and hasattr(self._recorder, 'action_converter'):
            pending_inputs = self._recorder.action_converter.pending_inputs
            if pending_inputs:
                for element_key in list(pending_inputs.keys()):
                    action = self._recorder.action_converter.finalize_input(element_key)
                    if action:
                        self.yaml_writer.add_step(action)
        
        # Add submit step to YAML
        if submit_element_info and self.yaml_writer:
            try:
                is_in_form = await page.evaluate("""
                    (buttonText) => {
                        const textLower = buttonText ? buttonText.toLowerCase() : '';
                        const submitSelectors = ['input[type="submit"]', 'button[type="submit"]', 'button:not([type])'];
                        for (const selector of submitSelectors) {
                            const elements = Array.from(document.querySelectorAll(selector));
                            for (const el of elements) {
                                if (el.offsetParent === null || el.style.display === 'none') continue;
                                const elText = (el.textContent || el.innerText || el.value || '').trim().toLowerCase();
                                if (!buttonText || elText === textLower || elText.includes(textLower)) {
                                    let parent = el.parentElement;
                                    while (parent && parent !== document.body) {
                                        if (parent.tagName && parent.tagName.toUpperCase() === 'FORM') {
                                            return true;
                                        }
                                        parent = parent.parentElement;
                                    }
                                    return false;
                                }
                            }
                        }
                        return false;
                    }
                """, button_text)
                submit_element_info['isInForm'] = is_in_form
            except:
                submit_element_info['isInForm'] = False
            
            converter = ActionConverter()
            event_data = {'element': submit_element_info}
            action = converter.convert_click(event_data)
            
            if action and action.get('action') == 'submit':
                self.yaml_writer.add_step(action)
        
        result['element_found'] = submit_element_info is not None
        
        if not result['element_found']:
            result['error'] = "Submit button not found"
            return result
        
        # Capture URL before submit to detect navigation
        url_before_submit = page.url
        
        submit_success = await cursor_controller.submit_form(button_text)
        
        if not submit_success:
            result['error'] = "Failed to submit form"
            return result
        
        # Wait for navigation if submit caused one (form submission often navigates)
        logger.info(f"[SUBMIT_HANDLER] Before wait_for_navigation_after_click - URL: {url_before_submit}")
        navigation_occurred = await wait_for_navigation_after_click(page, url_before_submit, timeout=5.0)
        logger.info(f"[SUBMIT_HANDLER] After wait_for_navigation_after_click - Navigation occurred: {navigation_occurred}, Current URL: {page.url}")
        
        # Wait for page to stabilize
        logger.info(f"[SUBMIT_HANDLER] Calling _wait_for_page_stable...")
        await self._wait_for_page_stable(timeout=5.0)
        logger.info(f"[SUBMIT_HANDLER] _wait_for_page_stable completed")
        
        state_after = await ActionStateCapture.capture_state(page)
        result['state_after'] = state_after
        
        changes = ActionStateCapture.compare_states(state_before, state_after)
        result['changes'] = changes
        
        validation = ActionStateCapture.validate_expected_changes('submit', state_before, state_after)
        result['action_worked'] = validation['action_worked']
        result['success'] = result['element_found'] and result['action_worked']
        
        duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
        
        element_info = {
            'button_text': button_text,
            'tag': submit_element_info.get('tagName') if submit_element_info else None
        }
        
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_after.get('url', ''),
                'title': state_after.get('title', ''),
                'element_count': state_after.get('element_count', 0),
                'html_hash': state_after.get('html_hash'),
                'network_idle': state_after.get('network_idle', False)
            })
            
            warnings = []
            if result['element_found'] and not result['action_worked']:
                warnings.append("Submit button found but form may not have submitted")
            
            if result['success']:
                self.recorder_logger.log_user_action(
                    action_type='submit',
                    element_info=element_info,
                    success=True,
                    duration_ms=duration_ms,
                    page_state=state_after,
                    details={'url_changed': changes.get('url_changed'), 'html_changed': changes.get('html_changed')}
                )
            else:
                level = 'CRITICAL' if not result['element_found'] else 'WARNING'
                if level == 'CRITICAL':
                    self.recorder_logger.log_critical_failure(
                        action='pw-submit',
                        error=result.get('error', 'Action failed'),
                        element_info=element_info,
                        page_state=state_before
                    )
                else:
                    self.recorder_logger.log_user_action(
                        action_type='submit',
                        element_info=element_info,
                        success=False,
                        duration_ms=duration_ms,
                        error=result.get('error'),
                        warnings=warnings,
                        page_state=state_after
                    )
        
        return result

