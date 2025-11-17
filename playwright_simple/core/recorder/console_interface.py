#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Console interface module.

Provides interactive console for commands during recording.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from threading import Thread
import sys

logger = logging.getLogger(__name__)


class ConsoleInterface:
    """Interactive console interface for recording commands."""
    
    def __init__(self):
        """Initialize console interface."""
        self.command_handlers: Dict[str, Callable] = {}
        self.is_running = False
        self.input_thread: Optional[Thread] = None
        self.command_queue = asyncio.Queue()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
    
    def register_command(self, command: str, handler: Callable):
        """
        Register command handler.
        
        Args:
            command: Command name
            handler: Async function to handle the command
        """
        self.command_handlers[command] = handler
    
    async def start(self, loop: asyncio.AbstractEventLoop):
        """
        Start console interface.
        
        Args:
            loop: Event loop for async operations
        """
        self.loop = loop
        self.is_running = True
        
        # Start input thread
        self.input_thread = Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        
        logger.info("Console interface started")
    
    def stop(self):
        """Stop console interface."""
        self.is_running = False
        if self.input_thread:
            self.input_thread.join(timeout=1.0)
        logger.info("Console interface stopped")
    
    def _input_loop(self):
        """Input loop running in separate thread."""
        while self.is_running:
            try:
                # Read input (non-blocking would be better, but this works)
                line = input().strip()
                if line and self.loop:
                    # Schedule command processing in event loop
                    asyncio.run_coroutine_threadsafe(
                        self._process_command(line),
                        self.loop
                    )
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error reading input: {e}")
                break
    
    async def _process_command(self, line: str):
        """Process command from input."""
        if not line:
            return
        
        parts = line.split(None, 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''
        
        # Remove quotes from args if present
        if args.startswith('"') and args.endswith('"'):
            args = args[1:-1]
        elif args.startswith("'") and args.endswith("'"):
            args = args[1:-1]
        
        # Also put command in queue for wait_for_command
        try:
            await self.command_queue.put({'command': command, 'args': args})
        except Exception as e:
            logger.debug(f"Error putting command in queue: {e}")
        
        # Execute handler if exists
        if command in self.command_handlers:
            try:
                logger.info(f"Executing command: {command}")
                await self.command_handlers[command](args)
            except Exception as e:
                logger.error(f"Error executing command '{command}': {e}", exc_info=True)
                print(f"❌ Error executing command '{command}': {e}")
        elif command == 'help':
            self._show_help()
        else:
            print(f"❓ Unknown command: {command}. Type 'help' for available commands.")
    
    def _show_help(self):
        """Show help message."""
        print("\n📝 Available commands:")
        print("\n🎬 Recording commands:")
        print("   start - Start recording")
        print("   save - Save YAML without stopping (continues recording)")
        print("   exit - Exit without saving")
        print("   pause - Pause recording")
        print("   resume - Resume recording")
        print('   caption "text" - Add caption/subtitle step')
        print('   subtitle "text" - Add subtitle to last step (for video)')
        print('   audio "text" - Add audio narration step')
        print('   audio-step "text" - Add audio to last step (for video narration)')
        print("   screenshot - Take screenshot")
        print("\n🎯 Playwright Direct Commands (for AI assistants & manual testing):")
        print("   find \"text\" - Find element by text")
        print("   find selector \"#id\" - Find element by CSS selector")
        print("   find role button - Find element by ARIA role")
        print("   find-all \"text\" - Find all matching elements")
        print("   pw-click \"text\" - Click element using Playwright directly")
        print("   pw-click selector \"#id\" - Click by selector")
        print("   pw-click role button [0] - Click by role (with index)")
        print("   pw-type \"text\" into \"field\" - Type text into field")
        print("   pw-press \"Enter\" - Press a key (Enter, Tab, Escape, Space, etc.)")
        print("   pw-wait \"text\" [timeout] - Wait for element to appear")
        print("   pw-info - Show page information (URL, title, etc.)")
        print("   pw-html [selector] [--pretty] [--max-length N] - Get HTML of page or element")
        print("\n👆 Cursor commands (if available):")
        print("   cursor show/hide/move <x> <y>/info - Control cursor overlay")
        print("   click [<text>] - Click element by text")
        print("                    Examples: 'click Entrar', 'click submit'")
        print("   type <text> [into <field>] - Type text into a field")
        print("   press <key> - Press a key (Enter, Tab, Escape, Space, etc.)")
        print("\n💡 Examples:")
        print("   find \"Entrar\"")
        print("   pw-click \"Entrar\"")
        print("   pw-type \"admin@example.com\" into \"E-mail\"")
        print("   pw-wait \"Login\" 10")
        print("   help - Show this help")
        print()
    
    async def wait_for_command(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Wait for command from queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Command dictionary or None
        """
        try:
            return await asyncio.wait_for(self.command_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
    def send_command(self, command: str, args: Any = None):
        """
        Send command to queue.
        
        Args:
            command: Command name
            args: Command arguments
        """
        asyncio.run_coroutine_threadsafe(
            self.command_queue.put({'command': command, 'args': args}),
            self.loop
        )

