#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for playwright-simple.

Handles test execution, video recording, and reporting.
"""

import asyncio
import traceback
from pathlib import Path
from typing import Callable, List, Tuple, Optional, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .config import TestConfig
from .base import SimpleTestBase
from .video import VideoManager

# Try to import OdooTestBase (optional dependency)
try:
    from ..odoo.base import OdooTestBase
    ODOO_AVAILABLE = True
except ImportError:
    OdooTestBase = None
    ODOO_AVAILABLE = False


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
        
        result = {
            "name": test_name,
            "status": "unknown",
            "error": None,
            "duration": 0,
            "video_path": None,
            "screenshots": [],
        }
        
        start_time = datetime.now()
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
            
            # Create page
            page = await context.new_page()
            
            # Create test instance - detect if Odoo test is needed
            # Check if test function has Odoo-specific attributes or annotations
            print(f"  🔧 Criando instância de teste...")
            test = self._create_test_instance(page, test_name, test_func)
            print(f"  ✅ Instância criada: {type(test).__name__}")
            
            # Inject cursor IMMEDIATELY after creating test instance (before navigation)
            # This ensures cursor is visible from the start of the video
            print(f"  🖱️  Injetando cursor...")
            await test.cursor_manager.inject(force=True)
            await asyncio.sleep(0.5)  # Small delay to ensure cursor is rendered
            print(f"  ✅ Cursor injetado")
            
            # Navigate to base URL first
            if self.config.base_url:
                print(f"  🌐 Navegando para: {self.config.base_url}")
                await page.goto(self.config.base_url, wait_until="networkidle", timeout=self.config.browser.navigation_timeout)
                await asyncio.sleep(1)
                # Re-inject cursor after navigation to ensure it's visible
                await test.cursor_manager.inject(force=True)
                await asyncio.sleep(0.3)
                # Take debug screenshot
                screenshots_dir = Path(self.config.screenshots.dir)
                debug_screenshot = screenshots_dir / test_name / "debug_initial_page.png"
                debug_screenshot.parent.mkdir(parents=True, exist_ok=True)
                await page.screenshot(path=str(debug_screenshot), full_page=True)
                print(f"  📸 Screenshot inicial salvo: {debug_screenshot}")
            
            # Load session if test function has load_session attribute
            if hasattr(test_func, 'load_session') and test_func.load_session:
                print(f"  💾 Carregando sessão: {test_func.load_session}")
                session_loaded = await test.load_session(test_func.load_session)
                if session_loaded:
                    print(f"  ✅ Sessão carregada com sucesso")
                    # Navigate to base URL after loading session
                    if self.config.base_url:
                        await page.goto(self.config.base_url, wait_until="networkidle", timeout=self.config.browser.navigation_timeout)
                        await asyncio.sleep(0.5)
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
            await test_func(page, test)
            print(f"  ✅ Teste executado com sucesso")
            
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
            
            result["status"] = "passed"
            print(f"  ✅ {test_name} passed")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["error_traceback"] = traceback.format_exc()
            print(f"  ❌ {test_name} failed: {e}")
            print(f"  📋 Traceback completo:")
            print(traceback.format_exc())
            
            # Capture screenshot on failure
            if self.config.screenshots.on_failure and 'test' in locals():
                try:
                    screenshot_path = await test.screenshot_manager.capture_on_failure(e)
                    result["screenshots"].append(str(screenshot_path))
                    print(f"  📸 Screenshot de erro salvo: {screenshot_path}")
                except Exception as screenshot_error:
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
                    print(f"  ⚠️  Erro ao capturar screenshot da página: {e}")
        
        finally:
            # Cleanup
            if 'page' in locals():
                await asyncio.sleep(1)
                await page.close()
            
            if create_context and context:
                await asyncio.sleep(1)
                await context.close()
            
            # Get video path and rename to test name
            # Playwright creates videos with hash in record_video_dir, we rename after
            if self.config.video.enabled:
                # Wait a bit for video to be finalized after context close
                await asyncio.sleep(2)
                
                # Find the most recently created video file in video_dir (not in subdirs)
                video_extensions = ['.webm', '.mp4']
                all_videos = []
                for ext in video_extensions:
                    # Only search directly in video_dir, not subdirectories
                    all_videos.extend(list(self.video_manager.video_dir.glob(f"*{ext}")))
                
                if all_videos:
                    # Get the most recent video (should be from this test)
                    found_video = max(all_videos, key=lambda p: p.stat().st_mtime)
                    
                    # Rename to test name
                    expected_name = f"{test_name}.webm" if self.config.video.codec == "webm" else f"{test_name}.mp4"
                    expected_path = self.video_manager.video_dir / expected_name
                    
                    if found_video != expected_path:
                        if expected_path.exists():
                            expected_path.unlink()
                        found_video.rename(expected_path)
                        print(f"  📹 Vídeo renomeado para: {expected_path.name}")
                    else:
                        print(f"  📹 Vídeo salvo: {expected_path.name}")
                    
                    result["video_path"] = str(expected_path)
                else:
                    print(f"  ⚠️  Vídeo não encontrado para {test_name}")
        
        # Calculate duration
        end_time = datetime.now()
        result["duration"] = (end_time - start_time).total_seconds()
        
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
                except Exception:
                    pass
            # Remove empty subdirectories
            for subdir in self.video_manager.video_dir.iterdir():
                if subdir.is_dir():
                    try:
                        subdir.rmdir()
                    except Exception:
                        pass
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
                print(f"❌ Error during test execution: {e}")
                traceback.print_exc()
            finally:
                await browser.close()
                await asyncio.sleep(1)
        
        return self.test_results
    
    async def _run_parallel(self, browser: Browser, tests: List[Tuple[str, Callable]], workers: int):
        """Run tests in parallel."""
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
            Test base instance (SimpleTestBase or OdooTestBase)
        """
        # Check if test function expects OdooTestBase
        import inspect
        
        # Check function signature
        sig = inspect.signature(test_func)
        params = list(sig.parameters.values())
        
        # If second parameter is annotated as OdooTestBase, use it
        if len(params) >= 2:
            param = params[1]  # Second parameter is usually 'test'
            if param.annotation != inspect.Parameter.empty:
                annotation_str = str(param.annotation)
                if 'OdooTestBase' in annotation_str and ODOO_AVAILABLE:
                    return OdooTestBase(page, self.config, test_name)
        
        # Check if test function module is from odoo
        if hasattr(test_func, '__module__'):
            if 'odoo' in test_func.__module__ and ODOO_AVAILABLE:
                return OdooTestBase(page, self.config, test_name)
        
        # Default to SimpleTestBase
        return SimpleTestBase(page, self.config, test_name)
    
    def _print_summary(self):
        """Print test execution summary."""
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
        Get test execution results.
        
        Returns:
            List of test result dictionaries
        """
        return self.test_results
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get execution summary.
        
        Returns:
            Dictionary with summary statistics
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


