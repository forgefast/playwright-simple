#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for playwright-simple.

Handles test execution, video recording, and reporting.
"""

import asyncio
import logging
import re
import subprocess
import traceback
import json
from pathlib import Path
from typing import Callable, List, Tuple, Optional, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .config import TestConfig
from .base import SimpleTestBase
from .video import VideoManager
from .tts import TTSManager
from .exceptions import ElementNotFoundError, NavigationError, VideoProcessingError
from .constants import (
    CLEANUP_DELAY,
    VIDEO_FINALIZATION_DELAY,
    FFMPEG_TIMEOUT,
    FFMPEG_VERSION_CHECK_TIMEOUT,
    HOVER_EFFECT_ELEMENT_ID,
)

# Try to import OdooTestBase (optional dependency)
try:
    from ..odoo.base import OdooTestBase
    ODOO_AVAILABLE = True
except ImportError:
    OdooTestBase = None
    ODOO_AVAILABLE = False

# Try to import ForgeERPTestBase (optional dependency)
try:
    from ..forgeerp.base import ForgeERPTestBase
    FORGEERP_AVAILABLE = True
except ImportError:
    ForgeERPTestBase = None
    FORGEERP_AVAILABLE = False

logger = logging.getLogger(__name__)


def _log_action(action: str, test_name: str, details: Optional[Dict[str, Any]] = None, level: str = "INFO"):
    """
    Log structured action for debugging.
    
    Args:
        action: Action name (e.g., "test_started", "navigation", "click")
        test_name: Name of current test
        details: Additional details to log
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "test": test_name,
        "action": action,
    }
    if details:
        log_data.update(details)
    
    log_message = json.dumps(log_data, ensure_ascii=False)
    
    if level == "DEBUG":
        logger.debug(log_message)
    elif level == "WARNING":
        logger.warning(log_message)
    elif level == "ERROR":
        logger.error(log_message)
    else:
        logger.info(log_message)


