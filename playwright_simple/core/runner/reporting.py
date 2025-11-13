#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test reporting module.

Handles test result reporting and summary generation.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..config import TestConfig
from ..video import VideoManager

logger = logging.getLogger(__name__)


class TestReporter:
    """Handles test result reporting."""
    
    def __init__(
        self,
        config: TestConfig,
        video_manager: VideoManager
    ):
        """
        Initialize test reporter.
        
        Args:
            config: Test configuration
            video_manager: Video manager instance
        """
        self.config = config
        self.video_manager = video_manager
    
    def print_summary(self, test_results: List[Dict[str, Any]], start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> None:
        """
        Print test execution summary to console.
        
        Shows total tests, passed, failed, duration, and video/screenshot counts.
        
        Args:
            test_results: List of test result dictionaries
            start_time: Execution start time
            end_time: Execution end time
        """
        if not test_results:
            return
        
        total = len(test_results)
        passed = sum(1 for r in test_results if r["status"] == "passed")
        failed = total - passed
        
        total_duration = sum(r["duration"] for r in test_results)
        if start_time and end_time:
            wall_time = (end_time - start_time).total_seconds()
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
            for result in test_results:
                if result["status"] == "failed":
                    print(f"  - {result['name']}: {result['error']}")
        
        print(f"\n📹 Videos saved to: {self.video_manager.video_dir}")
        print(f"📸 Screenshots saved to: {self.config.screenshots.dir}")
    
    def get_results(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get all test execution results.
        
        Args:
            test_results: List of test result dictionaries
            
        Returns:
            Copy of test results list
        """
        return test_results.copy()
    
    def get_summary(self, test_results: List[Dict[str, Any]], start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get execution summary statistics.
        
        Args:
            test_results: List of test result dictionaries
            start_time: Execution start time
            end_time: Execution end time
        
        Returns:
            Dictionary with summary statistics:
            - total: Total number of tests
            - passed: Number of passed tests
            - failed: Number of failed tests
            - duration: Total execution duration
            - start_time: Execution start time
            - end_time: Execution end time
        """
        if not test_results:
            return {}
        
        total = len(test_results)
        passed = sum(1 for r in test_results if r["status"] == "passed")
        failed = total - passed
        total_duration = sum(r["duration"] for r in test_results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "total_duration": total_duration,
            "wall_time": (end_time - start_time).total_seconds() if start_time and end_time else total_duration,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        }

