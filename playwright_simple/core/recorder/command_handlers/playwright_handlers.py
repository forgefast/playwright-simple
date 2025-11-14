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
        """Handle pw-click command - click using Playwright directly."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            print("❌ Playwright commands not available")
            return
        
        commands = self._get_playwright_commands()
        if not commands:
            print("❌ Page not available")
            return
        
        # Get cursor controller if available
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not args:
            print("❌ Usage: pw-click \"text\" | pw-click selector \"#id\" | pw-click role button [index]")
            return
        
        args = args.strip()
        index = 0
        
        # Check for index
        if '[' in args and ']' in args:
            try:
                index_part = args[args.index('[')+1:args.index(']')]
                index = int(index_part)
                args = args[:args.index('[')].strip()
            except:
                pass
        
        # Try to parse different formats
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
            success = await commands.click(selector=selector, cursor_controller=cursor_controller)
        elif args.startswith('role '):
            role = args[5:].strip().strip('"\'')
            success = await commands.click(role=role, index=index, cursor_controller=cursor_controller)
        else:
            # Treat as text
            text = args.strip('"\'')
            success = await commands.click(text=text, index=index, cursor_controller=cursor_controller)
        
        if success:
            print(f"✅ Clicked successfully")
        else:
            print(f"❌ Failed to click")
            print("   Usage examples:")
            print("     pw-click \"Entrar\"")
            print("     pw-click selector \"#login-button\"")
            print("     pw-click role button [0]")
    
    async def handle_pw_type(self, args: str) -> None:
        """Handle pw-type command - type using Playwright directly."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            print("❌ Playwright commands not available")
            return
        
        commands = self._get_playwright_commands()
        if not commands:
            print("❌ Page not available")
            return
        
        # Get cursor controller if available
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        if not args:
            print("❌ Usage: pw-type \"text\" into \"field\" | pw-type \"text\" selector \"#id\"")
            return
        
        args = args.strip()
        
        # Check for "into" keyword (support both " into " and "--into")
        if ' --into ' in args or ' --into' in args:
            # Replace --into with into for parsing
            args = args.replace('--into', 'into')
        
        if ' into ' in args.lower():
            parts = args.split(' into ', 1)
            if len(parts) == 2:
                text = parts[0].strip().strip('"\'')
                field = parts[1].strip().strip('"\'')
                
                if field.startswith('selector '):
                    selector = field[9:].strip().strip('"\'')
                    success = await commands.type_text(text, selector=selector, cursor_controller=cursor_controller)
                else:
                    success = await commands.type_text(text, into=field, cursor_controller=cursor_controller)
                
                if success:
                    print(f"✅ Typed '{text}' into '{field}'")
                else:
                    print(f"❌ Failed to type into '{field}'")
                return
        
        # No "into" - just type the text
        text = args.strip('"\'')
        print(f"⚠️  No field specified. Use: pw-type \"{text}\" into \"field\"")
    
    async def handle_pw_submit(self, args: str) -> None:
        """Handle pw-submit command - submit form using Playwright."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            print("❌ Playwright commands not available")
            return
        
        commands = self._get_playwright_commands()
        if not commands:
            print("❌ Page not available")
            return
        
        # Get cursor controller if available
        cursor_controller = None
        if self._get_cursor_controller:
            cursor_controller = self._get_cursor_controller()
        
        # Parse button text (optional)
        button_text = args.strip().strip('"\'') if args.strip() else None
        
        success = await commands.submit_form(button_text=button_text, cursor_controller=cursor_controller)
        
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

