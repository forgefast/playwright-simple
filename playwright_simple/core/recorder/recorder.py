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
from .config import RecorderConfig

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
    
    def __init__(
        self,
        output_path: Path = None,
        config: RecorderConfig = None,
        # Legacy parameters for backward compatibility
        initial_url: str = None,
        headless: bool = False,
        debug: bool = False,
        fast_mode: bool = False,
        mode: str = 'write',
        log_level: str = None,
        log_file: Path = None
    ):
        """
        Initialize recorder.
        
        Args:
            output_path: Path to output YAML file (legacy parameter, use config instead)
            config: RecorderConfig instance (preferred way)
            initial_url: Initial URL to open (legacy parameter, use config instead)
            headless: Run browser in headless mode (legacy parameter, use config instead)
            debug: Enable debug mode (legacy parameter, use config instead)
            fast_mode: Accelerate steps (legacy parameter, use config instead)
            mode: 'write' or 'read' (legacy parameter, use config instead)
            log_level: Log level (legacy parameter, use config instead)
            log_file: Optional log file path (legacy parameter, use config instead)
        
        Note:
            Either provide `config` (preferred) or use legacy parameters.
            If both are provided, `config` takes precedence.
        """
        # Handle configuration: prefer config object, fallback to legacy parameters
        if config is not None:
            self.config = config
        elif output_path is not None:
            # Create config from legacy parameters
            self.config = RecorderConfig.from_kwargs(
                output_path=output_path,
                initial_url=initial_url,
                headless=headless,
                debug=debug,
                fast_mode=fast_mode,
                mode=mode,
                log_level=log_level,
                log_file=log_file
            )
        else:
            raise ValueError("Either 'config' or 'output_path' must be provided")
        
        # Extract configuration values for backward compatibility
        self.output_path = self.config.output_path
        self.initial_url = self.config.initial_url
        self.headless = self.config.headless
        self.debug = self.config.debug
        self.mode = self.config.mode
        
        # Initialize recorder logger
        console_level = 'DEBUG' if self.config.debug else self.config.log_level
        self.recorder_logger = RecorderLogger(
            name="recorder",
            console_level=console_level,
            file_level='DEBUG',  # Always DEBUG for file
            log_file=self.config.log_file
        )
        
        # Initialize browser manager - will be configured with video options if needed
        # Configure slow_mo based on speed_level
        # Ultra fast mode should not use slow_mo to maximize performance
        # Normal/fast modes use slow_mo=100 for smooth video recording
        from .config import SpeedLevel
        slow_mo_value = None if self.config.speed_level == SpeedLevel.ULTRA_FAST else 100
        self.browser_manager = BrowserManager(headless=self.config.headless, slow_mo=slow_mo_value)
        self.event_capture: Optional[EventCapture] = None
        self.cursor_controller: Optional[CursorController] = None
        self.action_converter = ActionConverter(recorder_logger=self.recorder_logger)
        
        # In write mode: YAMLWriter, in read mode: load YAML steps
        if self.mode == 'write':
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
            self.yaml_steps = yaml_data.get('steps', []) if yaml_data else []
            logger.info(f"🎬 DEBUG: Loaded YAML - steps count: {len(self.yaml_steps)}, steps type: {type(self.yaml_steps)}")
            if self.yaml_steps:
                logger.info(f"🎬 DEBUG: First step: {self.yaml_steps[0]}")
            # Get initial_url from YAML if not provided
            if not self.config.initial_url or self.config.initial_url == 'about:blank':
                first_step = self.yaml_steps[0] if self.yaml_steps else {}
                if first_step.get('action') == 'go_to':
                    self.initial_url = first_step.get('url', 'about:blank')
                elif 'base_url' in yaml_data:
                    self.initial_url = yaml_data.get('base_url', 'about:blank')
            
            # Load video configuration from YAML if available
            self.video_config = None
            self.video_manager = None
            self.video_start_time = None
            logger.info(f"🎬 VIDEO DEBUG: Checking video config - VIDEO_AVAILABLE={VIDEO_AVAILABLE}, mode={self.config.mode}")
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
        self.fast_mode = self.config.fast_mode  # Keep for backward compatibility
        self.speed_level = self.config.speed_level  # Preferred: use speed_level
        
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
        self.console.register_command('pw-press', self.command_handlers.handle_pw_press)
        
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
                # Also pass speed_level so EventCapture can adjust polling delays
                self.event_capture = EventCapture(
                    page, 
                    debug=self.debug, 
                    event_handlers_instance=self.event_handlers, 
                    recorder_logger=self.recorder_logger,
                    speed_level=self.speed_level
                )
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
                self.cursor_controller = CursorController(
                    page, 
                    fast_mode=self.fast_mode, 
                    speed_level=self.speed_level,
                    recorder_logger=self.recorder_logger
                )
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
                # Adjust wait time based on speed_level for better performance
                before_close_wait_time = time.time()
                logger.info(f"🎬 VIDEO DEBUG: Starting wait before closing context at {before_close_wait_time:.2f}s")
                
                # Calculate wait time based on speed_level
                from .config import SpeedLevel
                if self.speed_level == SpeedLevel.ULTRA_FAST:
                    wait_time = 1.0  # Ultra fast: 1s wait (reduced from 3s)
                elif self.speed_level == SpeedLevel.FAST:
                    wait_time = 2.0  # Fast: 2s wait
                else:
                    wait_time = 3.0  # Normal/Slow: 3s wait (original)
                
                await asyncio.sleep(wait_time)
                after_close_wait_time = time.time()
                wait_elapsed = after_close_wait_time - before_close_wait_time
                logger.info(f"🎬 VIDEO DEBUG: Wait completed, elapsed: {wait_elapsed:.2f}s (speed_level: {self.speed_level})")
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
                    
                    # Process video using VideoProcessor
                    if hasattr(self, 'steps') and self.steps:
                        try:
                            from .video.processor import VideoProcessor
                            test_name = self.yaml_data.get('name', 'test') if hasattr(self, 'yaml_data') and self.yaml_data else 'test'
                            
                            processor = VideoProcessor(self.steps, self.video_config)
                            current_video_path = await processor.process_video(expected_path_final, test_name)
                            
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
                            
                            # Clean up temporary files
                            await processor.cleanup_temp_files(self.video_manager.video_dir, test_name)
                        except Exception as e:
                            logger.warning(f"Error processing video: {e}", exc_info=True)
                            print(f"⚠️  Erro ao processar vídeo: {e}")
                            import traceback
                            print(f"⚠️  DEBUG: Traceback: {traceback.format_exc()}")
                    
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
    
    async def _generate_srt_file(self, video_path: Path) -> Optional[Path]:
        """Generate SRT file (delegates to video.subtitles module)."""
        from .video.subtitles import SubtitleGenerator
        if not hasattr(self, 'steps') or not self.steps:
            return None
        generator = SubtitleGenerator(self.steps, self.video_config)
        return await generator.generate_srt_file(video_path)
    
    async def _generate_and_add_subtitles(self, video_path: Path) -> Optional[Path]:
        """Generate and add subtitles (delegates to video.subtitles module)."""
        from .video.subtitles import SubtitleGenerator
        if not hasattr(self, 'steps') or not self.steps:
            return video_path
        generator = SubtitleGenerator(self.steps, self.video_config)
        return await generator.generate_and_add_subtitles(video_path)
    
    async def _generate_and_add_audio(self, video_path: Path, test_name: str) -> Optional[Path]:
        """Generate and add audio (delegates to video.audio_embedder module)."""
        from .video.audio_embedder import AudioEmbedder
        if not hasattr(self, 'steps') or not self.steps:
            return video_path
        embedder = AudioEmbedder(self.steps, self.video_config)
        return await embedder.generate_and_add_audio(video_path, test_name)
    
    async def _cleanup_temp_files(self, video_dir: Path, test_name: str):
        """Clean up temporary files (delegates to video.processor module)."""
        from .video.processor import VideoProcessor
        if not hasattr(self, 'steps') or not self.steps:
            return
        processor = VideoProcessor(self.steps, self.video_config)
        await processor.cleanup_temp_files(video_dir, test_name)
    
    def _estimate_audio_duration(self, text: str) -> float:
        """Estimate audio duration (delegates to playback module)."""
        from .playback import estimate_audio_duration
        return estimate_audio_duration(text)
    
    async def _wait_for_page_stable(self, timeout: float = 10.0) -> None:
        """Wait for page to stabilize (delegates to page_stability module)."""
        from .page_stability import wait_for_page_stable
        await wait_for_page_stable(
            self.page,
            timeout=timeout,
            speed_level=self.speed_level,
            fast_mode=self.fast_mode,
            recorder_logger=self.recorder_logger
        )
    
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
    
    def _get_tts_manager(self):
        """Get TTS manager (delegates to playback module)."""
        from .playback import get_tts_manager
        # Check if already created
        if hasattr(self, '_tts_manager') and self._tts_manager:
            return self._tts_manager
        video_dir = None
        if hasattr(self, 'video_config') and self.video_config and hasattr(self.video_config, 'dir'):
            video_dir = Path(self.video_config.dir)
        tts_manager, cache_dir = get_tts_manager(getattr(self, 'video_config', None), video_dir)
        if tts_manager:
            self._tts_manager = tts_manager
            self._audio_cache_dir = cache_dir
        return tts_manager
    
    async def _play_audio_for_step(self, text: str) -> float:
        """Play audio for step (delegates to playback module)."""
        from .playback import play_audio_for_step
        if not text or not text.strip():
            return 0.0
        tts_manager = self._get_tts_manager()
        cache_dir = getattr(self, '_audio_cache_dir', None)
        return await play_audio_for_step(tts_manager, text, cache_dir)
    
    async def _execute_yaml_steps(self):
        """Execute YAML steps using playback module."""
        from .playback import execute_yaml_steps
        
        # Get video start time
        if hasattr(self, 'video_start_time') and self.video_start_time:
            video_start_time = self.video_start_time
        else:
            video_start_time = datetime.now()
        
        # Get video directory
        video_dir = None
        if hasattr(self, 'video_config') and self.video_config and hasattr(self.video_config, 'dir'):
            video_dir = Path(self.video_config.dir)
        
        # Execute steps using playback module
        self.steps = await execute_yaml_steps(
            yaml_steps=self.yaml_steps,
            page=self.page,
            command_handlers=self.command_handlers,
            recorder_logger=self.recorder_logger,
            speed_level=self.speed_level,
            video_start_time=video_start_time,
            video_config=getattr(self, 'video_config', None),
            video_dir=video_dir
        )
    
    async def _handle_keydown(self, event_data: dict):
        """Handle keydown event (delegates to write_mode module)."""
        from .write_mode import handle_keydown_event
        await handle_keydown_event(
            event_data,
            self.action_converter,
            self.yaml_writer,
            self.page,
            self.is_recording,
            self.is_paused,
            self.debug
        )
    
    async def _find_submit_button(self, context_element: dict) -> Optional[Dict[str, Any]]:
        """Find submit button (delegates to write_mode module)."""
        from .write_mode import find_submit_button
        page = self.event_capture.page if self.event_capture and self.event_capture.page else self.page
        return await find_submit_button(page, context_element)
    

