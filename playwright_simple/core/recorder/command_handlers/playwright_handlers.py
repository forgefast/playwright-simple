#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Direct Handlers.

Handles Playwright direct commands (find, click, type, submit, wait, info, html).
"""

from typing import Optional, Callable

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
        
        self._playwright_commands = PlaywrightCommands(page, fast_mode=fast_mode)
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
        Handle pw-click command using unified function.
        
        IMPORTANT: Programmatic clicks (CLI commands) should add directly to YAML,
        not depend on event_capture. This is the standard pattern for test automation.
        """
        from ...playwright_commands.unified import unified_click, parse_click_args
        from ..action_converter import ActionConverter
        from ..element_identifier import ElementIdentifier
        
        page = self._get_page()
        if not page:
            print("❌ Page not available")
            return
        
        if not args:
            print("❌ Usage: pw-click \"text\" | pw-click selector \"#id\" | pw-click role button [index]")
            return
        
        # Get fast_mode from recorder if available
        fast_mode = False
        if self._recorder:
            fast_mode = getattr(self._recorder, 'fast_mode', False)
        
        # Get cursor controller if available
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        # Parse arguments using unified parser
        parsed = parse_click_args(args)
        
        # CRITICAL: Get element information BEFORE clicking
        # This allows us to create YAML action directly, without depending on event_capture
        element_info = None
        try:
            # Find the element and get its information
            element_info = await page.evaluate("""
                ({text, selector, role, index}) => {
                    let elements = [];
                    
                    if (selector) {
                        elements = Array.from(document.querySelectorAll(selector));
                    } else if (role) {
                        elements = Array.from(document.querySelectorAll(`[role="${role}"]`));
                    } else if (text) {
                        const textLower = text.toLowerCase();
                        // Find by text - same logic as click
                        const allClickable = document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"], [role="link"]');
                        for (const el of allClickable) {
                            if (el.offsetParent === null || el.style.display === 'none') continue;
                            const elText = (el.textContent || el.innerText || el.value || '').trim().toLowerCase();
                            if (elText === textLower || elText.includes(textLower)) {
                                elements.push(el);
                            }
                        }
                    }
                    
                    // Filter visible elements
                    elements = elements.filter(el => el.offsetParent !== null && el.style.display !== 'none');
                    
                    if (elements.length > index && elements[index]) {
                        const el = elements[index];
                        // Serialize element info (same format as event_capture)
                        return {
                            tagName: el.tagName || '',
                            text: (el.textContent || el.innerText || el.value || '').trim(),
                            id: el.id || '',
                            className: el.className || '',
                            href: el.href || el.getAttribute('href') || '',
                            type: el.type || '',
                            name: el.name || '',
                            value: el.value || '',
                            role: el.getAttribute('role') || '',
                            ariaLabel: el.getAttribute('aria-label') || ''
                        };
                    }
                    return null;
                }
            """, {
                'text': parsed.get('text'),
                'selector': parsed.get('selector'),
                'role': parsed.get('role'),
                'index': parsed.get('index', 0)
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error getting element info before click: {e}")
        
        # Use unified click function
        success = await unified_click(
            page=page,
            text=parsed['text'],
            selector=parsed['selector'],
            role=parsed['role'],
            index=parsed['index'],
            cursor_controller=cursor_controller,
            fast_mode=fast_mode
        )
        
        if success:
            print(f"✅ Clicked successfully")
            
            # CRITICAL: Add action directly to YAML for programmatic clicks
            # This is the standard pattern - programmatic actions don't depend on event_capture
            if element_info and self.yaml_writer:
                # Get action_converter from recorder if available
                action_converter = None
                if self._recorder:
                    action_converter = getattr(self._recorder, 'action_converter', None)
                
                if action_converter:
                    # Create event_data in the same format as event_capture
                    event_data = {
                        'element': element_info,
                        'timestamp': None  # Not needed for programmatic actions
                    }
                    
                    # Convert to YAML action
                    action = action_converter.convert_click(event_data)
                    if action:
                        self.yaml_writer.add_step(action)
                        print(f"📝 Click: {action.get('description', '')}")
                    else:
                        import logging
                        logging.getLogger(__name__).warning(f"Failed to convert programmatic click to action: {element_info}")
                else:
                    import logging
                    logging.getLogger(__name__).warning("ActionConverter not available for programmatic click")
        else:
            print(f"❌ Failed to click")
            print("   Usage examples:")
            print("     pw-click \"Entrar\"")
            print("     pw-click selector \"#login-button\"")
            print("     pw-click role button [0]")
    
    async def handle_pw_type(self, args: str) -> None:
        """
        Handle pw-type command using unified function.
        
        IMPORTANT: Programmatic typing (CLI commands) should add steps to YAML:
        1. Click on the field (to focus it, like a real user would)
        2. Type the text
        
        This ensures the YAML reflects the actual user workflow.
        """
        from ...playwright_commands.unified import unified_type, unified_click, parse_type_args
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
        
        # Get cursor controller if available
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
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
        if field_element_info:
            # Click on the field using unified_click
            field_clicked = await unified_click(
                page=page,
                text=parsed['into'],
                selector=parsed['selector'],
                cursor_controller=cursor_controller,
                fast_mode=fast_mode
            )
            
            if field_clicked and self.yaml_writer:
                # Add click step to YAML
                action_converter = None
                if self._recorder:
                    action_converter = getattr(self._recorder, 'action_converter', None)
                
                if action_converter:
                    event_data = {
                        'element': field_element_info,
                        'timestamp': None
                    }
                    click_action = action_converter.convert_click(event_data)
                    if click_action:
                        self.yaml_writer.add_step(click_action)
                        print(f"📝 Click: {click_action.get('description', '')}")
        
        # STEP 2: Type the text
        success = await unified_type(
            page=page,
            text=parsed['text'],
            into=parsed['into'],
            selector=parsed['selector'],
            cursor_controller=cursor_controller,
            fast_mode=fast_mode
        )
        
        if success:
            field = parsed['selector'] or parsed['into'] or 'field'
            print(f"✅ Typed '{parsed['text']}' into '{field}'")
            
            # STEP 3: Add type step to YAML
            if field_element_info and self.yaml_writer:
                action_converter = None
                if self._recorder:
                    action_converter = getattr(self._recorder, 'action_converter', None)
                
                if action_converter:
                    # Create input event data (same format as event_capture)
                    input_event_data = {
                        'element': field_element_info,
                        'value': parsed['text'],
                        'timestamp': None
                    }
                    
                    # Use convert_input to create the action
                    # But we need to finalize it immediately since it's programmatic
                    action_converter.convert_input(input_event_data)
                    
                    # Finalize the input immediately (don't wait for blur)
                    element_id = field_element_info.get('id', '')
                    element_name = field_element_info.get('name', '')
                    element_type = field_element_info.get('type', '')
                    element_key = f"{element_id}:{element_name}:{element_type}"
                    
                    type_action = action_converter.finalize_input(element_key)
                    if type_action:
                        self.yaml_writer.add_step(type_action)
                        value_preview = type_action.get('text', '')[:50]
                        if len(type_action.get('text', '')) > 50:
                            value_preview += '...'
                        print(f"📝 Type: {type_action.get('description', '')} = '{value_preview}'")
        else:
            field = parsed['selector'] or parsed['into'] or 'field'
            print(f"❌ Failed to type into '{field}'")
    
    async def handle_pw_submit(self, args: str) -> None:
        """
        Handle pw-submit command using unified function.
        
        IMPORTANT: Programmatic submit (CLI commands) should add step to YAML as 'submit' action,
        not 'click'. This differentiates submit buttons from regular clicks.
        """
        from ...playwright_commands.unified import unified_submit
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
        
        # Get cursor controller if available
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
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
            import logging
            logging.getLogger(__name__).debug(f"Error getting submit element info before submit: {e}")
        
        # Use unified submit function
        success = await unified_submit(
            page=page,
            button_text=button_text,
            cursor_controller=cursor_controller,
            fast_mode=fast_mode
        )
        
        if success:
            if button_text:
                print(f"✅ Form submitted (button: '{button_text}')")
            else:
                print("✅ Form submitted")
            
            # CRITICAL: Add submit action directly to YAML for programmatic submits
            # This is the standard pattern - programmatic actions don't depend on event_capture
            if submit_element_info and self.yaml_writer:
                # Get action_converter from recorder if available
                action_converter = None
                if self._recorder:
                    action_converter = getattr(self._recorder, 'action_converter', None)
                
                if action_converter:
                    # Create event_data in the same format as event_capture
                    # Mark as submit button explicitly
                    submit_element_info['type'] = 'submit'  # Ensure it's marked as submit
                    event_data = {
                        'element': submit_element_info,
                        'timestamp': None  # Not needed for programmatic actions
                    }
                    
                    # Convert to YAML action (should create 'submit' action, not 'click')
                    action = action_converter.convert_click(event_data)
                    if action:
                        # Ensure it's a submit action, not click
                        if action.get('action') != 'submit':
                            # Force it to be submit if it's a submit button
                            action['action'] = 'submit'
                            action['description'] = f"Submeter formulário: {action.get('description', '')}"
                        self.yaml_writer.add_step(action)
                        print(f"📝 Submit: {action.get('description', '')}")
                    else:
                        import logging
                        logging.getLogger(__name__).warning(f"Failed to convert programmatic submit to action: {submit_element_info}")
                else:
                    import logging
                    logging.getLogger(__name__).warning("ActionConverter not available for programmatic submit")
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

