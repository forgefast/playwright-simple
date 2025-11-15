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
    
    def __init__(self, output_path: Path, initial_url: str = None, headless: bool = False, debug: bool = False, fast_mode: bool = False, mode: str = 'write'):
        """
        Initialize recorder.
        
        Args:
            output_path: Path to output YAML file
            initial_url: Initial URL to open (default: about:blank)
            headless: Run browser in headless mode
            debug: Enable debug mode (verbose logging)
            fast_mode: Accelerate steps (reduce delays, instant animations)
            mode: 'write' for recording (export), 'read' for playback (import)
        """
        self.output_path = Path(output_path)
        self.initial_url = initial_url or 'about:blank'
        self.headless = headless
        self.debug = debug
        self.mode = mode  # 'write' or 'read'
        
        # Initialize browser manager - will be configured with video options if needed
        self.browser_manager = BrowserManager(headless=headless)
        self.event_capture: Optional[EventCapture] = None
        self.cursor_controller: Optional[CursorController] = None
        self.action_converter = ActionConverter()
        
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
            is_paused_getter=lambda: self.is_paused
        )
        
        self.command_handlers = CommandHandlers(
            yaml_writer=self.yaml_writer,
            event_capture_getter=lambda: self.event_capture,
            cursor_controller_getter=lambda: self.cursor_controller,
            recording_state_setter=lambda v: setattr(self, 'is_recording', v),
            paused_state_setter=lambda v: setattr(self, 'is_paused', v),
            page_getter=lambda: self.page if hasattr(self, 'page') else None,
            recorder=self  # Pass recorder so handlers can access action_converter for programmatic actions
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
            
            # Initialize event capture only in write mode
            if self.mode == 'write':
                # Initialize event capture EARLY - before navigation if possible
                # This allows script injection to happen as soon as page loads
                # Pass event_handlers so event_capture can process events immediately
                self.event_capture = EventCapture(page, debug=self.debug, event_handlers_instance=self.event_handlers)
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
                self.cursor_controller = CursorController(page)
                # Start cursor at center of screen (or last position if available)
                await self.cursor_controller.start()
                # Set up navigation listener (encapsulated method, same logic as before)
                self.cursor_controller.setup_navigation_listener()
            
            if self.mode == 'write':
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
            else:  # read mode
                self.is_recording = True  # Set to True so handlers work
                logger.info("✅ Playback mode initialized - executing YAML steps...")
                await self._execute_yaml_steps()
                logger.info("YAML steps execution completed")
            
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
        # In read mode, yaml_writer is None, so use yaml_steps length instead
        if self.mode == 'read':
            steps_count = len(self.yaml_steps) if hasattr(self, 'yaml_steps') and self.yaml_steps else 0
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
        
        # Stop event capture (only in write mode)
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
        
        # Stop command server (only in write mode)
        if self.command_server:
            try:
                await self.command_server.stop()
            except Exception as e:
                logger.debug(f"Error stopping command server: {e}")
        
        # Stop console (only in write mode)
        if self.mode == 'write':
            try:
                logger.info("Stopping console interface...")
                self.console.stop()
            except Exception as e:
                logger.debug(f"Error stopping console: {e}")
        
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
                expected_name = f"{test_name}.webm" if self.video_config.codec == "webm" else f"{test_name}.mp4"
                expected_path = self.video_manager.video_dir / expected_name
                
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
                    # Rename video to test name
                    if found_video != expected_path:
                        if expected_path.exists():
                            expected_path.unlink()
                        found_video.rename(expected_path)
                        logger.info(f"Video renamed to: {expected_path.name}")
                        print(f"📹 Vídeo renomeado para: {expected_path.name}")
                    else:
                        logger.info(f"Video already has correct name: {expected_path.name}")
                        print(f"📹 Vídeo salvo: {expected_path.name}")
                    
                    # Clean up old videos with hash-based names (after renaming)
                    # Re-scan to get updated list
                    all_videos_after = []
                    for ext in video_extensions:
                        all_videos_after.extend(list(self.video_manager.video_dir.glob(f"*{ext}")))
                    
                    for video_file in all_videos_after:
                        if video_file == expected_path:
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
            logger.error("No page available for executing steps!")
            raise RuntimeError("Page not available")
        
        # Log page and context info for debugging
        page_url = self.page.url if hasattr(self.page, 'url') else 'unknown'
        context_info = 'no context'
        if hasattr(self, 'browser_manager') and self.browser_manager.context:
            context_info = f'context={id(self.browser_manager.context)}'
            if hasattr(self.browser_manager.context, '_options'):
                video_enabled = 'record_video_dir' in str(self.browser_manager.context._options)
                context_info += f', video={video_enabled}'
        
        # Track video recording start time
        import time
        video_start_time = time.time()
        logger.info(f"🎬 VIDEO DEBUG: Starting YAML steps execution at {video_start_time:.2f}")
        logger.info(f"Executing {len(self.yaml_steps)} YAML steps on page={id(self.page)}, {context_info}, url={page_url}")
        
        for i, step in enumerate(self.yaml_steps, 1):
            action = step.get('action')
            description = step.get('description', '')
            step_start_time = time.time()
            elapsed = step_start_time - video_start_time
            logger.info(f"🎬 VIDEO DEBUG: Step {i}/{len(self.yaml_steps)} starting at {elapsed:.2f}s - {action} - {description}")
            logger.info(f"[{i}/{len(self.yaml_steps)}] Executing: {action} - {description}")
            
            try:
                if action == 'go_to':
                    url = step.get('url')
                    if url:
                        await self.page.goto(url, wait_until='domcontentloaded')
                        try:
                            await self.page.wait_for_load_state('networkidle', timeout=10000)
                        except:
                            await self.page.wait_for_load_state('load', timeout=5000)
                
                elif action == 'click':
                    text = step.get('text')
                    selector = step.get('selector')
                    
                    # Wait for page to be ready before clicking (especially after navigation)
                    try:
                        await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
                        await self.page.wait_for_load_state('networkidle', timeout=10000)
                    except:
                        pass  # Continue even if timeout
                    
                    if text:
                        await self.command_handlers.handle_pw_click(f'"{text}"')
                    elif selector:
                        await self.command_handlers.handle_pw_click(f'selector "{selector}"')
                    else:
                        logger.warning(f"Click step has no text or selector: {step}")
                
                elif action == 'type':
                    text = step.get('text', '')
                    selector = step.get('selector')
                    field_text = step.get('field_text')
                    if selector:
                        await self.command_handlers.handle_pw_type(f'"{text}" selector "{selector}"')
                    elif field_text:
                        await self.command_handlers.handle_pw_type(f'"{text}" into "{field_text}"')
                    else:
                        await self.command_handlers.handle_pw_type(f'"{text}"')
                
                elif action == 'submit':
                    button_text = step.get('button_text') or step.get('text')
                    if button_text:
                        await self.command_handlers.handle_pw_submit(f'"{button_text}"')
                    else:
                        await self.command_handlers.handle_pw_submit('')
                
            except Exception as e:
                step_error_time = time.time()
                elapsed = step_error_time - video_start_time
                logger.error(f"🎬 VIDEO DEBUG: Step {i} ERROR at {elapsed:.2f}s")
                logger.error(f"Error executing step {i} ({action}): {e}", exc_info=True)
                raise
            
            step_end_time = time.time()
            elapsed = step_end_time - video_start_time
            logger.info(f"🎬 VIDEO DEBUG: Step {i}/{len(self.yaml_steps)} completed at {elapsed:.2f}s")
        
        steps_end_time = time.time()
        total_elapsed = steps_end_time - video_start_time
        logger.info(f"🎬 VIDEO DEBUG: All steps completed at {total_elapsed:.2f}s")
        logger.info("✅ All YAML steps executed successfully")

        # Wait a bit after all steps to ensure video captures everything
        # This is especially important for the last action
        # Playwright writes video frames asynchronously, so we need to wait for all frames
        await asyncio.sleep(2.0)
        after_wait_time = time.time()
        elapsed_after_wait = after_wait_time - video_start_time
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
    

