#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Type handler for Playwright commands.
"""

import asyncio
import logging
from typing import Dict, Any

from .base_handler import BaseHandler
from ...playwright_commands.unified import parse_type_args
from ..action_state_capture import ActionStateCapture

logger = logging.getLogger(__name__)


class TypeHandler(BaseHandler):
    """Handles type commands."""
    
    async def handle_type(self, args: str) -> Dict[str, Any]:
        """Handle type command."""
        result = {
            'success': False,
            'element_found': False,
            'action_worked': False,
            'state_before': {},
            'state_after': {},
            'changes': {},
            'error': None,
            'warnings': [],
            'field_value_before': None,
            'field_value_after': None
        }
        
        page = self._get_page()
        if not page:
            result['error'] = "Page not available"
            return result
        
        if not args:
            result['error'] = "No arguments provided"
            return result
        
        action_id = f"type_{args}"
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
        
        parsed = parse_type_args(args)
        
        if not parsed['text']:
            result['error'] = "No text specified"
            return result
        
        # Wait for page to be ready before looking for field
        try:
            await page.wait_for_load_state('domcontentloaded', timeout=5000)
        except:
            pass
        
        # Get field element info and value before
        field_element_info = None
        field_selector_for_value = None
        
        # Wait for field to appear if we're looking for it by label/name
        if parsed['into']:
            try:
                # Wait for input fields with matching label to be available
                await page.wait_for_function("""
                    (fieldText) => {
                        const textLower = fieldText.toLowerCase();
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        for (const input of inputs) {
                            if (input.offsetParent === null || input.style.display === 'none') continue;
                            if (input.type === 'hidden') continue;
                            const labels = input.labels || [];
                            for (const label of labels) {
                                const labelText = (label.textContent || '').trim().toLowerCase();
                                if (labelText === textLower || labelText.includes(textLower)) {
                                    return true;
                                }
                            }
                            if (input.placeholder && input.placeholder.toLowerCase().includes(textLower)) {
                                return true;
                            }
                        }
                        return false;
                    }
                """, parsed['into'], timeout=5000)
            except:
                pass  # Continue even if timeout - will try to find field anyway
        
        try:
            if parsed['selector']:
                # Wait for selector to be available
                try:
                    await page.wait_for_selector(parsed['selector'], state='visible', timeout=5000)
                except:
                    pass  # Continue even if timeout
                    
                field_element_info = await page.evaluate("""
                    (selector) => {
                        const el = document.querySelector(selector);
                        if (!el) return null;
                        return {
                            tagName: el.tagName || '',
                            text: (el.textContent || el.innerText || el.value || '').trim(),
                            id: el.id || '',
                            className: el.className || '',
                            type: el.type || '',
                            name: el.name || '',
                            value: el.value || '',
                            placeholder: el.placeholder || '',
                            label: (el.labels && el.labels.length > 0) 
                                ? (el.labels[0].textContent || '').trim() 
                                : ''
                        };
                    }
                """, parsed['selector'])
                field_selector_for_value = parsed['selector']
            elif parsed['into']:
                field_element_info = await page.evaluate("""
                    (fieldText) => {
                        const textLower = fieldText.toLowerCase();
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        for (const input of inputs) {
                            if (input.offsetParent === null || input.style.display === 'none') continue;
                            if (input.type === 'hidden') continue;
                            const labels = input.labels || [];
                            for (const label of labels) {
                                const labelText = (label.textContent || '').trim().toLowerCase();
                                if (labelText === textLower || labelText.includes(textLower)) {
                                    return {
                                        tagName: input.tagName || '',
                                        id: input.id || '',
                                        name: input.name || '',
                                        type: input.type || '',
                                        value: input.value || '',
                                        placeholder: input.placeholder || '',
                                        label: labelText
                                    };
                                }
                            }
                            if (input.placeholder && input.placeholder.toLowerCase().includes(textLower)) {
                                return {
                                    tagName: input.tagName || '',
                                    id: input.id || '',
                                    name: input.name || '',
                                    type: input.type || '',
                                    value: input.value || '',
                                    placeholder: input.placeholder || ''
                                };
                            }
                        }
                        return null;
                    }
                """, parsed['into'])
                if field_element_info and field_element_info.get('id'):
                    field_selector_for_value = f"#{field_element_info['id']}"
        except Exception as e:
            logger.debug(f"Error getting field element info: {e}")
        
        if field_selector_for_value:
            try:
                result['field_value_before'] = await page.input_value(field_selector_for_value)
            except:
                try:
                    result['field_value_before'] = await page.evaluate(f"""
                        (selector) => {{
                            const el = document.querySelector(selector);
                            return el ? el.value : null;
                        }}
                    """, field_selector_for_value)
                except:
                    pass
        
        # Click field if not focused
        field_clicked = False
        field_already_focused = False
        
        if field_element_info:
            try:
                active_element = await page.evaluate("""
                    () => {
                        const active = document.activeElement;
                        if (!active) return null;
                        return {
                            id: active.id || '',
                            name: active.name || ''
                        };
                    }
                """)
                if active_element:
                    field_id = field_element_info.get('id', '')
                    field_name = field_element_info.get('name', '')
                    if (active_element.get('id') == field_id and field_id) or \
                       (active_element.get('name') == field_name and field_name):
                        field_already_focused = True
            except:
                pass
        
        if not field_already_focused and field_element_info:
            if parsed['selector']:
                field_clicked = await cursor_controller.click_by_selector(parsed['selector'])
            elif parsed['into']:
                field_clicked = await cursor_controller.click_by_text(parsed['into'])
        
        result['element_found'] = field_clicked or field_element_info is not None
        
        if not result['element_found']:
            result['error'] = "Field not found"
            return result
        
        # Type text
        field_selector = parsed['selector'] or parsed['into'] or None
        type_success = await cursor_controller.type_text(parsed['text'], field_selector)
        
        if not type_success:
            result['error'] = "Failed to type text"
            return result
        
        delay = self._get_delay_from_speed_level(0.3, 0.01)
        await asyncio.sleep(delay)
        
        if field_selector_for_value:
            try:
                result['field_value_after'] = await page.input_value(field_selector_for_value)
            except:
                try:
                    result['field_value_after'] = await page.evaluate(f"""
                        (selector) => {{
                            const el = document.querySelector(selector);
                            return el ? el.value : null;
                        }}
                    """, field_selector_for_value)
                except:
                    pass
        
        value_before = result.get('field_value_before', '')
        value_after = result.get('field_value_after', '')
        expected_text = parsed['text']
        
        result['action_worked'] = (
            value_after != value_before and
            expected_text.lower() in value_after.lower()
        )
        
        state_after = await ActionStateCapture.capture_state(page)
        result['state_after'] = state_after
        
        changes = ActionStateCapture.compare_states(state_before, state_after)
        result['changes'] = changes
        
        result['success'] = result['element_found'] and result['action_worked']
        
        # Wait for page to stabilize after typing (may trigger dynamic updates)
        await self._wait_for_page_stable(timeout=10.0)
        
        duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
        
        field = parsed.get('into') or parsed.get('selector') or 'field'
        element_info = {
            'field': field,
            'text': parsed['text'],
            'value_before': value_before,
            'value_after': value_after
        }
        
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_after.get('url', ''),
                'title': state_after.get('title', ''),
                'element_count': state_after.get('element_count', 0)
            })
            
            warnings = []
            if result['element_found'] and not result['action_worked']:
                warnings.append(f"Field found but value may not have changed correctly")
            
            if result['success']:
                self.recorder_logger.log_user_action(
                    action_type='type',
                    element_info=element_info,
                    success=True,
                    duration_ms=duration_ms,
                    page_state=state_after,
                    details={'value_changed': value_after != value_before}
                )
            else:
                level = 'CRITICAL' if not result['element_found'] else 'WARNING'
                if level == 'CRITICAL':
                    self.recorder_logger.log_critical_failure(
                        action='pw-type',
                        error=result.get('error', 'Action failed'),
                        element_info=element_info,
                        page_state=state_before
                    )
                else:
                    self.recorder_logger.log_user_action(
                        action_type='type',
                        element_info=element_info,
                        success=False,
                        duration_ms=duration_ms,
                        error=result.get('error'),
                        warnings=warnings,
                        page_state=state_after
                    )
        
        return result

