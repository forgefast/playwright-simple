#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for SimpleTestBase class.
"""

import pytest
from playwright.async_api import async_playwright
from playwright_simple import SimpleTestBase, TestConfig


@pytest.mark.asyncio
async def test_base_initialization():
    """Test SimpleTestBase initialization."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig()
        test = SimpleTestBase(page, config, "test_name")
        
        assert test.page == page
        assert test.config == config
        assert test.test_name == "test_name"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_go_to():
    """Test go_to method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Mock page.goto
        original_goto = page.goto
        called_url = None
        
        async def mock_goto(url, **kwargs):
            nonlocal called_url
            called_url = url
            return await original_goto("data:text/html,<html><body>Test</body></html>")
        
        page.goto = mock_goto
        
        config = TestConfig(base_url="http://test.com")
        test = SimpleTestBase(page, config)
        
        await test.go_to("/path")
        assert called_url == "http://test.com/path"
        
        await test.go_to("http://absolute.com/path")
        assert called_url == "http://absolute.com/path"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_wait():
    """Test wait method."""
    import time
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        test = SimpleTestBase(page, TestConfig())
        
        start = time.time()
        await test.wait(0.1)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        
        await context.close()
        await browser.close()


