#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test execution module.

Handles execution of individual tests.
"""

import asyncio
import logging
import traceback
from pathlib import Path
from typing import Callable, List, Optional, Dict, Any
from datetime import datetime
from playwright.async_api import Browser, BrowserContext, Page

from ..config import TestConfig
from ..base import SimpleTestBase
from ..video import VideoManager
from ..exceptions import ElementNotFoundError, NavigationError, VideoProcessingError
from ..constants import CLEANUP_DELAY, VIDEO_FINALIZATION_DELAY, HOVER_EFFECT_ELEMENT_ID, CLICK_EFFECT_ELEMENT_ID
from .video_processor import VideoProcessor
from .subtitle_generator import SubtitleGenerator
from .audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

# Try to import OdooTestBase (optional dependency)
try:
    from ...odoo.base import OdooTestBase
    ODOO_AVAILABLE = True
except ImportError:
    OdooTestBase = None
    ODOO_AVAILABLE = False

# Try to import ForgeERPTestBase (optional dependency)
try:
    from ...forgeerp.base import ForgeERPTestBase
    FORGEERP_AVAILABLE = True
except ImportError:
    ForgeERPTestBase = None
    FORGEERP_AVAILABLE = False


def _log_action(action: str, test_name: str, details: Optional[Dict[str, Any]] = None, level: str = "INFO"):
    """
    Log structured action for debugging.
    
    Args:
        action: Action name (e.g., "test_started", "navigation", "click")
        test_name: Name of current test
        details: Additional details to log
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    import json
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


