#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Server for Recorder.

Allows external commands (from CLI) to control an active recording session.
Uses file-based IPC for communication.
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CommandServer:
    """File-based command server for recorder."""
    
    def __init__(self, recorder_instance, session_id: Optional[str] = None):
        """
        Initialize command server.
        
        Args:
            recorder_instance: Recorder instance to control
            session_id: Optional session ID (defaults to PID-based)
        """
        self.recorder = recorder_instance
        self.session_id = session_id or f"recorder_{os.getpid()}"
        
        # Use temp directory for command files
        self.temp_dir = Path(tempfile.gettempdir()) / "playwright-simple"
        self.temp_dir.mkdir(exist_ok=True)
        
        self.command_file = self.temp_dir / f"{self.session_id}.commands"
        self.response_file = self.temp_dir / f"{self.session_id}.response"
        self.lock_file = self.temp_dir / f"{self.session_id}.lock"
        
        self.is_running = False
        self.command_handlers: Dict[str, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default command handlers."""
        self.register_handler('find', self._handle_find)
        self.register_handler('find-all', self._handle_find_all)
        self.register_handler('click', self._handle_click)
        self.register_handler('type', self._handle_type)
        self.register_handler('wait', self._handle_wait)
        self.register_handler('info', self._handle_info)
        self.register_handler('html', self._handle_html)
        self.register_handler('navigate', self._handle_navigate)
    
    def register_handler(self, command: str, handler: Callable):
        """Register a command handler."""
        self.command_handlers[command] = handler
    
    async def start(self):
        """Start command server."""
        self.is_running = True
        
        # Create lock file to indicate server is running
        self.lock_file.write_text(json.dumps({
            'session_id': self.session_id,
            'pid': os.getpid(),
            'started_at': datetime.now().isoformat()
        }))
        
        # Start polling loop
        asyncio.create_task(self._poll_commands())
        logger.info(f"Command server started (session: {self.session_id})")
    
    async def stop(self):
        """Stop command server."""
        self.is_running = False
        
        # Clean up files
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
            if self.command_file.exists():
                self.command_file.unlink()
            if self.response_file.exists():
                self.response_file.unlink()
        except Exception as e:
            logger.debug(f"Error cleaning up command files: {e}")
        
        logger.info("Command server stopped")
    
    async def _poll_commands(self):
        """Poll for commands from file."""
        while self.is_running:
            try:
                if self.command_file.exists():
                    # Read command
                    content = self.command_file.read_text()
                    if content.strip():
                        command_data = json.loads(content)
                        
                        # Process command
                        response = await self._process_command(command_data)
                        
                        # Write response
                        self.response_file.write_text(json.dumps(response))
                        
                        # Clear command file
                        self.command_file.write_text('')
                        
                        logger.debug(f"Processed command: {command_data.get('command')}")
                
                await asyncio.sleep(0.1)  # Poll every 100ms
                
            except json.JSONDecodeError:
                # Invalid JSON, clear file
                if self.command_file.exists():
                    self.command_file.write_text('')
            except Exception as e:
                logger.error(f"Error polling commands: {e}", exc_info=True)
                await asyncio.sleep(0.5)
    
    async def _process_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a command."""
        command = command_data.get('command', '').lower()
        args = command_data.get('args', '')
        command_id = command_data.get('id', '')
        
        try:
            if command in self.command_handlers:
                result = await self.command_handlers[command](args)
                return {
                    'success': True,
                    'id': command_id,
                    'result': result
                }
            else:
                return {
                    'success': False,
                    'id': command_id,
                    'error': f'Unknown command: {command}'
                }
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}", exc_info=True)
            return {
                'success': False,
                'id': command_id,
                'error': str(e)
            }
    
    async def _handle_find(self, args: str) -> Dict[str, Any]:
        """Handle find command."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands import PlaywrightCommands
        commands = PlaywrightCommands(page)
        
        args = args.strip()
        
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
            element = await commands.find_element(selector=selector)
        elif args.startswith('role '):
            role = args[5:].strip().strip('"\'')
            element = await commands.find_element(role=role)
        else:
            text = args.strip('"\'')
            element = await commands.find_element(text=text)
        
        return {'element': element}
    
    async def _handle_find_all(self, args: str) -> Dict[str, Any]:
        """Handle find-all command."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands import PlaywrightCommands
        commands = PlaywrightCommands(page)
        
        args = args.strip()
        
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
            elements = await commands.find_all_elements(selector=selector)
        elif args.startswith('role '):
            role = args[5:].strip().strip('"\'')
            elements = await commands.find_all_elements(role=role)
        else:
            text = args.strip('"\'')
            elements = await commands.find_all_elements(text=text)
        
        return {'elements': elements}
    
    async def _handle_click(self, args: str) -> Dict[str, Any]:
        """Handle click command."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands import PlaywrightCommands
        commands = PlaywrightCommands(page)
        
        # Get cursor controller if available
        cursor_controller = None
        if hasattr(self.recorder, 'cursor_controller') and self.recorder.cursor_controller:
            cursor_controller = self.recorder.cursor_controller
        
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
        
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
            success = await commands.click(selector=selector, cursor_controller=cursor_controller)
        elif args.startswith('role '):
            role = args[5:].strip().strip('"\'')
            success = await commands.click(role=role, index=index, cursor_controller=cursor_controller)
        else:
            text = args.strip('"\'')
            success = await commands.click(text=text, index=index, cursor_controller=cursor_controller)
        
        return {'success': success}
    
    async def _handle_type(self, args: str) -> Dict[str, Any]:
        """Handle type command."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands import PlaywrightCommands
        commands = PlaywrightCommands(page)
        
        args = args.strip()
        
        if ' into ' in args.lower():
            parts = args.split(' into ', 1)
            if len(parts) == 2:
                text = parts[0].strip().strip('"\'')
                field = parts[1].strip().strip('"\'')
                
                if field.startswith('selector '):
                    selector = field[9:].strip().strip('"\'')
                    success = await commands.type_text(text, selector=selector)
                else:
                    success = await commands.type_text(text, into=field)
                
                return {'success': success}
        
        return {'error': 'Usage: type "text" into "field"'}
    
    async def _handle_wait(self, args: str) -> Dict[str, Any]:
        """Handle wait command."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands import PlaywrightCommands
        commands = PlaywrightCommands(page)
        
        args = args.strip()
        timeout = 5000
        
        parts = args.split()
        if len(parts) >= 2 and parts[-1].isdigit():
            timeout = int(parts[-1]) * 1000
            args = ' '.join(parts[:-1])
        
        if args.startswith('selector '):
            selector = args[9:].strip().strip('"\'')
            success = await commands.wait_for_element(selector=selector, timeout=timeout)
        elif args.startswith('role '):
            role = args[5:].strip().strip('"\'')
            success = await commands.wait_for_element(role=role, timeout=timeout)
        else:
            text = args.strip('"\'')
            success = await commands.wait_for_element(text=text, timeout=timeout)
        
        return {'success': success}
    
    async def _handle_info(self, args: str) -> Dict[str, Any]:
        """Handle info command."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands import PlaywrightCommands
        commands = PlaywrightCommands(page)
        
        info = await commands.get_page_info()
        return {'info': info}
    
    async def _handle_html(self, args: str) -> Dict[str, Any]:
        """Handle html command - get HTML of page or element."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands import PlaywrightCommands
        commands = PlaywrightCommands(page)
        
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
        
        if html is not None:
            return {'html': html, 'length': len(html)}
        else:
            return {'error': 'Failed to get HTML'}
    
    def _get_page(self):
        """Get page from recorder."""
        # Try recorder.page first
        if hasattr(self.recorder, 'page') and self.recorder.page:
            return self.recorder.page
        
        # Try browser_manager.page
        if hasattr(self.recorder, 'browser_manager') and self.recorder.browser_manager:
            if hasattr(self.recorder.browser_manager, 'page') and self.recorder.browser_manager.page:
                return self.recorder.browser_manager.page
            
            # Try to get from context
            if hasattr(self.recorder.browser_manager, 'context') and self.recorder.browser_manager.context:
                context = self.recorder.browser_manager.context
                # Playwright context has pages property
                try:
                    if hasattr(context, 'pages'):
                        pages = context.pages
                        if pages and len(pages) > 0:
                            return pages[0]
                except Exception:
                    pass
        
        return None
    
    async def _handle_navigate(self, args: str) -> Dict[str, Any]:
        """Handle navigate command."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands import PlaywrightCommands
        commands = PlaywrightCommands(page)
        
        url = args.strip().strip('"\'')
        success = await commands.navigate(url)
        return {'success': success}


