#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for element finder.

These tests ensure element finding logic works correctly.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright, Page

from playwright_simple.core.playwright_commands.element_interactions.element_finder import ElementFinder


@pytest.fixture
async def browser_page():
    """Create a browser page for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        yield page
        await browser.close()


@pytest.mark.asyncio
async def test_find_by_text_submit_button(browser_page: Page):
    """Test finding submit button by text."""
    await browser_page.set_content("""
        <html>
            <body>
                <form>
                    <button type="submit">Submit</button>
                </form>
            </body>
        </html>
    """)
    
    finder = ElementFinder(browser_page)
    result = await finder.find_by_text("Submit")
    
    assert result is not None, "Should find submit button"
    assert result.get('found') is True, "Result should indicate found"
    assert result.get('isSubmit') is True, "Should identify as submit button"


@pytest.mark.asyncio
async def test_find_input_by_label(browser_page: Page):
    """Test finding input by label text."""
    await browser_page.set_content("""
        <html>
            <body>
                <label for="email">Email</label>
                <input id="email" type="email" />
            </body>
        </html>
    """)
    
    finder = ElementFinder(browser_page)
    result = await finder.find_input_by_label("Email")
    
    assert result is not None, "Should find input by label"
    assert result.get('found') is True, "Result should indicate found"
    assert 'x' in result and 'y' in result, "Result should contain coordinates"


@pytest.mark.asyncio
async def test_find_submit_button(browser_page: Page):
    """Test finding submit button in form."""
    await browser_page.set_content("""
        <html>
            <body>
                <form>
                    <button type="submit">Submit Form</button>
                </form>
            </body>
        </html>
    """)
    
    finder = ElementFinder(browser_page)
    result = await finder.find_submit_button("Submit")
    
    assert result is not None, "Should find submit button"
    assert result.get('found') is True, "Result should indicate found"
    assert 'x' in result and 'y' in result, "Result should contain coordinates"
    assert 'text' in result, "Result should contain button text"

