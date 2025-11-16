#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for element interactions.

These tests prevent regressions in core functionality.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright, Page

from playwright_simple.core.playwright_commands.element_interactions import ElementInteractions


@pytest.fixture
async def browser_page():
    """Create a browser page for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        yield page
        await browser.close()


@pytest.mark.asyncio
async def test_click_by_text(browser_page: Page):
    """Test clicking element by text."""
    await browser_page.set_content("""
        <html>
            <body>
                <button>Click Me</button>
            </body>
        </html>
    """)
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.click(text="Click Me")
    
    assert result is True, "Click by text should succeed"


@pytest.mark.asyncio
async def test_click_by_selector(browser_page: Page):
    """Test clicking element by selector."""
    await browser_page.set_content("""
        <html>
            <body>
                <button id="test-btn">Test Button</button>
            </body>
        </html>
    """)
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.click(selector="#test-btn")
    
    assert result is True, "Click by selector should succeed"


@pytest.mark.asyncio
async def test_type_text(browser_page: Page):
    """Test typing text into input field."""
    await browser_page.set_content("""
        <html>
            <body>
                <label for="test-input">Test Input</label>
                <input id="test-input" type="text" />
            </body>
        </html>
    """)
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.type_text(text="Hello World", into="Test Input")
    
    assert result is True, "Type text should succeed"
    
    # Verify text was typed
    value = await browser_page.evaluate("document.getElementById('test-input').value")
    assert value == "Hello World", f"Expected 'Hello World', got '{value}'"


@pytest.mark.asyncio
async def test_type_text_by_selector(browser_page: Page):
    """Test typing text into input field by selector."""
    await browser_page.set_content("""
        <html>
            <body>
                <input id="test-input" type="text" />
            </body>
        </html>
    """)
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.type_text(text="Test", selector="#test-input")
    
    assert result is True, "Type text by selector should succeed"
    
    # Verify text was typed
    value = await browser_page.evaluate("document.getElementById('test-input').value")
    assert value == "Test", f"Expected 'Test', got '{value}'"


@pytest.mark.asyncio
async def test_submit_form(browser_page: Page):
    """Test form submission."""
    await browser_page.set_content("""
        <html>
            <body>
                <form id="test-form">
                    <input type="text" name="test" />
                    <button type="submit">Submit</button>
                </form>
            </body>
        </html>
    """)
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.submit_form(button_text="Submit")
    
    assert result is True, "Submit form should succeed"


@pytest.mark.asyncio
async def test_click_nonexistent_element(browser_page: Page):
    """Test clicking non-existent element returns False."""
    await browser_page.set_content("<html><body></body></html>")
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.click(text="Non Existent")
    
    assert result is False, "Click on non-existent element should return False"


@pytest.mark.asyncio
async def test_type_nonexistent_field(browser_page: Page):
    """Test typing into non-existent field returns False."""
    await browser_page.set_content("<html><body></body></html>")
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.type_text(text="Test", into="Non Existent")
    
    assert result is False, "Type into non-existent field should return False"

