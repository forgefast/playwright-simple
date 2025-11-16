#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Click handler for Playwright commands.
"""

import logging
from typing import Dict, Any

from .base_handler import BaseHandler
from ...playwright_commands.unified import parse_click_args
from ..action_state_capture import ActionStateCapture

logger = logging.getLogger(__name__)


class ClickHandler(BaseHandler):
    """Handles click commands."""
    
    async def handle_click(self, args: str) -> Dict[str, Any]:
        """Handle click command."""
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
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-click',
                    error="Page not available",
                    page_state=None
                )
            return result
        
        if not args:
            result['error'] = "No arguments provided"
            return result
        
        action_id = f"click_{args}"
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
        
        parsed = parse_click_args(args)
        
        element_found = False
        if parsed['text']:
            element_found = await cursor_controller.click_by_text(parsed['text'])
        elif parsed['selector']:
            element_found = await cursor_controller.click_by_selector(parsed['selector'])
        elif parsed['role']:
            element_found = await cursor_controller.click_by_role(parsed['role'], parsed['index'])
        else:
            result['error'] = "Invalid arguments"
            return result
        
        result['element_found'] = element_found
        
        if not element_found:
            result['error'] = "Element not found"
            if self.recorder_logger:
                duration_ms = self.recorder_logger.end_action_timer(action_id)
                self.recorder_logger.log_critical_failure(
                    action='pw-click',
                    error=f"Element not found: {args}",
                    element_info={'text': parsed.get('text'), 'selector': parsed.get('selector'), 'role': parsed.get('role')},
                    page_state=state_before
                )
            return result
        
        await self._wait_for_page_stable(timeout=10.0)
        
        state_after = await ActionStateCapture.capture_state(page)
        result['state_after'] = state_after
        
        changes = ActionStateCapture.compare_states(state_before, state_after)
        result['changes'] = changes
        
        validation = ActionStateCapture.validate_expected_changes('click', state_before, state_after)
        result['action_worked'] = validation['action_worked']
        result['success'] = element_found and result['action_worked']
        
        duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
        
        element_info = {
            'text': parsed.get('text'),
            'selector': parsed.get('selector'),
            'role': parsed.get('role')
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
            if element_found and not result['action_worked']:
                warnings.append("Element found but action did not work (no state change detected)")
            
            if result['success']:
                self.recorder_logger.log_user_action(
                    action_type='click',
                    element_info=element_info,
                    success=True,
                    duration_ms=duration_ms,
                    page_state=state_after,
                    details={'url_changed': changes.get('url_changed'), 'html_changed': changes.get('html_changed')}
                )
            else:
                level = 'CRITICAL' if not element_found else 'WARNING'
                if level == 'CRITICAL':
                    self.recorder_logger.log_critical_failure(
                        action='pw-click',
                        error=result.get('error', 'Action failed'),
                        element_info=element_info,
                        page_state=state_before
                    )
                else:
                    self.recorder_logger.log_user_action(
                        action_type='click',
                        element_info=element_info,
                        success=False,
                        duration_ms=duration_ms,
                        error=result.get('error'),
                        warnings=warnings,
                        page_state=state_after
                    )
        
        if element_found and not result['action_worked']:
            result['warnings'].append("Element found but action may not have worked (no state changes detected)")
        
        if result['success']:
            print(f"✅ Clicked successfully")
        else:
            if not element_found:
                print(f"❌ Failed to click - element not found")
            else:
                print(f"⚠️  Clicked but action may not have worked (no state changes detected)")
        
        return result

