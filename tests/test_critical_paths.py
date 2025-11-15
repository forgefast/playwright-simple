#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Critical Path Tests - Playwright Simple

These tests MUST ALWAYS pass. They are smoke tests that validate
core functionality hasn't been broken.
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


# ============================================================================
# PROJECT-SPECIFIC CRITICAL TESTS
# ============================================================================
# These tests MUST ALWAYS pass - they validate core functionality

@pytest.mark.asyncio
async def test_critical_click_by_text(browser_page: Page):
    """CRITICAL: Click by text must work."""
    await browser_page.set_content("""
        <html>
            <body>
                <button>Click Me</button>
            </body>
        </html>
    """)
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.click(text="Click Me")
    
    assert result is True, "CRITICAL: Click by text must work"


@pytest.mark.asyncio
async def test_critical_type_by_label(browser_page: Page):
    """CRITICAL: Type by label must work."""
    await browser_page.set_content("""
        <html>
            <body>
                <label for="test-input">Test Input</label>
                <input id="test-input" type="text" />
            </body>
        </html>
    """)
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.type_text(text="Test Value", into="Test Input")
    
    assert result is True, "CRITICAL: Type by label must work"
    
    # Verify value was set
    value = await browser_page.evaluate("document.getElementById('test-input').value")
    assert value == "Test Value", f"CRITICAL: Value must be set correctly, got '{value}'"


@pytest.mark.asyncio
async def test_critical_submit_form(browser_page: Page):
    """CRITICAL: Form submission must work."""
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
    
    assert result is True, "CRITICAL: Form submission must work"


@pytest.mark.asyncio
async def test_critical_full_login_flow(browser_page: Page):
    """CRITICAL: Complete login flow (email + password + submit) must work."""
    await browser_page.set_content("""
        <html>
            <body>
                <form id="login-form">
                    <label for="email">Email</label>
                    <input id="email" type="email" name="email" />
                    
                    <label for="password">Password</label>
                    <input id="password" type="password" name="password" />
                    
                    <button type="submit">Login</button>
                </form>
            </body>
        </html>
    """)
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    
    # Type email
    result = await interactions.type_text(text="test@example.com", into="Email")
    assert result is True, "CRITICAL: Email typing must work"
    
    email_value = await browser_page.evaluate("document.getElementById('email').value")
    assert email_value == "test@example.com", f"CRITICAL: Email must be set, got '{email_value}'"
    
    # Type password
    result = await interactions.type_text(text="password123", into="Password")
    assert result is True, "CRITICAL: Password typing must work"
    
    password_value = await browser_page.evaluate("document.getElementById('password').value")
    assert password_value == "password123", f"CRITICAL: Password must be set, got '{password_value}'"
    
    # Submit form
    result = await interactions.submit_form(button_text="Login")
    assert result is True, "CRITICAL: Form submission must work"


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def test_imports_work():
    """CRITICAL: Validate that critical imports work."""
    from playwright_simple.core.playwright_commands.element_interactions import ElementInteractions
    # yaml_actions removed - use Recorder instead
    from playwright_simple.core.recorder.recorder import Recorder
    from playwright_simple.core.recorder import event_capture
    
    assert ElementInteractions is not None, "CRITICAL: ElementInteractions must import"
    assert Recorder is not None, "CRITICAL: Recorder must import (replaces yaml_actions)"
    assert event_capture is not None, "CRITICAL: event_capture module must import"


def test_basic_functionality():
    """CRITICAL: Validate basic functionality exists."""
    from playwright_simple.core.playwright_commands.element_interactions import ElementInteractions
    
    # Check that critical methods exist
    assert hasattr(ElementInteractions, 'click'), "CRITICAL: click method must exist"
    assert hasattr(ElementInteractions, 'type_text'), "CRITICAL: type_text method must exist"
    assert hasattr(ElementInteractions, 'submit_form'), "CRITICAL: submit_form method must exist"

