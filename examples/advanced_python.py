#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Python test example for playwright-simple.

Demonstrates advanced features like drag-and-drop, scrolling, and complex assertions.
"""

import asyncio
from playwright_simple import TestRunner, TestConfig


async def test_drag_and_drop(page, test):
    """Test drag and drop functionality."""
    await test.go_to("/kanban")
    
    # Drag item from "To Do" to "In Progress"
    await test.drag(
        source='[data-status="todo"] .task-item:first-child',
        target='[data-status="in-progress"]',
        description="Move task to In Progress"
    )
    
    # Assert task moved
    await test.assert_count('[data-status="in-progress"] .task-item', 1)


async def test_scrolling(page, test):
    """Test scrolling functionality."""
    await test.go_to("/long-page")
    
    # Scroll down
    await test.scroll(direction="down", amount=500)
    await test.wait(0.5)
    
    # Scroll up
    await test.scroll(direction="up", amount=300)
    await test.wait(0.5)
    
    # Scroll specific element
    await test.scroll(selector=".scrollable-container", direction="down", amount=200)


async def test_complex_assertions(page, test):
    """Test complex assertion scenarios."""
    await test.go_to("/products")
    
    # Assert element is visible
    await test.assert_visible('.product-list', "Product list")
    
    # Assert element count
    await test.assert_count('.product-item', 10, "Product items")
    
    # Assert attribute value
    await test.assert_attr(
        selector='.product-item:first-child',
        attribute="data-id",
        expected="12345",
        description="Product ID"
    )
    
    # Assert text content
    await test.assert_text('.product-title', "Featured Product")


async def test_screenshots(page, test):
    """Test screenshot functionality."""
    await test.go_to("/dashboard")
    
    # Manual screenshot
    await test.screenshot("dashboard_initial")
    
    # Screenshot of specific element
    await test.screenshot(element=".dashboard-widget", name="widget")
    
    # Full page screenshot
    await test.screenshot(name="dashboard_full", full_page=True)


async def test_wait_conditions(page, test):
    """Test various wait conditions."""
    await test.go_to("/dynamic-content")
    
    # Wait for element to appear
    await test.wait_for('.dynamic-element', state="visible", description="Dynamic element")
    
    # Wait for text to appear
    await test.wait_for_text('.status-message', "Content loaded", description="Status message")
    
    # Wait for URL change
    await test.click('a.nav-link', "Navigation link")
    await test.wait_for_url("/new-page")


if __name__ == "__main__":
    config = TestConfig(
        base_url="http://localhost:8000",
        cursor_style="dot",
        cursor_color="#ff0000",
        video_enabled=True,
        video_quality="high",
        screenshots_auto=True,
        screenshots_full_page=True,
    )
    
    runner = TestRunner(config=config)
    
    asyncio.run(runner.run_all([
        ("01_drag_and_drop", test_drag_and_drop),
        ("02_scrolling", test_scrolling),
        ("03_complex_assertions", test_complex_assertions),
        ("04_screenshots", test_screenshots),
        ("05_wait_conditions", test_wait_conditions),
    ]))