class TestRunner:
    """
    Runner for executing Playwright tests with video recording and reporting.
    
    Example:
        ```python
        config = TestConfig(base_url="http://localhost:8000")
        runner = TestRunner(config=config)
        
        async def test_login(page, test):
            await test.login("admin", "senha123")
        
        await runner.run_all([("01_login", test_login)])
        ```
    """
    
    def __init__(
        self,
        config: Optional[TestConfig] = None,
        base_url: Optional[str] = None,
        videos_dir: Optional[str] = None,
        headless: Optional[bool] = None,
        viewport: Optional[Dict[str, int]] = None
    ):
        """
        Initialize test runner.
        
        Args:
            config: Test configuration (creates default if not provided)
            base_url: Base URL (overrides config if provided)
            videos_dir: Videos directory (overrides config if provided)
            headless: Headless mode (overrides config if provided)
            viewport: Viewport size (overrides config if provided)
        """
        # Create or update config
        if config is None:
            config = TestConfig()
        
        if base_url:
            config.base_url = base_url
        if videos_dir:
            config.video.dir = videos_dir
        if headless is not None:
            config.browser.headless = headless
        if viewport:
            config.browser.viewport = viewport
        
        self.config = config
        self.video_manager = VideoManager(config.video)
        
        # Test execution tracking
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    async def run_test(
        self,
        test_name: str,
        test_func: Callable,
        browser: Optional[Browser] = None,
        context: Optional[BrowserContext] = None
    ) -> Dict[str, Any]:
        """
        Execute a single test and record video.
        
        Args:
            test_name: Name of test (used for video filename)
            test_func: Test function (async def test_func(page, test))
            browser: Browser instance (creates new if not provided)
            context: Context instance (creates new if not provided)
            
        Returns:
            Dictionary with test results
        """
        print(f"\n🎬 Running test: {test_name}")
        _log_action("test_started", test_name, {
            "base_url": self.config.base_url,
            "headless": self.config.browser.headless,
            "viewport": self.config.browser.viewport
        })
        
        result = {
            "name": test_name,
            "status": "unknown",
            "error": None,
            "duration": 0,
            "video_path": None,
            "screenshots": [],
        }
        
        # Track test steps for subtitles
        test_steps = []
        step_start_times = {}
        start_time = datetime.now()
        video_start_time = None  # Time when video recording actually starts (context creation)
        create_context = context is None
        
        try:
            # Create context if needed
            if create_context:
                if browser is None:
                    raise ValueError("If context is not provided, browser must be provided")
                
                # Get video options - pass viewport to ensure video size matches viewport
                video_options = self.video_manager.get_context_options(
                    test_name, 
                    viewport=self.config.browser.viewport
                )
                
                # Store test name for later video renaming
                self._current_test_name = test_name
                
                # Capture context creation time - this is when video recording actually begins
                context_creation_time = datetime.now()
                
                context = await browser.new_context(
                    viewport=self.config.browser.viewport,
                    locale=self.config.browser.locale,
                    device_scale_factor=1,
                    java_script_enabled=True,
                    ignore_https_errors=True,
                    **video_options
                )
                context.set_default_timeout(self.config.browser.timeout)
                context.set_default_navigation_timeout(self.config.browser.navigation_timeout)
                
                # Register context for video management
                self.video_manager.register_context(context, test_name)
                _log_action("context_created", test_name, {
                    "video_enabled": self.config.video.enabled,
                    "viewport": self.config.browser.viewport
                })
            
            # Create page
            page = await context.new_page()
            _log_action("page_created", test_name)
            
            # Use context creation time as video start time (when recording actually began)
            if create_context and context_creation_time:
                video_start_time = context_creation_time
            
            # Create test instance - detect if Odoo test is needed
            # Check if test function has Odoo-specific attributes or annotations
            print(f"  🔧 Criando instância de teste...")
            test = self._create_test_instance(page, test_name, test_func)
            test_type = type(test).__name__
            print(f"  ✅ Instância criada: {test_type}")
            _log_action("test_instance_created", test_name, {"test_type": test_type})
            
            # Cursor will be injected by CursorController when actions are executed
            # CursorController is the single source of truth for cursor visualization
            # No need to inject CursorManager cursor here
            
            # Remove hover effect and hide click effect if disabled (they might have been created)
            from .constants import CLICK_EFFECT_ELEMENT_ID
            await page.evaluate(f"""
                (function() {{
                    const HOVER_EFFECT_ID = '{HOVER_EFFECT_ELEMENT_ID}';
                    const CLICK_EFFECT_ID = '{CLICK_EFFECT_ELEMENT_ID}';
                    
                    // Remove hover effect
                    const hoverEffect = document.getElementById(HOVER_EFFECT_ID);
                    if (hoverEffect) {{
                        hoverEffect.remove();
                    }}
                    
                    // Hide click effect (it should only appear during clicks)
                    const clickEffect = document.getElementById(CLICK_EFFECT_ID);
                    if (clickEffect) {{
                        clickEffect.style.opacity = '0';
                        clickEffect.style.display = 'none';
                        clickEffect.style.width = '0px';
                        clickEffect.style.height = '0px';
                    }}
                }})();
            """)
            
            await asyncio.sleep(0.2)  # Reduced delay
            print(f"  ✅ Cursor injetado")
            
            # Navigate to base URL first
            if self.config.base_url:
                print(f"  🌐 Navegando para: {self.config.base_url}")
                _log_action("navigation_started", test_name, {"url": self.config.base_url})
                try:
                    await page.goto(self.config.base_url, wait_until="load", timeout=self.config.browser.navigation_timeout)
                    final_url = page.url
                    page_title = await page.title()
                    _log_action("navigation_completed", test_name, {
                        "final_url": final_url,
                        "title": page_title
                    })
                except Exception as nav_error:
                    _log_action("navigation_failed", test_name, {
                        "url": self.config.base_url,
                        "error": str(nav_error)
                    }, level="ERROR")
                    raise
                await asyncio.sleep(0.3)  # Reduced delay
                # After navigation, just ensure cursor exists (don't force re-inject to avoid duplicates)
                # The init script should handle cursor creation on page load
                # CursorController will handle cursor restoration after navigation
                # No need to use CursorManager
                
                # Remove hover effect and hide click effect again after navigation (in case they were recreated)
                from .constants import CLICK_EFFECT_ELEMENT_ID
                await page.evaluate(f"""
                    (function() {{
                        const HOVER_EFFECT_ID = '{HOVER_EFFECT_ELEMENT_ID}';
                        const CLICK_EFFECT_ID = '{CLICK_EFFECT_ELEMENT_ID}';
                        
                        // Remove hover effect
                        const hoverEffect = document.getElementById(HOVER_EFFECT_ID);
                        if (hoverEffect) {{
                            hoverEffect.remove();
                        }}
                        
                        // Hide click effect (it should only appear during clicks)
                        const clickEffect = document.getElementById(CLICK_EFFECT_ID);
                        if (clickEffect) {{
                            clickEffect.style.opacity = '0';
                            clickEffect.style.display = 'none';
                            clickEffect.style.width = '0px';
                            clickEffect.style.height = '0px';
                        }}
                    }})();
                """)
                
                await asyncio.sleep(0.1)
            
            # Load session if test function has load_session attribute
            if hasattr(test_func, 'load_session') and test_func.load_session:
                print(f"  💾 Carregando sessão: {test_func.load_session}")
                session_loaded = await test.load_session(test_func.load_session)
                if session_loaded:
                    print(f"  ✅ Sessão carregada com sucesso")
                    # Navigate to base URL after loading session
                    if self.config.base_url:
                        await page.goto(self.config.base_url, wait_until="load", timeout=self.config.browser.navigation_timeout)
                        await asyncio.sleep(0.2)  # Reduced delay
                else:
                    print(f"  ⚠️  Sessão não encontrada")
            
            # Set up console message listener to capture JavaScript logs
            console_messages = []
            def handle_console(msg):
                console_messages.append(msg.text)
                if "DEBUG" in msg.text or "cursor" in msg.text.lower() or "error" in msg.text.lower():
                    print(f"  📜 Console: {msg.text}")
            
            page.on("console", handle_console)
            
            # Run test
            print(f"  ▶️  Executando teste...")
            _log_action("test_execution_started", test_name)
            
            # Use video_start_time if available, otherwise use start_time
            # video_start_time is when recording actually began (context creation)
            reference_time = video_start_time if video_start_time else start_time
            
            # Pass test_steps list and video_start_time to test function if it accepts them
            # This allows YAML parsers to populate it with step information
            if hasattr(test_func, '__code__'):
                import inspect
                sig = inspect.signature(test_func)
                if 'test_steps' in sig.parameters:
                    # Check if function also accepts video_start_time
                    if 'video_start_time' in sig.parameters:
                        await test_func(page, test, test_steps=test_steps, video_start_time=reference_time)
                    else:
                        await test_func(page, test, test_steps=test_steps)
                else:
                    await test_func(page, test)
            else:
                await test_func(page, test)
            
            print(f"  ✅ Teste executado com sucesso")
            _log_action("test_execution_completed", test_name, {
                "steps_count": len(test_steps)
            })
            
            # Print summary of console messages
            if console_messages:
                debug_messages = [m for m in console_messages if "DEBUG" in m or "cursor" in m.lower()]
                if debug_messages:
                    print(f"  📜 Console messages relacionados ao cursor ({len(debug_messages)}):")
                    for msg in debug_messages[:10]:  # Show first 10
                        print(f"     {msg}")
            
            # Save session if test function has save_session attribute
            if hasattr(test_func, 'save_session') and test_func.save_session:
                session_name = test_func.save_session if isinstance(test_func.save_session, str) else test_name
                await test.save_session(session_name)
            
            # Collect screenshot metadata
            screenshot_metadata = test.screenshot_manager.get_metadata()
            if screenshot_metadata:
                result["screenshots_metadata"] = list(screenshot_metadata.values())
                _log_action("screenshots_captured", test_name, {
                    "count": len(screenshot_metadata)
                })
            
            result["status"] = "passed"
            print(f"  ✅ {test_name} passed")
            _log_action("test_passed", test_name)
            
        except (ElementNotFoundError, NavigationError) as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["error_traceback"] = traceback.format_exc()
            logger.error(f"Test '{test_name}' failed with {type(e).__name__}: {e}")
            print(f"  ❌ {test_name} failed: {e}")
            _log_action("test_failed", test_name, {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }, level="ERROR")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["error_traceback"] = traceback.format_exc()
            logger.error(f"Test '{test_name}' failed with unexpected error: {e}", exc_info=True)
            print(f"  ❌ {test_name} failed: {e}")
            print(f"  📋 Traceback completo:")
            print(traceback.format_exc())
            _log_action("test_failed", test_name, {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }, level="ERROR")
            
            # Capture screenshot on failure
            if self.config.screenshots.on_failure and 'test' in locals():
                try:
                    screenshot_path = await test.screenshot_manager.capture_on_failure(e)
                    result["screenshots"].append(str(screenshot_path))
                    print(f"  📸 Screenshot de erro salvo: {screenshot_path}")
                except Exception as screenshot_error:
                    logger.warning(f"Error capturing failure screenshot: {screenshot_error}")
                    print(f"  ⚠️  Erro ao capturar screenshot: {screenshot_error}")
            
            # Also try to capture page screenshot directly
            if 'page' in locals():
                try:
                    screenshots_dir = Path(self.config.screenshots.dir)
                    error_screenshot = screenshots_dir / test_name / "error_page.png"
                    error_screenshot.parent.mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path=str(error_screenshot), full_page=True)
                    print(f"  📸 Screenshot da página de erro salvo: {error_screenshot}")
                except Exception as e:
                    logger.warning(f"Error capturing page screenshot: {e}")
                    print(f"  ⚠️  Erro ao capturar screenshot da página: {e}")
                
                # Also save HTML content of the page
                try:
                    screenshots_dir = Path(self.config.screenshots.dir)
                    error_html = screenshots_dir / test_name / "error_page.html"
                    error_html.parent.mkdir(parents=True, exist_ok=True)
                    html_content = await page.content()
                    error_html.write_text(html_content, encoding='utf-8')
                    print(f"  📄 HTML da página de erro salvo: {error_html}")
                except Exception as e:
                    logger.warning(f"Error capturing page HTML: {e}")
                    print(f"  ⚠️  Erro ao capturar HTML da página: {e}")
        
        finally:
            # Cleanup (reduced delays)
            if 'page' in locals():
                await asyncio.sleep(CLEANUP_DELAY)
                await page.close()
            
            if create_context and context:
                await asyncio.sleep(CLEANUP_DELAY)
                await context.close()
            
            # Get video path and rename to test name
            # Playwright creates videos with hash in record_video_dir, we rename after
            if self.config.video.enabled:
                # Wait a bit for video to be finalized after context close
                await asyncio.sleep(VIDEO_FINALIZATION_DELAY)
                
                # Find the most recently created video file in video_dir (not in subdirs)
                video_extensions = ['.webm', '.mp4']
                all_videos = []
                for ext in video_extensions:
                    # Only search directly in video_dir, not subdirectories
                    all_videos.extend(list(self.video_manager.video_dir.glob(f"*{ext}")))
                
                if all_videos:
                    # Get the most recent video (should be from this test)
                    found_video = max(all_videos, key=lambda p: p.stat().st_mtime)
                    
                    # Playwright always records in webm, so we need to convert if mp4 is requested
                    expected_name = f"{test_name}.webm" if self.config.video.codec == "webm" else f"{test_name}.mp4"
                    expected_path = self.video_manager.video_dir / expected_name
                    
                    # If codec is mp4 but video is webm, we need to process it to convert
                    # This ensures subtitles are embedded during conversion
                    needs_conversion = self.config.video.codec == "mp4" and found_video.suffix == ".webm"
                    
                    # Don't rename yet if we need to process - processing will handle the rename
                    if not needs_conversion:
                        if found_video != expected_path:
                            if expected_path.exists():
                                expected_path.unlink()
                            found_video.rename(expected_path)
                            print(f"  📹 Vídeo renomeado para: {expected_path.name}")
                        else:
                            print(f"  📹 Vídeo salvo: {expected_path.name}")
                        # Update expected_path to point to the renamed file
                        expected_path = found_video if found_video == expected_path else expected_path
                    else:
                        # Keep webm name for processing, will be converted to mp4
                        print(f"  📹 Vídeo gravado: {found_video.name} (será convertido para MP4 com legendas)")
                    
                    # Delete old videos with numeric prefixes or technical names
                    # Pattern: videos starting with numbers (01_, 02_, etc.) or hash-based names
                    for video_file in all_videos:
                        if video_file == expected_path:
                            continue  # Don't delete the current video
                        
                        video_name = video_file.stem  # Name without extension
                        
                        # Check if it's an old numbered video (01_, 02_, etc.)
                        is_numbered = re.match(r'^\d{2}_', video_name)
                        
                        # Check if it's a hash-based technical name (Playwright default)
                        is_hash_based = re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-', video_name)
                        
                        # Check if it's a very short technical name (likely auto-generated)
                        is_technical = len(video_name) < 10 and not any(c.isalpha() for c in video_name[:5])
                        
                        # Delete if it matches any of these patterns
                        if is_numbered or is_hash_based or is_technical:
                            try:
                                video_file.unlink()
                                print(f"  🗑️  Vídeo antigo deletado: {video_file.name}")
                            except Exception as e:
                                logger.warning(f"Erro ao deletar vídeo antigo {video_file.name}: {e}")
                    
                    # Process video: speed, subtitles, and audio in ONE pass (much faster!)
                    # Generate narration if enabled
                    narration_audio = None
                    if self.config.video.narration and test_steps:
                        _log_action("narration_generation_started", test_name)
                        narration_audio = await self._generate_narration(
                            test_steps,
                            expected_path.parent,
                            test_name
                        )
                        if narration_audio:
                            _log_action("narration_generated", test_name, {
                                "audio_path": str(narration_audio)
                            })
                    
                    needs_processing = (
                        self.config.video.speed != 1.0 or
                        (self.config.video.subtitles and test_steps) or
                        self.config.video.audio_file or
                        narration_audio or
                        needs_conversion  # Always process if we need to convert webm to mp4
                    )
                    
                    if needs_processing:
                        _log_action("video_processing_started", test_name, {
                            "speed": self.config.video.speed,
                            "subtitles": self.config.video.subtitles,
                            "has_audio": bool(self.config.video.audio_file or narration_audio),
                            "needs_conversion": needs_conversion
                        })
                        # Use the original found_video (webm) for processing if conversion is needed
                        video_to_process = found_video if needs_conversion else expected_path
                        # Use video_start_time for subtitle timing if available
                        subtitle_reference_time = video_start_time if video_start_time else start_time
                        final_path = await self._process_video_all_in_one(
                            video_to_process,
                            test_steps,
                            subtitle_reference_time,
                            narration_audio=narration_audio
                        )
                        if final_path and final_path.exists():
                            # If we converted, rename to expected mp4 name
                            if needs_conversion and final_path.suffix == ".mp4":
                                if expected_path.exists():
                                    expected_path.unlink()
                                final_path.rename(expected_path)
                                final_path = expected_path
                            
                            # Verify final video exists and is valid
                            if not final_path.exists():
                                raise RuntimeError(f"Vídeo processado não encontrado: {final_path}")
                            
                            # If MP4 was requested, verify it's actually MP4
                            if self.config.video.codec == "mp4" and final_path.suffix != ".mp4":
                                raise RuntimeError(f"Vídeo deveria ser MP4 mas é {final_path.suffix}: {final_path}")
                            
                            result["video_path"] = str(final_path)
                            _log_action("video_processed", test_name, {
                                "video_path": str(final_path)
                            })
                        else:
                            # Processing failed - this is a critical error if MP4 was requested
                            if self.config.video.codec == "mp4":
                                error_msg = f"Falha ao processar vídeo para MP4 com legendas. Vídeo esperado: {expected_path}"
                                logger.error(error_msg)
                                raise RuntimeError(error_msg)
                            else:
                                result["video_path"] = str(expected_path)
                                _log_action("video_processing_failed", test_name, level="WARNING")
                    else:
                        result["video_path"] = str(expected_path)
                        _log_action("video_saved", test_name, {
                            "video_path": str(expected_path)
                        })
                else:
                    print(f"  ⚠️  Vídeo não encontrado para {test_name}")
                    _log_action("video_not_found", test_name, level="WARNING")
        
        # Calculate duration
        end_time = datetime.now()
        result["duration"] = (end_time - start_time).total_seconds()
        
        # Calculate expected minimum duration based on test steps
        # This helps detect if test failed early or was too short
        expected_min_duration = None
        if 'test_steps' in locals() and test_steps:
            # Sum up all step durations (minimum 1s per step)
            # Handle both TestStep objects and dicts
            from ..core.step import TestStep
            durations = []
            for step in test_steps:
                if isinstance(step, TestStep):
                    durations.append(step.duration or 1.0)
                elif isinstance(step, dict):
                    durations.append(step.get('duration', 1.0))
                else:
                    durations.append(1.0)
            expected_min_duration = sum(durations)
            # Add buffer for navigation, waits, etc. (at least 2s per step)
            expected_min_duration = max(expected_min_duration, len(test_steps) * 2.0)
        elif hasattr(test_func, '__code__'):
            # Try to estimate from function complexity (rough estimate)
            # For YAML tests, we can get step count from metadata if available
            try:
                import inspect
                # If test function has steps metadata, use it
                if hasattr(test_func, 'yaml_steps_count'):
                    step_count = test_func.yaml_steps_count
                    expected_min_duration = step_count * 2.0  # At least 2s per step
            except Exception:
                pass
        
        # Validate video if it was generated
        if result.get("video_path") and self.config.video.enabled:
            video_path = Path(result["video_path"])
            if video_path.exists():
                video_validation = self.video_manager.validate_video(
                    video_path,
                    test_duration=result["duration"]
                )
                result["video_validation"] = video_validation
                
                # Additional validation: check if video/test duration is too short
                if expected_min_duration and result["duration"] < expected_min_duration * 0.5:
                    # Test duration is less than 50% of expected - likely failed early
                    video_validation["warnings"].append(
                        f"Test duration ({result['duration']:.2f}s) is much shorter than expected minimum "
                        f"({expected_min_duration:.2f}s). Test may have failed early or steps were skipped."
                    )
                    _log_action("test_duration_too_short", test_name, {
                        "actual_duration": result["duration"],
                        "expected_min_duration": expected_min_duration,
                        "ratio": result["duration"] / expected_min_duration if expected_min_duration > 0 else 0
                    }, level="WARNING")
                
                if not video_validation["valid"]:
                    _log_action("video_validation_failed", test_name, {
                        "errors": video_validation["errors"],
                        "warnings": video_validation["warnings"]
                    }, level="WARNING")
                    # Don't fail test, but log warning
                    if result["status"] == "passed":
                        result["status"] = "warning"
                else:
                    _log_action("video_validated", test_name, {
                        "playable": video_validation["playable"],
                        "size_ok": video_validation["size_ok"],
                        "duration_ok": video_validation["duration_ok"],
                        "expected_min_duration": expected_min_duration
                    })
        
        # Validate screenshots if any were captured
        if 'test' in locals() and hasattr(test, 'screenshot_manager'):
            screenshot_validation = test.screenshot_manager.validate_screenshots()
            result["screenshot_validation"] = screenshot_validation
            
            if not screenshot_validation["valid"]:
                _log_action("screenshot_validation_failed", test_name, {
                    "errors": screenshot_validation["errors"],
                    "warnings": screenshot_validation["warnings"]
                }, level="WARNING")
            else:
                _log_action("screenshots_validated", test_name, {
                    "total": screenshot_validation["total"],
                    "valid_count": screenshot_validation["valid_count"]
                })
        
        _log_action("test_finished", test_name, {
            "status": result["status"],
            "duration": result["duration"],
            "video_path": result.get("video_path"),
            "screenshots_count": len(result.get("screenshots_metadata", []))
        })
        
        return result
    
    async def run_all(
        self,
        tests: List[Tuple[str, Callable]],
        parallel: bool = False,
        workers: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Execute all tests and generate videos.
        
        Args:
            tests: List of tuples (test_name, test_function)
            parallel: Whether to run tests in parallel
            workers: Number of parallel workers (if parallel=True)
            
        Returns:
            List of test results
        """
        print("🚀 Starting test execution...")
        print(f"📁 Videos will be saved to: {self.video_manager.video_dir}")
        print(f"📸 Screenshots will be saved to: {self.config.screenshots.dir}")
        
        # Clear old videos (including subdirectories)
        if self.video_manager.video_dir.exists():
            video_files = list(self.video_manager.video_dir.glob("**/*.webm")) + \
                         list(self.video_manager.video_dir.glob("**/*.mp4"))
            for video_file in video_files:
                try:
                    video_file.unlink()
                except Exception as e:
                    logger.debug(f"Error removing old video file {video_file}: {e}")
            # Remove empty subdirectories
            for subdir in self.video_manager.video_dir.iterdir():
                if subdir.is_dir():
                    try:
                        subdir.rmdir()
                    except Exception as e:
                        logger.debug(f"Error removing empty subdirectory {subdir}: {e}")
            if video_files:
                print(f"  ✅ Removed {len(video_files)} old video(s)")
        
        self.start_time = datetime.now()
        self.test_results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config.browser.headless,
                slow_mo=self.config.browser.slow_mo
            )
            
            try:
                if parallel and workers > 1:
                    # Run tests in parallel
                    await self._run_parallel(browser, tests, workers)
                else:
                    # Run tests sequentially
                    for test_name, test_func in tests:
                        result = await self.run_test(test_name, test_func, browser=browser)
                        self.test_results.append(result)
                
                self.end_time = datetime.now()
                
                # Print summary
                self._print_summary()
                
            except Exception as e:
                logger.error(f"Error during test execution: {e}", exc_info=True)
                print(f"❌ Error during test execution: {e}")
                traceback.print_exc()
            finally:
                await browser.close()
                await asyncio.sleep(1)
        
        return self.test_results
    
    async def _run_parallel(
        self, 
        browser: Browser, 
        tests: List[Tuple[str, Callable]], 
        workers: int
    ) -> None:
        """
        Run multiple tests in parallel with limited concurrency.
        
        Args:
            browser: Browser instance to use for all tests
            tests: List of (test_name, test_function) tuples
            workers: Maximum number of concurrent tests
        """
        semaphore = asyncio.Semaphore(workers)
        
        async def run_with_semaphore(test_name: str, test_func: Callable):
            async with semaphore:
                return await self.run_test(test_name, test_func, browser=browser)
        
        tasks = [run_with_semaphore(test_name, test_func) for test_name, test_func in tests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"  ❌ Error in parallel execution: {result}")
            else:
                self.test_results.append(result)
    
    def _create_test_instance(self, page: Page, test_name: str, test_func: Callable) -> SimpleTestBase:
        """
        Create appropriate test instance based on test function type.
        
        Args:
            page: Playwright page instance
            test_name: Name of the test
            test_func: Test function
            
        Returns:
            Test base instance (SimpleTestBase, OdooTestBase, or ForgeERPTestBase)
        """
        # Check if test function expects specific test base
        import inspect
        
        # Check function signature
        sig = inspect.signature(test_func)
        params = list(sig.parameters.values())
        
        # If second parameter is annotated, check which type it expects
        if len(params) >= 2:
            param = params[1]  # Second parameter is usually 'test'
            if param.annotation != inspect.Parameter.empty:
                annotation_str = str(param.annotation)
                # Check for ForgeERPTestBase first (more specific)
                if 'ForgeERPTestBase' in annotation_str and FORGEERP_AVAILABLE:
                    return ForgeERPTestBase(page, self.config, test_name)
                # Check for OdooTestBase
                if 'OdooTestBase' in annotation_str and ODOO_AVAILABLE:
                    return OdooTestBase(page, self.config, test_name)
        
        # Check if test function module is from forgeerp
        if hasattr(test_func, '__module__'):
            if 'forgeerp' in test_func.__module__ and FORGEERP_AVAILABLE:
                return ForgeERPTestBase(page, self.config, test_name)
            # Check if test function module is from odoo
            if 'odoo' in test_func.__module__ and ODOO_AVAILABLE:
                return OdooTestBase(page, self.config, test_name)
        
        # Default to SimpleTestBase
        return SimpleTestBase(page, self.config, test_name)
    
    def _print_summary(self) -> None:
        """
        Print test execution summary to console.
        
        Shows total tests, passed, failed, duration, and video/screenshot counts.
        """
        if not self.test_results:
            return
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "passed")
        failed = total - passed
        
        total_duration = sum(r["duration"] for r in self.test_results)
        if self.start_time and self.end_time:
            wall_time = (self.end_time - self.start_time).total_seconds()
        else:
            wall_time = total_duration
        
        print("\n" + "=" * 60)
        print("📊 Test Execution Summary")
        print("=" * 60)
        print(f"Total tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total duration: {total_duration:.2f}s")
        print(f"⏱️  Wall time: {wall_time:.2f}s")
        print("=" * 60)
        
        if failed > 0:
            print("\n❌ Failed tests:")
            for result in self.test_results:
                if result["status"] == "failed":
                    print(f"  - {result['name']}: {result['error']}")
        
        print(f"\n📹 Videos saved to: {self.video_manager.video_dir}")
        print(f"📸 Screenshots saved to: {self.config.screenshots.dir}")
    
    def get_results(self) -> List[Dict[str, Any]]:
        """
        Get all test execution results.
        
        Returns:
            List of result dictionaries, each containing:
            - name: Test name
            - status: "passed" or "failed"
            - error: Error message if failed
            - duration: Test duration in seconds
            - video_path: Path to video file if generated
            - screenshots: List of screenshot paths
        """
        return self.test_results.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get execution summary statistics.
        
        Returns:
            Dictionary with summary statistics:
            - total: Total number of tests
            - passed: Number of passed tests
            - failed: Number of failed tests
            - duration: Total execution duration
            - start_time: Execution start time
            - end_time: Execution end time
        """
        if not self.test_results:
            return {}
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "passed")
        failed = total - passed
        total_duration = sum(r["duration"] for r in self.test_results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "total_duration": total_duration,
            "wall_time": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else total_duration,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }
    
    async def _process_video_speed(self, video_path: Path, speed: float) -> Optional[Path]:
        """
        Process video to change playback speed using ffmpeg.
        
        Args:
            video_path: Path to original video
            speed: Playback speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = 2x slower)
            
        Returns:
            Path to processed video, or None if processing failed
        """
        if speed == 1.0:
            return video_path
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print(f"  ⚠️  ffmpeg não encontrado. Vídeo não será processado.")
            return video_path
        
        # Create temporary output path
        output_path = video_path.parent / f"{video_path.stem}_processed{video_path.suffix}"
        
        try:
            # Calculate PTS (presentation timestamp) scale
            # For speed > 1.0: video plays faster (pts scale < 1.0)
            # For speed < 1.0: video plays slower (pts scale > 1.0)
            pts_scale = 1.0 / speed
            
            # Use ffmpeg to change video speed
            # -filter:v "setpts=PTS*{pts_scale}" changes video speed
            # -filter:a "atempo={speed}" changes audio speed (if audio exists)
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-filter:v', f'setpts=PTS*{pts_scale}',
                '-c:v', 'libvpx-vp9' if video_path.suffix == '.webm' else 'libx264',
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            # Handle audio speed (atempo range is 0.5 to 2.0, so we may need multiple filters)
            if speed != 1.0:
                if speed > 2.0:
                    # Speed > 2.0: need multiple atempo filters (each max 2.0)
                    num_filters = int(speed / 2.0) + (1 if speed % 2.0 > 0 else 0)
                    atempo_chain = []
                    remaining_speed = speed
                    for _ in range(num_filters):
                        if remaining_speed >= 2.0:
                            atempo_chain.append('atempo=2.0')
                            remaining_speed /= 2.0
                        else:
                            atempo_chain.append(f'atempo={remaining_speed}')
                            break
                    audio_filter = ','.join(atempo_chain)
                elif speed < 0.5:
                    # Speed < 0.5: need multiple atempo filters (each min 0.5)
                    num_filters = int(0.5 / speed) + (1 if 0.5 % speed > 0 else 0)
                    atempo_chain = []
                    remaining_speed = speed
                    for _ in range(num_filters):
                        if remaining_speed <= 0.5:
                            atempo_chain.append('atempo=0.5')
                            remaining_speed *= 2.0
                        else:
                            atempo_chain.append(f'atempo={remaining_speed}')
                            break
                    audio_filter = ','.join(atempo_chain)
                else:
                    # Single atempo filter (0.5 <= speed <= 2.0)
                    audio_filter = f'atempo={speed}'
                
                cmd.insert(5, '-filter:a')
                cmd.insert(6, audio_filter)
                cmd.insert(7, '-c:a')
                cmd.insert(8, 'libopus' if video_path.suffix == '.webm' else 'aac')
            else:
                # No audio processing needed
                cmd.insert(5, '-an')  # Remove audio
            
            # Run ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=FFMPEG_TIMEOUT
            )
            
            if result.returncode == 0 and output_path.exists():
                # Replace original with processed video
                video_path.unlink()
                output_path.rename(video_path)
                return video_path
            else:
                print(f"  ⚠️  Erro ao processar vídeo: {result.stderr[:200]}")
                if output_path.exists():
                    output_path.unlink()
                return video_path
                
        except subprocess.TimeoutExpired as e:
            logger.error(f"Timeout processing video: {e}")
            print(f"  ⚠️  Timeout ao processar vídeo")
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Video processing timeout: {e}") from e
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Failed to process video: {e}") from e
    
    async def _process_video_all_in_one(
        self,
        video_path: Path,
        test_steps: List[Any],  # Can be TestStep objects or dicts
        start_time: datetime,
        narration_audio: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Process video with speed, subtitles, and audio in ONE ffmpeg pass (much faster!).
        
        Args:
            video_path: Path to original video
            test_steps: List of test steps for subtitles
            start_time: Test start time
            
        Returns:
            Path to processed video, or None if processing failed
        """
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print(f"  ⚠️  ffmpeg não encontrado. Vídeo não será processado.")
            return video_path
        
        # Determine output extension based on config
        output_ext = ".mp4" if self.config.video.codec == "mp4" else video_path.suffix
        output_path = video_path.parent / f"{video_path.stem}_processed{output_ext}"
        
        try:
            # Build complex filter combining speed, subtitles, and audio
            video_filters = []
            audio_filters = []
            input_files = ['-i', str(video_path)]
            
            # 1. Speed adjustment
            if self.config.video.speed != 1.0:
                pts_scale = 1.0 / self.config.video.speed
                video_filters.append(f'setpts=PTS*{pts_scale}')
                
                # Audio speed adjustment
                if self.config.video.speed > 2.0:
                    num_filters = int(self.config.video.speed / 2.0) + (1 if self.config.video.speed % 2.0 > 0 else 0)
                    atempo_chain = []
                    remaining_speed = self.config.video.speed
                    for _ in range(num_filters):
                        if remaining_speed >= 2.0:
                            atempo_chain.append('atempo=2.0')
                            remaining_speed /= 2.0
                        else:
                            atempo_chain.append(f'atempo={remaining_speed}')
                            break
                    audio_filters.append(','.join(atempo_chain))
                elif self.config.video.speed < 0.5:
                    num_filters = int(0.5 / self.config.video.speed) + (1 if 0.5 % self.config.video.speed > 0 else 0)
                    atempo_chain = []
                    remaining_speed = self.config.video.speed
                    for _ in range(num_filters):
                        if remaining_speed <= 0.5:
                            atempo_chain.append('atempo=0.5')
                            remaining_speed *= 2.0
                        else:
                            atempo_chain.append(f'atempo={remaining_speed}')
                            break
                    audio_filters.append(','.join(atempo_chain))
                else:
                    audio_filters.append(f'atempo={self.config.video.speed}')
            
            # 2. Subtitles (if enabled and steps available)
            if self.config.video.subtitles and test_steps:
                # test_steps can be TestStep objects or dicts - _generate_srt_file handles both
                srt_path = await self._generate_srt_file(video_path, test_steps, start_time)
                if srt_path and srt_path.exists():
                    # Use absolute path for subtitles filter to avoid path issues
                    srt_absolute = srt_path.resolve()
                    # Escape single quotes in path if any
                    srt_path_escaped = str(srt_absolute).replace("'", "'\\''")
                    # Use subtitles filter with absolute path
                    video_filters.append(f"subtitles='{srt_path_escaped}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2'")
            
            # 3. Build ffmpeg command
            cmd = ['ffmpeg'] + input_files
            
            # Add audio inputs (narration takes priority, then background audio)
            audio_inputs = []
            if narration_audio and narration_audio.exists():
                audio_inputs.append(str(narration_audio))
            if self.config.video.audio_file:
                audio_path = Path(self.config.video.audio_file)
                if audio_path.exists():
                    audio_inputs.append(str(audio_path))
            
            for i, audio_input in enumerate(audio_inputs):
                # Loop background audio if mixing with narration
                if len(audio_inputs) > 1 and i == len(audio_inputs) - 1:
                    cmd.extend(['-stream_loop', '-1'])
                cmd.extend(['-i', audio_input])
            
            # Build filter_complex for video and audio
            filter_complex_parts = []
            video_output_label = '[v]'
            audio_output_label = '[a]'
            
            # Video filters
            if video_filters:
                video_filter_chain = ','.join(video_filters)
                filter_complex_parts.append(f'[0:v]{video_filter_chain}{video_output_label}')
            else:
                video_output_label = '[0:v]'  # Use input directly
            
            # Audio handling
            has_audio_input = len(audio_inputs) > 0
            
            if has_audio_input:
                # Mix video audio (if exists) with narration/background audio
                num_audio_inputs = len(audio_inputs)
                if audio_filters:
                    # Apply speed to video audio, then mix with narration/background
                    if num_audio_inputs == 1:
                        filter_complex_parts.append(f'[0:a]{",".join(audio_filters)}[a0];[a0][1:a]amix=inputs=2{audio_output_label}')
                    else:
                        # Multiple audio inputs (narration + background)
                        filter_complex_parts.append(f'[0:a]{",".join(audio_filters)}[a0];[a0][1:a][2:a]amix=inputs=3{audio_output_label}')
                else:
                    # Just mix audio (no speed adjustment)
                    if num_audio_inputs == 1:
                        filter_complex_parts.append(f'[0:a][1:a]amix=inputs=2{audio_output_label}')
                    else:
                        filter_complex_parts.append(f'[0:a][1:a][2:a]amix=inputs=3{audio_output_label}')
            elif audio_filters:
                # Only speed adjustment
                filter_complex_parts.append(f'[0:a]{",".join(audio_filters)}{audio_output_label}')
            else:
                audio_output_label = '[0:a]'  # Use input directly
            
            # Apply filter_complex if needed
            if filter_complex_parts:
                cmd.extend(['-filter_complex', ';'.join(filter_complex_parts)])
                # Map video stream
                if video_output_label == '[v]':
                    cmd.extend(['-map', '[v]'])
                else:
                    cmd.extend(['-map', '0:v'])
                # Map audio stream (only if audio exists)
                if audio_output_label != '[0:a]':
                    cmd.extend(['-map', audio_output_label])
                else:
                    # Check if input has audio stream before mapping
                    # Use '?' to make it optional (won't fail if no audio)
                    cmd.extend(['-map', '0:a?'])
                
                # Video codec (re-encode if we have video filters or need to convert format)
                # If output should be mp4 but input is webm, always re-encode
                needs_reencode = bool(video_filters) or (self.config.video.codec == "mp4" and video_path.suffix == ".webm")
                if needs_reencode:
                    cmd.extend(['-c:v', 'libx264'])  # Always use libx264 for mp4
                else:
                    cmd.extend(['-c:v', 'copy'])  # No video filters, just copy
            else:
                # No filters, just copy streams
                cmd.extend(['-c:v', 'copy'])
                cmd.extend(['-c:a', 'copy'])
                cmd.extend(['-y', str(output_path)])
                # Run simple copy command
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0 and output_path.exists():
                    video_path.unlink()
                    output_path.rename(video_path)
                    return video_path
                return video_path
            
            # Audio codec
            if has_audio_input or audio_filters:
                cmd.extend(['-c:a', 'libopus' if video_path.suffix == '.webm' else 'aac'])
                if has_audio_input:
                    cmd.extend(['-shortest'])  # End when shortest stream ends
            else:
                cmd.extend(['-c:a', 'copy'])
            
            cmd.extend(['-y', str(output_path)])
            
            # Run ffmpeg (single pass - much faster!)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and output_path.exists():
                # If output is different format (e.g., mp4 from webm), delete original and use output
                if output_path.suffix != video_path.suffix:
                    video_path.unlink()  # Delete original webm
                    # Return the output file (mp4)
                    final_video = output_path
                else:
                    # Same format, rename output to original name
                    video_path.unlink()
                    output_path.rename(video_path)
                    final_video = video_path
                
                # Clean up SRT file if created (but keep it for debugging for now)
                # TODO: Remove this after verifying subtitle timing
                if self.config.video.subtitles and test_steps:
                    srt_path = final_video.parent / f"{final_video.stem}.srt"
                    if srt_path.exists():
                        # Log SRT content for debugging
                        logger.debug(f"SRT file generated: {srt_path}")
                        # Keep SRT for now to verify timing
                        # srt_path.unlink()
                
                print(f"  ⚡ Vídeo processado (velocidade, legendas, áudio) em uma única passada")
                # Verify output file exists and is valid
                if not final_video.exists():
                    error_msg = f"Vídeo processado não encontrado após processamento: {final_video}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                # Verify format if MP4 was requested
                if self.config.video.codec == "mp4" and final_video.suffix != ".mp4":
                    error_msg = f"Vídeo deveria ser MP4 mas é {final_video.suffix}: {final_video}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                return final_video
            else:
                # Get full error message
                error_output = result.stderr if result.stderr else result.stdout or 'Erro desconhecido'
                error_msg = f"Erro ao processar vídeo com ffmpeg: {error_output[:1000]}"
                logger.error(f"FFmpeg error (full): {error_output}")
                print(f"  ❌ {error_msg}")
                # Also print last few lines for debugging
                if result.stderr:
                    stderr_lines = result.stderr.strip().split('\n')
                    print(f"  📋 Últimas linhas do erro:")
                    for line in stderr_lines[-5:]:
                        if line.strip():
                            print(f"     {line}")
                if output_path.exists():
                    output_path.unlink()
                # If MP4 was requested, this is a critical failure
                if self.config.video.codec == "mp4":
                    raise RuntimeError(f"Falha ao processar vídeo para MP4: {error_msg}")
                return video_path
                
        except subprocess.TimeoutExpired as e:
            logger.error(f"Timeout processing video: {e}")
            print(f"  ⚠️  Timeout ao processar vídeo")
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Video processing timeout: {e}") from e
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Failed to process video: {e}") from e
    
    async def _generate_narration(
        self,
        test_steps: List[Any],  # Can be TestStep objects or dicts
        output_dir: Path,
        test_name: str
    ) -> Optional[Path]:
        """
        Generate TTS narration from test steps.
        
        Args:
            test_steps: List of test steps
            output_dir: Directory to save narration
            test_name: Name of test
            
        Returns:
            Path to narration audio file, or None if generation failed
        """
        try:
            tts_manager = TTSManager(
                lang=self.config.video.narration_lang,
                engine=self.config.video.narration_engine,
                slow=self.config.video.narration_slow
            )
            
            narration_audio = await tts_manager.generate_narration(
                test_steps,
                output_dir,
                test_name
            )
            
            return narration_audio
        except ImportError as e:
            logger.error(f"TTS library not available: {e}")
            print(f"  ⚠️  {e}")
            print(f"  💡 Instale a biblioteca TTS: pip install gtts")
            return None
        except TTSGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error generating narration: {e}", exc_info=True)
            raise TTSGenerationError(f"Failed to generate narration: {e}") from e
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    async def _generate_srt_file(self, video_path: Path, test_steps: List[Any], start_time: datetime) -> Optional[Path]:
        """
        Generate SRT subtitle file from test steps.
        
        Args:
            video_path: Path to video file
            test_steps: List of test steps (TestStep objects or dicts with 'text', 'start_time', 'duration')
            start_time: Video start time (when context was created, when recording began)
            
        Returns:
            Path to SRT file, or None if generation failed or subtitles disabled
        """
        # Don't generate SRT if subtitles are disabled
        if not self.config.video.subtitles:
            return None
        
        if not test_steps:
            return None
        
        srt_path = video_path.parent / f"{video_path.stem}.srt"
        
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                # Convert TestStep objects to dicts for processing
                from ..core.step import TestStep
                step_dicts = []
                for step in test_steps:
                    if isinstance(step, TestStep):
                        step_dicts.append(step.to_dict())
                    elif isinstance(step, dict):
                        step_dicts.append(step)
                    else:
                        logger.warning(f"Unknown step type: {type(step)}, skipping")
                        continue
                
                # Sort steps by start time to ensure proper ordering
                sorted_steps = sorted(step_dicts, key=lambda s: s.get('start_time', 0))
                
                # Process steps and eliminate overlaps
                # Strategy: Build a timeline where each subtitle ends before the next one starts
                processed_steps = []
                subtitle_index = 1
                gap = 0.1  # 100ms gap between subtitles to prevent overlap
                min_duration = self.config.video.subtitle_min_duration  # Use config value (default: 0.5s)
                
                # First pass: calculate end times for all steps
                for i, step in enumerate(sorted_steps):
                    # Get timing from step (TestStep objects have start_time_seconds, end_time_seconds)
                    step_start = step.get('start_time', 0)
                    step_end = step.get('end_time')
                    step_duration = step.get('duration', 0)
                    
                    # If end_time is not provided, calculate from start + duration
                    if step_end is None:
                        step_end = step_start + step_duration
                    
                    # Priority: subtitle > text > description > auto-generated
                    step_text = step.get('subtitle') or step.get('text') or step.get('description', f'Passo {subtitle_index}')
                    
                    # Use actual duration, but ensure minimum for visibility (prevents glitches)
                    actual_duration = step_end - step_start
                    if actual_duration < min_duration:
                        # Extend end time to meet minimum duration
                        step_end = step_start + min_duration
                        actual_duration = min_duration
                    
                    # Store step with calculated end time
                    processed_steps.append({
                        'start': step_start,
                        'end': step_end,
                        'text': step_text,
                        'index': subtitle_index,
                        'duration': actual_duration
                    })
                    subtitle_index += 1
                
                # Second pass: adjust end times to prevent overlaps
                # Strategy: Iterate through all steps and ensure each ends before any subsequent step starts
                # Do multiple passes to handle cascading adjustments
                max_iterations = 10
                for iteration in range(max_iterations):
                    has_overlaps = False
                    for i in range(len(processed_steps)):
                        current_step = processed_steps[i]
                        
                        # Find the earliest subsequent step that starts while this one is active
                        earliest_next_start = None
                        for j in range(i + 1, len(processed_steps)):
                            next_step_start = processed_steps[j]['start']
                            # If next step starts before or at the same time as current step ends, we have overlap
                            # Use <= to catch edge cases where they're exactly equal
                            if next_step_start <= current_step['end']:
                                if earliest_next_start is None or next_step_start < earliest_next_start:
                                    earliest_next_start = next_step_start
                        
                        # If there's overlap, adjust end time to end just before the earliest overlapping step
                        if earliest_next_start is not None:
                            # End this subtitle just before the next one starts (with gap)
                            # Priority: prevent overlap over minimum duration
                            # If a step starts before this one ends, this one must end before it starts
                            new_end = earliest_next_start - gap
                            # But ensure it's at least a tiny bit visible (0.1s minimum)
                            new_end = max(current_step['start'] + 0.1, new_end)
                            # Always update if there's any change needed (even if new_end >= current_end, 
                            # we need to ensure it's before the next step)
                            if abs(new_end - current_step['end']) > 0.001:  # Use small epsilon for comparison
                                current_step['end'] = new_end
                                has_overlaps = True
                    
                    # If no overlaps were found, we're done
                    if not has_overlaps:
                        break
                
                # Final pass: ensure no overlaps remain (safety check)
                # Process multiple times to handle cascading adjustments
                for final_iteration in range(10):
                    made_changes = False
                    for i in range(len(processed_steps)):
                        current_step = processed_steps[i]
                        for j in range(i + 1, len(processed_steps)):
                            next_step = processed_steps[j]
                            # If there's still overlap (even by a tiny amount), force current step to end before next starts
                            # Use >= to catch edge cases
                            if current_step['end'] >= next_step['start']:
                                new_end = next_step['start'] - gap
                                # Ensure minimum visibility (but allow very short subtitles if needed to prevent overlap)
                                new_end = max(current_step['start'] + 0.05, new_end)  # Reduced to 50ms minimum
                                if abs(new_end - current_step['end']) > 0.001:  # Only update if there's a meaningful change
                                    current_step['end'] = new_end
                                    made_changes = True
                    if not made_changes:
                        break
                
                # Third pass: write subtitles (only those with valid duration)
                subtitle_index = 1
                for step in processed_steps:
                    if step['end'] > step['start']:
                        start_time_str = self._format_srt_time(step['start'])
                        end_time_str = self._format_srt_time(step['end'])
                        
                        # Write SRT entry
                        f.write(f"{subtitle_index}\n")
                        f.write(f"{start_time_str} --> {end_time_str}\n")
                        f.write(f"{step['text']}\n\n")
                        
                        subtitle_index += 1
            
            return srt_path
        except Exception as e:
            logger.error(f"Error generating SRT file: {e}", exc_info=True)
            print(f"  ⚠️  Erro ao gerar arquivo SRT: {e}")
            return None
    
    async def _add_subtitles(self, video_path: Path, test_steps: List[Dict[str, Any]], start_time: datetime) -> Optional[Path]:
        """
        Add subtitles to video using ffmpeg.
        
        Args:
            video_path: Path to video file
            test_steps: List of test steps
            start_time: Test start time
            
        Returns:
            Path to video with subtitles, or original path if processing failed
        """
        # Don't add subtitles if disabled
        if not self.config.video.subtitles:
            return video_path
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print(f"  ⚠️  ffmpeg não encontrado. Legendas não serão adicionadas.")
            return video_path
        
        # Generate SRT file
        srt_path = await self._generate_srt_file(video_path, test_steps, start_time)
        if not srt_path or not srt_path.exists():
            return video_path
        
        # Create output path
        output_path = video_path.parent / f"{video_path.stem}_with_subtitles{video_path.suffix}"
        
        try:
            # Use ffmpeg subtitles filter for proper SRT support
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vf', f"subtitles='{srt_path}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2'",
                '-c:v', 'libvpx-vp9' if video_path.suffix == '.webm' else 'libx264',
                '-c:a', 'copy',  # Copy audio as-is
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and output_path.exists():
                video_path.unlink()
                output_path.rename(video_path)
                srt_path.unlink()  # Clean up SRT file
                return video_path
            else:
                # Fallback: try drawtext if subtitles filter fails
                print(f"  ⚠️  Tentando método alternativo para legendas...")
                return await self._add_subtitles_drawtext(video_path, test_steps)
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.warning(f"Error processing subtitles, trying fallback method: {e}")
            print(f"  ⚠️  Erro ao processar legendas: {e}")
            if output_path.exists():
                output_path.unlink()
            return await self._add_subtitles_drawtext(video_path, test_steps)
    
    async def _add_subtitles_drawtext(self, video_path: Path, test_steps: List[Dict[str, Any]]) -> Optional[Path]:
        """
        Add subtitles to video using ffmpeg drawtext filter (fallback method).
        
        This is used when the subtitles filter fails. Drawtext is less flexible
        but more compatible across different ffmpeg versions.
        
        Args:
            video_path: Path to video file
            test_steps: List of test steps with timing information
            
        Returns:
            Path to video with subtitles, or original path if processing failed
            
        Raises:
            VideoProcessingError: If video processing fails
        """
        output_path = video_path.parent / f"{video_path.stem}_with_subtitles{video_path.suffix}"
        
        try:
            # Build drawtext filters for each step
            drawtext_filters = []
            for i, step in enumerate(test_steps, 1):
                step_start = step.get('start_time', 0)
                step_duration = step.get('duration', 2.0)
                step_text = step.get('text', step.get('description', f'Passo {i}'))
                
                # Escape special characters for drawtext
                escaped_text = step_text.replace(':', '\\:').replace("'", "\\'").replace('[', '\\[').replace(']', '\\]')
                
                # Create drawtext filter for this step
                drawtext_filter = (
                    f"drawtext=text='{escaped_text}':"
                    f"fontsize=24:"
                    f"fontcolor=white:"
                    f"x=(w-text_w)/2:"
                    f"y=h-th-20:"
                    f"box=1:"
                    f"boxcolor=black@0.7:"
                    f"boxborderw=5:"
                    f"enable='between(t,{step_start},{step_start + step_duration})'"
                )
                drawtext_filters.append(drawtext_filter)
            
            # Combine all filters
            if drawtext_filters:
                filter_complex = ','.join(drawtext_filters)
                
                cmd = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-vf', filter_complex,
                    '-c:v', 'libvpx-vp9' if video_path.suffix == '.webm' else 'libx264',
                    '-c:a', 'copy',
                    '-y',
                    str(output_path)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0 and output_path.exists():
                    video_path.unlink()
                    output_path.rename(video_path)
                    return video_path
            
            return video_path
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing subtitles (drawtext): {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Failed to process subtitles with drawtext: {e}") from e
    
    async def _add_audio(self, video_path: Path, audio_file: str) -> Optional[Path]:
        """
        Add audio track to video using ffmpeg.
        
        Args:
            video_path: Path to video file
            audio_file: Path to audio file (mp3, wav, etc.)
            
        Returns:
            Path to video with audio, or original path if processing failed
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            print(f"  ⚠️  Arquivo de áudio não encontrado: {audio_file}")
            return video_path
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print(f"  ⚠️  ffmpeg não encontrado. Áudio não será adicionado.")
            return video_path
        
        output_path = video_path.parent / f"{video_path.stem}_with_audio{video_path.suffix}"
        
        try:
            # Mix audio with video (loop audio if shorter than video)
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-stream_loop', '-1',  # Loop audio if needed
                '-i', str(audio_path),
                '-c:v', 'copy',  # Copy video as-is
                '-c:a', 'libopus' if video_path.suffix == '.webm' else 'aac',
                '-shortest',  # End when shortest stream ends
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and output_path.exists():
                video_path.unlink()
                output_path.rename(video_path)
                return video_path
            else:
                print(f"  ⚠️  Erro ao adicionar áudio: {result.stderr[:200]}")
                return video_path
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Failed to process audio: {e}") from e


