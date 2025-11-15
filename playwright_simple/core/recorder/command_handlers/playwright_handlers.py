#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Direct Handlers.

Handles Playwright direct commands (find, click, type, submit, wait, info, html).
"""

import logging
from typing import Optional, Callable

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
        recorder = None
    ):
        """Initialize Playwright handlers."""
        self.yaml_writer = yaml_writer
        self._get_page = page_getter
        self._get_cursor_controller = cursor_controller_getter
        self._playwright_commands = None
        self._recorder = recorder  # Store recorder reference for fast_mode
    
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
    
    async def handle_pw_click(self, args: str) -> None:
        """
        Handle pw-click command using CursorController directly.
        
        IMPORTANT: Programmatic clicks (CLI commands) trigger DOM events that
        event_capture will capture and add to YAML automatically.
        """
        from ...playwright_commands.unified import parse_click_args
        
        page = self._get_page()
        if not page:
            print("❌ Page not available")
            return
        
        if not args:
            print("❌ Usage: pw-click \"text\" | pw-click selector \"#id\" | pw-click role button [index]")
            return
        
        # Get cursor controller
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            print("❌ CursorController not available")
            return
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Parse arguments using unified parser
        parsed = parse_click_args(args)
        
        # Execute click using CursorController
        success = False
        if parsed['text']:
            success = await cursor_controller.click_by_text(parsed['text'])
        elif parsed['selector']:
            success = await cursor_controller.click_by_selector(parsed['selector'])
        elif parsed['role']:
            success = await cursor_controller.click_by_role(parsed['role'], parsed['index'])
        else:
            print("❌ Usage: pw-click \"text\" | pw-click selector \"#id\" | pw-click role button [index]")
            return
        
        if success:
            print(f"✅ Clicked successfully")
            # event_capture will capture the DOM events and add to YAML automatically
        else:
            print(f"❌ Failed to click")
            print("   Usage examples:")
            print("     pw-click \"Entrar\"")
            print("     pw-click selector \"#login-button\"")
            print("     pw-click role button [0]")
    
    async def handle_pw_type(self, args: str) -> None:
        """
        Handle pw-type command using CursorController directly.
        
        IMPORTANT: Programmatic typing (CLI commands) triggers DOM events that
        event_capture will capture and add to YAML automatically.
        """
        from ...playwright_commands.unified import parse_type_args
        from ..action_converter import ActionConverter
        from ..element_identifier import ElementIdentifier
        
        page = self._get_page()
        if not page:
            print("❌ Page not available")
            return
        
        if not args:
            print("❌ Usage: pw-type \"text\" into \"field\" | pw-type \"text\" selector \"#id\"")
            return
        
        # Get fast_mode from recorder if available
        fast_mode = False
        if self._recorder:
            fast_mode = getattr(self._recorder, 'fast_mode', False)
        
        # Get cursor controller
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            print("❌ CursorController not available")
            return
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Parse arguments using unified parser
        parsed = parse_type_args(args)
        
        if not parsed['text']:
            print(f"⚠️  No field specified. Use: pw-type \"text\" into \"field\"")
            return
        
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
        
        # STEP 1: Click on the field first (like a real user would)
        # This focuses the field and ensures it's ready for typing
        # event_capture will capture this click and add to YAML
        if field_element_info and (parsed['into'] or parsed['selector']):
            field_clicked = False
            if parsed['selector']:
                field_clicked = await cursor_controller.click_by_selector(parsed['selector'])
            elif parsed['into']:
                field_clicked = await cursor_controller.click_by_text(parsed['into'])
        
        # STEP 2: Type the text using CursorController
        field_selector = parsed['selector'] or parsed['into'] or None
        success = await cursor_controller.type_text(parsed['text'], field_selector)
        
        if success:
            field = parsed['selector'] or parsed['into'] or 'field'
            print(f"✅ Typed '{parsed['text']}' into '{field}'")
            # event_capture will capture the input events and add to YAML automatically
        else:
            field = parsed['selector'] or parsed['into'] or 'field'
            print(f"❌ Failed to type into '{field}'")
    
    async def handle_pw_submit(self, args: str) -> None:
        """
        Handle pw-submit command using CursorController directly.
        
        IMPORTANT: Programmatic submit (CLI commands) triggers DOM events that
        event_capture will capture and add to YAML automatically.
        """
        from ..action_converter import ActionConverter
        from ..element_identifier import ElementIdentifier
        
        page = self._get_page()
        if not page:
            print("❌ Page not available")
            return
        
        # Get fast_mode from recorder if available
        fast_mode = False
        if self._recorder:
            fast_mode = getattr(self._recorder, 'fast_mode', False)
        
        # Get cursor controller
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            print("❌ CursorController not available")
            return
        
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
                        print(f"📝 Type: {action.get('description', '')} = '{value_preview}'")
        
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
                print(f"📝 Submit: {action.get('description', '')}")
        
        # Get cursor controller
        if not cursor_controller:
            if self._get_cursor_controller:
                cursor_controller = self._get_cursor_controller()
        
        if not cursor_controller:
            print("❌ CursorController not available")
            return
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Use CursorController directly
        success = await cursor_controller.submit_form(button_text)
        
        if success:
            if button_text:
                print(f"✅ Form submitted (button: '{button_text}')")
            else:
                print("✅ Form submitted")
        else:
            if button_text:
                print(f"❌ Failed to submit form (button: '{button_text}' not found)")
            else:
                print("❌ Failed to submit form (no submit button found)")
            print("   💡 Make sure you're on a page with a form")
            print("   💡 Try: pw-submit \"Entrar\" to specify button text")
    
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

