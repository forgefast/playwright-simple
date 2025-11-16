#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Direct Handlers.

Handles Playwright direct commands (find, click, type, submit, wait, info, html).
"""

import logging
import asyncio
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

# Try to import PlaywrightCommands
try:
    from ...playwright_commands import PlaywrightCommands
    PLAYWRIGHT_COMMANDS_AVAILABLE = True
except ImportError:
    PlaywrightCommands = None
    PLAYWRIGHT_COMMANDS_AVAILABLE = False


class PlaywrightHandlers:
    """Handles Playwright direct commands."""
    
    def __init__(
        self,
        yaml_writer,
        page_getter: Optional[Callable] = None,
        cursor_controller_getter: Optional[Callable] = None,
        recorder = None,
        recorder_logger = None
    ):
        """Initialize Playwright handlers."""
        self.yaml_writer = yaml_writer
        self._get_page = page_getter
        self._get_cursor_controller = cursor_controller_getter
        self._playwright_commands = None
        self._recorder = recorder  # Store recorder reference for fast_mode
        self.recorder_logger = recorder_logger
    
    def _get_playwright_commands(self):
        """Get or create PlaywrightCommands instance."""
        if self._playwright_commands:
            return self._playwright_commands
        
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            return None
        
        if not self._get_page:
            return None
        
        page = self._get_page()
        if not page:
            return None
        
        # Get fast_mode from recorder if available
        fast_mode = False
        if self._recorder:
            fast_mode = getattr(self._recorder, 'fast_mode', False)
        
        # During recording, always enable animations for better video quality
        # fast_mode reduces delays but keeps visual animations
        self._playwright_commands = PlaywrightCommands(page, fast_mode=fast_mode, enable_animations=True)
        return self._playwright_commands
    
    async def handle_find(self, args: str) -> None:
        """Handle find command - find element by text, selector, or role."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            print("❌ Playwright commands not available")
            return
        
        commands = self._get_playwright_commands()
        if not commands:
            print("❌ Page not available")
            return
        
        if not args:
            print("❌ Usage: find \"text\" | find selector \"#id\" | find role button")
            return
        
        args = args.strip()
        
        # Try to parse different formats
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
            element = await commands.find_element(selector=selector)
        elif args.startswith('role '):
            role = args[5:].strip().strip('"\'')
            element = await commands.find_element(role=role)
        else:
            # Treat as text
            text = args.strip('"\'')
            element = await commands.find_element(text=text)
        
        if element:
            print(f"✅ Element found:")
            print(f"   Tag: {element.get('tag', 'N/A')}")
            print(f"   Text: {element.get('text', 'N/A')[:100]}")
            print(f"   ID: {element.get('id', 'N/A')}")
            print(f"   Class: {element.get('className', 'N/A')[:50]}")
            print(f"   Visible: {element.get('visible', False)}")
        else:
            print(f"❌ Element not found")
            print("   Usage examples:")
            print("     find \"Entrar\"")
            print("     find selector \"#login-button\"")
            print("     find role button")
    
    async def handle_find_all(self, args: str) -> None:
        """Handle find-all command - find all matching elements."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            print("❌ Playwright commands not available")
            return
        
        commands = self._get_playwright_commands()
        if not commands:
            print("❌ Page not available")
            return
        
        if not args:
            print("❌ Usage: find-all \"text\" | find-all selector \"#id\" | find-all role button")
            return
        
        args = args.strip()
        
        # Try to parse different formats
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
            elements = await commands.find_all_elements(selector=selector)
        elif args.startswith('role '):
            role = args[5:].strip().strip('"\'')
            elements = await commands.find_all_elements(role=role)
        else:
            # Treat as text
            text = args.strip('"\'')
            elements = await commands.find_all_elements(text=text)
        
        if elements:
            print(f"✅ Found {len(elements)} element(s):")
            for i, element in enumerate(elements[:10]):  # Limit to 10
                print(f"   [{i}] {element.get('tag', 'N/A')} - {element.get('text', 'N/A')[:50]}")
            if len(elements) > 10:
                print(f"   ... and {len(elements) - 10} more")
        else:
            print(f"❌ No elements found")
    
    async def handle_pw_click(self, args: str) -> Dict[str, Any]:
        """
        Handle pw-click command using CursorController directly.
        
        IMPORTANT: Programmatic clicks (CLI commands) trigger DOM events that
        event_capture will capture and add to YAML automatically.
        
        Returns:
            Dictionary with validation result:
            - success: bool - Element found AND action worked
            - element_found: bool - Element was found
            - action_worked: bool - Action actually worked (state changed)
            - state_before: dict - State before action
            - state_after: dict - State after action
            - changes: dict - Detected changes
            - error: str - Error message if any
            - warnings: list - Warnings (e.g., element found but action didn't work)
        """
        from ...playwright_commands.unified import parse_click_args
        from ..action_state_capture import ActionStateCapture
        
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
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-click',
                    error="No arguments provided"
                )
            return result
        
        # Start timer
        action_id = f"click_{args}"
        if self.recorder_logger:
            self.recorder_logger.start_action_timer(action_id)
        
        # Capture state before action
        state_before = await ActionStateCapture.capture_state(page)
        result['state_before'] = state_before
        
        # Log action start
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_before.get('url', ''),
                'title': state_before.get('title', ''),
                'element_count': state_before.get('element_count', 0)
            })
        
        # Get cursor controller
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            result['error'] = "CursorController not available"
            print("❌ CursorController not available")
            return result
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Parse arguments using unified parser
        parsed = parse_click_args(args)
        
        # Execute click using CursorController
        element_found = False
        if parsed['text']:
            element_found = await cursor_controller.click_by_text(parsed['text'])
        elif parsed['selector']:
            element_found = await cursor_controller.click_by_selector(parsed['selector'])
        elif parsed['role']:
            element_found = await cursor_controller.click_by_role(parsed['role'], parsed['index'])
        else:
            result['error'] = "Invalid arguments"
            if self.recorder_logger:
                duration_ms = self.recorder_logger.end_action_timer(action_id)
                self.recorder_logger.log_critical_failure(
                    action='pw-click',
                    error="Invalid arguments",
                    page_state=state_before
                )
            return result
        
        result['element_found'] = element_found
        
        if not element_found:
            result['error'] = "Element not found"
            duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-click',
                    error=f"Element not found: {args}",
                    element_info={'text': parsed.get('text'), 'selector': parsed.get('selector'), 'role': parsed.get('role')},
                    page_state=state_before
                )
            return result
        
        # Wait for page to stabilize after click
        try:
            if self._recorder and hasattr(self._recorder, '_wait_for_page_stable'):
                await self._recorder._wait_for_page_stable(timeout=10.0)
            else:
                # Fallback: wait for load states
                await page.wait_for_load_state('domcontentloaded', timeout=5000)
                # Get fast_mode from recorder
                fast_mode = getattr(self._recorder, 'fast_mode', False) if self._recorder else False
                delay = 0.01 if fast_mode else 0.5
                await asyncio.sleep(delay)
                try:
                    await page.wait_for_load_state('networkidle', timeout=3000)
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error waiting for page stable: {e}")
        
        # Capture state after action
        state_after = await ActionStateCapture.capture_state(page)
        result['state_after'] = state_after
        logger.info(f"[STATE_AFTER] URL: {state_after.get('url', 'N/A')}, Title: {state_after.get('title', 'N/A')}, Elements: {state_after.get('element_count', 0)}")
        
        # Compare states and validate
        changes = ActionStateCapture.compare_states(state_before, state_after)
        result['changes'] = changes
        
        validation = ActionStateCapture.validate_expected_changes('click', state_before, state_after)
        result['action_worked'] = validation['action_worked']
        result['success'] = element_found and result['action_worked']
        
        # End timer and log result
        duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
        
        # Build element info
        element_info = {
            'text': parsed.get('text'),
            'selector': parsed.get('selector'),
            'role': parsed.get('role')
        }
        
        # Update page state
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_after.get('url', ''),
                'title': state_after.get('title', ''),
                'element_count': state_after.get('element_count', 0),
                'html_hash': state_after.get('html_hash'),
                'network_idle': state_after.get('network_idle', False)
            })
        
        # Log result
        if self.recorder_logger:
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
        
        # Determine overall success
        result['success'] = element_found and result['action_worked']
        
        if element_found and not result['action_worked']:
            result['warnings'].append("Element found but action may not have worked (no state changes detected)")
            logger.warning(f"[WARNING] pw-click - Element found but no state changes detected: {args}")
        
        if result['success']:
            print(f"✅ Clicked successfully")
        else:
            if not element_found:
                print(f"❌ Failed to click - element not found")
            else:
                print(f"⚠️  Clicked but action may not have worked (no state changes detected)")
            print("   Usage examples:")
            print("     pw-click \"Entrar\"")
            print("     pw-click selector \"#login-button\"")
            print("     pw-click role button [0]")
    
        return result
    
    async def handle_pw_type(self, args: str) -> Dict[str, Any]:
        """
        Handle pw-type command using CursorController directly.
        
        IMPORTANT: Programmatic typing (CLI commands) triggers DOM events that
        event_capture will capture and add to YAML automatically.
        
        Returns:
            Dictionary with validation result (same structure as handle_pw_click)
        """
        from ...playwright_commands.unified import parse_type_args
        from ..action_converter import ActionConverter
        from ..element_identifier import ElementIdentifier
        from ..action_state_capture import ActionStateCapture
        
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
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-type',
                    error="Page not available",
                    page_state=None
                )
            return result
        
        if not args:
            result['error'] = "No arguments provided"
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-type',
                    error="No arguments provided"
                )
            return result
        
        # Start timer
        action_id = f"type_{args}"
        if self.recorder_logger:
            self.recorder_logger.start_action_timer(action_id)
        
        # Capture state before action
        state_before = await ActionStateCapture.capture_state(page)
        result['state_before'] = state_before
        
        # Log action start
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_before.get('url', ''),
                'title': state_before.get('title', ''),
                'element_count': state_before.get('element_count', 0)
            })
        
        # Get fast_mode from recorder if available
        fast_mode = False
        if self._recorder:
            fast_mode = getattr(self._recorder, 'fast_mode', False)
        
        # Get cursor controller
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            result['error'] = "CursorController not available"
            print("❌ CursorController not available")
            return result
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Parse arguments using unified parser
        parsed = parse_type_args(args)
        
        if not parsed['text']:
            result['error'] = "No text specified"
            duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-type',
                    error="No text specified",
                    page_state=state_before
                )
            return result
        
        # CRITICAL: Get element information BEFORE clicking/typing
        # This allows us to create YAML actions directly
        field_element_info = None
        try:
            # Find the input field and get its information
            if parsed['selector']:
                # Find by selector
                field_element_info = await page.evaluate("""
                    (selector) => {
                        const el = document.querySelector(selector);
                        if (!el) return null;
                        return {
                            tagName: el.tagName || '',
                            text: (el.textContent || el.innerText || el.value || '').trim(),
                            id: el.id || '',
                            className: el.className || '',
                            href: '',
                            type: el.type || '',
                            name: el.name || '',
                            value: el.value || '',
                            role: el.getAttribute('role') || '',
                            ariaLabel: el.getAttribute('aria-label') || '',
                            placeholder: el.placeholder || '',
                            label: (el.labels && el.labels.length > 0) 
                                ? (el.labels[0].textContent || '').trim() 
                                : ''
                        };
                    }
                """, parsed['selector'])
            elif parsed['into']:
                # Find by text (label, placeholder, name, id, etc.)
                field_element_info = await page.evaluate("""
                    (fieldText) => {
                        const textLower = fieldText.toLowerCase();
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        
                        for (const input of inputs) {
                            if (input.offsetParent === null || input.style.display === 'none') continue;
                            if (input.type === 'hidden') continue;
                            
                            // Check label
                            const labels = input.labels || [];
                            for (const label of labels) {
                                const labelText = (label.textContent || '').trim().toLowerCase();
                                if (labelText === textLower || labelText.includes(textLower)) {
                                    return {
                                        tagName: input.tagName || '',
                                        text: (input.textContent || input.innerText || input.value || '').trim(),
                                        id: input.id || '',
                                        className: input.className || '',
                                        href: '',
                                        type: input.type || '',
                                        name: input.name || '',
                                        value: input.value || '',
                                        role: input.getAttribute('role') || '',
                                        ariaLabel: input.getAttribute('aria-label') || '',
                                        placeholder: input.placeholder || '',
                                        label: labelText
                                    };
                                }
                            }
                            
                            // Check placeholder
                            if (input.placeholder && input.placeholder.toLowerCase().includes(textLower)) {
                                return {
                                    tagName: input.tagName || '',
                                    text: (input.textContent || input.innerText || input.value || '').trim(),
                                    id: input.id || '',
                                    className: input.className || '',
                                    href: '',
                                    type: input.type || '',
                                    name: input.name || '',
                                    value: input.value || '',
                                    role: input.getAttribute('role') || '',
                                    ariaLabel: input.getAttribute('aria-label') || '',
                                    placeholder: input.placeholder || '',
                                    label: ''
                                };
                            }
                            
                            // Check name/id
                            if ((input.name && input.name.toLowerCase().includes(textLower)) ||
                                (input.id && input.id.toLowerCase().includes(textLower))) {
                                return {
                                    tagName: input.tagName || '',
                                    text: (input.textContent || input.innerText || input.value || '').trim(),
                                    id: input.id || '',
                                    className: input.className || '',
                                    href: '',
                                    type: input.type || '',
                                    name: input.name || '',
                                    value: input.value || '',
                                    role: input.getAttribute('role') || '',
                                    ariaLabel: input.getAttribute('aria-label') || '',
                                    placeholder: input.placeholder || '',
                                    label: ''
                                };
                            }
                        }
                        return null;
                    }
                """, parsed['into'])
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error getting field element info before type: {e}")
        
        # Get field value before typing
        field_selector_for_value = None
        if parsed['selector']:
            field_selector_for_value = parsed['selector']
        elif parsed['into']:
            # Try to find selector for the field
            try:
                field_selector_for_value = await page.evaluate(f"""
                    (fieldText) => {{
                        const textLower = fieldText.toLowerCase();
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        for (const input of inputs) {{
                            if (input.offsetParent === null) continue;
                            const labels = input.labels || [];
                            for (const label of labels) {{
                                const labelText = (label.textContent || '').trim().toLowerCase();
                                if (labelText === textLower || labelText.includes(textLower)) {{
                                    return input.id ? `#${{input.id}}` : `input[name="${{input.name}}"]`;
                                }}
                            }}
                        }}
                        return null;
                    }}
                """, parsed['into'])
            except:
                pass
        
        # Capture field value before
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
        
        # STEP 1: Click on the field first (like a real user would)
        # This focuses the field and ensures it's ready for typing
        # NOTE: We only click if the field is not already focused
        # If there was a click action before this type action, the field might already be focused
            field_clicked = False
        field_already_focused = False
        
        # Check if field is already focused
        if field_element_info:
            try:
                active_element = await page.evaluate("""
                    () => {
                        const active = document.activeElement;
                        if (!active) return null;
                        return {
                            tag: active.tagName,
                            id: active.id || '',
                            name: active.name || '',
                            type: active.type || ''
                        };
                    }
                """)
                if active_element:
                    field_id = field_element_info.get('id', '')
                    field_name = field_element_info.get('name', '')
                    if (active_element.get('id') == field_id and field_id) or \
                       (active_element.get('name') == field_name and field_name):
                        field_already_focused = True
                        if self.recorder_logger:
                            self.recorder_logger.debug(
                                message=f"Field already focused, skipping click before type",
                                details={'field': parsed['into'] or parsed['selector'], 'active_element': active_element}
                            )
            except:
                pass  # Continue to click if check fails
        
        # Only click if field is not already focused
        if not field_already_focused and field_element_info and (parsed['into'] or parsed['selector']):
            if self.recorder_logger:
                self.recorder_logger.log_user_action(
                    action_type='click',
                    element_info=field_element_info,
                    details={'reason': 'focus_field_before_type', 'field': parsed['into'] or parsed['selector']}
                )
            if parsed['selector']:
                field_clicked = await cursor_controller.click_by_selector(parsed['selector'])
            elif parsed['into']:
                field_clicked = await cursor_controller.click_by_text(parsed['into'])
        
        result['element_found'] = field_clicked or field_element_info is not None
        
        if not result['element_found']:
            result['error'] = "Field not found"
            field = parsed['selector'] or parsed['into'] or 'field'
            duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-type',
                    error=f"Field not found: '{field}'",
                    element_info={'field': field},
                    page_state=state_before
                )
            return result
        
        # STEP 2: Type the text using CursorController
        field_selector = parsed['selector'] or parsed['into'] or None
        type_success = await cursor_controller.type_text(parsed['text'], field_selector)
        
        if not type_success:
            result['error'] = "Failed to type text"
            field = parsed['selector'] or parsed['into'] or 'field'
            duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-type',
                    error=f"Failed to type into '{field}'",
                    element_info={'field': field, 'text': parsed['text']},
                    page_state=state_before
                )
            return result
        
        # Wait a bit for value to be set
        fast_mode = getattr(self._recorder, 'fast_mode', False) if self._recorder else False
        delay = 0.01 if fast_mode else 0.3
        await asyncio.sleep(delay)
        
        # Capture field value after
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
        
        # Validate if value changed
        value_before = result.get('field_value_before', '')
        value_after = result.get('field_value_after', '')
        expected_text = parsed['text']
        
        # Check if value contains the typed text
        result['action_worked'] = (
            value_after != value_before and
            expected_text.lower() in value_after.lower()
        )
        
        # Capture state after
        state_after = await ActionStateCapture.capture_state(page)
        result['state_after'] = state_after
        
        changes = ActionStateCapture.compare_states(state_before, state_after)
        result['changes'] = changes
        
        # Determine overall success
        result['success'] = result['element_found'] and result['action_worked']
        
        # End timer
        duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
        
        # Build element info
        field = parsed.get('into') or parsed.get('selector') or 'field'
        element_info = {
            'field': field,
            'text': parsed['text'],
            'value_before': value_before,
            'value_after': value_after
        }
        
        # Update page state
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_after.get('url', ''),
                'title': state_after.get('title', ''),
                'element_count': state_after.get('element_count', 0)
            })
        
        # Log result
        if self.recorder_logger:
            warnings = []
            if result['element_found'] and not result['action_worked']:
                warnings.append(f"Field found but value may not have changed correctly (before: '{value_before}', after: '{value_after}')")
            
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
    
    async def handle_pw_submit(self, args: str) -> Dict[str, Any]:
        """
        Handle pw-submit command using CursorController directly.
        
        IMPORTANT: Programmatic submit (CLI commands) triggers DOM events that
        event_capture will capture and add to YAML automatically.
        
        Returns:
            Dictionary with validation result (same structure as handle_pw_click)
        """
        from ..action_converter import ActionConverter
        from ..element_identifier import ElementIdentifier
        from ..action_state_capture import ActionStateCapture
        
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
                    action='pw-submit',
                    error="Page not available",
                    page_state=None
                )
            return result
        
        # Start timer
        action_id = f"submit_{args}"
        if self.recorder_logger:
            self.recorder_logger.start_action_timer(action_id)
        
        # Capture state before action
        state_before = await ActionStateCapture.capture_state(page)
        result['state_before'] = state_before
        
        # Log action start
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_before.get('url', ''),
                'title': state_before.get('title', ''),
                'element_count': state_before.get('element_count', 0)
            })
        
        # Get fast_mode from recorder if available
        fast_mode = False
        if self._recorder:
            fast_mode = getattr(self._recorder, 'fast_mode', False)
        
        # Get cursor controller
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            result['error'] = "CursorController not available"
            print("❌ CursorController not available")
            return result
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Parse button text (optional)
        button_text = args.strip().strip('"\'') if args.strip() else None
        
        # CRITICAL: Get element information BEFORE submitting
        # This allows us to create YAML action directly
        submit_element_info = None
        try:
            # Find the submit button and get its information
            if button_text:
                submit_element_info = await page.evaluate("""
                    (buttonText) => {
                        const textLower = buttonText.toLowerCase();
                        // Find submit buttons
                        const submitSelectors = ['input[type="submit"]', 'button[type="submit"]', 'button:not([type])'];
                        for (const selector of submitSelectors) {
                            const elements = Array.from(document.querySelectorAll(selector));
                            for (const el of elements) {
                                if (el.offsetParent === null || el.style.display === 'none') continue;
                                const elText = (el.textContent || el.innerText || el.value || '').trim().toLowerCase();
                                if (elText === textLower || elText.includes(textLower)) {
                                    // Check if it's actually a submit button
                                    const isSubmit = el.type === 'submit' || 
                                                    (el.tagName?.toUpperCase() === 'BUTTON' && 
                                                     (el.type === 'submit' || el.type === ''));
                                    if (isSubmit) {
                                        return {
                                            tagName: el.tagName || '',
                                            text: (el.textContent || el.innerText || el.value || '').trim(),
                                            id: el.id || '',
                                            className: el.className || '',
                                            href: '',
                                            type: el.type || 'submit',
                                            name: el.name || '',
                                            value: el.value || '',
                                            role: el.getAttribute('role') || '',
                                            ariaLabel: el.getAttribute('aria-label') || ''
                                        };
                                    }
                                }
                            }
                        }
                        return null;
                    }
                """, button_text)
            else:
                # Find first submit button if no text specified
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
                                    className: el.className || '',
                                    href: '',
                                    type: el.type || 'submit',
                                    name: el.name || '',
                                    value: el.value || '',
                                    role: el.getAttribute('role') || '',
                                    ariaLabel: el.getAttribute('aria-label') || ''
                                };
                            }
                        }
                        return null;
                    }
                """)
        except Exception as e:
            logger.debug(f"Error getting submit element info before submit: {e}")
        
        # CRITICAL: Finalize all pending inputs BEFORE adding submit step
        # This ensures inputs (like password) are captured before submit
        if self.yaml_writer and hasattr(self._recorder, 'event_handlers'):
            pending_inputs = self._recorder.action_converter.pending_inputs
            if pending_inputs:
                logger.info(f"Submit detected: finalizing {len(pending_inputs)} pending input(s) before submit")
                for element_key in list(pending_inputs.keys()):
                    action = self._recorder.action_converter.finalize_input(element_key)
                    if action:
                        self.yaml_writer.add_step(action)
                        value_preview = action.get('text', '')[:50]
                        if len(action.get('text', '')) > 50:
                            value_preview += '...'
                        logger.info(f"Finalized input before submit: {action.get('description', '')} = '{value_preview}'")
                        # Log is handled by event_handlers
        
        # CRITICAL: Add submit step to YAML BEFORE submitting
        # This ensures the step is captured even if event_capture misses the click
        if submit_element_info and self.yaml_writer:
            # Add isInForm information if not present
            if 'isInForm' not in submit_element_info:
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
            
            # Convert to action using ActionConverter
            converter = ActionConverter()
            event_data = {'element': submit_element_info}
            action = converter.convert_click(event_data)
            
            if action and action.get('action') == 'submit':
                self.yaml_writer.add_step(action)
                logger.info(f"Added submit step: {action.get('description', '')}")
                # Log is handled by event_handlers
        
        # Check if submit button was found
        result['element_found'] = submit_element_info is not None
        
        if not result['element_found']:
            result['error'] = "Submit button not found"
            duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-submit',
                    error=f"Submit button not found: {button_text or 'default'}",
                    element_info={'button_text': button_text},
                    page_state=state_before
                )
            return result
        
        # Get cursor controller (if not already got)
        if not cursor_controller:
            if self._get_cursor_controller:
                cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            result['error'] = "CursorController not available"
            print("❌ CursorController not available")
            return result
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        logger.info(f"[SUBMIT] Button found, submitting form: {button_text or 'default'}")
        
        # Use CursorController directly
        submit_success = await cursor_controller.submit_form(button_text)
        
        if not submit_success:
            result['error'] = "Failed to submit form"
            duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='pw-submit',
                    error=f"Failed to submit form: {button_text or 'default'}",
                    element_info={'button_text': button_text},
                    page_state=state_before
                )
            return result
        
        # Wait for navigation/page reload after submit
        try:
            if self._recorder and hasattr(self._recorder, '_wait_for_page_stable'):
                await self._recorder._wait_for_page_stable(timeout=10.0)
            else:
                # Fallback: wait for load states
                await page.wait_for_load_state('domcontentloaded', timeout=5000)
                await asyncio.sleep(0.5)
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000)
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error waiting for page stable after submit: {e}")
        
        # Capture state after action
        state_after = await ActionStateCapture.capture_state(page)
        result['state_after'] = state_after
        logger.info(f"[STATE_AFTER] URL: {state_after.get('url', 'N/A')}, Title: {state_after.get('title', 'N/A')}, Elements: {state_after.get('element_count', 0)}")
        
        # Compare states and validate
        changes = ActionStateCapture.compare_states(state_before, state_after)
        result['changes'] = changes
        
        validation = ActionStateCapture.validate_expected_changes('submit', state_before, state_after)
        result['action_worked'] = validation['action_worked']
        
        # Determine overall success
        result['success'] = result['element_found'] and result['action_worked']
        
        # End timer
        duration_ms = self.recorder_logger.end_action_timer(action_id) if self.recorder_logger else None
        
        # Build element info
        element_info = {
            'button_text': button_text,
            'tag': submit_element_info.get('tagName') if submit_element_info else None
        }
        
        # Update page state
        if self.recorder_logger:
            self.recorder_logger.set_page_state({
                'url': state_after.get('url', ''),
                'title': state_after.get('title', ''),
                'element_count': state_after.get('element_count', 0),
                'html_hash': state_after.get('html_hash'),
                'network_idle': state_after.get('network_idle', False)
            })
        
        # Log result
        if self.recorder_logger:
            warnings = []
            if result['element_found'] and not result['action_worked']:
                warnings.append("Submit button found but form may not have submitted (no state changes detected)")
            
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
    
    async def handle_pw_wait(self, args: str) -> None:
        """Handle pw-wait command - wait for element using Playwright."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            print("❌ Playwright commands not available")
            return
        
        commands = self._get_playwright_commands()
        if not commands:
            print("❌ Page not available")
            return
        
        if not args:
            print("❌ Usage: pw-wait \"text\" [timeout] | pw-wait selector \"#id\" [timeout]")
            return
        
        args = args.strip()
        timeout = 5000  # Default 5 seconds
        
        # Check for timeout
        parts = args.split()
        if len(parts) >= 2 and parts[-1].isdigit():
            timeout = int(parts[-1]) * 1000  # Convert to milliseconds
            args = ' '.join(parts[:-1])
        
        # Try to parse different formats
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
            success = await commands.wait_for_element(selector=selector, timeout=timeout)
        elif args.startswith('role '):
            role = args[5:].strip().strip('"\'')
            success = await commands.wait_for_element(role=role, timeout=timeout)
        else:
            # Treat as text
            text = args.strip('"\'')
            success = await commands.wait_for_element(text=text, timeout=timeout)
        
        if success:
            print(f"✅ Element appeared")
        else:
            print(f"❌ Element did not appear within {timeout/1000}s")
    
    async def handle_pw_info(self, args: str) -> None:
        """Handle pw-info command - get page information."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            print("❌ Playwright commands not available")
            return
        
        commands = self._get_playwright_commands()
        if not commands:
            print("❌ Page not available")
            return
        
        info = await commands.get_page_info()
        if info:
            print(f"📄 Page Information:")
            print(f"   URL: {info.get('url', 'N/A')}")
            print(f"   Title: {info.get('title', 'N/A')}")
            print(f"   Ready State: {info.get('ready_state', 'N/A')}")
        else:
            print("❌ Failed to get page information")
    
    async def handle_pw_html(self, args: str) -> None:
        """Handle pw-html command - get HTML of page or element."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            print("❌ Playwright commands not available")
            return
        
        commands = self._get_playwright_commands()
        if not commands:
            print("❌ Page not available")
            return
        
        args = args.strip()
        selector = None
        pretty = False
        max_length = None
        
        # Parse arguments
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
        elif args.startswith('--selector '):
            parts = args.split('--selector ', 1)
            if len(parts) > 1:
                selector = parts[1].strip().strip('"\'')
        elif args and not args.startswith('--'):
            # Treat as selector if it looks like one
            selector = args.strip().strip('"\'')
        
        # Check for flags
        if '--pretty' in args or '-p' in args:
            pretty = True
        
        if '--max-length' in args or '--max' in args:
            parts = args.split('--max-length' if '--max-length' in args else '--max', 1)
            if len(parts) > 1:
                try:
                    max_length = int(parts[1].split()[0])
                except:
                    pass
        
        html = await commands.get_html(selector=selector, pretty=pretty, max_length=max_length)
        
        if html:
            length = len(html)
            if max_length and length > max_length:
                print(f"📄 HTML ({length} caracteres, truncado):")
            else:
                print(f"📄 HTML ({length} caracteres):")
            print("-" * 60)
            print(html)
            print("-" * 60)
            
            # Suggest saving to file if long
            if length > 1000:
                print(f"\n💡 Dica: HTML é grande ({length} caracteres). Considere salvar em arquivo:")
                selector_part = f' selector "{selector}"' if selector else ''
                print(f"   playwright-simple html{selector_part} > page.html")
        else:
            print("❌ Failed to get HTML")
            if selector:
                print(f"   Element with selector '{selector}' not found")

