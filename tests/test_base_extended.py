#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extended tests for SimpleTestBase class.
"""

import pytest
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_simple import SimpleTestBase, TestConfig


@pytest.mark.asyncio
async def test_back():
    """Test back navigation."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("data:text/html,<html><body>Page 1</body></html>")
        await page.goto("data:text/html,<html><body>Page 2</body></html>")
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.back()
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_forward():
    """Test forward navigation."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("data:text/html,<html><body>Page 1</body></html>")
        await page.goto("data:text/html,<html><body>Page 2</body></html>")
        await page.go_back()
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.forward()
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_refresh():
    """Test page refresh."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("data:text/html,<html><body>Test</body></html>")
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.refresh()
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_click():
    """Test click method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<button id="test-btn">Click me</button>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.click('#test-btn', "Test button")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_double_click():
    """Test double click method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<button id="test-btn">Double click me</button>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.double_click('#test-btn', "Test button")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_right_click():
    """Test right click method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<button id="test-btn">Right click me</button>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.right_click('#test-btn', "Test button")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_type():
    """Test type method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<input type="text" id="test-input" />')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.type('#test-input', 'test text', "Test input")
        
        value = await page.input_value('#test-input')
        assert value == 'test text'
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_select():
    """Test select method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('''
            <select id="test-select">
                <option value="1">Option 1</option>
                <option value="2">Option 2</option>
            </select>
        ''')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.select('#test-select', 'Option 2', "Test select")
        
        value = await page.input_value('#test-select')
        assert value == '2'
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_hover():
    """Test hover method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<button id="test-btn">Hover me</button>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.hover('#test-btn', "Test button")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_assert_text():
    """Test assert_text method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<div id="test-div">Hello World</div>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.assert_text('#test-div', 'Hello', "Test div")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_assert_visible():
    """Test assert_visible method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<div id="test-div">Visible</div>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.assert_visible('#test-div', "Test div")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_assert_url():
    """Test assert_url method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("data:text/html,<html><body>Test</body></html>")
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        # Use pattern that matches the actual URL (assert_url uses 'in' check)
        await test.assert_url('data:text/html')
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_assert_count():
    """Test assert_count method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('''
            <div class="item">Item 1</div>
            <div class="item">Item 2</div>
            <div class="item">Item 3</div>
        ''')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.assert_count('.item', 3, "Items")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_assert_attr():
    """Test assert_attr method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<input type="text" id="test-input" value="test" />')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.assert_attr('#test-input', 'value', 'test', "Test input")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_fill_form():
    """Test fill_form method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('''
            <input type="text" name="name" />
            <input type="text" name="email" />
        ''')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.fill_form({
            'input[name="name"]': 'John',
            'input[name="email"]': 'john@example.com'
        })
        
        name_value = await page.input_value('input[name="name"]')
        email_value = await page.input_value('input[name="email"]')
        
        assert name_value == 'John'
        assert email_value == 'john@example.com'
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_get_text():
    """Test get_text method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<div id="test-div">Hello World</div>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        text = await test.get_text('#test-div', "Test div")
        assert 'Hello' in text
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_get_attr():
    """Test get_attr method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<input type="text" id="test-input" value="test" />')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        value = await test.get_attr('#test-input', 'value', "Test input")
        assert value == 'test'
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_is_visible():
    """Test is_visible method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<div id="test-div">Visible</div>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        visible = await test.is_visible('#test-div', "Test div")
        assert visible is True
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_is_enabled():
    """Test is_enabled method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<button id="test-btn">Enabled</button>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        enabled = await test.is_enabled('#test-btn', "Test button")
        assert enabled is True
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_wait_for():
    """Test wait_for method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        # Set content after a delay
        import asyncio
        async def delayed_content():
            await asyncio.sleep(0.1)
            await page.set_content('<div id="test-div">Delayed</div>')
        
        asyncio.create_task(delayed_content())
        await test.wait_for('#test-div', timeout=5000)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_wait_for_url():
    """Test wait_for_url method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        # Navigate to a URL first
        target_url = "data:text/html,<html><body>Test</body></html>"
        await page.goto(target_url)
        
        # wait_for_url should work immediately since we're already on the URL
        # Use the exact URL or a pattern that matches
        await test.wait_for_url(target_url, timeout=1000)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_wait_for_text():
    """Test wait_for_text method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await page.set_content('<div id="test-div">Hello World</div>')
        await test.wait_for_text('#test-div', 'Hello', timeout=5000)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_go_to_invalid_url():
    """Test go_to with invalid URL."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        from playwright_simple.core.exceptions import NavigationError
        
        with pytest.raises(NavigationError):
            await test.go_to("invalid-url")
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_navigate():
    """Test navigate method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('''
            <a href="#" data-menu="Menu1">Menu1</a>
            <a href="#" data-menu="Menu2">Menu2</a>
        ''')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.navigate(["Menu1"])
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_scroll():
    """Test scroll method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<div style="height: 2000px;">Long content</div>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        await test.scroll(direction="down", amount=500)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_screenshot():
    """Test screenshot method."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<div>Test content</div>')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TestConfig(screenshots=TestConfig().screenshots)
            config.screenshots.dir = tmpdir
            test = SimpleTestBase(page, config, "test_screenshot")
            
            screenshot_path = await test.screenshot("test_screenshot")
            assert screenshot_path.exists()
        
        await context.close()
        await browser.close()

