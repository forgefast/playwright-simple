#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test orchestration module.

Handles execution of multiple tests (sequential or parallel).
"""

import asyncio
import logging
import traceback
from typing import Callable, List, Tuple, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser

from ..config import TestConfig
from ..video import VideoManager
from .test_executor import TestExecutor

logger = logging.getLogger(__name__)


class TestOrchestrator:
    """Handles orchestration of multiple tests."""
    
    def __init__(
        self,
        config: TestConfig,
        video_manager: VideoManager,
        test_executor: TestExecutor
    ):
        """
        Initialize test orchestrator.
        
        Args:
            config: Test configuration
            video_manager: Video manager instance
            test_executor: Test executor instance
        """
        self.config = config
        self.video_manager = video_manager
        self.test_executor = test_executor
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
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
                        result = await self.test_executor.execute(test_name, test_func, browser=browser)
                        self.test_results.append(result)
                
                self.end_time = datetime.now()
                
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
                return await self.test_executor.execute(test_name, test_func, browser=browser)
        
        tasks = [run_with_semaphore(test_name, test_func) for test_name, test_func in tests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"  ❌ Error in parallel execution: {result}")
            else:
                self.test_results.append(result)