def find_active_sessions() -> list:
    """Find all active recording sessions."""
    temp_dir = Path(tempfile.gettempdir()) / "playwright-simple"
    if not temp_dir.exists():
        return []
    
    sessions = []
    for lock_file in temp_dir.glob("*.lock"):
        try:
            data = json.loads(lock_file.read_text())
            # Check if process is still running
            if PSUTIL_AVAILABLE:
                try:
                    process = psutil.Process(data['pid'])
                    if process.is_running():
                        sessions.append({
                            'session_id': data['session_id'],
                            'pid': data['pid'],
                            'started_at': data.get('started_at')
                        })
                    else:
                        # Process died, clean up
                        lock_file.unlink()
                except psutil.NoSuchProcess:
                    # Process died, clean up
                    lock_file.unlink()
            else:
                # Without psutil, just check if file exists and is recent
                # (less reliable but works)
                sessions.append({
                    'session_id': data['session_id'],
                    'pid': data['pid'],
                    'started_at': data.get('started_at')
                })
        except Exception as e:
            logger.debug(f"Error reading lock file {lock_file}: {e}")
    
    return sessions


def send_command(command: str, args: str = "", session_id: Optional[str] = None, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Send command to active recording session.
    
    Args:
        command: Command name
        args: Command arguments
        session_id: Optional session ID (uses first available if not specified)
        timeout: Timeout in seconds
    
    Returns:
        Response dictionary
    """
    import time
    import uuid
    
    temp_dir = Path(tempfile.gettempdir()) / "playwright-simple"
    temp_dir.mkdir(exist_ok=True)
    
    # Find session
    if not session_id:
        sessions = find_active_sessions()
        if not sessions:
            return {'success': False, 'error': 'No active recording session found'}
        session_id = sessions[0]['session_id']
    
    command_file = temp_dir / f"{session_id}.commands"
    response_file = temp_dir / f"{session_id}.response"
    
    # Check if session exists
    lock_file = temp_dir / f"{session_id}.lock"
    if not lock_file.exists():
        return {'success': False, 'error': f'Session {session_id} not found'}
    
    # Send command
    command_id = str(uuid.uuid4())
    command_data = {
        'id': command_id,
        'command': command,
        'args': args
    }
    
    command_file.write_text(json.dumps(command_data))
    
    # Wait for response
    start_time = time.time()
    while time.time() - start_time < timeout:
        if response_file.exists():
            try:
                response_data = json.loads(response_file.read_text())
                if response_data.get('id') == command_id:
                    # Clear response
                    response_file.write_text('')
                    return response_data
            except json.JSONDecodeError:
                pass
        
        time.sleep(0.1)
    
    return {'success': False, 'error': 'Timeout waiting for response'}

