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
from datetime import datetime

from .event_capture import EventCapture
from .action_converter import ActionConverter
from .yaml_writer import YAMLWriter
from .console_interface import ConsoleInterface
from .utils.browser import BrowserManager
from .event_handlers import EventHandlers
from .command_handlers import CommandHandlers
from .command_server import CommandServer
from .recorder_logger import RecorderLogger

logger = logging.getLogger(__name__)

# Try to import video management (optional, for video recording in read mode)
try:
    from ..video import VideoManager
    from ...extensions.video.config import VideoConfig  # Three dots: core/recorder -> core -> extensions
    from ..constants import VIDEO_FINALIZATION_DELAY
    VIDEO_AVAILABLE = True
except ImportError as e:
    VideoManager = None
    VideoConfig = None
    VIDEO_FINALIZATION_DELAY = 0.1
    VIDEO_AVAILABLE = False
    logger.debug(f"Video management not available: {e}")

# Try to import cursor controller (optional)
try:
    from .cursor_controller import CursorController
    CURSOR_AVAILABLE = True
except ImportError:
    CursorController = None
    CURSOR_AVAILABLE = False


class Recorder:
    """Main recorder class that coordinates event capture, conversion, and YAML writing."""
    
    def __init__(self, output_path: Path, initial_url: str = None, headless: bool = False, debug: bool = False, fast_mode: bool = False, mode: str = 'write', log_level: str = None, log_file: Path = None):
        """
        Initialize recorder.
        
        Args:
            output_path: Path to output YAML file
            initial_url: Initial URL to open (default: about:blank)
            headless: Run browser in headless mode
            debug: Enable debug mode (verbose logging)
            fast_mode: Accelerate steps (reduce delays, instant animations)
            mode: 'write' for recording (export), 'read' for playback (import)
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
        """
        self.output_path = Path(output_path)
        self.initial_url = initial_url or 'about:blank'
        self.headless = headless
        self.debug = debug
        self.mode = mode  # 'write' or 'read'
        
        # Initialize recorder logger
        console_level = 'DEBUG' if debug else log_level
        self.recorder_logger = RecorderLogger(
            name="recorder",
            console_level=console_level,
            file_level='DEBUG',  # Always DEBUG for file
            log_file=log_file
        )
        
        # Initialize browser manager - will be configured with video options if needed
        self.browser_manager = BrowserManager(headless=headless)
        self.event_capture: Optional[EventCapture] = None
        self.cursor_controller: Optional[CursorController] = None
        self.action_converter = ActionConverter(recorder_logger=self.recorder_logger)
        
        # In write mode: YAMLWriter, in read mode: load YAML steps
        if mode == 'write':
            self.yaml_writer = YAMLWriter(self.output_path)
            self.yaml_steps = None
            self.yaml_data = None
            # Video recording is only available in read mode (from YAML config)
            self.video_config = None
            self.video_manager = None
            self.video_start_time = None
        else:  # read mode
            self.yaml_writer = None
            # Load YAML file
            if not self.output_path.exists():
                raise FileNotFoundError(f"YAML file not found: {self.output_path}")
            import yaml
            with open(self.output_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
            self.yaml_data = yaml_data
            self.yaml_steps = yaml_data.get('steps', [])
            # Get initial_url from YAML if not provided
            if not initial_url:
                first_step = self.yaml_steps[0] if self.yaml_steps else {}
                if first_step.get('action') == 'go_to':
                    self.initial_url = first_step.get('url', 'about:blank')
                elif 'base_url' in yaml_data:
                    self.initial_url = yaml_data.get('base_url', 'about:blank')
            
            # Load video configuration from YAML if available
            self.video_config = None
            self.video_manager = None
            self.video_start_time = None
            logger.info(f"🎬 VIDEO DEBUG: Checking video config - VIDEO_AVAILABLE={VIDEO_AVAILABLE}, mode={mode}")
            if yaml_data:
                logger.info(f"🎬 VIDEO DEBUG: yaml_data exists, has 'config': {'config' in yaml_data}")
                if 'config' in yaml_data:
                    logger.info(f"🎬 VIDEO DEBUG: config keys: {list(yaml_data['config'].keys())}")
                    logger.info(f"🎬 VIDEO DEBUG: has 'video': {'video' in yaml_data['config']}")
                    if 'video' in yaml_data['config']:
                        logger.info(f"🎬 VIDEO DEBUG: video config: {yaml_data['config']['video']}")
            
            if VIDEO_AVAILABLE and yaml_data and 'config' in yaml_data and 'video' in yaml_data['config']:
                try:
                    video_data = yaml_data['config']['video']
                    logger.info(f"🎬 VIDEO DEBUG: Loading video config from YAML: {video_data}")
                    self.video_config = VideoConfig(
                        enabled=video_data.get('enabled', False),
                        quality=video_data.get('quality', 'high'),
                        codec=video_data.get('codec', 'webm'),
                        dir=video_data.get('dir', 'videos'),
                        speed=video_data.get('speed', 1.0),
                        subtitles=video_data.get('subtitles', False),
                        hard_subtitles=video_data.get('hard_subtitles', False),
                        audio=video_data.get('audio', False),
                        narration=video_data.get('narration', False),
                        narration_lang=video_data.get('narration_lang', 'pt-BR'),
                        narration_engine=video_data.get('narration_engine', 'gtts'),
                        narration_slow=video_data.get('narration_slow', False)
                    )
                    logger.info(f"🎬 VIDEO DEBUG: VideoConfig created - enabled={self.video_config.enabled}")
                    if self.video_config.enabled:
                        self.video_manager = VideoManager(self.video_config)
                        logger.info(f"🎬 VIDEO DEBUG: VideoManager created successfully")
                        logger.info(f"Video recording enabled: {self.video_config.dir}, quality={self.video_config.quality}, codec={self.video_config.codec}")
                    else:
                        logger.info(f"🎬 VIDEO DEBUG: VideoConfig.enabled is False, not creating VideoManager")
                except Exception as e:
                    logger.warning(f"Error loading video config from YAML: {e}", exc_info=True)
                    self.video_config = None
                    self.video_manager = None
            else:
                logger.info(f"🎬 VIDEO DEBUG: Video config not loaded - VIDEO_AVAILABLE={VIDEO_AVAILABLE}, has_yaml_data={bool(yaml_data)}, has_config={'config' in yaml_data if yaml_data else False}, has_video={'video' in yaml_data.get('config', {}) if yaml_data and 'config' in yaml_data else False}")
        
        self.console = ConsoleInterface()
        
        self.is_recording = False
        self.is_paused = False
        self.fast_mode = fast_mode  # Accelerate steps (reduce delays, instant animations)
        
        # Initialize command server for external commands
        self.command_server: Optional[CommandServer] = None
        
        # Initialize handlers
        self.event_handlers = EventHandlers(
            action_converter=self.action_converter,
            yaml_writer=self.yaml_writer,
            is_recording_getter=lambda: self.is_recording,
            is_paused_getter=lambda: self.is_paused,
            recorder_logger=self.recorder_logger
        )
        
        self.command_handlers = CommandHandlers(
            yaml_writer=self.yaml_writer,
            event_capture_getter=lambda: self.event_capture,
            cursor_controller_getter=lambda: self.cursor_controller,
            recording_state_setter=lambda v: setattr(self, 'is_recording', v),
            paused_state_setter=lambda v: setattr(self, 'is_paused', v),
            page_getter=lambda: self.page if hasattr(self, 'page') else None,
            recorder=self,  # Pass recorder so handlers can access action_converter for programmatic actions
            recorder_logger=self.recorder_logger
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
        self.console.register_command('subtitle', self.command_handlers.handle_subtitle)
        self.console.register_command('audio', self.command_handlers.handle_audio)
        self.console.register_command('audio-step', self.command_handlers.handle_audio_step)
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
        # Track start time for duration calculation
        self.recorder_start_time = datetime.now()
        
        # Log recorder started
        if self.recorder_logger:
            self.recorder_logger.log_screen_event(
                event_type='recorder_started',
                page_state=None,
                details={'mode': self.mode, 'initial_url': self.initial_url, 'headless': self.headless, 'fast_mode': self.fast_mode}
            )
        
        try:
            # Clean up old sessions before starting (with timeout to avoid blocking)
            from .command_server import cleanup_old_sessions
            try:
                cleaned = cleanup_old_sessions(force=True, timeout=5.0)
                if cleaned > 0:
                    logger.info(f"Cleaned up {cleaned} old recording session(s) before starting")
                    if self.recorder_logger:
                        self.recorder_logger.log_screen_event(
                            event_type='cleanup_completed',
                            page_state=None,
                            details={'cleaned_sessions': cleaned}
                        )
            except Exception as e:
                logger.warning(f"Error during cleanup (continuing anyway): {e}")
                if self.recorder_logger:
                    self.recorder_logger.warning(
                        message=f"Error during cleanup: {e}",
                        details={'operation': 'cleanup_old_sessions'}
                    )
            
            # Configure browser manager with video options if needed
            if self.mode == 'read':
                has_video_manager = hasattr(self, 'video_manager') and self.video_manager is not None
                has_video_config = hasattr(self, 'video_config') and self.video_config is not None
                enabled = self.video_config.enabled if has_video_config else False
                logger.info(f"🎬 VIDEO DEBUG: Checking video setup - mode={self.mode}, has_video_manager={has_video_manager}, has_video_config={has_video_config}, enabled={enabled}")
            
            if self.mode == 'read' and hasattr(self, 'video_manager') and self.video_manager and hasattr(self, 'video_config') and self.video_config and self.video_config.enabled:
                # Get test name from YAML
                test_name = self.yaml_data.get('name', 'playback') if self.yaml_data else 'playback'
                
                # Get viewport from browser config or YAML, or use default
                viewport = {'width': 1920, 'height': 1080}
                if self.yaml_data and 'config' in self.yaml_data and 'browser' in self.yaml_data['config']:
                    browser_config = self.yaml_data['config']['browser']
                    if 'viewport' in browser_config:
                        viewport = browser_config['viewport']
                
                # Get video options from VideoManager
                video_options = self.video_manager.get_context_options(test_name, viewport=viewport)
                logger.info(f"Video options from VideoManager: {video_options}")
                
                # Configure browser manager to use video
                self.browser_manager.record_video = True
                self.browser_manager.video_dir = str(self.video_manager.video_dir)
                self.browser_manager.viewport = viewport
                logger.info(f"BrowserManager configured: record_video={self.browser_manager.record_video}, video_dir={self.browser_manager.video_dir}, viewport={self.browser_manager.viewport}")
                
                # Capture video start time
                import time
                self.video_start_time = datetime.now()
                video_start_timestamp = time.time()
                logger.info(f"🎬 VIDEO DEBUG: Video recording STARTED at timestamp {video_start_timestamp:.2f}")
                
                # Start browser using browser_manager (will create context with video)
                page = await self.browser_manager.start()
                self.page = page  # Store page reference for command handlers
                
                browser_started_time = time.time()
                elapsed_since_start = browser_started_time - video_start_timestamp
                logger.info(f"🎬 VIDEO DEBUG: Browser started at {elapsed_since_start:.2f}s after video start")
                
                # Log browser started
                if self.recorder_logger:
                    try:
                        page_url = page.url if hasattr(page, 'url') else 'N/A'
                    except:
                        page_url = 'N/A'
                    self.recorder_logger.log_screen_event(
                        event_type='browser_started',
                        page_state={'url': page_url},
                        details={'video_enabled': True, 'test_name': test_name, 'viewport': viewport, 'elapsed_seconds': elapsed_since_start}
                    )
                
                # Verify page and context are from browser_manager
                logger.info(f"Browser started: page={id(page)}, browser_manager.page={id(self.browser_manager.page) if self.browser_manager.page else 'None'}, context={id(self.browser_manager.context) if self.browser_manager.context else 'None'}")
                
                # Register context for video management
                if self.browser_manager.context:
                    self.video_manager.register_context(self.browser_manager.context, test_name)
                    # Set longer timeouts for video recording
                    self.browser_manager.context.set_default_timeout(60000)  # 60 seconds
                    self.browser_manager.context.set_default_navigation_timeout(60000)  # 60 seconds
                    
                    # Verify video is enabled in context
                    context_options = getattr(self.browser_manager.context, '_options', {})
                    has_video = 'record_video_dir' in context_options or 'recordVideo' in str(context_options)
                    logger.info(f"🎬 VIDEO DEBUG: Context has video recording: {has_video}")
                    logger.info(f"Video recording in context: {has_video}, options keys: {list(context_options.keys()) if isinstance(context_options, dict) else 'N/A'}")
                    
                    # Check for any timeout settings that might affect video
                    context_timeout = getattr(self.browser_manager.context, '_timeout_settings', None)
                    if context_timeout:
                        logger.info(f"🎬 VIDEO DEBUG: Context timeout settings: {context_timeout}")
                
                logger.info(f"Browser started with video recording enabled for test: {test_name}")
            else:
                # Normal browser start (no video or write mode)
                page = await self.browser_manager.start()
                self.page = page  # Store page reference for command handlers
                
                # Log browser started
                if self.recorder_logger:
                    try:
                        page_url = page.url if hasattr(page, 'url') else 'N/A'
                    except:
                        page_url = 'N/A'
                    self.recorder_logger.log_screen_event(
                        event_type='browser_started',
                        page_state={'url': page_url},
                        details={'video_enabled': False, 'mode': self.mode}
                    )
            
            # Initialize event capture only in write mode
            if self.mode == 'write':
                # Initialize event capture EARLY - before navigation if possible
                # This allows script injection to happen as soon as page loads
                # Pass event_handlers so event_capture can process events immediately
                self.event_capture = EventCapture(page, debug=self.debug, event_handlers_instance=self.event_handlers, recorder_logger=self.recorder_logger)
                self._setup_event_handlers()
                
                # Log event capture initialized
                if self.recorder_logger:
                    self.recorder_logger.log_screen_event(
                        event_type='event_capture_initialized',
                        page_state={'url': page.url if hasattr(page, 'url') else 'N/A'},
                        details={'debug': self.debug}
                    )
            
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
                
                # Log initial navigation
                if self.recorder_logger:
                    try:
                        page_title = await page.title()
                    except:
                        page_title = 'N/A'
                    self.recorder_logger.log_screen_event(
                        event_type='initial_navigation',
                        page_state={'url': page.url, 'title': page_title},
                        details={'target_url': self.initial_url}
                    )
                
                # Wait for page to be fully loaded (important for dynamic content like Odoo)
                try:
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    logger.info("Page network idle - ready for interactions")
                except Exception as e:
                    logger.warning(f"Network idle timeout, continuing anyway: {e}")
                    if self.recorder_logger:
                        self.recorder_logger.warning(
                            message=f"Network idle timeout: {e}",
                            details={'operation': 'wait_for_networkidle', 'timeout': 10000}
                        )
                    # Fallback: wait for load state
                    try:
                        await page.wait_for_load_state('load', timeout=5000)
                    except:
                        pass  # Continue even if timeout
                
                # Add initial navigation as first step (only in write mode)
                if self.mode == 'write':
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
                self.cursor_controller = CursorController(page, fast_mode=self.fast_mode, recorder_logger=self.recorder_logger)
                # Start cursor at center of screen (or last position if available)
                await self.cursor_controller.start()
                # Set up navigation listener (encapsulated method, same logic as before)
                self.cursor_controller.setup_navigation_listener()
                
                # Log cursor controller started
                if self.recorder_logger:
                    self.recorder_logger.log_screen_event(
                        event_type='cursor_controller_started',
                        page_state={'url': page.url if hasattr(page, 'url') else 'N/A'},
                        details={'fast_mode': self.fast_mode}
                    )
            
            if self.mode == 'write':
                # Start console interface
                loop = asyncio.get_event_loop()
                await self.console.start(loop)
                
                # Start recording
                logger.info("Starting event capture...")
                await self.event_capture.start()
                
                # Log event capture started
                if self.recorder_logger:
                    self.recorder_logger.log_screen_event(
                        event_type='event_capture_started',
                        page_state={'url': page.url if hasattr(page, 'url') else 'N/A'},
                        details={}
                    )
                
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
                
                # Log script verification
                if self.recorder_logger:
                    self.recorder_logger.log_screen_event(
                        event_type='script_verification',
                        page_state={'url': page.url if hasattr(page, 'url') else 'N/A'},
                        details={'script_ready': script_ready}
                    )
                
                if not script_ready:
                    logger.warning("Script may not be fully ready, but continuing...")
                    if self.recorder_logger:
                        self.recorder_logger.warning(
                            message="Script may not be fully ready",
                            details={'operation': 'script_verification'}
                        )
                
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
                
                # Log state change: is_recording = True
                self._log_state_change('is_recording', False, True, {'mode': 'write'})
                
                # Start command server for external commands
                self.command_server = CommandServer(self)
                await self.command_server.start()
                
                print("✅ Recording started! Interact with the browser.")
                print("   Type commands in the console (e.g., 'exit' to finish)")
                print("   Or use CLI commands: playwright-simple find \"text\", playwright-simple click \"text\", etc.\n")
                
                await self._wait_for_exit()
                logger.info("_wait_for_exit() returned, calling stop()...")
            else:  # read mode
                self.is_recording = True  # Set to True so handlers work
                logger.info("✅ Playback mode initialized - executing YAML steps...")
                
                # Log state change: is_recording = True (read mode)
                self._log_state_change('is_recording', False, True, {'mode': 'read'})
                
                await self._execute_yaml_steps()
                logger.info("YAML steps execution completed")
            
        except Exception as e:
            logger.error(f"Error in recorder: {e}", exc_info=True)
            
            # Log critical failure with context
            if self.recorder_logger:
                try:
                    page_url = self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'
                    try:
                        if self.page and hasattr(self.page, 'title'):
                            page_title = await self.page.title()
                        else:
                            page_title = 'N/A'
                    except:
                        page_title = 'N/A'
                    page_state = {'url': page_url, 'title': page_title}
                except:
                    page_state = {'url': 'N/A', 'title': 'N/A'}
                
                self.recorder_logger.log_critical_failure(
                    action='recorder_start',
                    error=str(e),
                    page_state=page_state,
                    details={'mode': self.mode, 'initial_url': self.initial_url}
                )
            
            print(f"❌ Error: {e}")
            raise
        finally:
            logger.info("Finally block: calling stop()...")
            # Stop command server
            if self.command_server:
                await self.command_server.stop()
            await self.stop()
    
    def _log_state_change(self, state_name: str, old_value: Any, new_value: Any, details: Dict[str, Any] = None):
        """Helper method to log state changes."""
        if self.recorder_logger:
            try:
                page_url = self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'
            except:
                page_url = 'N/A'
            self.recorder_logger.log_screen_event(
                event_type='state_changed',
                page_state={'url': page_url},
                details={'state_name': state_name, 'old_value': old_value, 'new_value': new_value, **(details or {})}
            )
    
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
        
        # Calculate duration if start time is available
        duration_seconds = None
        if hasattr(self, 'recorder_start_time') and self.recorder_start_time:
            duration_seconds = (datetime.now() - self.recorder_start_time).total_seconds()
        
        # Check if we have steps to save (even if already stopped)
        # In read mode, yaml_writer is None, so use yaml_steps length instead
        if self.mode == 'read':
            steps_count = len(self.yaml_steps) if hasattr(self, 'yaml_steps') and self.yaml_steps and isinstance(self.yaml_steps, list) else 0
        else:
            steps_count = self.yaml_writer.get_steps_count() if self.yaml_writer else 0
        logger.info(f"Current state - is_recording: {self.is_recording}, steps_count: {steps_count}, mode: {self.mode}")
        
        if not self.is_recording and steps_count == 0:
            logger.info("Not recording and no steps to save, exiting stop()")
            return
        
        # Mark as not recording
        was_recording = self.is_recording
        self.is_recording = False
        logger.info(f"Set is_recording to False (was: {was_recording})")
        
        # Log state change: is_recording = False
        self._log_state_change('is_recording', was_recording, False)
        
        # Stop event capture (only in write mode)
        if self.event_capture:
            try:
                logger.info("Stopping event capture...")
                await self.event_capture.stop()
            except Exception as e:
                logger.debug(f"Error stopping event capture: {e}")
                if self.recorder_logger:
                    self.recorder_logger.log_critical_failure(
                        action='stop_event_capture',
                        error=str(e),
                        page_state={'url': self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'}
                    )
        
        # Stop cursor controller
        if self.cursor_controller:
            try:
                await self.cursor_controller.stop()
            except Exception as e:
                logger.debug(f"Error stopping cursor controller: {e}")
                if self.recorder_logger:
                    self.recorder_logger.log_critical_failure(
                        action='stop_cursor_controller',
                        error=str(e),
                        page_state={'url': self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'}
                    )
        
        # Stop command server (only in write mode)
        if self.command_server:
            try:
                await self.command_server.stop()
            except Exception as e:
                logger.debug(f"Error stopping command server: {e}")
                if self.recorder_logger:
                    self.recorder_logger.log_critical_failure(
                        action='stop_command_server',
                        error=str(e),
                        page_state={'url': self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'}
                    )
        
        # Stop console (only in write mode)
        if self.mode == 'write':
            try:
                logger.info("Stopping console interface...")
                self.console.stop()
            except Exception as e:
                logger.debug(f"Error stopping console: {e}")
                if self.recorder_logger:
                    self.recorder_logger.log_critical_failure(
                        action='stop_console',
                        error=str(e),
                        page_state={'url': self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'}
                    )
        
        # Save YAML if requested (only in write mode)
        if save and self.mode == 'write' and self.yaml_writer:
            logger.info(f"Stopping recording. Total steps captured: {steps_count}")
            
            if steps_count > 0:
                logger.info(f"Attempting to save YAML to: {self.output_path}")
                success = self.yaml_writer.save()
                if success:
                    saved_path = self.output_path.resolve()
                    logger.info(f"✅ YAML saved successfully to: {saved_path}")
                    logger.info(f"Total steps: {steps_count}")
                    
                    # Log YAML saved
                    if self.recorder_logger:
                        try:
                            page_url = self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'
                        except:
                            page_url = 'N/A'
                        self.recorder_logger.log_screen_event(
                            event_type='yaml_saved',
                            page_state={'url': page_url},
                            details={'file_path': str(saved_path), 'total_steps': steps_count, 'duration_seconds': duration_seconds}
                        )
                    
                    print(f"\n✅ Recording saved!")
                    print(f"   File: {saved_path}")
                    print(f"   Total steps: {steps_count}")
                else:
                    logger.error(f"❌ Failed to save YAML to: {self.output_path}")
                    
                    # Log YAML save failed
                    if self.recorder_logger:
                        try:
                            page_url = self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'
                        except:
                            page_url = 'N/A'
                        self.recorder_logger.log_critical_failure(
                            action='yaml_save',
                            error=f"Failed to save YAML to {self.output_path}",
                            page_state={'url': page_url},
                            details={'file_path': str(self.output_path), 'total_steps': steps_count}
                        )
                    
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
        
        # Log recorder stopped with final statistics
        if self.recorder_logger:
            try:
                page_url = self.page.url if self.page and hasattr(self.page, 'url') else 'N/A'
            except:
                page_url = 'N/A'
            self.recorder_logger.log_screen_event(
                event_type='recorder_stopped',
                page_state={'url': page_url},
                details={'total_steps': steps_count, 'duration_seconds': duration_seconds, 'saved': save, 'mode': self.mode}
            )
        
        # Handle video recording in read mode
        if self.mode == 'read' and hasattr(self, 'video_manager') and self.video_manager and hasattr(self, 'video_config') and self.video_config and self.video_config.enabled:
            try:
                test_name = self.yaml_data.get('name', 'playback') if self.yaml_data else 'playback'
                
                # Track video recording duration
                import time
                if hasattr(self, 'video_start_time'):
                    video_duration = (datetime.now() - self.video_start_time).total_seconds()
                    logger.info(f"🎬 VIDEO DEBUG: Video recording duration so far: {video_duration:.2f}s")
                
                # CRITICAL: Verify page and context are still the same before closing
                if self.browser_manager.context and self.page:
                    page_context = self.page.context if hasattr(self.page, 'context') else None
                    if page_context and id(page_context) != id(self.browser_manager.context):
                        logger.error(f"⚠️  CRITICAL: Page context ({id(page_context)}) != browser_manager context ({id(self.browser_manager.context)})")
                        logger.error(f"   Video is being recorded in browser_manager.context, but page is using a different context!")
                        logger.error(f"   This explains why video stops early - it's recording a different browser instance!")
                
                # Wait before closing context to ensure all actions are captured in video
                # Playwright writes video asynchronously, so we need to wait for all frames
                # Increase wait time to ensure all frames are written
                before_close_wait_time = time.time()
                logger.info(f"🎬 VIDEO DEBUG: Starting wait before closing context at {before_close_wait_time:.2f}s")
                await asyncio.sleep(3.0)
                after_close_wait_time = time.time()
                wait_elapsed = after_close_wait_time - before_close_wait_time
                logger.info(f"🎬 VIDEO DEBUG: Wait completed, elapsed: {wait_elapsed:.2f}s")
                logger.info("Waiting before closing context to ensure video captures all actions")
                
                # IMPORTANT: Playwright finalizes video when context closes
                # We must ensure the context we're closing is the one that has video recording
                if self.browser_manager.context:
                    context_id = id(self.browser_manager.context)
                    before_close_time = time.time()
                    logger.info(f"🎬 VIDEO DEBUG: About to close context {context_id} at {before_close_time:.2f}s")
                    logger.info(f"Closing context {context_id} to finalize video...")
                    await self.browser_manager.context.close()
                    after_close_time = time.time()
                    close_elapsed = after_close_time - before_close_time
                    logger.info(f"🎬 VIDEO DEBUG: Context closed, elapsed: {close_elapsed:.2f}s")
                    logger.info("Context closed, video should be finalized")
                
                # Wait for video to be finalized - Playwright saves videos asynchronously
                # We need to wait and check periodically
                import re
                import time
                video_extensions = ['.webm', '.mp4']
                # Playwright always saves as .webm initially, we'll convert if needed
                expected_name_initial = f"{test_name}.webm"  # Playwright default
                expected_name_final = f"{test_name}.mp4" if self.video_config.codec == "mp4" else f"{test_name}.webm"
                expected_path_initial = self.video_manager.video_dir / expected_name_initial
                expected_path_final = self.video_manager.video_dir / expected_name_final
                
                # Wait up to 10 seconds for video to be created
                max_wait_time = 10.0
                wait_interval = 0.5
                waited = 0.0
                found_video = None
                
                while waited < max_wait_time:
                    # Check for video files
                    all_videos = []
                    for ext in video_extensions:
                        all_videos.extend(list(self.video_manager.video_dir.glob(f"*{ext}")))
                    
                    if all_videos:
                        # Get the most recent video (should be from this test)
                        found_video = max(all_videos, key=lambda p: p.stat().st_mtime)
                        # Check if video was created recently (within last 15 seconds)
                        video_age = time.time() - found_video.stat().st_mtime
                        if video_age < 15:
                            # Video found and recent, break
                            break
                    
                    await asyncio.sleep(wait_interval)
                    waited += wait_interval
                
                if found_video:
                    # Convert to MP4 if needed
                    if self.video_config.codec == "mp4" and found_video.suffix == '.webm':
                        logger.info(f"Converting video from webm to mp4...")
                        print(f"🔄 Convertendo vídeo de webm para mp4...")
                        try:
                            import subprocess
                            mp4_path = found_video.parent / f"{found_video.stem}.mp4"
                            cmd = [
                                'ffmpeg',
                                '-i', str(found_video),
                                '-c:v', 'libx264',
                                '-c:a', 'aac',
                                '-movflags', '+faststart',
                                '-y',
                                str(mp4_path)
                            ]
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                            if result.returncode == 0 and mp4_path.exists():
                                found_video.unlink()
                                found_video = mp4_path
                                logger.info(f"Video converted to mp4: {mp4_path.name}")
                                print(f"✅ Vídeo convertido para mp4")
                            else:
                                logger.warning(f"Video conversion failed: {result.stderr[:200]}")
                                print(f"⚠️  Erro ao converter vídeo, mantendo webm")
                        except Exception as e:
                            logger.warning(f"Error converting video: {e}", exc_info=True)
                            print(f"⚠️  Erro ao converter vídeo: {e}")
                    
                    # Rename video to final expected name
                    if found_video != expected_path_final:
                        if expected_path_final.exists():
                            expected_path_final.unlink()
                        found_video.rename(expected_path_final)
                        logger.info(f"Video renamed to: {expected_path_final.name}")
                        print(f"📹 Vídeo renomeado para: {expected_path_final.name}")
                    else:
                        logger.info(f"Video already has correct name: {expected_path_final.name}")
                        print(f"📹 Vídeo salvo: {expected_path_final.name}")
                    
                    # Process video in sequence: subtitles first, then audio
                    # This ensures audio is added to video that already has subtitles embedded
                    current_video_path = expected_path_final
                    
                    # Step 1: Generate and add subtitles if enabled
                    if self.video_config.subtitles and hasattr(self, 'step_timestamps') and self.step_timestamps:
                        logger.info("🎬 Generating subtitles for video...")
                        logger.info(f"🎬 DEBUG: step_timestamps count: {len(self.step_timestamps)}")
                        print(f"📝 Gerando legendas para o vídeo...")
                        print(f"📝 DEBUG: {len(self.step_timestamps)} steps com timestamps")
                        try:
                            result_video = await self._generate_and_add_subtitles(current_video_path)
                            if result_video and result_video.exists():
                                current_video_path = result_video
                                logger.info(f"Video with subtitles ready: {current_video_path.name}")
                                print(f"✅ Vídeo com legendas pronto: {current_video_path.name}")
                                print(f"✅ DEBUG: Vídeo final: {current_video_path.resolve()}")
                            else:
                                logger.warning(f"⚠️  DEBUG: result_video is None or doesn't exist: {result_video}")
                                print(f"⚠️  DEBUG: Vídeo com legendas não foi gerado corretamente")
                        except Exception as e:
                            logger.warning(f"Error generating subtitles: {e}", exc_info=True)
                            print(f"⚠️  Erro ao gerar legendas: {e}")
                            import traceback
                            print(f"⚠️  DEBUG: Traceback: {traceback.format_exc()}")
                    
                    # Step 2: Generate and add audio narration if enabled
                    # Use current_video_path (which may already have subtitles embedded)
                    if (self.video_config.audio or self.video_config.narration) and hasattr(self, 'step_timestamps') and self.step_timestamps:
                        logger.info("🎤 Generating audio narration for video...")
                        logger.info(f"🎤 DEBUG: step_timestamps count: {len(self.step_timestamps)}")
                        logger.info(f"🎤 DEBUG: video_config.audio={self.video_config.audio}, video_config.narration={self.video_config.narration}")
                        print(f"🔊 Gerando narração de áudio para o vídeo...")
                        print(f"🔊 DEBUG: {len(self.step_timestamps)} steps com timestamps")
                        print(f"🔊 DEBUG: audio={self.video_config.audio}, narration={self.video_config.narration}")
                        try:
                            # Extract test name from YAML or use default
                            test_name = self.yaml_data.get('name', 'test') if hasattr(self, 'yaml_data') and self.yaml_data else 'test'
                            logger.info(f"🎤 DEBUG: Using test_name: {test_name}")
                            print(f"🔊 DEBUG: Nome do teste: {test_name}")
                            result_video = await self._generate_and_add_audio(current_video_path, test_name)
                            if result_video and result_video.exists():
                                current_video_path = result_video
                                logger.info(f"Video with audio ready: {current_video_path.name}")
                                print(f"✅ Vídeo com áudio pronto: {current_video_path.name}")
                                print(f"✅ DEBUG: Vídeo final: {current_video_path.resolve()}")
                            else:
                                logger.warning(f"⚠️  DEBUG: result_video is None or doesn't exist: {result_video}")
                                print(f"⚠️  DEBUG: Vídeo com áudio não foi gerado corretamente")
                        except Exception as e:
                            logger.warning(f"Error generating audio: {e}", exc_info=True)
                            print(f"⚠️  Erro ao gerar áudio: {e}")
                            import traceback
                            print(f"⚠️  DEBUG: Traceback: {traceback.format_exc()}")
                    
                    # Ensure final video has correct name
                    if current_video_path != expected_path_final:
                        final_name = self.yaml_data.get('name', 'test') if hasattr(self, 'yaml_data') and self.yaml_data else 'test'
                        final_expected = self.video_manager.video_dir / f"{final_name}.mp4"
                        if current_video_path != final_expected:
                            if final_expected.exists():
                                final_expected.unlink()
                            current_video_path.rename(final_expected)
                            expected_path_final = final_expected
                        else:
                            expected_path_final = current_video_path
                    
                    # Clean up temporary files (SRT, MP3, intermediate videos)
                    # Extract test name for cleanup
                    test_name = self.yaml_data.get('name', 'test') if hasattr(self, 'yaml_data') and self.yaml_data else 'test'
                    await self._cleanup_temp_files(self.video_manager.video_dir, test_name)
                    
                    # Clean up old videos with hash-based names (after renaming)
                    # Re-scan to get updated list
                    all_videos_after = []
                    for ext in video_extensions:
                        all_videos_after.extend(list(self.video_manager.video_dir.glob(f"*{ext}")))
                    
                    for video_file in all_videos_after:
                        if video_file == expected_path_final:
                            continue
                        
                        video_name = video_file.stem
                        is_hash_based = re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-', video_name)
                        is_technical = len(video_name) < 10 and not any(c.isalpha() for c in video_name[:5])
                        
                        if is_hash_based or is_technical:
                            try:
                                video_file.unlink()
                                logger.debug(f"Deleted old video: {video_file.name}")
                            except Exception as e:
                                logger.warning(f"Error deleting old video {video_file.name}: {e}")
                else:
                    logger.warning("No video files found in video directory after waiting")
                    print(f"⚠️  Vídeo não foi encontrado após {max_wait_time}s de espera")
                
                # Browser and playwright are managed by browser_manager
                # They will be closed when browser_manager.stop() is called below
                    
            except Exception as e:
                logger.error(f"Error handling video recording: {e}", exc_info=True)
        
        # Close browser (always, even if save=False)
        # browser_manager handles all browser/context cleanup
        try:
            # Don't close if we already closed context for video (to avoid double close)
            video_context_closed = (self.mode == 'read' and 
                                   hasattr(self, 'video_manager') and self.video_manager and 
                                   hasattr(self, 'video_config') and self.video_config and 
                                   self.video_config.enabled and 
                                   self.browser_manager.context)
            if not video_context_closed:
                await self.browser_manager.stop()
            elif self.browser_manager.browser:
                # Context already closed, just close browser and playwright
                if self.browser_manager.browser:
                    await self.browser_manager.browser.close()
                if self.browser_manager.playwright:
                    await self.browser_manager.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}", exc_info=True)
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    async def _generate_srt_file(self, video_path: Path) -> Optional[Path]:
        """
        Generate SRT subtitle file from step timestamps.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to SRT file, or None if generation failed
        """
        logger.info(f"🎬 DEBUG: _generate_srt_file called")
        logger.info(f"🎬 DEBUG: hasattr step_timestamps: {hasattr(self, 'step_timestamps')}")
        if hasattr(self, 'step_timestamps'):
            logger.info(f"🎬 DEBUG: step_timestamps is not None: {self.step_timestamps is not None}")
            if self.step_timestamps:
                logger.info(f"🎬 DEBUG: step_timestamps length: {len(self.step_timestamps)}")
            else:
                logger.warning(f"🎬 DEBUG: step_timestamps is EMPTY list!")
        else:
            logger.warning(f"🎬 DEBUG: step_timestamps attribute does NOT exist!")
        
        if not hasattr(self, 'step_timestamps') or not self.step_timestamps:
            logger.warning("No step timestamps available for subtitle generation")
            print(f"⚠️  DEBUG: Não há step_timestamps para gerar SRT")
            return None
        
        srt_path = video_path.parent / f"{video_path.stem}.srt"
        min_duration = 0.5  # Minimum subtitle duration in seconds
        gap = 0.1  # Gap between subtitles to prevent overlap
        
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                
                # Process steps and eliminate overlaps
                processed_steps = []
                logger.info(f"🎬 DEBUG: Processing {len(self.step_timestamps)} step_timestamps for SRT")
                steps_with_subtitle = 0
                steps_without_subtitle = 0
                
                for step_data in self.step_timestamps:
                    step_start = step_data.get('start_time', 0)
                    step_end = step_data.get('end_time', step_start + 1.0)
                    step_duration = step_end - step_start
                    
                    # Get text from step (use subtitle field, not description)
                    step_text = step_data.get('subtitle')
                    if not step_text:
                        # If no subtitle, skip this step (for continuity, we only show steps with subtitles)
                        steps_without_subtitle += 1
                        logger.debug(f"🎬 DEBUG: Skipping step without subtitle: action={step_data.get('action')}, start={step_start:.2f}s")
                        continue
                    
                    steps_with_subtitle += 1
                    logger.debug(f"🎬 DEBUG: Processing step with subtitle: '{step_text}', start={step_start:.2f}s, end={step_end:.2f}s")
                    
                    # Ensure minimum duration
                    if step_duration < min_duration:
                        step_end = step_start + min_duration
                        step_duration = min_duration
                    
                    processed_steps.append({
                        'start': step_start,
                        'end': step_end,
                        'text': step_text,
                        'duration': step_duration
                    })
                
                # Adjust end times for subtitle continuity
                # If a step has a subtitle and the next step doesn't have one (or has same),
                # extend current subtitle until next step with different subtitle
                for i in range(len(processed_steps)):
                    current = processed_steps[i]
                    # Find next step with a different subtitle (or end of list)
                    next_different_index = None
                    for j in range(i + 1, len(processed_steps)):
                        next_step = processed_steps[j]
                        if next_step['text'] != current['text']:
                            next_different_index = j
                            break
                    
                    if next_different_index is not None:
                        # Extend current subtitle until next different subtitle starts
                        next_step = processed_steps[next_different_index]
                        current['end'] = next_step['start'] - gap
                        current['duration'] = current['end'] - current['start']
                    # If no next different subtitle, keep original end time
                
                # Adjust end times to prevent overlaps (after continuity extension)
                for i in range(len(processed_steps)):
                    current = processed_steps[i]
                    # Find next step that starts before this one ends
                    for j in range(i + 1, len(processed_steps)):
                        next_step = processed_steps[j]
                        if next_step['start'] <= current['end']:
                            # Adjust current end to be before next start
                            new_end = next_step['start'] - gap
                            new_end = max(current['start'] + 0.1, new_end)  # Minimum 0.1s visibility
                            current['end'] = new_end
                            current['duration'] = new_end - current['start']
                            break
                
                logger.info(f"🎬 DEBUG: Steps with subtitle: {steps_with_subtitle}, without subtitle: {steps_without_subtitle}")
                logger.info(f"🎬 DEBUG: Processed {len(processed_steps)} steps for SRT file")
                
                # Write SRT entries
                srt_entries_written = 0
                for step in processed_steps:
                    if step['end'] > step['start'] and step['text']:
                        start_str = self._format_srt_time(step['start'])
                        end_str = self._format_srt_time(step['end'])
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_str} --> {end_str}\n")
                        f.write(f"{step['text']}\n\n")
                        subtitle_index += 1
                        srt_entries_written += 1
                
                logger.info(f"🎬 DEBUG: Wrote {srt_entries_written} SRT entries to file")
            
            if srt_path.exists():
                srt_size = srt_path.stat().st_size
                logger.info(f"SRT file generated: {srt_path} ({srt_size} bytes)")
                print(f"✅ DEBUG: Arquivo SRT gerado: {srt_path.name} ({srt_size} bytes)")
            else:
                logger.warning(f"⚠️  DEBUG: SRT file was NOT created: {srt_path}")
                print(f"⚠️  DEBUG: Arquivo SRT NÃO foi criado: {srt_path}")
            
            return srt_path
        except Exception as e:
            logger.error(f"Error generating SRT file: {e}", exc_info=True)
            return None
    
    async def _generate_and_add_subtitles(self, video_path: Path) -> Optional[Path]:
        """
        Generate SRT file and add subtitles to video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to video with subtitles, or original path if processing failed
        """
        # Generate SRT file
        srt_path = await self._generate_srt_file(video_path)
        if not srt_path or not srt_path.exists():
            logger.warning("SRT file not generated, skipping subtitle processing")
            return video_path
        
        # Check if hard_subtitles is enabled
        if not self.video_config.hard_subtitles:
            logger.info("Hard subtitles disabled, SRT file generated but not embedded")
            print(f"📝 Arquivo SRT gerado: {srt_path.name} (não queimado no vídeo)")
            return video_path
        
        # Check if ffmpeg is available
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffmpeg not found, cannot embed subtitles")
            print(f"⚠️  ffmpeg não encontrado. Legendas não serão queimadas no vídeo.")
            return video_path
        
        # Process video with ffmpeg to embed subtitles
        # Always output as MP4 to ensure compatibility
        output_path = video_path.parent / f"{video_path.stem}.mp4"
        if output_path == video_path and video_path.suffix == '.mp4':
            # If same path, use _with_subtitles suffix temporarily
            output_path = video_path.parent / f"{video_path.stem}_with_subtitles.mp4"
        
        # Ensure output_path is absolute
        output_path = output_path.resolve()
        
        try:
            import subprocess
            # Escape SRT filename for ffmpeg filter
            srt_filename = srt_path.name
            srt_escaped = srt_filename.replace(':', '\\:').replace('[', '\\[').replace(']', '\\]').replace("'", "\\'")
            
            # Determine codec based on output file extension or config
            output_ext = output_path.suffix.lower()
            if output_ext == '.mp4' or self.video_config.codec == 'mp4':
                video_codec = 'libx264'
                audio_codec = 'aac'  # MP4 requires AAC audio
            else:
                video_codec = 'libvpx-vp9'
                audio_codec = 'copy'
            
            # Build ffmpeg command to burn subtitles into video
            # Strategy: Use a simple filename approach to avoid path escaping issues
            # Copy SRT to a simple name in the same directory as video
            video_absolute = str(video_path.resolve())
            srt_absolute = str(srt_path.resolve())
            
            # Create a temporary SRT with a simple name (no spaces, no special chars)
            import shutil
            simple_srt_name = "subtitles_temp.srt"
            simple_srt_path = video_path.parent / simple_srt_name
            srt_escaped_absolute = None  # Initialize to avoid UnboundLocalError
            
            try:
                # Copy SRT to simple filename
                shutil.copy2(srt_path, simple_srt_path)
                logger.info(f"🎬 DEBUG: SRT copiado para nome simples: {simple_srt_name}")
                
                # Use simple filename in filter (relative to video directory)
                # This avoids all path escaping issues
                filter_expr = f"subtitles={simple_srt_name}:force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20'"
                
                cmd = [
                    'ffmpeg',
                    '-i', video_absolute,  # Use absolute path for video input
                    '-vf', filter_expr,
                ]
            except Exception as e:
                logger.warning(f"⚠️  Erro ao copiar SRT: {e}")
                # Fallback: try with absolute path (may fail with special chars)
                srt_for_filter = srt_absolute.replace('\\', '/')
                srt_escaped_absolute = srt_for_filter.replace(' ', '\\ ').replace(':', '\\:').replace('[', '\\[').replace(']', '\\]').replace("'", "\\'")
                filter_expr = f"subtitles='{srt_escaped_absolute}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20'"
                cmd = [
                    'ffmpeg',
                    '-i', video_absolute,
                    '-vf', filter_expr,
                ]
                simple_srt_path = None  # Don't try to clean up
            
            # Always use MP4 codecs for output
            # Otimização: usar preset 'ultrafast' para codificação mais rápida
            if output_ext == '.mp4' or self.video_config.codec == 'mp4':
                cmd.extend([
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',  # Otimização: codificação mais rápida
                    '-crf', '23',  # Qualidade razoável (18-28 é aceitável, 23 é padrão)
                    '-c:a', 'aac',
                    '-b:a', '128k',  # Otimização: bitrate de áudio reduzido
                    '-movflags', '+faststart',
                ])
            else:
                cmd.extend([
                    '-c:v', video_codec,
                    '-c:a', audio_codec,
                ])
            
            cmd.extend([
                '-y',
                str(output_path)
            ])
            
            logger.info(f"Processing video with subtitles: {srt_path.name}")
            logger.info(f"🎬 DEBUG: SRT path (absolute): {srt_absolute}")
            if srt_escaped_absolute:
                logger.info(f"🎬 DEBUG: SRT path (escaped): {srt_escaped_absolute}")
            else:
                logger.info(f"🎬 DEBUG: SRT path (using simple filename): {simple_srt_name}")
            logger.info(f"🎬 DEBUG: Video input (absolute): {video_absolute}")
            logger.info(f"🎬 DEBUG: Video output: {output_path}")
            logger.info(f"🎬 DEBUG: FFmpeg command: {' '.join(cmd)}")
            print(f"🎬 Processando vídeo com legendas (burn)...")
            print(f"🎬 DEBUG: Queimando legendas do arquivo: {srt_path.name}")
            print(f"🎬 DEBUG: Vídeo de entrada: {video_path.name}")
            print(f"🎬 DEBUG: Vídeo de saída: {output_path.name}")
            
            # Use absolute path for output in command
            cmd_absolute = cmd[:-1] + [str(output_path)]  # Replace last element (output path) with absolute path
            
            result = subprocess.run(
                cmd_absolute,
                cwd=str(video_path.parent),  # Run from video directory (so simple_srt_name works)
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Clean up temporary SRT file (if we created one)
            if simple_srt_path and simple_srt_path.exists():
                try:
                    simple_srt_path.unlink()
                    logger.debug(f"🎬 DEBUG: Arquivo SRT temporário removido: {simple_srt_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Não foi possível remover SRT temporário: {e}")
            
            # Log ffmpeg output for debugging
            if result.returncode != 0:
                # Get full error message (stderr usually contains the actual error)
                error_output = result.stderr if result.stderr else result.stdout
                logger.warning(f"🎬 DEBUG: FFmpeg return code: {result.returncode}")
                logger.warning(f"🎬 DEBUG: FFmpeg stderr (full): {error_output}")
                logger.warning(f"🎬 DEBUG: FFmpeg stdout: {result.stdout}")
                print(f"⚠️  DEBUG: FFmpeg retornou código {result.returncode}")
                if error_output:
                    # Try to extract the actual error message (usually after version info)
                    error_lines = error_output.split('\n')
                    # Skip version info and find actual error
                    actual_error = '\n'.join([line for line in error_lines if line and not line.startswith('ffmpeg version') and not line.startswith('built with') and not line.startswith('configuration:')])
                    if actual_error:
                        print(f"⚠️  DEBUG: Erro FFmpeg: {actual_error[:500]}")
                    else:
                        print(f"⚠️  DEBUG: Erro FFmpeg completo: {error_output[:500]}")
                
            
            if result.returncode == 0 and output_path.exists():
                # Replace original video with subtitled version
                if video_path.exists() and video_path != output_path:
                    video_path.unlink()
                if output_path != video_path:
                    output_path.rename(video_path)
                # Clean up SRT file (subtitles are now embedded)
                if srt_path.exists():
                    try:
                        srt_path.unlink()
                        logger.debug(f"Cleaned up SRT file: {srt_path.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove SRT file: {e}")
                logger.info(f"Video processed with subtitles: {video_path.name}")
                print(f"✅ Vídeo processado com legendas embutidas: {video_path.name}")
                return video_path
            else:
                error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
                logger.warning(f"ffmpeg failed to embed subtitles: {error_msg}")
                print(f"⚠️  Erro ao processar vídeo com legendas")
                print(f"   Detalhes: {error_msg[:200]}")
                if output_path.exists():
                    output_path.unlink()
                return video_path
        except Exception as e:
            logger.error(f"Error processing video with subtitles: {e}", exc_info=True)
            print(f"⚠️  Erro ao processar vídeo: {e}")
            if output_path.exists():
                output_path.unlink()
            return video_path
    
    async def _generate_and_add_audio(self, video_path: Path, test_name: str) -> Optional[Path]:
        """
        Generate audio narration from step timestamps and add to video.
        
        Args:
            video_path: Path to video file
            test_name: Name of test (for audio filename)
            
        Returns:
            Path to video with audio, or original path if processing failed
        """
        logger.info(f"🎤 DEBUG: _generate_and_add_audio called")
        logger.info(f"🎤 DEBUG: hasattr step_timestamps: {hasattr(self, 'step_timestamps')}")
        if hasattr(self, 'step_timestamps'):
            logger.info(f"🎤 DEBUG: step_timestamps is not None: {self.step_timestamps is not None}")
            if self.step_timestamps:
                logger.info(f"🎤 DEBUG: step_timestamps length: {len(self.step_timestamps)}")
            else:
                logger.warning(f"🎤 DEBUG: step_timestamps is EMPTY list!")
        else:
            logger.warning(f"🎤 DEBUG: step_timestamps attribute does NOT exist!")
        
        if not hasattr(self, 'step_timestamps') or not self.step_timestamps:
            logger.warning("No step timestamps available for audio generation")
            print(f"⚠️  DEBUG: Não há step_timestamps para gerar áudio")
            return video_path
        
        # Check if TTS is available
        try:
            from ..tts import TTSManager
        except ImportError:
            logger.warning("TTSManager not available, skipping audio generation")
            print(f"⚠️  TTSManager não disponível. Instale: pip install edge-tts")
            return video_path
        
        # Determine which config to use (audio or narration)
        use_audio_config = self.video_config.audio
        if use_audio_config:
            lang = self.video_config.audio_lang
            engine = self.video_config.audio_engine
            voice = getattr(self.video_config, 'audio_voice', None)
            rate = getattr(self.video_config, 'audio_rate', None)
            pitch = getattr(self.video_config, 'audio_pitch', None)
            volume = getattr(self.video_config, 'audio_volume', None)
        else:
            lang = self.video_config.narration_lang
            engine = self.video_config.narration_engine
            voice = getattr(self.video_config, 'narration_voice', None)
            rate = None
            pitch = None
            volume = None
        
        # Default to edge-tts if not specified (better voices)
        if not engine or engine == 'gtts':
            engine = 'edge-tts'
            logger.info("Using edge-tts for better voice quality")
        
        try:
            # Create TTSManager
            # Check if edge-tts is available before creating TTSManager
            # Try importing edge_tts directly first
            try:
                import edge_tts
                # Test if it actually works
                edge_tts_available = True
                logger.info(f"🎤 DEBUG: edge_tts importado com sucesso")
                logger.info(f"🎤 DEBUG: edge_tts module path: {edge_tts.__file__ if hasattr(edge_tts, '__file__') else 'unknown'}")
            except ImportError as e:
                edge_tts_available = False
                logger.warning(f"edge-tts not available, cannot generate audio: {e}")
                logger.warning(f"🎤 DEBUG: ImportError ao importar edge_tts: {e}")
                logger.warning(f"🎤 DEBUG: Python path: {__import__('sys').path}")
                print(f"⚠️  edge-tts não está disponível. Instale: pip install edge-tts")
                print(f"⚠️  DEBUG: Erro de importação: {e}")
                print(f"⚠️  DEBUG: Tente executar: python3 -m pip install edge-tts")
                return video_path
            except Exception as e:
                edge_tts_available = False
                logger.error(f"🎤 DEBUG: Erro inesperado ao importar edge_tts: {e}", exc_info=True)
                print(f"⚠️  Erro ao importar edge-tts: {e}")
                return video_path
            
            logger.info(f"🎤 DEBUG: Criando TTSManager com engine={engine}, lang={lang}, voice={voice}")
            try:
                tts_manager = TTSManager(
                    lang=lang,
                    engine=engine,
                    slow=False,
                    voice=voice,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
                logger.info(f"🎤 DEBUG: TTSManager criado com sucesso")
            except ImportError as e:
                logger.error(f"🎤 DEBUG: ImportError ao criar TTSManager: {e}", exc_info=True)
                print(f"⚠️  Erro ao criar TTSManager: {e}")
                return video_path
            except Exception as e:
                logger.error(f"🎤 DEBUG: Erro inesperado ao criar TTSManager: {e}", exc_info=True)
                print(f"⚠️  Erro inesperado ao criar TTSManager: {e}")
                return video_path
            
            # Convert step_timestamps to format expected by TTSManager
            # TTSManager expects steps with 'audio', 'subtitle', 'description', 'start_time'
            # Implement continuity: audio continues until next step with different audio or empty string
            # IMPORTANT: We need to include ALL steps (even without audio) to maintain video sync
            # Steps without audio will be filled with silence
            tts_steps = []
            current_audio_text = None
            
            logger.info(f"🎤 DEBUG: Processing {len(self.step_timestamps)} step_timestamps for audio generation")
            steps_with_audio = 0
            steps_without_audio = 0
            
            for i, step_data in enumerate(self.step_timestamps, 1):
                step = step_data.get('step', {})
                step_start_time = step_data.get('start_time', 0.0)
                step_end_time = step_data.get('end_time', step_start_time + step_data.get('duration', 0.0))
                step_duration = step_end_time - step_start_time
                
                # Check for audio field in step
                # IMPORTANT: audio is stored directly in step_data (from _execute_yaml_steps)
                # It's also in step dict (from YAML), but step_data takes precedence
                step_audio = step_data.get('audio')
                if step_audio is None:
                    # Fallback to step dict if not in step_data
                    step_audio = step.get('audio')
                
                logger.debug(f"🎤 DEBUG: Step {i}: step_audio from step_data={step_data.get('audio')}, from step={step.get('audio')}, final={step_audio}")
                
                if step_audio is not None:
                    # Explicit audio field: update current_audio_text
                    if step_audio == '':
                        # Empty string means clear audio
                        current_audio_text = None
                        logger.debug(f"🎤 DEBUG: Step {i}: Audio cleared (empty string)")
                    else:
                        # New audio text
                        current_audio_text = step_audio
                        steps_with_audio += 1
                        logger.debug(f"🎤 DEBUG: Step {i}: Audio set to '{current_audio_text}'")
                else:
                    steps_without_audio += 1
                    logger.debug(f"🎤 DEBUG: Step {i}: No audio field, continuing previous: '{current_audio_text}'")
                # If no audio field, current_audio_text continues from previous step
                
                # Add step to tts_steps (even if no audio - will be filled with silence)
                # This ensures video synchronization
                tts_steps.append({
                    'audio': current_audio_text,  # None if no audio, text if audio configured
                    'start_time': step_start_time,
                    'duration': step_duration,
                    'end_time': step_end_time
                })
            
            logger.info(f"🎤 DEBUG: Steps with audio: {steps_with_audio}, without audio: {steps_without_audio}")
            logger.info(f"🎤 DEBUG: Total tts_steps prepared: {len(tts_steps)}")
            
            if not tts_steps:
                logger.warning("No steps prepared for audio generation")
                print(f"⚠️  Nenhum step preparado para geração de áudio")
                return video_path
            
            # Check if we have any audio text at all
            steps_with_audio_text = sum(1 for s in tts_steps if s.get('audio'))
            if steps_with_audio_text == 0:
                logger.warning("No steps with audio text found (all steps have None audio)")
                print(f"⚠️  Nenhum step com texto de áudio encontrado (todos têm audio=None)")
                print(f"⚠️  DEBUG: Verifique se os steps no YAML têm o campo 'audio' preenchido")
                return video_path
            
            # Generate narration with timing (return_timed_audio=True)
            # This generates a single MP3 file with all audio segments and silence, synchronized with video
            logger.info(f"Generating audio narration for {len(tts_steps)} steps...")
            logger.info(f"🎤 DEBUG: Steps with audio text: {steps_with_audio_text}/{len(tts_steps)}")
            print(f"🔊 Gerando narração para {len(tts_steps)} steps...")
            print(f"🔊 DEBUG: {steps_with_audio_text} steps têm texto de áudio")
            
            # Show sample of what we're sending to TTSManager
            sample_steps = [s for s in tts_steps if s.get('audio')][:3]
            for i, sample in enumerate(sample_steps, 1):
                logger.info(f"🎤 DEBUG: Sample step {i}: audio='{sample.get('audio')}', start={sample.get('start_time'):.2f}s, duration={sample.get('duration'):.2f}s")
            
            try:
                narration_audio = await tts_manager.generate_narration(
                    tts_steps,
                    video_path.parent,
                    test_name,
                    return_timed_audio=True  # Returns single file with all audio + silence, synchronized with video
                )
                
                logger.info(f"🎤 DEBUG: generate_narration returned: {narration_audio}")
                if narration_audio:
                    logger.info(f"🎤 DEBUG: narration_audio path exists: {narration_audio.exists()}")
                    if narration_audio.exists():
                        logger.info(f"🎤 DEBUG: narration_audio size: {narration_audio.stat().st_size} bytes")
                
                if not narration_audio or not narration_audio.exists():
                    logger.warning("Audio narration generation failed")
                    logger.warning(f"🎤 DEBUG: narration_audio is None or doesn't exist: {narration_audio}")
                    print(f"⚠️  Falha ao gerar narração de áudio")
                    print(f"⚠️  DEBUG: TTSManager.generate_narration retornou: {narration_audio}")
                    return video_path
            except Exception as e:
                logger.error(f"🎤 DEBUG: Exception during generate_narration: {e}", exc_info=True)
                print(f"⚠️  Erro ao gerar narração: {e}")
                import traceback
                print(f"⚠️  DEBUG: Traceback: {traceback.format_exc()}")
                return video_path
            
            logger.info(f"Audio narration generated: {narration_audio.name} ({narration_audio.stat().st_size / 1024:.1f} KB)")
            print(f"✅ Narração de áudio gerada: {narration_audio.name}")
            
            # Verify audio file is valid
            audio_duration = tts_manager._get_audio_duration(narration_audio)
            logger.info(f"Audio duration: {audio_duration:.2f}s")
            print(f"📊 Duração do áudio: {audio_duration:.2f}s")
            
            # Embed audio into video MP4
            logger.info("Embedding audio into video MP4...")
            print(f"🎬 Embutindo áudio no vídeo MP4...")
            
            try:
                import subprocess
                # Check if ffmpeg is available
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("ffmpeg not found, cannot embed audio")
                print(f"⚠️  ffmpeg não encontrado. Áudio não será embutido no vídeo.")
                return video_path
            
            # Output will be MP4 (even if input is webm, we convert)
            # Use same name as input but ensure .mp4 extension
            # If input is already MP4, use temporary suffix to avoid overwriting
            if video_path.suffix == '.mp4':
                output_path = video_path.parent / f"{video_path.stem}_with_audio.mp4"
            else:
                output_path = video_path.parent / f"{video_path.stem}.mp4"
            
            # Ensure output_path is absolute
            output_path = output_path.resolve()
            
            # Build ffmpeg command to embed audio
            # Video input may already have subtitles embedded, so we preserve them
            # For MP4, we use AAC codec for audio
            # IMPORTANT: Use absolute paths for all inputs
            video_input_absolute = str(video_path.resolve())
            audio_input_absolute = str(narration_audio.resolve())
            
            # Verify files exist before processing
            if not video_path.exists():
                logger.error(f"Video file does not exist: {video_path}")
                print(f"❌ Erro: Arquivo de vídeo não encontrado: {video_path}")
                return video_path
            
            if not narration_audio.exists():
                logger.error(f"Audio file does not exist: {narration_audio}")
                print(f"❌ Erro: Arquivo de áudio não encontrado: {narration_audio}")
                return video_path
            
            logger.info(f"🎤 DEBUG: Video file exists: {video_path.exists()}, size: {video_path.stat().st_size} bytes")
            logger.info(f"🎤 DEBUG: Audio file exists: {narration_audio.exists()}, size: {narration_audio.stat().st_size} bytes")
            
            cmd = [
                'ffmpeg',
                '-i', video_input_absolute,  # Video input (may already have subtitles) - absolute path
                '-i', audio_input_absolute,  # Audio input (MP3 with all segments + silence) - absolute path
                '-c:v', 'libx264',  # Re-encode video to ensure compatibility (preserves subtitles)
                '-preset', 'ultrafast',  # Otimização: codificação mais rápida
                '-crf', '23',  # Qualidade razoável
                '-c:a', 'aac',  # AAC codec for MP4
                '-b:a', '128k',  # Otimização: bitrate de áudio reduzido (era 192k)
                '-map', '0:v:0',  # Use video from first input (with subtitles if embedded)
                '-map', '1:a:0',  # Use audio from second input
                '-shortest',  # End when shortest stream ends (sync with audio)
                '-movflags', '+faststart',  # Fast start for web playback
                '-y',  # Overwrite output
                str(output_path)  # Output path is already absolute
            ]
            
            logger.info(f"Running ffmpeg to embed audio: {' '.join(cmd)}")
            logger.info(f"🎤 DEBUG: Video input (relative): {video_path}")
            logger.info(f"🎤 DEBUG: Video input (absolute): {video_input_absolute}")
            logger.info(f"🎤 DEBUG: Audio input (relative): {narration_audio}")
            logger.info(f"🎤 DEBUG: Audio input (absolute): {audio_input_absolute}")
            logger.info(f"🎤 DEBUG: Video output (absolute): {output_path}")
            print(f"🔄 Processando vídeo com áudio...")
            print(f"🎤 DEBUG: Embutindo áudio do arquivo: {narration_audio.name}")
            print(f"🎤 DEBUG: Vídeo de entrada: {video_path.name}")
            print(f"🎤 DEBUG: Vídeo de saída: {output_path.name}")
            
            result = subprocess.run(
                cmd,
                cwd=str(video_path.parent),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout (video processing can take time)
            )
            
            # Log ffmpeg output for debugging
            if result.returncode != 0:
                # Get full error message
                error_output = result.stderr if result.stderr else result.stdout
                logger.warning(f"🎤 DEBUG: FFmpeg return code: {result.returncode}")
                logger.warning(f"🎤 DEBUG: FFmpeg stderr (full): {error_output}")
                logger.warning(f"🎤 DEBUG: FFmpeg stdout: {result.stdout}")
                print(f"⚠️  DEBUG: FFmpeg retornou código {result.returncode}")
                if error_output:
                    # Try to extract the actual error message (usually after version info)
                    error_lines = error_output.split('\n')
                    # Skip version info and find actual error
                    actual_error = '\n'.join([line for line in error_lines if line and not line.startswith('ffmpeg version') and not line.startswith('built with') and not line.startswith('configuration:')])
                    if actual_error:
                        print(f"⚠️  DEBUG: Erro FFmpeg: {actual_error[:500]}")
                    else:
                        print(f"⚠️  DEBUG: Erro FFmpeg completo: {error_output[:500]}")
            
            if result.returncode == 0 and output_path.exists():
                # Verify output file
                output_size = output_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"Video with audio created: {output_path.name} ({output_size:.1f} MB)")
                print(f"✅ Vídeo com áudio criado: {output_path.name} ({output_size:.1f} MB)")
                
                # Replace original video with audio version
                if video_path.exists() and video_path != output_path:
                    video_path.unlink()
                if output_path != video_path:
                    output_path.rename(video_path)
                
                logger.info(f"Video processed with embedded audio: {video_path.name}")
                print(f"✅ Vídeo processado com áudio embutido: {video_path.name}")
                
                # Clean up temporary audio file (audio is now embedded)
                if narration_audio.exists():
                    try:
                        narration_audio.unlink()
                        logger.info(f"Cleaned up temporary audio file: {narration_audio.name}")
                    except Exception as e:
                        logger.warning(f"Could not delete temporary audio file: {e}")
                
                return video_path
            else:
                error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
                logger.warning(f"ffmpeg failed to embed audio: {error_msg}")
                print(f"⚠️  Erro ao embutir áudio no vídeo")
                print(f"   Detalhes: {error_msg[:200]}")
                if output_path.exists():
                    output_path.unlink()
                return video_path
                
        except ImportError as e:
            logger.warning(f"TTS library not available: {e}")
            print(f"⚠️  Biblioteca TTS não disponível: {e}")
            print(f"💡 Instale: pip install edge-tts")
            return video_path
        except Exception as e:
            logger.error(f"Error generating audio: {e}", exc_info=True)
            print(f"⚠️  Erro ao gerar áudio: {e}")
            return video_path
    
    async def _cleanup_temp_files(self, video_dir: Path, test_name: str):
        """
        Clean up temporary files (SRT, MP3, intermediate videos) leaving only final MP4.
        
        Args:
            video_dir: Directory containing video files
            test_name: Name of test (to identify final video)
        """
        try:
            # Find final video (should be MP4 with test name)
            final_video = video_dir / f"{test_name}.mp4"
            if not final_video.exists():
                # Try to find any MP4 file as final
                mp4_files = list(video_dir.glob("*.mp4"))
                if mp4_files:
                    final_video = max(mp4_files, key=lambda p: p.stat().st_mtime)
                    logger.info(f"Using most recent MP4 as final video: {final_video.name}")
            
            # Clean up temporary files
            cleaned = []
            
            # Remove SRT files
            for srt_file in video_dir.glob("*.srt"):
                try:
                    srt_file.unlink()
                    cleaned.append(srt_file.name)
                    logger.debug(f"Removed SRT: {srt_file.name}")
                except Exception as e:
                    logger.warning(f"Could not remove SRT {srt_file.name}: {e}")
            
            # Remove MP3 files (narration audio)
            for mp3_file in video_dir.glob("*.mp3"):
                try:
                    mp3_file.unlink()
                    cleaned.append(mp3_file.name)
                    logger.debug(f"Removed MP3: {mp3_file.name}")
                except Exception as e:
                    logger.warning(f"Could not remove MP3 {mp3_file.name}: {e}")
            
            # Remove intermediate video files (webm, _with_subtitles, _with_audio, etc.)
            for video_file in video_dir.glob("*"):
                if video_file.is_file():
                    # Skip final video
                    if video_file == final_video:
                        continue
                    
                    # Remove webm files (intermediate)
                    if video_file.suffix == '.webm':
                        try:
                            video_file.unlink()
                            cleaned.append(video_file.name)
                            logger.debug(f"Removed intermediate video: {video_file.name}")
                        except Exception as e:
                            logger.warning(f"Could not remove video {video_file.name}: {e}")
                    
                    # Remove files with temporary suffixes
                    if any(suffix in video_file.stem for suffix in ['_with_subtitles', '_with_audio', '_tts_temp']):
                        try:
                            video_file.unlink()
                            cleaned.append(video_file.name)
                            logger.debug(f"Removed temporary file: {video_file.name}")
                        except Exception as e:
                            logger.warning(f"Could not remove temporary file {video_file.name}: {e}")
            
            # Remove temporary TTS directories
            import shutil
            for temp_dir in video_dir.glob("*_tts_temp"):
                if temp_dir.is_dir():
                    try:
                        shutil.rmtree(temp_dir)
                        cleaned.append(temp_dir.name)
                        logger.debug(f"Removed temporary TTS directory: {temp_dir.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove TTS directory {temp_dir.name}: {e}")
            
            if cleaned:
                logger.info(f"Cleaned up {len(cleaned)} temporary files")
                print(f"🧹 Limpeza: {len(cleaned)} arquivos temporários removidos")
            else:
                logger.debug("No temporary files to clean up")
                
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}", exc_info=True)
    
    async def _wait_for_page_stable(self, timeout: float = 10.0) -> None:
        """
        Wait for page to stabilize after an action.
        
        This implements dynamic wait that detects when page stops changing:
        - Waits for network idle
        - Waits for DOM to stabilize
        - Waits for any loading indicators to disappear
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        # Log screen event: waiting for page stability
        if self.recorder_logger and self.recorder_logger.is_debug:
            try:
                page_title = await self.page.title()
            except:
                page_title = 'N/A'
            page_state = {
                'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                'title': page_title
            }
            self.recorder_logger.log_screen_event(
                event_type='waiting_for_stability',
                page_state=page_state,
                details={'timeout': timeout}
            )
        
        try:
            # First, wait for DOM to be ready
            await self.page.wait_for_load_state('domcontentloaded', timeout=int(timeout * 1000))
            
            # Log screen event: DOM ready
            if self.recorder_logger and self.recorder_logger.is_debug:
                try:
                    page_title = await self.page.title()
                except:
                    page_title = 'N/A'
                page_state = {
                    'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                    'title': page_title
                }
                self.recorder_logger.log_screen_event(
                    event_type='dom_ready',
                    page_state=page_state
                )
        except Exception:
            pass
        
        try:
            # Wait for network to be idle (no requests for 500ms)
            await self.page.wait_for_load_state('networkidle', timeout=int(timeout * 1000))
            
            # Log screen event: network idle
            if self.recorder_logger and self.recorder_logger.is_debug:
                try:
                    page_title = await self.page.title()
                except:
                    page_title = 'N/A'
                page_state = {
                    'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                    'title': page_title,
                    'network_idle': True
                }
                self.recorder_logger.log_screen_event(
                    event_type='network_idle',
                    page_state=page_state
                )
        except Exception:
            # Fallback: wait for load state
            try:
                await self.page.wait_for_load_state('load', timeout=int(timeout * 1000))
                
                # Log screen event: page loaded
                if self.recorder_logger and self.recorder_logger.is_debug:
                    try:
                        page_title = await self.page.title()
                    except:
                        page_title = 'N/A'
                    page_state = {
                        'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                        'title': page_title
                    }
                    self.recorder_logger.log_screen_event(
                        event_type='page_loaded',
                        page_state=page_state
                    )
            except Exception:
                pass
        
        # Additional wait for dynamic content (Odoo, HTMX, etc.)
        # Check if page is still loading by monitoring DOM changes
        try:
            initial_html = await self.page.content()
            await asyncio.sleep(0.5)  # Wait a bit
            final_html = await self.page.content()
            
            # If HTML changed, wait a bit more
            if initial_html != final_html:
                await asyncio.sleep(0.5)
        except Exception:
            pass
    
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
    
    async def _execute_yaml_steps(self):
        """Execute YAML steps using internal handler functions."""
        if not self.yaml_steps:
            logger.warning("No YAML steps to execute")
            return
        
        # Verify we're using the correct page (same one that has video recording)
        if not self.page:
            error_msg = "No page available for executing steps!"
            if self.recorder_logger:
                self.recorder_logger.log_critical_failure(
                    action='execute_yaml_steps',
                    error=error_msg,
                    page_state=None,
                    details={'mode': self.mode}
                )
            logger.error(error_msg)
            raise RuntimeError("Page not available")
        
        # Log page and context info for debugging
        page_url = self.page.url if hasattr(self.page, 'url') else 'unknown'
        context_info = 'no context'
        if hasattr(self, 'browser_manager') and self.browser_manager.context:
            context_info = f'context={id(self.browser_manager.context)}'
            if hasattr(self.browser_manager.context, '_options'):
                video_enabled = 'record_video_dir' in str(self.browser_manager.context._options)
                context_info += f', video={video_enabled}'
        
        # Track video recording start time and step timestamps for subtitles
        import time
        # Use video_start_time (datetime) to calculate correct timestamps
        if hasattr(self, 'video_start_time') and self.video_start_time:
            video_start_datetime = self.video_start_time
        else:
            # Fallback: use current time if video_start_time not set
            video_start_datetime = datetime.now()
        
        video_start_timestamp = time.time()
        self.step_timestamps = []  # Store timestamps for subtitle generation
        
        # Log screen event: execution started
        if self.recorder_logger:
            total_steps = len(self.yaml_steps) if self.yaml_steps and isinstance(self.yaml_steps, list) else 0
            try:
                if hasattr(self.page, 'title'):
                    page_title = await self.page.title()
                else:
                    page_title = 'N/A'
            except:
                page_title = 'N/A'
            self.recorder_logger.log_screen_event(
                event_type='yaml_execution_started',
                page_state={'url': page_url, 'title': page_title},
                details={'total_steps': total_steps, 'context_info': context_info}
            )
        
        # Track current subtitle and audio for continuity
        current_subtitle = None
        current_audio = None
        
        for i, step in enumerate(self.yaml_steps, 1):
            action = step.get('action')
            description = step.get('description', '')
            subtitle = step.get('subtitle')  # Use subtitle field, not description
            audio = step.get('audio')  # Use audio field
            
            # Calculate step start time relative to video start
            step_start_datetime = datetime.now()
            step_start_elapsed = (step_start_datetime - video_start_datetime).total_seconds()
            
            # Set step context in logger
            if self.recorder_logger:
                self.recorder_logger.set_step_context(i, action)
            
            # Log step execution start
            if self.recorder_logger:
                try:
                    if hasattr(self.page, 'title'):
                        page_title = await self.page.title()
                    else:
                        page_title = 'N/A'
                except:
                    page_title = 'N/A'
                page_state = {
                    'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                    'title': page_title
                }
                self.recorder_logger.set_page_state(page_state)
            
            # Handle subtitle continuity
            # If step has subtitle, use it; if not, continue previous subtitle
            if subtitle is not None:
                if subtitle == '':
                    # Empty string means clear subtitle
                    current_subtitle = None
                    logger.debug(f"🎬 DEBUG: Step {i}: Subtitle cleared (empty string)")
                else:
                    current_subtitle = subtitle
                    logger.debug(f"🎬 DEBUG: Step {i}: Subtitle set to '{current_subtitle}'")
            # If no subtitle field and current_subtitle exists, continue it
            elif current_subtitle:
                logger.debug(f"🎬 DEBUG: Step {i}: Subtitle continues from previous: '{current_subtitle}'")
            
            # Handle audio continuity (similar to subtitles)
            if audio is not None:
                if audio == '':
                    # Empty string means clear audio
                    current_audio = None
                    logger.debug(f"🎬 DEBUG: Step {i}: Audio cleared (empty string)")
                else:
                    current_audio = audio
                    logger.debug(f"🎬 DEBUG: Step {i}: Audio set to '{current_audio}'")
            # If no audio field and current_audio exists, continue it
            elif current_audio:
                logger.debug(f"🎬 DEBUG: Step {i}: Audio continues from previous: '{current_audio}'")
            
            # Store step start time for subtitle and audio generation
            step_data = {
                'step': step,
                'start_time': step_start_elapsed,  # Relative to video start (datetime-based)
                'action': action,
                'description': description,
                'subtitle': current_subtitle,  # Store current subtitle (may be from previous step)
                'audio': current_audio  # Store current audio (may be from previous step)
            }
            
            logger.debug(f"🎬 DEBUG: Step {i} step_data: subtitle='{current_subtitle}', audio='{current_audio}'")
            
            # Start timer for step execution
            step_action_id = f"step_{i}_{action}"
            if self.recorder_logger:
                self.recorder_logger.start_action_timer(step_action_id)
            
            try:
                if action == 'go_to':
                    url = step.get('url')
                    if url:
                        # Log screen event: navigation
                        if self.recorder_logger:
                            self.recorder_logger.log_screen_event(
                                event_type='navigation',
                                page_state={'url': url, 'previous_url': self.page.url if hasattr(self.page, 'url') else ''}
                            )
                        await self.page.goto(url, wait_until='domcontentloaded')
                        # Use dynamic wait to detect when page stops changing
                        await self._wait_for_page_stable(timeout=10.0)
                        # Log screen event: page loaded
                        if self.recorder_logger:
                            try:
                                page_title = await self.page.title()
                            except:
                                page_title = 'N/A'
                            self.recorder_logger.log_screen_event(
                                event_type='page_loaded',
                                page_state={'url': self.page.url, 'title': page_title}
                            )
                
                elif action == 'click':
                    text = step.get('text')
                    selector = step.get('selector')
                    
                    # Wait for page to be ready before clicking
                    try:
                        await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                    except:
                        pass
                    
                    if text:
                        result = await self.command_handlers.handle_pw_click(f'"{text}"')
                    elif selector:
                        result = await self.command_handlers.handle_pw_click(f'selector "{selector}"')
                    else:
                        logger.warning(f"Click step has no text or selector: {step}")
                        result = {'success': False, 'error': 'No text or selector'}
                    
                    # Log step execution result
                    if self.recorder_logger:
                        duration_ms = self.recorder_logger.end_action_timer(step_action_id)
                        element_info = {'text': text, 'selector': selector} if text or selector else None
                        try:
                            if hasattr(self.page, 'title'):
                                page_title = await self.page.title()
                            else:
                                page_title = 'N/A'
                        except:
                            page_title = 'N/A'
                        page_state = {
                            'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                            'title': page_title
                        }
                        self.recorder_logger.log_step_execution(
                            step_number=i,
                            action=action,
                            success=result.get('success', False) if result else False,
                            duration_ms=duration_ms,
                            error=result.get('error') if result else None,
                            element_info=element_info,
                            page_state=page_state
                        )
                    
                    # Use dynamic wait to detect when page stops changing after click
                    await self._wait_for_page_stable(timeout=10.0)
                
                elif action == 'type':
                    text = step.get('text', '')
                    selector = step.get('selector')
                    field_text = step.get('field_text')
                    if selector:
                        result = await self.command_handlers.handle_pw_type(f'"{text}" selector "{selector}"')
                    elif field_text:
                        result = await self.command_handlers.handle_pw_type(f'"{text}" into "{field_text}"')
                    else:
                        result = await self.command_handlers.handle_pw_type(f'"{text}"')
                    
                    # Log step execution result
                    if self.recorder_logger:
                        duration_ms = self.recorder_logger.end_action_timer(step_action_id)
                        element_info = {'field': field_text or selector, 'text': text}
                        try:
                            if hasattr(self.page, 'title'):
                                page_title = await self.page.title()
                            else:
                                page_title = 'N/A'
                        except:
                            page_title = 'N/A'
                        page_state = {
                            'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                            'title': page_title
                        }
                        self.recorder_logger.log_step_execution(
                            step_number=i,
                            action=action,
                            success=result.get('success', False) if result else False,
                            duration_ms=duration_ms,
                            error=result.get('error') if result else None,
                            element_info=element_info,
                            page_state=page_state
                        )
                    
                    # Use dynamic wait to detect when page stops changing after type
                    await self._wait_for_page_stable(timeout=5.0)
                
                elif action == 'submit':
                    button_text = step.get('button_text') or step.get('text')
                    if button_text:
                        result = await self.command_handlers.handle_pw_submit(f'"{button_text}"')
                    else:
                        result = await self.command_handlers.handle_pw_submit('')
                    
                    # Log step execution result
                    if self.recorder_logger:
                        duration_ms = self.recorder_logger.end_action_timer(step_action_id)
                        element_info = {'button_text': button_text}
                        try:
                            if hasattr(self.page, 'title'):
                                page_title = await self.page.title()
                            else:
                                page_title = 'N/A'
                        except:
                            page_title = 'N/A'
                        page_state = {
                            'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                            'title': page_title
                        }
                        self.recorder_logger.log_step_execution(
                            step_number=i,
                            action=action,
                            success=result.get('success', False) if result else False,
                            duration_ms=duration_ms,
                            error=result.get('error') if result else None,
                            element_info=element_info,
                            page_state=page_state
                        )
                    
                    # Use dynamic wait to detect when page stops changing after submit
                    await self._wait_for_page_stable(timeout=10.0)
                
                elif action == 'wait':
                    # Wait action - reduce time in fast_mode
                    seconds = step.get('seconds', 1.0)
                    if self.fast_mode:
                        # In fast mode, reduce wait time significantly (but keep minimum for video)
                        seconds = max(seconds * 0.1, 0.1)  # 10% of original, minimum 0.1s
                    await asyncio.sleep(seconds)
                    
                    # Log wait step
                    if self.recorder_logger:
                        duration_ms = self.recorder_logger.end_action_timer(step_action_id)
                        self.recorder_logger.log_step_execution(
                            step_number=i,
                            action=action,
                            success=True,
                            duration_ms=duration_ms,
                            details={'wait_seconds': seconds}
                        )
                
            except Exception as e:
                step_error_datetime = datetime.now()
                step_error_elapsed = (step_error_datetime - video_start_datetime).total_seconds()
                
                # Log critical failure
                if self.recorder_logger:
                    duration_ms = self.recorder_logger.end_action_timer(step_action_id)
                    page_state = {
                        'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                        'title': await self.page.title() if hasattr(self.page, 'title') else 'N/A'
                    }
                    self.recorder_logger.log_critical_failure(
                        action=f'step_{i}_{action}',
                        error=str(e),
                        page_state=page_state
                    )
                    self.recorder_logger.log_step_execution(
                        step_number=i,
                        action=action,
                        success=False,
                        duration_ms=duration_ms,
                        error=str(e),
                        page_state=page_state
                    )
                
                # Store error time for subtitle
                step_data['end_time'] = step_error_elapsed
                step_data['duration'] = step_error_elapsed - step_data['start_time']
                self.step_timestamps.append(step_data)
                raise
            
            # Calculate step end time relative to video start
            step_end_datetime = datetime.now()
            step_end_elapsed = (step_end_datetime - video_start_datetime).total_seconds()
            step_duration = step_end_elapsed - step_data['start_time']
            
            # Store step end time for subtitle generation
            step_data['end_time'] = step_end_elapsed
            step_data['duration'] = step_duration
            self.step_timestamps.append(step_data)
        
        steps_end_datetime = datetime.now()
        total_elapsed = (steps_end_datetime - video_start_datetime).total_seconds()
        
        # Log screen event: execution completed
        if self.recorder_logger:
            try:
                page_url = self.page.url if hasattr(self.page, 'url') else 'N/A'
                if hasattr(self.page, 'title'):
                    page_title = await self.page.title()
                else:
                    page_title = 'N/A'
            except:
                page_url = 'N/A'
                page_title = 'N/A'
            page_state = {
                'url': page_url,
                'title': page_title
            }
            total_steps = len(self.yaml_steps) if self.yaml_steps and isinstance(self.yaml_steps, list) else 0
            self.recorder_logger.log_screen_event(
                event_type='yaml_execution_completed',
                page_state=page_state,
                details={'total_steps': total_steps, 'total_duration_seconds': total_elapsed}
            )
        
        # Debug: show what's in step_timestamps (only in debug mode)
        if self.recorder_logger and self.recorder_logger.is_debug and self.step_timestamps:
            steps_with_subtitle = sum(1 for s in self.step_timestamps if s.get('subtitle'))
            steps_with_audio = sum(1 for s in self.step_timestamps if s.get('audio'))
            logger.info(f"🎬 DEBUG: Steps with subtitle: {steps_with_subtitle}/{len(self.step_timestamps)}")
            logger.info(f"🎬 DEBUG: Steps with audio: {steps_with_audio}/{len(self.step_timestamps)}")
        else:
            logger.warning(f"🎬 DEBUG: step_timestamps is EMPTY! No timestamps collected!")
        
        logger.info("✅ All YAML steps executed successfully")

        # Wait a bit after all steps to ensure video captures everything
        # This is especially important for the last action
        # Playwright writes video frames asynchronously, so we need to wait for all frames
        await asyncio.sleep(2.0)
        after_wait_datetime = datetime.now()
        elapsed_after_wait = (after_wait_datetime - video_start_datetime).total_seconds()
        logger.info(f"🎬 VIDEO DEBUG: After wait delay at {elapsed_after_wait:.2f}s")
        logger.info("Waiting after steps completion to ensure video captures final actions")
        
        # Verify we're still using the same context that has video recording
        if hasattr(self, 'browser_manager') and self.browser_manager.context:
            context_id = id(self.browser_manager.context)
            page_context_id = id(self.page.context) if hasattr(self.page, 'context') else None
            logger.info(f"🎬 VIDEO DEBUG: Context verification - browser_manager.context={context_id}, page.context={page_context_id}")
            logger.info(f"Context verification after steps: browser_manager.context={context_id}, page.context={page_context_id}")
            if page_context_id and context_id != page_context_id:
                logger.error(f"⚠️  CONTEXT MISMATCH! Page is using different context than browser_manager!")
                logger.error(f"   This means video is being recorded in a different context!")
    
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
    

