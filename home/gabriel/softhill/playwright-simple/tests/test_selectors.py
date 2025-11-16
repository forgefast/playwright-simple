#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for selectors module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from playwright_simple.core.selectors import SelectorManager


@pytest.mark.asyncio
async def test_selector_manager_init():
    """Test SelectorManager initialization."""
    page = MagicMock()
    manager = SelectorManager(page, timeout=5000, retry_count=2)
    
    assert manager.page == page
    assert manager.timeout == 5000
    assert manager.retry_count == 2


@pytest.mark.asyncio
async def test_selector_find_element():
    """Test finding element."""
    page = MagicMock()
    # Create proper locator chain: page.locator().first
    first_locator = MagicMock()
    first_locator.wait_for = AsyncMock()
    first_locator.count = AsyncMock(return_value=1)
    
    locator = MagicMock()
    locator.first = first_locator
    page.locator = MagicMock(return_value=locator)
    
    manager = SelectorManager(page, retry_count=0)  # Disable retries for faster test
    
    result = await manager.find_element("button")
    
    assert result == first_locator
    page.locator.assert_called_with("button")
    first_locator.wait_for.assert_called_once()


@pytest.mark.asyncio
async def test_selector_find_element_not_found():
    """Test finding element that doesn't exist."""
    page = MagicMock()
    locator = MagicMock()
    locator.wait_for = AsyncMock(side_effect=Exception("Not found"))
    locator.count = AsyncMock(return_value=0)
    page.locator = MagicMock(return_value=locator)
    
    manager = SelectorManager(page, retry_count=0)
    
    result = await manager.find_element("button")
    
    assert result is None


@pytest.mark.asyncio
async def test_selector_wait_for_element():
    """Test waiting for element."""
    page = MagicMock()
    # Create proper locator chain: page.locator().first
    first_locator = MagicMock()
    first_locator.wait_for = AsyncMock()
    first_locator.count = AsyncMock(return_value=1)
    
    locator = MagicMock()
    locator.first = first_locator
    page.locator = MagicMock(return_value=locator)
    
    manager = SelectorManager(page, timeout=1000, retry_count=0)  # Short timeout for faster test
    
    result = await manager.wait_for_element("button")
    
    assert result == first_locator


@pytest.mark.asyncio
async def test_selector_wait_for_element_timeout():
    """Test waiting for element that times out."""
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    
    page = MagicMock()
    locator = MagicMock()
    locator.wait_for = AsyncMock(side_effect=Exception("Timeout"))
    locator.count = AsyncMock(return_value=0)
    page.locator = MagicMock(return_value=locator)
    
    manager = SelectorManager(page, retry_count=0)
    
    with pytest.raises(PlaywrightTimeoutError):
        await manager.wait_for_element("button")


def test_selector_by_text():
    """Test creating selector by text."""
    page = MagicMock()
    manager = SelectorManager(page)
    
    selector = manager.by_text("Click me")
    assert selector == 'text=Click me'
    
    selector = manager.by_text("Click me", exact=True)
    assert selector == 'text="Click me"'


def test_selector_by_role():
    """Test creating selector by role."""
    page = MagicMock()
    manager = SelectorManager(page)
    
    selector = manager.by_role("button")
    assert selector == 'role=button'
    
    selector = manager.by_role("button", name="Submit")
    assert 'role=button' in selector
    assert 'name="Submit"' in selector


def test_selector_by_test_id():
    """Test creating selector by test ID."""
    page = MagicMock()
    manager = SelectorManager(page)
    
    selector = manager.by_test_id("submit-button")
    assert selector == '[data-testid="submit-button"]'


def test_selector_by_label():
    """Test creating selector by label."""
    page = MagicMock()
    manager = SelectorManager(page)
    
    selector = manager.by_label("Username")
    assert selector == 'label:has-text("Username")'


def test_selector_generate_alternatives():
    """Test generating alternative selectors."""
    page = MagicMock()
    manager = SelectorManager(page)
    
    # Test button alternatives
    alternatives = manager._generate_alternatives("button")
    assert '[role="button"]' in alternatives
    
    # Test link alternatives
    alternatives = manager._generate_alternatives("a.link")
    assert '[role="link"]' in alternatives

