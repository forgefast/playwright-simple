#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic Python test example for playwright-simple.

This example demonstrates basic usage of the library.
"""

import asyncio
from playwright_simple import TestRunner, TestConfig


async def test_basic_login(page, test):
    """Basic login test."""
    # Navigate to login page
    await test.go_to("/login")
    
    # Fill login form
    await test.type('input[name="username"]', "admin", "Username field")
    await test.type('input[name="password"]', "password123", "Password field")
    
    # Click login button
    await test.click('button[type="submit"]', "Login button")
    
    # Wait for dashboard
    await test.wait_for_url("/dashboard")
    
    # Assert we're logged in
    await test.assert_text(".user-name", "admin")


async def test_form_filling(page, test):
    """Test form filling helper."""
    await test.go_to("/form")
    
    # Use fill_form helper
    await test.fill_form({
        'input[name="name"]': "John Doe",
        'input[name="email"]': "john@example.com",
        'input[name="phone"]': "1234567890",
    })
    
    # Submit form
    await test.click('button[type="submit"]', "Submit button")
    
    # Assert success message
    await test.assert_text(".success-message", "Form submitted successfully")


async def test_navigation(page, test):
    """Test navigation methods."""
    await test.go_to("/")
    
    # Navigate through menus
    await test.navigate(["Products", "Electronics", "Phones"])
    
    # Go back
    await test.back()
    
    # Go forward
    await test.forward()
    
    # Refresh page
    await test.refresh()


if __name__ == "__main__":
    # Configuration
    config = TestConfig(
        base_url="http://localhost:8000",
        cursor_style="arrow",
        cursor_color="#007bff",
        video_enabled=True,
        screenshots_auto=True,
    )
    
    # Create runner
    runner = TestRunner(config=config)
    
    # Run tests
    asyncio.run(runner.run_all([
        ("01_basic_login", test_basic_login),
        ("02_form_filling", test_form_filling),
        ("03_navigation", test_navigation),
    ]))