class TestExecutor:
    """Handles execution of individual tests."""
    
    def __init__(
        self,
        config: TestConfig,
        video_manager: VideoManager,
        video_processor: VideoProcessor,
        subtitle_generator: SubtitleGenerator,
        audio_processor: AudioProcessor
    ):
        """
        Initialize test executor.
        
        Args:
            config: Test configuration
            video_manager: Video manager instance
            video_processor: Video processor instance
            subtitle_generator: Subtitle generator instance
            audio_processor: Audio processor instance
        """
        self.config = config
        self.video_manager = video_manager
        self.video_processor = video_processor
        self.subtitle_generator = subtitle_generator
        self.audio_processor = audio_processor
        self._command_server = None
        self._test_instance = None
    
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
    
    async def execute(
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
        import time
        test_start_time = time.time()
        print(f"\n🎬 Running test: {test_name}")
        print(f"  ⏱️  Performance: Teste iniciado às {time.strftime('%H:%M:%S')}")
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
        start_time = datetime.now()
        video_start_time = None  # Time when video recording actually starts (context creation)
        create_context = context is None
        
        try:
            # Create browser if needed
            if browser is None:
                from playwright.async_api import async_playwright
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(
                    headless=self.config.browser.headless,
                    slow_mo=self.config.browser.slow_mo
                )
                # Store playwright instance for cleanup
                self._playwright = playwright
                self._browser_created = True
            else:
                self._playwright = None
                self._browser_created = False
            
            # Create context if needed
            if create_context:
                
                # Get video options - pass viewport to ensure video size matches viewport
                video_options = self.video_manager.get_context_options(
                    test_name, 
                    viewport=self.config.browser.viewport
                )
                
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
            self._test_instance = test  # Store for CommandServer access
            test_type = type(test).__name__
            print(f"  ✅ Instância criada: {test_type}")
            _log_action("test_instance_created", test_name, {"test_type": test_type})
            
            # Inicializar control interface para comunicação externa
            try:
                from ..control_interface import ControlInterface
                test._control_interface = ControlInterface(test_name)
                logger.debug(f"Control interface initialized for {test_name}")
            except Exception as e:
                logger.debug(f"Could not initialize control interface: {e}")
                test._control_interface = None
            
            # Criar CommandServer para permitir comandos CLI durante execução
            try:
                from ..recorder.command_server import CommandServer
                
                # Criar mock Recorder que expõe a página e test instance
                class MockRecorder:
                    def __init__(self, page, test_instance):
                        self.page = page
                        self.test_instance = test_instance
                        self.cursor_controller = None  # Não necessário para comandos básicos
                
                mock_recorder = MockRecorder(page, test)
                self._command_server = CommandServer(mock_recorder)
                await self._command_server.start()
                logger.debug("CommandServer iniciado para comandos CLI durante execução")
            except Exception as e:
                logger.debug(f"Could not start CommandServer: {e}")
                self._command_server = None
            
            # Inject cursor IMMEDIATELY after creating test instance (before navigation)
            # This ensures cursor is visible from the start of the video
            print(f"  🖱️  Injetando cursor...")
            await test.cursor_manager.inject(force=True)
            
            # Try to restore cursor position from storage, or move to center
            viewport = page.viewport_size or {"width": 1920, "height": 1080}
            center_x = viewport['width'] / 2
            center_y = viewport['height'] / 2
            
            # Try to get last cursor position from storage
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
                initial_x = int(position.get('x'))
                initial_y = int(position.get('y'))
                logger.info(f"Restoring cursor position from storage: ({initial_x}, {initial_y})")
                # Move cursor visual first
                await test.cursor_manager.move_to(initial_x, initial_y)
                # Then sync Playwright mouse position to match cursor visual
                await page.mouse.move(initial_x, initial_y)
            else:
                # Move cursor to center of screen to ensure it's visible
            await test.cursor_manager.move_to(center_x, center_y)
                # Sync Playwright mouse position
                await page.mouse.move(center_x, center_y)
            
            # Set up navigation listener to restore cursor position after navigation
            async def on_navigation(frame):
                """Restore cursor position after navigation."""
                try:
                    # Only handle main frame navigation
                    if frame != page.main_frame:
                        return
                    
                    # Wait for page to be ready
                    try:
                        await page.wait_for_load_state('domcontentloaded', timeout=5000)
                    except:
                        pass
                    
                    # Get last position from storage
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
                        x = int(position.get('x'))
                        y = int(position.get('y'))
                        logger.info(f"🖱️  [DEBUG] Navigation detected, restoring cursor to ({x}, {y})")
                        # CRITICAL: Store position BEFORE injecting cursor
                        # This ensures cursor is created at correct position, not center
                        await page.evaluate(f"""
                            () => {{
                                const pos = {{x: {x}, y: {y}}};
                                window.__playwright_cursor_last_position = pos;
                                try {{
                                    sessionStorage.setItem('__playwright_cursor_last_position', JSON.stringify(pos));
                                }} catch (e) {{
                                    // sessionStorage might not be available
                                }}
                            }}
                        """)
                        # Re-inject cursor (will use stored position, not center)
                        await test.cursor_manager.inject(force=True)
                        logger.info(f"🖱️  [DEBUG] Cursor injected at ({x}, {y}), syncing mouse")
                        # Sync Playwright mouse position to match cursor visual (cursor already at correct position)
                        await page.mouse.move(x, y)
                        logger.info(f"Cursor restored after navigation: ({x}, {y})")
                        logger.info(f"🖱️  [DEBUG] Cursor and mouse restored to ({x}, {y})")
                    else:
                        # No saved position, re-inject cursor (will use last position from move_to)
                        await test.cursor_manager.inject(force=True)
                        # Try to get current cursor position and sync mouse
                        try:
                            current_pos = await page.evaluate("""
                                () => {
                                    const cursor = document.getElementById('__playwright_cursor');
                                    if (cursor) {
                                        const rect = cursor.getBoundingClientRect();
                                        return {x: rect.left + rect.width / 2, y: rect.top + rect.height / 2};
                                    }
                                    return null;
                                }
                            """)
                            if current_pos:
                                await page.mouse.move(int(current_pos['x']), int(current_pos['y']))
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"Error restoring cursor after navigation: {e}")
                    # Try to restore anyway
                    try:
                        await test.cursor_manager.inject(force=True)
                    except:
                        pass
            
            # Listen for navigation events
            page.on('framenavigated', on_navigation)
            
            # Remove hover effect and hide click effect if disabled (they might have been created)
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
            print(f"  ✅ Cursor injetado e posicionado no centro")
            
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
                await test.cursor_manager._ensure_cursor_exists()
                
                # Remove hover effect and hide click effect again after navigation (in case they were recreated)
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
            
            # Salvar erro no control interface
            if 'test' in locals() and hasattr(test, '_control_interface') and test._control_interface:
                try:
                    step_number = len(test_steps) if test_steps else None
                    test._control_interface.save_error(e, step_number)
                    
                    # Capturar HTML automaticamente para análise
                    if 'page' in locals() and page:
                        try:
                            html = await page.content()
                            html_file = Path("/tmp/playwright_html.html")
                            html_file.write_text(html, encoding='utf-8')
                            
                            # Salvar versão simplificada
                            try:
                                simplified = await page.evaluate("""
                                    () => {
                                        const buttons = Array.from(document.querySelectorAll('button, a[role="button"], input[type="submit"], input[type="button"]'))
                                            .map(btn => ({
                                                text: btn.textContent?.trim() || btn.value || btn.getAttribute('aria-label') || '',
                                                tag: btn.tagName.toLowerCase(),
                                                id: btn.id || '',
                                                class: btn.className || '',
                                                visible: btn.offsetParent !== null
                                            }))
                                            .filter(btn => btn.visible && btn.text);
                                        
                                        const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea'))
                                            .map(inp => ({
                                                type: inp.type,
                                                placeholder: inp.placeholder || '',
                                                name: inp.name || '',
                                                id: inp.id || '',
                                                label: inp.labels?.[0]?.textContent?.trim() || ''
                                            }));
                                        
                                        return JSON.stringify({
                                            buttons: buttons,
                                            inputs: inputs,
                                            url: window.location.href,
                                            title: document.title
                                        }, null, 2);
                                    }
                                """)
                                simplified_file = Path("/tmp/playwright_html_simplified.json")
                                simplified_file.write_text(simplified, encoding='utf-8')
                            except Exception as html_error:
                                logger.debug(f"Error capturing simplified HTML: {html_error}")
                        except Exception as html_error:
                            logger.debug(f"Error capturing HTML on error: {html_error}")
                except Exception as save_error:
                    logger.debug(f"Error saving error to control interface: {save_error}")
            
            # Try debug extension if available
            if 'test' in locals() and hasattr(test, 'extensions'):
                debug_ext = test.extensions.get('debug')
                if debug_ext:
                    should_continue = await debug_ext.on_error(
                        error=e,
                        page=page,
                        step_number=len(test_steps) if test_steps else None,
                        action=test_steps[-1].get('action') if test_steps else None
                    )
                    if should_continue:
                        result["status"] = "continued"
                        print(f"  🔄 Continuing after debug session...")
            
            # Capture screenshot on failure
            if self.config.screenshots.on_failure and 'test' in locals():
                try:
                    screenshot_path = await test.screenshot_manager.capture_on_failure(e)
                    result["screenshots"].append(str(screenshot_path))
                    print(f"  📸 Screenshot de erro salvo: {screenshot_path}")
                except Exception as screenshot_error:
                    logger.warning(f"Error capturing failure screenshot: {screenshot_error}")
                    print(f"  ⚠️  Erro ao capturar screenshot: {screenshot_error}")
            
            # Save HTML content of the page (more useful for debugging than screenshots)
            if 'page' in locals():
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
            
            # Cleanup browser and playwright if we created them
            if hasattr(self, '_browser_created') and self._browser_created:
                if browser:
                    await browser.close()
                if hasattr(self, '_playwright') and self._playwright:
                    await self._playwright.stop()
            
            # Stop CommandServer if it was started
            if self._command_server:
                try:
                    await self._command_server.stop()
                    logger.debug("CommandServer parado após execução do teste")
                except Exception as e:
                    logger.debug(f"Error stopping CommandServer: {e}")
                finally:
                    self._command_server = None
            
            # Cleanup orphan browser processes
            try:
                from ..recorder.command_server import cleanup_old_sessions
                cleaned = cleanup_old_sessions(force=True, timeout=5.0)
                if cleaned > 0:
                    logger.debug(f"Cleaned up {cleaned} orphan browser process(es) after test execution")
            except Exception as e:
                logger.debug(f"Error cleaning up orphan processes: {e}")
            
            # Get video path and rename to test name
            # Playwright creates videos with hash in record_video_dir, we rename after
            if self.config.video.enabled:
                # Wait a bit for video to be finalized after context close
                await asyncio.sleep(VIDEO_FINALIZATION_DELAY)
                
                # Find the most recently created video file in video_dir (not in subdirs)
                import re
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
                    video_processing_start = time.time()
                    logger.info(f"Preparando processamento de vídeo: found_video={found_video.name if found_video else None}, expected_path={expected_path.name}, needs_conversion={needs_conversion}")
                    print(f"  ⏱️  Performance: Iniciando processamento de vídeo às {time.strftime('%H:%M:%S')}")
                    # Generate narration/audio if enabled
                    narration_audio = None
                    narration_start = time.time()
                    # Use audio field from steps if config.video.audio is enabled, otherwise use narration
                    if (self.config.video.audio or self.config.video.narration) and test_steps:
                        _log_action("narration_generation_started", test_name)
                        # Use audio config if audio is enabled, otherwise use narration config
                        if self.config.video.audio:
                            # Create TTSManager with audio config
                            from ..tts import TTSManager
                            tts_manager = TTSManager(
                                lang=self.config.video.audio_lang,
                                engine=self.config.video.audio_engine,
                                slow=False,
                                voice=getattr(self.config.video, 'audio_voice', None),
                                rate=getattr(self.config.video, 'audio_rate', None),
                                pitch=getattr(self.config.video, 'audio_pitch', None),
                                volume=getattr(self.config.video, 'audio_volume', None)
                            )
                            # Return timed audio list for synchronization with steps
                            narration_audio = await tts_manager.generate_narration(
                                test_steps,
                                expected_path.parent,
                                test_name,
                                return_timed_audio=True  # Return list of (audio_path, start_time) tuples
                            )
                        else:
                            # Use narration config
                            narration_audio = await self.audio_processor.generate_narration(
                                test_steps,
                                expected_path.parent,
                                test_name
                            )
                        narration_duration = time.time() - narration_start
                        if narration_audio:
                            print(f"  ⏱️  Performance: Áudio gerado em {narration_duration:.2f}s")
                            _log_action("narration_generated", test_name, {
                                "audio_path": str(narration_audio),
                                "duration": narration_duration
                            })
                        else:
                            print(f"  ⏱️  Performance: Áudio não gerado (tempo: {narration_duration:.2f}s)")
                    
                    # Process if we need to add intro screen, modify video, or convert format
                    # Only process if there's actually something to do
                    needs_processing = (
                        (test_name is not None) or  # Need to add intro screen
                        self.config.video.speed != 1.0 or
                        (self.config.video.subtitles and test_steps) or
                        self.config.video.audio_file or
                        (self.config.video.audio and test_steps) or  # Audio from steps
                        narration_audio or
                        needs_conversion  # Always process if we need to convert webm to mp4
                    )
                    
                    logger.info(f"needs_processing={needs_processing} (test_name={test_name is not None}, speed={self.config.video.speed}, subtitles={self.config.video.subtitles and bool(test_steps)}, audio_file={bool(self.config.video.audio_file)}, narration={bool(narration_audio)}, needs_conversion={needs_conversion})")
                    print(f"  🔍 DEBUG: needs_processing={needs_processing}")
                    
                    if needs_processing:
                        print(f"  🔍 DEBUG: Entrando no bloco de processamento")
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
                        try:
                            process_all_start = time.time()
                            logger.info(f"Chamando process_all_in_one: video={video_to_process.name}, test_name={test_name}")
                            print(f"  🔍 DEBUG: Chamando process_all_in_one: video={video_to_process.name}, test_name={test_name}")
                            print(f"  ⏱️  Performance: Chamando process_all_in_one às {time.strftime('%H:%M:%S')}")
                            final_path = await self.video_processor.process_all_in_one(
                                video_to_process,
                                test_steps,
                                subtitle_reference_time,
                                self.subtitle_generator,
                                self.audio_processor,
                                narration_audio=narration_audio,
                                test_name=test_name
                            )
                            process_all_duration = time.time() - process_all_start
                            logger.info(f"process_all_in_one retornou: {final_path.name if final_path else None} (suffix={final_path.suffix if final_path else None}) em {process_all_duration:.2f}s")
                            print(f"  ⏱️  Performance: process_all_in_one concluído em {process_all_duration:.2f}s")
                        except VideoProcessingError as e:
                            logger.error(f"Erro ao processar vídeo: {e}", exc_info=True)
                            if self.config.video.codec == "mp4":
                                raise RuntimeError(f"Falha ao processar vídeo para MP4: {e}") from e
                            # If not MP4, use original video
                            final_path = video_to_process
                        except Exception as e:
                            logger.error(f"Erro inesperado ao processar vídeo: {e}", exc_info=True)
                            if self.config.video.codec == "mp4":
                                raise RuntimeError(f"Falha ao processar vídeo para MP4: {e}") from e
                            final_path = video_to_process
                        if final_path and final_path.exists():
                            # Rename processed video to expected name if needed
                            rename_start = time.time()
                            # Check if final_path is a processed file (_processed suffix) or different from expected
                            needs_rename = (
                                "_processed" in final_path.stem or  # Video has _processed in name
                                final_path != expected_path  # Video name doesn't match expected
                            )
                            
                            if needs_rename:
                                logger.info(f"Renomeando vídeo processado: {final_path.name} -> {expected_path.name}")
                                print(f"  📹 Renomeando vídeo: {final_path.name} -> {expected_path.name}")
                                if expected_path.exists():
                                    expected_path.unlink()
                                final_path.rename(expected_path)
                                final_path = expected_path
                                rename_duration = time.time() - rename_start
                                print(f"  ✅ Vídeo renomeado com sucesso: {expected_path.name}")
                                print(f"  ⏱️  Performance: Renomeação concluída em {rename_duration:.3f}s")
                            
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
        test_total_duration = time.time() - test_start_time
        result["duration"] = (end_time - start_time).total_seconds()
        print(f"  ⏱️  Performance: Teste '{test_name}' concluído em {test_total_duration:.2f}s total")
        if self.config.video.enabled and 'video_processing_start' in locals():
            video_processing_total = time.time() - video_processing_start
            print(f"  ⏱️  Performance: Processamento de vídeo total: {video_processing_total:.2f}s")
        
        # Calculate expected minimum duration based on test steps
        # This helps detect if test failed early or was too short
        expected_min_duration = None
        if 'test_steps' in locals() and test_steps:
            # Sum up all step durations (minimum 1s per step)
            # Handle both TestStep objects and dicts
            from ..step import TestStep
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

