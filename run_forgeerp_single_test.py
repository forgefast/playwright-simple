#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run a single ForgeERP test to generate video.
"""

import asyncio
from playwright_simple import TestRunner, TestConfig
from playwright_simple.forgeerp import ForgeERPTestBase


async def test_forgeerp_navigation(page, test: ForgeERPTestBase):
    """Test basic navigation in ForgeERP."""
    # Navigate to different pages
    await test.go_to("/")  # Home
    await test.wait(1)
    await test.go_to_setup()
    await test.wait(1)
    await test.go_to_provision()
    await test.wait(1)
    await test.go_to_status()
    await test.wait(1)
    await test.go_to_deploy()
    await test.wait(1)
    await test.go_to_diagnostics()
    await test.wait(1)


async def main():
    """Run single ForgeERP test with video."""
    config = TestConfig.load(
        base_url="http://localhost:8000",
        cursor_style="arrow",
        cursor_color="#6366f1",  # ForgeERP indigo
        video_enabled=True,
        video_quality="high",
        browser_headless=True,
        browser_slow_mo=500,
    )
    
    runner = TestRunner(config=config)
    
    # Run single test
    await runner.run_all([
        ("forgeerp_navigation", test_forgeerp_navigation)
    ])
    
    # Print summary
    runner._print_summary()


if __name__ == "__main__":
    asyncio.run(main())

