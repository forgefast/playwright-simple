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
        self._recorder = recorder  # Store recorder reference for fast_mode and speed_level
        self.recorder_logger = recorder_logger
    
    def _get_delay_from_speed_level(self, normal_delay: float, fast_delay: float = None) -> float:
        """
        Get delay based on speed_level from recorder.
        
        Args:
            normal_delay: Delay for NORMAL/SLOW mode
            fast_delay: Optional delay for FAST mode (defaults to normal_delay * 0.1)
        
        Returns:
            Delay adjusted for speed_level
        """
        if not self._recorder:
            return normal_delay
        
        # Try to get speed_level first
        speed_level = getattr(self._recorder, 'speed_level', None)
        if speed_level:
            try:
                from ..config import SpeedLevel
                if speed_level == SpeedLevel.ULTRA_FAST:
                    return 0.0  # Ultra fast: no delay
                elif speed_level == SpeedLevel.FAST:
                    return fast_delay if fast_delay is not None else normal_delay * 0.1
                # NORMAL and SLOW use normal_delay
                return normal_delay
            except ImportError:
                pass
        
        # Fallback to fast_mode for backward compatibility
        fast_mode = getattr(self._recorder, 'fast_mode', False)
        if fast_mode:
            return fast_delay if fast_delay is not None else normal_delay * 0.1
        
        return normal_delay
    
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
        """Handle pw-click command."""
        from .click_handler import ClickHandler
        
        handler = ClickHandler(
            self.yaml_writer,
            self._get_page,
            self._get_cursor_controller,
            self._recorder,
            self.recorder_logger
        )
        return await handler.handle_click(args)
    
    async def handle_pw_type(self, args: str) -> Dict[str, Any]:
        """Handle pw-type command."""
        from .type_handler import TypeHandler
        
        handler = TypeHandler(
            self.yaml_writer,
            self._get_page,
            self._get_cursor_controller,
            self._recorder,
            self.recorder_logger
        )
        return await handler.handle_type(args)
    
    async def handle_pw_submit(self, args: str) -> Dict[str, Any]:
        """Handle pw-submit command."""
        from .submit_handler import SubmitHandler
        
        handler = SubmitHandler(
            self.yaml_writer,
            self._get_page,
            self._get_cursor_controller,
            self._recorder,
            self.recorder_logger
        )
        return await handler.handle_submit(args)
    
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

