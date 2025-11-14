#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal tests for SimpleTestBase - FASE 0 TDD.

These tests define the minimum requirements for SimpleTestBase.
Following TDD: write tests first, then implement.
"""

import pytest
from playwright.async_api import async_playwright
from playwright_simple import SimpleTestBase, TestConfig


@pytest.mark.asyncio
async def test_base_initialization_minimal():
    """
    Test: SimpleTestBase can be initialized with page and config.
    
    Requirement: SimpleTestBase must accept a Page and optional TestConfig.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://test.com")
        test = SimpleTestBase(page, config)
        
        assert test.page == page
        assert test.config == config
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_click_generic():
    """
    Test: SimpleTestBase can click on elements generically.
    
    Requirement: click() method must work with any web app.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple HTML page with a button
        await page.set_content("""
            <html>
                <body>
                    <button id="test-btn">Click Me</button>
                </body>
            </html>
        """)
        
        test = SimpleTestBase(page, TestConfig())
        
        # Click should work
        await test.click("#test-btn")
        
        # Verify button was clicked (we can check if it exists)
        button = page.locator("#test-btn")
        assert await button.count() == 1
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_type_generic():
    """
    Test: SimpleTestBase can type text into input fields generically.
    
    Requirement: type() method must work with any web app.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple HTML page with an input
        await page.set_content("""
            <html>
                <body>
                    <input id="test-input" type="text" />
                </body>
            </html>
        """)
        
        test = SimpleTestBase(page, TestConfig())
        
        # Type should work
        await test.type("#test-input", "Hello World")
        
        # Verify text was typed
        input_value = await page.locator("#test-input").input_value()
        assert input_value == "Hello World"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_fill_generic():
    """
    Test: SimpleTestBase can fill form fields generically.
    
    Requirement: fill() method must work with any web app.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple HTML page with an input
        await page.set_content("""
            <html>
                <body>
                    <input id="test-input" type="text" />
                </body>
            </html>
        """)
        
        test = SimpleTestBase(page, TestConfig())
        
        # Fill should work
        await test.fill("#test-input", "Filled Value")
        
        # Verify value was filled
        input_value = await page.locator("#test-input").input_value()
        assert input_value == "Filled Value"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_go_to_url():
    """
    Test: SimpleTestBase can navigate to URLs generically.
    
    Requirement: go_to() method must work with any web app.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://test.com")
        test = SimpleTestBase(page, config)
        
        # Mock page.goto to verify it's called
        called_url = None
        
        async def mock_goto(url, **kwargs):
            nonlocal called_url
            called_url = url
            # Return a mock response
            await page.set_content("<html><body>Test</body></html>")
        
        page.goto = mock_goto
        
        # go_to should work with relative URL
        await test.go_to("/path")
        assert called_url == "http://test.com/path"
        
        # go_to should work with absolute URL
        await test.go_to("http://absolute.com/path")
        assert called_url == "http://absolute.com/path"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_wait_for_element():
    """
    Test: SimpleTestBase can wait for elements generically.
    
    Requirement: wait_for() method must work with any web app.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        test = SimpleTestBase(page, TestConfig())
        
        # Create page with delayed element
        await page.set_content("""
            <html>
                <body>
                    <div id="delayed" style="display:none;">Content</div>
                    <script>
                        setTimeout(() => {
                            document.getElementById('delayed').style.display = 'block';
                        }, 100);
                    </script>
                </body>
            </html>
        """)
        
        # wait_for should work
        await test.wait_for("#delayed", timeout=5000)
        
        # Verify element is visible
        element = page.locator("#delayed")
        assert await element.is_visible()
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_assert_text():
    """
    Test: SimpleTestBase can assert text content generically.
    
    Requirement: assert_text() method must work with any web app.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple HTML page with text
        await page.set_content("""
            <html>
                <body>
                    <div id="content">Expected Text</div>
                </body>
            </html>
        """)
        
        test = SimpleTestBase(page, TestConfig())
        
        # assert_text should work
        await test.assert_text("#content", "Expected Text")
        
        # Should raise error if text doesn't match
        with pytest.raises(AssertionError):
            await test.assert_text("#content", "Wrong Text")
        
        await context.close()
        await browser.close()

