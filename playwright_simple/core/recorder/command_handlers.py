#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Console command handlers for recorder.

Handles user commands during recording session.
"""

import logging
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)

# Try to import PlaywrightCommands
try:
    from ..playwright_commands import PlaywrightCommands
    PLAYWRIGHT_COMMANDS_AVAILABLE = True
except ImportError:
    PlaywrightCommands = None
    PLAYWRIGHT_COMMANDS_AVAILABLE = False

# Try to import cursor controller (optional)
try:
    from .cursor_controller import CursorController
    CURSOR_AVAILABLE = True
except ImportError:
    CursorController = None
    CURSOR_AVAILABLE = False


class CommandHandlers:
    """Handles console commands during recording."""
    
    def __init__(
        self,
        yaml_writer,
        event_capture_getter: Callable,
        cursor_controller_getter: Callable,
        recording_state_setter: Callable,
        paused_state_setter: Callable,
        page_getter: Optional[Callable] = None
    ):
        """
        Initialize command handlers.
        
        Args:
            yaml_writer: YAMLWriter instance
            event_capture_getter: Callable that returns EventCapture instance
            cursor_controller_getter: Callable that returns CursorController instance
            recording_state_setter: Callable to set recording state
            paused_state_setter: Callable to set paused state
            page_getter: Optional callable that returns Playwright Page instance
        """
        self.yaml_writer = yaml_writer
        self._get_event_capture = event_capture_getter
        self._get_cursor_controller = cursor_controller_getter
        self._set_recording = recording_state_setter
        self._set_paused = paused_state_setter
        self._get_page = page_getter
        self._playwright_commands = None
    
    async def handle_start(self, args: str, is_recording: bool) -> None:
        """Handle start command."""
        if is_recording:
            print("⚠️  Already recording")
            return
        
        self._set_paused(False)
        self._set_recording(True)
        event_capture = self._get_event_capture()
        if event_capture:
            await event_capture.start()
        print("✅ Recording started")
    
    async def handle_save(self, args: str) -> None:
        """Handle save command - save YAML without stopping."""
        logger.info("Save command handler called")
        steps_count = self.yaml_writer.get_steps_count()
        
        if steps_count > 0:
            logger.info(f"Saving YAML (continuing recording)... Total steps: {steps_count}")
            success = self.yaml_writer.save()
            if success:
                saved_path = self.yaml_writer.output_path.resolve()
                logger.info(f"✅ YAML saved successfully to: {saved_path}")
                print(f"\n💾 YAML saved! (continuing recording)")
                print(f"   File: {saved_path}")
                print(f"   Steps saved: {steps_count}")
                print(f"   Continue interacting...\n")
            else:
                logger.error(f"❌ Failed to save YAML")
                print(f"\n❌ Failed to save YAML")
                print(f"   Check log file for details\n")
        else:
            logger.warning("No steps to save yet")
            print(f"\n⚠️  No steps recorded yet")
            print(f"   Continue interacting and try again\n")
    
    @property
    def output_path(self):
        """Get output path from yaml_writer."""
        return self.yaml_writer.output_path
    
    async def handle_exit(self, args: str) -> None:
        """Handle exit command - exit without saving."""
        logger.info("Exit command handler called")
        print("🚪 Exiting without saving...")
        logger.info("Exit command handler completed (stop(save=False) will be called from _wait_for_exit)")
    
    async def handle_pause(self, args: str) -> None:
        """Handle pause command."""
        self._set_paused(True)
        print("⏸️  Recording paused")
    
    async def handle_resume(self, args: str) -> None:
        """Handle resume command."""
        self._set_paused(False)
        print("▶️  Recording resumed")
    
    async def handle_caption(self, args: str) -> None:
        """Handle caption command."""
        if not args:
            print("❌ Usage: caption \"text\"")
            return
        
        self.yaml_writer.add_caption(args)
        print(f"📝 Caption added: {args}")
    
    async def handle_audio(self, args: str) -> None:
        """Handle audio command."""
        if not args:
            print("❌ Usage: audio \"text\"")
            return
        
        self.yaml_writer.add_audio(args)
        print(f"🔊 Audio added: {args}")
    
    async def handle_screenshot(self, args: str) -> None:
        """Handle screenshot command."""
        name = args if args else None
        self.yaml_writer.add_screenshot(name)
        print(f"📸 Screenshot step added: {name or 'auto'}")
    
    async def handle_cursor(self, args: str) -> None:
        """Handle cursor command."""
        if not CURSOR_AVAILABLE:
            cursor_controller = self._get_cursor_controller()
            if not cursor_controller:
                print("❌ Cursor controller not available")
                return
        else:
            cursor_controller = self._get_cursor_controller()
            if not cursor_controller:
                print("❌ Cursor controller not available")
                return
        
        args = args.strip().lower()
        
        if args == 'show':
            await cursor_controller.show()
            print("👆 Cursor shown")
        elif args == 'hide':
            await cursor_controller.hide()
            print("👆 Cursor hidden")
        elif args.startswith('move'):
            # Parse: cursor move x y
            parts = args.split()
            if len(parts) >= 3:
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                    await cursor_controller.move(x, y)
                    print(f"👆 Cursor moved to ({x}, {y})")
                except ValueError:
                    print("❌ Invalid coordinates. Usage: cursor move <x> <y>")
            else:
                print("❌ Usage: cursor move <x> <y>")
        elif args == 'info' or args == 'element':
            # Get element at cursor position
            element = await cursor_controller.get_element_at(
                cursor_controller.current_x,
                cursor_controller.current_y
            )
            if element:
                print(f"👆 Element at cursor:")
                print(f"   Tag: {element.get('tagName', 'N/A')}")
                print(f"   Text: {element.get('text', 'N/A')[:50]}")
                print(f"   ID: {element.get('id', 'N/A')}")
                print(f"   Name: {element.get('name', 'N/A')}")
            else:
                print("❌ No element at cursor position")
        else:
            print("📝 Cursor commands:")
            print("   cursor show - Show cursor")
            print("   cursor hide - Hide cursor")
            print("   cursor move <x> <y> - Move cursor to coordinates")
            print("   cursor info - Show element info at cursor position")
            if CURSOR_AVAILABLE:
                print("   click <text> - Click element by text (e.g., 'click Entrar')")
                print("   click - Click at cursor position")
                print("   type <text> [into <field>] - Type text into a field")
                print("   press <key> - Press a key (Enter, Tab, Escape, etc.)")
    
    async def handle_cursor_click(self, args: str) -> None:
        """Handle click command (cursor click by text or position)."""
        if not CURSOR_AVAILABLE:
            cursor_controller = self._get_cursor_controller()
            if not cursor_controller:
                print("❌ Cursor controller not available")
                return
        else:
            cursor_controller = self._get_cursor_controller()
            if not cursor_controller:
                print("❌ Cursor controller not available")
                return
        
        args = args.strip()
        
        if args:
            # Try to parse as coordinates first (for backward compatibility)
            parts = args.split()
            if len(parts) >= 2:
                try:
                    x = int(parts[0])
                    y = int(parts[1])
                    # It's coordinates
                    await cursor_controller.move(x, y)
                    await cursor_controller.click(x, y)
                    print(f"👆 Clicked at ({x}, {y})")
                    return
                except ValueError:
                    pass  # Not coordinates, treat as text
            
            # Treat as text to search for
            success = await cursor_controller.click_by_text(args)
            if success:
                print(f"👆 Clicked on '{args}'")
            else:
                print(f"❌ Element '{args}' not found")
                print("   Tips:")
                print("     - For buttons: click Entrar")
                print("     - For submit buttons: click submit (or click submit Entrar)")
                print("     - For inputs by placeholder: click placeholder senha")
                print("     - For inputs by label/name: click input senha")
                print("     - Use 'cursor info' to see element details")
        else:
            # Click at current cursor position
            if cursor_controller.current_x == 0 and cursor_controller.current_y == 0:
                print("❌ Cursor not positioned. Use 'cursor move <x> <y>' first or 'click <text>'")
            else:
                await cursor_controller.click()
                print(f"👆 Clicked at cursor position ({cursor_controller.current_x}, {cursor_controller.current_y})")
    
    async def handle_type(self, args: str) -> None:
        """Handle type command - type text into a field."""
        if not CURSOR_AVAILABLE:
            cursor_controller = self._get_cursor_controller()
            if not cursor_controller:
                print("❌ Cursor controller not available")
                return
        else:
            cursor_controller = self._get_cursor_controller()
            if not cursor_controller:
                print("❌ Cursor controller not available")
                return
        
        args = args.strip()
        
        if not args:
            print("❌ Usage: type <text> [into <field>]")
            print("   Examples:")
            print("     type admin")
            print("     type admin into E-mail")
            print("     type admin into login")
            return
        
        # Check if "into" is specified
        if ' into ' in args.lower():
            parts = args.split(' into ', 1)
            if len(parts) == 2:
                text = parts[0].strip()
                field = parts[1].strip()
                success = await cursor_controller.type_text(text, field)
                if success:
                    print(f"⌨️  Typed '{text}' into '{field}'")
                else:
                    print(f"❌ Field '{field}' not found")
                    print("   Tip: Use field label, placeholder, name, or id")
            else:
                print("❌ Invalid format. Usage: type <text> into <field>")
        else:
            # Type into focused field or first input
            success = await cursor_controller.type_text(args)
            if success:
                print(f"⌨️  Typed '{args}'")
            else:
                print(f"❌ No input field found to type into")
                print("   Tip: Use 'type <text> into <field>' to specify field")
    
    async def handle_press(self, args: str) -> None:
        """Handle press command - press a key."""
        if not CURSOR_AVAILABLE:
            cursor_controller = self._get_cursor_controller()
            if not cursor_controller:
                print("❌ Cursor controller not available")
                return
        else:
            cursor_controller = self._get_cursor_controller()
            if not cursor_controller:
                print("❌ Cursor controller not available")
                return
        
        args = args.strip()
        
        if not args:
            print("❌ Usage: press <key>")
            print("   Examples:")
            print("     press Enter")
            print("     press Tab")
            print("     press Escape")
            print("     press Space")
            return
        
        await cursor_controller.press_key(args)
        print(f"⌨️  Pressed key: {args}")
    
    def _get_playwright_commands(self):
        """Get or create PlaywrightCommands instance."""
        if not PLAYWRIGHT_COMMANDS_AVAILABLE:
            return None
        
        if self._playwright_commands is None and self._get_page:
            try:
                page = self._get_page()
                if page:
                    self._playwright_commands = PlaywrightCommands(page)
            except Exception as e:
                logger.debug(f"Error creating PlaywrightCommands: {e}")
        
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
        cursor_controller = self._get_cursor_controller()
        
        if not args:
            print("❌ Usage: pw-type \"text\" into \"field\" | pw-type \"text\" selector \"#id\"")
            return
        
        args = args.strip()
        
        # Check for "into" keyword
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
            import re
            match = re.search(r'--max-length\s+(\d+)|--max\s+(\d+)', args)
            if match:
                max_length = int(match.group(1) or match.group(2))
        
        html = await commands.get_html(selector=selector, pretty=pretty, max_length=max_length)
        
        if html:
            if max_length and len(html) > max_length:
                print(f"📄 HTML ({len(html)} characters, truncated):")
            else:
                print(f"📄 HTML ({len(html)} characters):")
            print("-" * 60)
            print(html)
            print("-" * 60)
            
            # Also suggest saving to file if long
            if len(html) > 1000:
                print(f"\n💡 Dica: HTML é grande ({len(html)} caracteres). Considere salvar em arquivo:")
                print(f"   playwright-simple html --selector \"{selector or ''}\" > page.html")
        else:
            if selector:
                print(f"❌ Elemento não encontrado ou erro ao obter HTML")
                print(f"   Seletor: {selector}")
            else:
                print("❌ Erro ao obter HTML da página")

