#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner module.

Main TestRunner class that orchestrates test execution using composition.
"""

from typing import Callable, List, Tuple, Optional, Dict, Any
from datetime import datetime
from playwright.async_api import Browser, BrowserContext

from ..config import TestConfig
from ..video import VideoManager
from .video_processor import VideoProcessor
from .subtitle_generator import SubtitleGenerator
from .audio_processor import AudioProcessor
from .test_executor import TestExecutor
from .test_orchestrator import TestOrchestrator
from .test_context import TestContextManager
from .reporting import TestReporter


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
        viewport: Optional[Dict[str, int]] = None,
        mode: str = 'write'
    ):
        """
        Initialize test runner.
        
        Args:
            config: Test configuration (creates default if not provided)
            base_url: Base URL (overrides config if provided)
            videos_dir: Videos directory (overrides config if provided)
            headless: Headless mode (overrides config if provided)
            viewport: Viewport size (overrides config if provided)
            mode: 'write' for recording (export), 'read' for playback (import)
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
        self.mode = mode  # Store mode for passing to Recorder
        self.video_manager = VideoManager(config.video)
        
        # Initialize service components
        self.video_processor = VideoProcessor(config)
        self.subtitle_generator = SubtitleGenerator(config)
        self.audio_processor = AudioProcessor(config)
        self.context_manager = TestContextManager(config)
        self.reporter = TestReporter(config, self.video_manager)
        
        # Initialize executor and orchestrator (they depend on other services)
        self.test_executor = TestExecutor(
            config,
            self.video_manager,
            self.video_processor,
            self.subtitle_generator,
            self.audio_processor
        )
        self.test_orchestrator = TestOrchestrator(
            config,
            self.video_manager,
            self.test_executor
        )
        
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
        return await self.test_executor.execute(test_name, test_func, browser=browser, context=context)
    
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
        self.start_time = datetime.now()
        results = await self.test_orchestrator.run_all(tests, parallel=parallel, workers=workers)
        self.end_time = datetime.now()
        self.test_results = results
        
        # Print summary using reporter
        self.reporter.print_summary(self.test_results, self.start_time, self.end_time)
        
        return results
    
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
        return self.reporter.get_results(self.test_results)
    
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
        return self.reporter.get_summary(self.test_results, self.start_time, self.end_time)

