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

# Try to import psutil for process checking
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

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
        # Playwright commands
        self.register_handler('find', self._handle_find)
        self.register_handler('find-all', self._handle_find_all)
        self.register_handler('click', self._handle_click)
        self.register_handler('type', self._handle_type)
        self.register_handler('submit', self._handle_submit)
        self.register_handler('wait', self._handle_wait)
        self.register_handler('info', self._handle_info)
        self.register_handler('html', self._handle_html)
        self.register_handler('navigate', self._handle_navigate)
        
        # Recording control commands
        self.register_handler('save', self._handle_save)
        self.register_handler('exit', self._handle_exit)
        self.register_handler('pause', self._handle_pause)
        self.register_handler('resume', self._handle_resume)
        self.register_handler('start', self._handle_start)
        
        # Metadata commands
        self.register_handler('caption', self._handle_caption)
        self.register_handler('subtitle', self._handle_subtitle)
        self.register_handler('audio', self._handle_audio)
        self.register_handler('audio-step', self._handle_audio_step)
        self.register_handler('screenshot', self._handle_screenshot)
        
        # Video config commands (simple implementation)
        self.register_handler('video-enable', self._handle_video_enable)
        self.register_handler('video-disable', self._handle_video_disable)
        self.register_handler('video-quality', self._handle_video_quality)
        self.register_handler('video-codec', self._handle_video_codec)
        self.register_handler('video-dir', self._handle_video_dir)
    
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
        """Handle click command using CursorController directly."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands.unified import parse_click_args
        
        # Get cursor controller
        cursor_controller = None
        if hasattr(self.recorder, 'cursor_controller') and self.recorder.cursor_controller:
            cursor_controller = self.recorder.cursor_controller
        
        if not cursor_controller:
            return {'error': 'CursorController not available'}
        
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
        
        return {'success': success}
    
    async def _handle_type(self, args: str) -> Dict[str, Any]:
        """Handle type command using CursorController directly."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        from ..playwright_commands.unified import parse_type_args
        
        # Get cursor controller
        cursor_controller = None
        if hasattr(self.recorder, 'cursor_controller') and self.recorder.cursor_controller:
            cursor_controller = self.recorder.cursor_controller
        
        if not cursor_controller:
            return {'error': 'CursorController not available'}
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Parse arguments using unified parser
        parsed = parse_type_args(args)
        
        if not parsed['text']:
            return {'error': 'Usage: type "text" into "field"'}
        
        # Execute type using CursorController
        field_selector = parsed['selector'] or parsed['into'] or None
        success = await cursor_controller.type_text(parsed['text'], field_selector)
        
        return {'success': success}
    
    async def _handle_submit(self, args: str) -> Dict[str, Any]:
        """Handle submit command using CursorController directly."""
        page = self._get_page()
        if not page:
            return {'error': 'Page not available'}
        
        # Get cursor controller
        cursor_controller = None
        if hasattr(self.recorder, 'cursor_controller') and self.recorder.cursor_controller:
            cursor_controller = self.recorder.cursor_controller
        
        if not cursor_controller:
            return {'error': 'CursorController not available'}
        
        # Ensure cursor controller is started
        if not cursor_controller.is_active:
            await cursor_controller.start()
        
        # Parse button text (optional)
        button_text = args.strip().strip('"\'') if args.strip() else None
        
        # Execute submit using CursorController
        success = await cursor_controller.submit_form(button_text)
        
        return {'success': success}
    
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
    
    # Recording control handlers
    async def _handle_save(self, args: str) -> Dict[str, Any]:
        """Handle save command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        await self.recorder.command_handlers.handle_save(args)
        return {'success': True, 'message': 'YAML saved (recording continues)'}
    
    async def _handle_exit(self, args: str) -> Dict[str, Any]:
        """Handle exit command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        await self.recorder.command_handlers.handle_exit(args)
        return {'success': True, 'message': 'Exiting without saving'}
    
    async def _handle_pause(self, args: str) -> Dict[str, Any]:
        """Handle pause command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        await self.recorder.command_handlers.handle_pause(args)
        return {'success': True, 'message': 'Recording paused'}
    
    async def _handle_resume(self, args: str) -> Dict[str, Any]:
        """Handle resume command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        await self.recorder.command_handlers.handle_resume(args)
        return {'success': True, 'message': 'Recording resumed'}
    
    async def _handle_start(self, args: str) -> Dict[str, Any]:
        """Handle start command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        is_recording = getattr(self.recorder, 'is_recording', False)
        await self.recorder.command_handlers.handle_start(args, is_recording)
        return {'success': True, 'message': 'Recording started'}
    
    # Metadata handlers
    async def _handle_caption(self, args: str) -> Dict[str, Any]:
        """Handle caption command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        text = args.strip().strip('"\'')
        if not text:
            return {'error': 'Caption text is required'}
        
        await self.recorder.command_handlers.handle_caption(text)
        return {'success': True, 'message': f'Caption added: {text}'}
    
    async def _handle_subtitle(self, args: str) -> Dict[str, Any]:
        """Handle subtitle command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        text = args.strip().strip('"\'') if args else ""
        
        await self.recorder.command_handlers.handle_subtitle(text)
        return {'success': True, 'message': f'Subtitle added to last step: {text}' if text else 'Subtitle cleared from last step'}
    
    async def _handle_audio_step(self, args: str) -> Dict[str, Any]:
        """Handle audio-step command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        text = args.strip().strip('"\'') if args else ""
        
        await self.recorder.command_handlers.handle_audio_step(text)
        return {'success': True, 'message': f'Audio added to last step: {text}' if text else 'Audio cleared from last step'}
    
    async def _handle_audio(self, args: str) -> Dict[str, Any]:
        """Handle audio command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        text = args.strip().strip('"\'')
        if not text:
            return {'error': 'Audio text is required'}
        
        await self.recorder.command_handlers.handle_audio(text)
        return {'success': True, 'message': f'Audio added: {text}'}
    
    async def _handle_screenshot(self, args: str) -> Dict[str, Any]:
        """Handle screenshot command."""
        if not hasattr(self.recorder, 'command_handlers'):
            return {'error': 'Command handlers not available'}
        
        # Parse name if provided
        name = args.strip().strip('"\'') if args.strip() else None
        await self.recorder.command_handlers.handle_screenshot(name or '')
        return {'success': True, 'message': f'Screenshot added: {name or "auto"}'}
    
    def _get_yaml_writer(self):
        """Get YAML writer from recorder."""
        if hasattr(self.recorder, 'yaml_writer') and self.recorder.yaml_writer:
            return self.recorder.yaml_writer
        return None
    
    async def _handle_video_enable(self, args: str) -> Dict[str, Any]:
        """Handle video-enable command."""
        yaml_writer = self._get_yaml_writer()
        if not yaml_writer:
            return {'error': 'YAML writer not available (not in write mode)'}
        yaml_writer.set_config('video', 'enabled', True)
        return {'success': True, 'message': 'Video recording enabled in YAML'}
    
    async def _handle_video_disable(self, args: str) -> Dict[str, Any]:
        """Handle video-disable command."""
        yaml_writer = self._get_yaml_writer()
        if not yaml_writer:
            return {'error': 'YAML writer not available (not in write mode)'}
        yaml_writer.set_config('video', 'enabled', False)
        return {'success': True, 'message': 'Video recording disabled in YAML'}
    
    async def _handle_video_quality(self, args: str) -> Dict[str, Any]:
        """Handle video-quality command."""
        yaml_writer = self._get_yaml_writer()
        if not yaml_writer:
            return {'error': 'YAML writer not available (not in write mode)'}
        quality = args.strip().lower()
        if quality not in ['low', 'medium', 'high']:
            return {'error': f'Invalid quality: {quality}. Must be low, medium, or high'}
        yaml_writer.set_config('video', 'quality', quality)
        return {'success': True, 'message': f'Video quality set to: {quality}'}
    
    async def _handle_video_codec(self, args: str) -> Dict[str, Any]:
        """Handle video-codec command."""
        yaml_writer = self._get_yaml_writer()
        if not yaml_writer:
            return {'error': 'YAML writer not available (not in write mode)'}
        codec = args.strip().lower()
        if codec not in ['webm', 'mp4']:
            return {'error': f'Invalid codec: {codec}. Must be webm or mp4'}
        yaml_writer.set_config('video', 'codec', codec)
        return {'success': True, 'message': f'Video codec set to: {codec}'}
    
    async def _handle_video_dir(self, args: str) -> Dict[str, Any]:
        """Handle video-dir command."""
        yaml_writer = self._get_yaml_writer()
        if not yaml_writer:
            return {'error': 'YAML writer not available (not in write mode)'}
        video_dir = args.strip().strip('"\'')
        yaml_writer.set_config('video', 'dir', video_dir)
        return {'success': True, 'message': f'Video directory set to: {video_dir}'}


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


def cleanup_orphan_browser_processes(timeout: float = 5.0) -> int:
    """
    Clean up orphaned browser processes (chromium, firefox, webkit, ffmpeg) from Playwright.
    
    Args:
        timeout: Maximum time to spend on cleanup (seconds)
    
    Returns:
        Number of processes killed
    """
    if not PSUTIL_AVAILABLE:
        return 0
    
    import time
    start_time = time.time()
    killed = 0
    
    try:
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
            if time.time() - start_time > timeout:
                break
            
            try:
                # Skip current process and its parents
                if proc.info['pid'] == current_pid:
                    continue
                
                # Check for browser processes
                name = proc.info['name'] or ''
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                is_browser_process = (
                    'chromium' in name.lower() or
                    'chrome' in name.lower() or
                    'firefox' in name.lower() or
                    'webkit' in name.lower() or
                    'ffmpeg' in name.lower() or
                    '/playwright/' in cmdline or
                    'playwright_chromiumdev_profile' in cmdline or
                    'playwright_firefoxdev_profile' in cmdline or
                    'playwright_webkitdev_profile' in cmdline
                )
                
                if is_browser_process:
                    # Check if parent is a playwright/python process or if it's orphaned
                    try:
                        parent = proc.parent()
                        if parent:
                            parent_cmdline = ' '.join(parent.cmdline() if parent else [])
                            is_playwright_parent = (
                                'playwright' in parent_cmdline.lower() or
                                'python' in parent_cmdline.lower() or
                                parent.info['pid'] == current_pid
                            )
                            
                            # Only kill if:
                            # 1. Parent is NOT a playwright/python process (orphaned)
                            # 2. Process has been running for more than 1 hour (likely orphaned)
                            if not is_playwright_parent or (time.time() - proc.create_time()) > 3600:
                                try:
                                    proc.terminate()
                                    proc.wait(timeout=1.0)
                                    killed += 1
                                    logger.debug(f"Killed orphaned browser process: {proc.info['pid']} ({name})")
                                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                                    try:
                                        proc.kill()
                                        killed += 1
                                    except psutil.NoSuchProcess:
                                        pass
                        else:
                            # No parent - definitely orphaned
                            try:
                                proc.terminate()
                                proc.wait(timeout=1.0)
                                killed += 1
                                logger.debug(f"Killed orphaned browser process (no parent): {proc.info['pid']} ({name})")
                            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                                try:
                                    proc.kill()
                                    killed += 1
                                except psutil.NoSuchProcess:
                                    pass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Can't check parent - only kill if very old (likely orphaned)
                        if (time.time() - proc.create_time()) > 3600:
                            try:
                                proc.terminate()
                                proc.wait(timeout=1.0)
                                killed += 1
                                logger.debug(f"Killed old browser process (can't check parent): {proc.info['pid']} ({name})")
                            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                                try:
                                    proc.kill()
                                    killed += 1
                                except psutil.NoSuchProcess:
                                    pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception as e:
                logger.debug(f"Error checking process {proc.info.get('pid')}: {e}")
                continue
    
    except Exception as e:
        logger.warning(f"Error cleaning up orphan browser processes: {e}")
    
    if killed > 0:
        logger.info(f"Cleaned up {killed} orphaned browser process(es)")
    
    return killed


def cleanup_old_sessions(force: bool = False, timeout: float = 5.0) -> int:
    """
    Clean up old recording sessions and their processes.
    
    Args:
        force: If True, kill all sessions. If False, only clean up dead processes.
        timeout: Maximum time to spend on cleanup (seconds)
    
    Returns:
        Number of processes killed/cleaned
    """
    import signal
    import time
    
    start_time = time.time()
    temp_dir = Path(tempfile.gettempdir()) / "playwright-simple"
    if not temp_dir.exists():
        # Still try to clean orphan browser processes
        if force:
            return cleanup_orphan_browser_processes(timeout=timeout)
        return 0
    
    cleaned = 0
    
    if not PSUTIL_AVAILABLE:
        # Without psutil, just remove all lock files if force=True
        if force:
            for lock_file in temp_dir.glob("*.lock"):
                if time.time() - start_time > timeout:
                    logger.warning(f"Cleanup timeout after {timeout}s, stopping")
                    break
                try:
                    lock_file.unlink()
                    cleaned += 1
                except:
                    pass
        return cleaned
    
    # With psutil, check each process
    for lock_file in temp_dir.glob("*.lock"):
        if time.time() - start_time > timeout:
            logger.warning(f"Cleanup timeout after {timeout}s, stopping")
            break
            
        try:
            data = json.loads(lock_file.read_text())
            pid = data['pid']
            session_id = data.get('session_id', 'unknown')
            
            try:
                process = psutil.Process(pid)
                
                # Check if it's a playwright-simple process
                try:
                    cmdline = ' '.join(process.cmdline())
                    is_playwright_simple = (
                        'playwright-simple' in cmdline or
                        'recorder' in cmdline.lower() or
                        'playwright_simple' in cmdline
                    )
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    # Can't read cmdline, assume it's not ours
                    is_playwright_simple = False
                
                if force or not is_playwright_simple:
                    # Kill process if force=True or not a playwright-simple process
                    if force:
                        try:
                            process.terminate()
                            # Wait a bit for graceful shutdown (with timeout)
                            try:
                                process.wait(timeout=1.0)  # Reduced from 2s
                            except psutil.TimeoutExpired:
                                # Force kill if didn't terminate
                                try:
                                    process.kill()
                                except psutil.NoSuchProcess:
                                    pass
                            logger.info(f"Killed process {pid} (session: {session_id})")
                            cleaned += 1
                        except psutil.NoSuchProcess:
                            pass
                        except Exception as e:
                            logger.debug(f"Error killing process {pid}: {e}")
                    
                    # Remove lock file
                    try:
                        lock_file.unlink()
                    except:
                        pass
                elif not process.is_running():
                    # Process died, clean up
                    try:
                        lock_file.unlink()
                        cleaned += 1
                    except:
                        pass
            except psutil.NoSuchProcess:
                # Process doesn't exist, clean up lock file
                try:
                    lock_file.unlink()
                    cleaned += 1
                except:
                    pass
            except Exception as e:
                logger.debug(f"Error checking process {pid}: {e}")
                # If we can't check, and force=True, remove lock file
                if force:
                    try:
                        lock_file.unlink()
                        cleaned += 1
                    except:
                        pass
        except Exception as e:
            logger.debug(f"Error reading lock file {lock_file}: {e}")
            # Remove invalid lock files
            if force:
                try:
                    lock_file.unlink()
                    cleaned += 1
                except:
                    pass
    
    # Also clean up command/response files from dead sessions
    if force:
        for cmd_file in temp_dir.glob("*.commands"):
            if time.time() - start_time > timeout:
                break
            try:
                cmd_file.unlink()
            except:
                pass
        for resp_file in temp_dir.glob("*.response"):
            if time.time() - start_time > timeout:
                break
            try:
                resp_file.unlink()
            except:
                pass
    
    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} old session(s)")
    
    # Also clean up orphan browser processes if force=True
    if force:
        browser_cleaned = cleanup_orphan_browser_processes(timeout=max(0, timeout - (time.time() - start_time)))
        cleaned += browser_cleaned
    
    return cleaned


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

