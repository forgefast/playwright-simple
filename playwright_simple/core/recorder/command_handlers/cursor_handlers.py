#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Handlers.

Handles cursor-related commands (cursor, click, type, press).
"""

from typing import Callable

# Try to import cursor controller (optional)
try:
    from ..cursor_controller import CursorController
    CURSOR_AVAILABLE = True
except ImportError:
    CursorController = None
    CURSOR_AVAILABLE = False


class CursorHandlers:
    """Handles cursor-related commands."""
    
    def __init__(
        self,
        yaml_writer,
        cursor_controller_getter: Callable
    ):
        """Initialize cursor handlers."""
        self.yaml_writer = yaml_writer
        self._get_cursor_controller = cursor_controller_getter
    
    async def handle_cursor(self, args: str) -> None:
        """Handle cursor command."""
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
        cursor_controller = self._get_cursor_controller()
        if not cursor_controller:
            print("❌ Cursor controller not available")
            return
        
        if not args:
            print("❌ Usage: press <key>")
            print("   Examples: press Enter, press Tab, press Escape")
            return
        
        key = args.strip()
        success = await cursor_controller.press_key(key)
        if success:
            print(f"⌨️  Pressed {key}")
        else:
            print(f"❌ Failed to press {key}")

