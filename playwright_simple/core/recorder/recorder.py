#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recorder module.

Main coordinator for recording user interactions.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .event_capture import EventCapture
from .action_converter import ActionConverter
from .yaml_writer import YAMLWriter
from .console_interface import ConsoleInterface
from .utils.browser import BrowserManager
from .event_handlers import EventHandlers
from .command_handlers import CommandHandlers
from .command_server import CommandServer

logger = logging.getLogger(__name__)

# Try to import cursor controller (optional)
try:
    from .cursor_controller import CursorController
    CURSOR_AVAILABLE = True
except ImportError:
    CursorController = None
    CURSOR_AVAILABLE = False


class Recorder:
    """Main recorder class that coordinates event capture, conversion, and YAML writing."""
    
    def __init__(self, output_path: Path, initial_url: str = None, headless: bool = False, debug: bool = False):
        """
        Initialize recorder.
        
        Args:
            output_path: Path to output YAML file
            initial_url: Initial URL to open (default: about:blank)
            headless: Run browser in headless mode
            debug: Enable debug mode (verbose logging)
        """
        self.output_path = Path(output_path)
        self.initial_url = initial_url or 'about:blank'
        self.headless = headless
        self.debug = debug
        
        self.browser_manager = BrowserManager(headless=headless)
        self.event_capture: Optional[EventCapture] = None
        self.cursor_controller: Optional[CursorController] = None
        self.action_converter = ActionConverter()
        self.yaml_writer = YAMLWriter(self.output_path)
        self.console = ConsoleInterface()
        
        self.is_recording = False
        self.is_paused = False
        
        # Initialize command server for external commands
        self.command_server: Optional[CommandServer] = None
        
        # Initialize handlers
        self.event_handlers = EventHandlers(
            action_converter=self.action_converter,
            yaml_writer=self.yaml_writer,
            is_recording_getter=lambda: self.is_recording,
            is_paused_getter=lambda: self.is_paused
        )
        
        self.command_handlers = CommandHandlers(
            yaml_writer=self.yaml_writer,
            event_capture_getter=lambda: self.event_capture,
            cursor_controller_getter=lambda: self.cursor_controller,
            recording_state_setter=lambda v: setattr(self, 'is_recording', v),
            paused_state_setter=lambda v: setattr(self, 'is_paused', v),
            page_getter=lambda: self.page if hasattr(self, 'page') else None
        )
        
        self._setup_console_commands()
    
    def _setup_console_commands(self):
        """Set up console command handlers."""
        # Wrap handlers to pass is_recording state
        async def cmd_start(args):
            await self.command_handlers.handle_start(args, self.is_recording)
        
        self.console.register_command('start', cmd_start)
        self.console.register_command('save', self.command_handlers.handle_save)
        self.console.register_command('exit', self.command_handlers.handle_exit)
        self.console.register_command('pause', self.command_handlers.handle_pause)
        self.console.register_command('resume', self.command_handlers.handle_resume)
        self.console.register_command('caption', self.command_handlers.handle_caption)
        self.console.register_command('audio', self.command_handlers.handle_audio)
        self.console.register_command('screenshot', self.command_handlers.handle_screenshot)
        
        # Playwright direct commands (useful for AI assistants and manual testing)
        self.console.register_command('find', self.command_handlers.handle_find)
        self.console.register_command('find-all', self.command_handlers.handle_find_all)
        self.console.register_command('pw-click', self.command_handlers.handle_pw_click)
        self.console.register_command('pw-type', self.command_handlers.handle_pw_type)
        self.console.register_command('pw-submit', self.command_handlers.handle_pw_submit)
        self.console.register_command('pw-wait', self.command_handlers.handle_pw_wait)
        self.console.register_command('pw-info', self.command_handlers.handle_pw_info)
        self.console.register_command('pw-html', self.command_handlers.handle_pw_html)
        
        if CURSOR_AVAILABLE:
            self.console.register_command('cursor', self.command_handlers.handle_cursor)
            self.console.register_command('click', self.command_handlers.handle_cursor_click)
            self.console.register_command('type', self.command_handlers.handle_type)
            self.console.register_command('press', self.command_handlers.handle_press)
    
    async def start(self):
        """Start recording session."""
        try:
            # Clean up old sessions before starting (with timeout to avoid blocking)
            from .command_server import cleanup_old_sessions
            try:
                cleaned = cleanup_old_sessions(force=True, timeout=5.0)
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} old recording session(s) before starting")
            except Exception as e:
                logger.warning(f"Error during cleanup (continuing anyway): {e}")
            
            page = await self.browser_manager.start()
            self.page = page  # Store page reference for command handlers
            
            # Initialize event capture EARLY - before navigation if possible
            # This allows script injection to happen as soon as page loads
            self.event_capture = EventCapture(page, debug=self.debug)
            self._setup_event_handlers()
            
            # Store initial URL for first step
            if self.initial_url and self.initial_url != 'about:blank':
                self.action_converter.initial_url = self.initial_url
                logger.info(f"Navigating to initial URL: {self.initial_url}")
                
                # Set up page event listeners BEFORE navigation to catch early events
                # This ensures script is injected as soon as DOM is ready
                async def on_dom_ready():
                    """Inject script as soon as DOM is ready."""
                    try:
                        if self.event_capture and not self.event_capture.is_capturing:
                            await self.event_capture._inject_capture_script()
                            logger.debug("Script injected on DOM ready")
                    except Exception as e:
                        logger.debug(f"Error injecting on DOM ready: {e}")
                
                def dom_ready_handler():
                    """Wrapper to handle domcontentloaded event."""
                    asyncio.create_task(on_dom_ready())
                
                page.on('domcontentloaded', dom_ready_handler)
                
                await page.goto(self.initial_url, wait_until='domcontentloaded')
                logger.info(f"Page loaded: {page.url}")
                
                # Wait for page to be fully loaded (important for dynamic content like Odoo)
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    logger.info("Page network idle - ready for interactions")
                except Exception as e:
                    logger.warning(f"Network idle timeout, continuing anyway: {e}")
                    # Fallback: wait for load state
                    try:
                        await page.wait_for_load_state('load', timeout=5000)
                    except:
                        pass  # Continue even if timeout
                
                # Add initial navigation as first step
                self.yaml_writer.add_step({
                    'action': 'go_to',
                    'url': self.initial_url,
                    'description': f"Navegar para {self.initial_url}"
                })
            else:
                logger.info("Starting at about:blank")
                await page.goto('about:blank')
            
            # Initialize cursor controller if available
            if CURSOR_AVAILABLE:
                self.cursor_controller = CursorController(page)
                # Start cursor at center of screen (or last position if available)
                await self.cursor_controller.start()
                
                # Set up navigation listener to preserve cursor position
                async def on_navigation(frame):
                    """Restore cursor position after navigation."""
                    try:
                        # Only handle main frame navigation
                        if frame != page.main_frame:
                            return
                        
                        if self.cursor_controller:
                            # Wait for page to be ready using dynamic waits
                            # First, wait for DOM to be ready (with reasonable timeout)
                            try:
                                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                            except Exception as e:
                                logger.debug(f"DOM ready timeout, continuing: {e}")
                                # Try to wait for at least document.readyState
                                try:
                                    await page.wait_for_function(
                                        "document.readyState === 'interactive' || document.readyState === 'complete'",
                                        timeout=5000
                                    )
                                except:
                                    pass  # Continue even if timeout
                            
                            # Wait for body to exist (ensures DOM is usable)
                            try:
                                await page.wait_for_selector('body', timeout=5000, state='attached')
                            except:
                                pass  # Continue even if timeout
                            
                            # Get last position from storage (persists across navigations)
                            # Try multiple times as storage might not be immediately available after navigation
                            position = None
                            for attempt in range(5):  # More attempts for reliability
                                try:
                                    position = await page.evaluate("""
                                        () => {
                                            // Try sessionStorage first (more reliable across navigations)
                                            try {
                                                const stored = sessionStorage.getItem('__playwright_cursor_last_position');
                                                if (stored) {
                                                    return JSON.parse(stored);
                                                }
                                            } catch (e) {
                                                // sessionStorage might not be available
                                            }
                                            // Fallback to window property
                                            return window.__playwright_cursor_last_position || null;
                                        }
                                    """)
                                    if position and position.get('x') and position.get('y'):
                                        break
                                    # Wait for storage to be available using dynamic wait
                                    try:
                                        await page.wait_for_function(
                                            "(() => { try { return sessionStorage.getItem('__playwright_cursor_last_position') !== null; } catch(e) { return window.__playwright_cursor_last_position !== undefined; } })()",
                                            timeout=300
                                        )
                                    except:
                                        pass  # Continue to next attempt
                                except:
                                    pass  # Continue to next attempt
                            
                            if position and position.get('x') and position.get('y'):
                                x = int(position.get('x'))
                                y = int(position.get('y'))
                                # Always restore cursor (force=True to reinject even if "active")
                                await self.cursor_controller.start(force=True, initial_x=x, initial_y=y)
                                # Also update controller's current position
                                self.cursor_controller.current_x = x
                                self.cursor_controller.current_y = y
                                logger.info(f"Cursor restored after navigation: ({x}, {y})")
                            else:
                                # No saved position, start at center
                                await self.cursor_controller.start(force=True)
                                logger.info("Cursor restored after navigation (center)")
                    except Exception as e:
                        logger.warning(f"Error restoring cursor after navigation: {e}")
                        # Try to restore anyway, even if there was an error
                        try:
                            if self.cursor_controller:
                                await self.cursor_controller.start(force=True)
                        except:
                            pass
                
                # Listen for navigation events
                page.on('framenavigated', on_navigation)
            
            # Start console interface
            loop = asyncio.get_event_loop()
            await self.console.start(loop)
            
            # Start recording
            logger.info("Starting event capture...")
            await self.event_capture.start()
            
            # Ensure script is fully ready before allowing interactions
            # Wait a bit more to ensure all event listeners are attached and polling is active
            await asyncio.sleep(0.3)  # Reduced from 0.5 since polling now starts immediately
            
            # Verify script is ready by checking if events array exists and polling is working
            script_ready = await page.evaluate("""
                () => {
                    return !!(window.__playwright_recording_initialized && 
                              window.__playwright_recording_events &&
                              document.body);
                }
            """)
            
            if not script_ready:
                logger.warning("Script may not be fully ready, but continuing...")
            
            # Do a test poll to ensure polling is working
            # This helps catch any events that happened during initialization
            try:
                test_poll = await page.evaluate("""
                    () => {
                        const events = window.__playwright_recording_events || [];
                        return events.length;
                    }
                """)
                if test_poll > 0:
                    logger.info(f"Found {test_poll} event(s) in queue during initialization")
            except:
                pass  # Ignore errors in test poll
            
            self.is_recording = True
            logger.info("✅ Recording started successfully - ready to capture interactions")
            
            # Start command server for external commands
            self.command_server = CommandServer(self)
            await self.command_server.start()
            
            print("✅ Recording started! Interact with the browser.")
            print("   Type commands in the console (e.g., 'exit' to finish)")
            print("   Or use CLI commands: playwright-simple find \"text\", playwright-simple click \"text\", etc.\n")
            
            await self._wait_for_exit()
            logger.info("_wait_for_exit() returned, calling stop()...")
            
        except Exception as e:
            logger.error(f"Error in recorder: {e}", exc_info=True)
            print(f"❌ Error: {e}")
            raise
        finally:
            logger.info("Finally block: calling stop()...")
            # Stop command server
            if self.command_server:
                await self.command_server.stop()
            await self.stop()
    
    def _setup_event_handlers(self):
        """Set up event handlers."""
        self.event_capture.on_event('click', self.event_handlers.handle_click)
        self.event_capture.on_event('input', self.event_handlers.handle_input)
        self.event_capture.on_event('blur', self.event_handlers.handle_blur)
        self.event_capture.on_event('navigation', self.event_handlers.handle_navigation)
        self.event_capture.on_event('scroll', self.event_handlers.handle_scroll)
        self.event_capture.on_event('keydown', self._handle_keydown)  # Keydown needs special handling
    
    async def stop(self, save: bool = True):
        """Stop recording and optionally save YAML."""
        logger.info(f"stop() method called (save={save})")
        
        # Check if we have steps to save (even if already stopped)
        steps_count = self.yaml_writer.get_steps_count()
        logger.info(f"Current state - is_recording: {self.is_recording}, steps_count: {steps_count}")
        
        if not self.is_recording and steps_count == 0:
            logger.info("Not recording and no steps to save, exiting stop()")
            return
        
        # Mark as not recording
        was_recording = self.is_recording
        self.is_recording = False
        logger.info(f"Set is_recording to False (was: {was_recording})")
        
        # Stop event capture
        if self.event_capture:
            try:
                logger.info("Stopping event capture...")
                await self.event_capture.stop()
            except Exception as e:
                logger.debug(f"Error stopping event capture: {e}")
        
        # Stop cursor controller
        if self.cursor_controller:
            try:
                await self.cursor_controller.stop()
            except Exception as e:
                logger.debug(f"Error stopping cursor controller: {e}")
        
        # Stop command server
        if self.command_server:
            try:
                await self.command_server.stop()
            except Exception as e:
                logger.debug(f"Error stopping command server: {e}")
        
        # Stop console
        try:
            logger.info("Stopping console interface...")
            self.console.stop()
        except Exception as e:
            logger.debug(f"Error stopping console: {e}")
        
        # Save YAML if requested
        if save:
            logger.info(f"Stopping recording. Total steps captured: {steps_count}")
            
            if steps_count > 0:
                logger.info(f"Attempting to save YAML to: {self.output_path}")
                success = self.yaml_writer.save()
                if success:
                    saved_path = self.output_path.resolve()
                    logger.info(f"✅ YAML saved successfully to: {saved_path}")
                    logger.info(f"Total steps: {steps_count}")
                    print(f"\n✅ Recording saved!")
                    print(f"   File: {saved_path}")
                    print(f"   Total steps: {steps_count}")
                else:
                    logger.error(f"❌ Failed to save YAML to: {self.output_path}")
                    print(f"\n❌ Failed to save recording")
                    print(f"   Expected location: {self.output_path.resolve()}")
                    print(f"   Check log file for details")
            else:
                logger.warning("⚠️  No steps recorded - no interactions were captured")
                print(f"\n⚠️  No steps recorded")
                print(f"   No file created (no interactions captured)")
                print(f"   Check log file for details")
        else:
            logger.info("Exiting without saving YAML")
            print(f"\n🚪 Exiting without saving")
            if steps_count > 0:
                print(f"   ⚠️  {steps_count} steps will be lost")
                print(f"   Use 'save' command before 'exit' to save progress")
        
        # Close browser (always, even if save=False)
        try:
            await self.browser_manager.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}", exc_info=True)
    
    async def _wait_for_exit(self):
        """Wait for exit command."""
        logger.info("Waiting for exit command...")
        while self.is_recording:
            try:
                # Check for console commands
                cmd = await self.console.wait_for_command(timeout=0.5)
                if cmd:
                    command = cmd.get('command')
                    logger.debug(f"Received command from queue: {command}")
                    if command == 'exit':
                        logger.info("Exit command received in _wait_for_exit!")
                        # Call stop() with save=False to exit without saving
                        await self.stop(save=False)
                        return
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error waiting for exit: {e}", exc_info=True)
                break
        logger.info("Exiting wait_for_exit loop (is_recording became False)")
    
    async def _handle_keydown(self, event_data: dict):
        """Handle keydown event."""
        if not self.is_recording or self.is_paused:
            if self.debug:
                logger.info(f"🔍 DEBUG: Keydown ignored - is_recording: {self.is_recording}, is_paused: {self.is_paused}")
            return
        
        if self.debug:
            logger.info(f"🔍 DEBUG: Handling keydown event: {event_data}")
        
        result = self.action_converter.convert_keydown(event_data)
        
        if not result:
            return
        
        # Handle special return types from convert_keydown
        if isinstance(result, dict) and result.get('type') == 'input_finalized':
            # Finalize input first
            input_action = result.get('input_action')
            if input_action:
                self.yaml_writer.add_step(input_action)
                value_preview = input_action.get('text', '')[:50]
                if len(input_action.get('text', '')) > 50:
                    value_preview += '...'
                logger.info(f"Added finalized input step: {input_action.get('description', '')} = '{value_preview}'")
                print(f"📝 Type: {input_action.get('description', '')} = '{value_preview}'")
            
            # Then try to find submit button instead of using Enter
            element_info = result.get('element', {})
            submit_action = await self._find_submit_button(element_info)
            if submit_action:
                self.yaml_writer.add_step(submit_action)
                logger.info(f"Added submit button click: {submit_action.get('description', '')}")
                print(f"📝 Click: {submit_action.get('description', '')}")
            else:
                # Fallback to Enter if no button found
                enter_action = {
                    'action': 'press',
                    'key': 'Enter',
                    'description': "Pressionar Enter"
                }
                self.yaml_writer.add_step(enter_action)
                print(f"📝 Key: {enter_action.get('description', '')}")
        
        elif isinstance(result, dict) and result.get('type') == 'enter_pressed':
            # Just Enter, try to find button
            element_info = result.get('element', {})
            submit_action = await self._find_submit_button(element_info)
            if submit_action:
                self.yaml_writer.add_step(submit_action)
                logger.info(f"Added submit button click: {submit_action.get('description', '')}")
                print(f"📝 Click: {submit_action.get('description', '')}")
            else:
                enter_action = {
                    'action': 'press',
                    'key': 'Enter',
                    'description': "Pressionar Enter"
                }
                self.yaml_writer.add_step(enter_action)
                print(f"📝 Key: {enter_action.get('description', '')}")
        
        elif isinstance(result, dict) and 'action' in result:
            # Regular action (Tab finalizes input, Escape, etc.)
            self.yaml_writer.add_step(result)
            print(f"📝 Key: {result.get('description', '')}")
    
    async def _find_submit_button(self, context_element: dict) -> Optional[Dict[str, Any]]:
        """
        Try to find a submit button on the page.
        Queries the page for common submit button patterns.
        """
        if not self.event_capture or not self.event_capture.page:
            return None
        
        try:
            # Query page for submit buttons
            buttons = await self.event_capture.page.evaluate("""
                () => {
                    const buttons = [];
                    // Find all buttons and inputs with type submit
                    document.querySelectorAll('button[type="submit"], input[type="submit"], button:not([type]), button[type="button"]').forEach(btn => {
                        const text = (btn.textContent || btn.value || btn.getAttribute('aria-label') || '').trim().toLowerCase();
                        if (text && text.length < 50) {
                            buttons.push({
                                text: text,
                                fullText: (btn.textContent || btn.value || '').trim(),
                                tagName: btn.tagName,
                                type: btn.type || '',
                                id: btn.id || '',
                                name: btn.name || ''
                            });
                        }
                    });
                    return buttons;
                }
            """)
            
            # Look for common submit button texts
            submit_keywords = ['entrar', 'login', 'submit', 'enviar', 'confirmar', 'salvar', 'save', 'log in', 'sign in']
            
            for button in buttons:
                button_text_lower = button.get('text', '').lower()
                if any(keyword in button_text_lower for keyword in submit_keywords):
                    # Found a submit button
                    full_text = button.get('fullText', '')
                    if full_text:
                        return {
                            'action': 'click',
                            'text': full_text,
                            'description': f"Clicar em '{full_text}'"
                        }
            
            return None
        except Exception as e:
            logger.debug(f"Error finding submit button: {e}")
            return None
    

