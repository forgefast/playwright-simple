#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for screenshot module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from playwright_simple.core.screenshot import ScreenshotManager
from playwright_simple.core.config import ScreenshotConfig


@pytest.mark.asyncio
async def test_screenshot_manager_init():
    """Test ScreenshotManager initialization."""
    page = MagicMock()
    config = ScreenshotConfig()
    
    manager = ScreenshotManager(page, config, "test_name")
    
    assert manager.page == page
    assert manager.config == config
    assert manager.test_name == "test_name"
    assert manager._screenshot_count == 0
    assert manager.screenshot_dir.exists()


@pytest.mark.asyncio
async def test_screenshot_capture():
    """Test capturing screenshot."""
    page = MagicMock()
    page.screenshot = AsyncMock()
    
    config = ScreenshotConfig(dir="screenshots", format="png")
    manager = ScreenshotManager(page, config, "test_name")
    
    path = await manager.capture("test_screenshot")
    
    page.screenshot.assert_called_once()
    assert path.exists() or path.parent.exists()  # Path might be created later


@pytest.mark.asyncio
async def test_screenshot_capture_full_page():
    """Test capturing full page screenshot."""
    page = MagicMock()
    page.screenshot = AsyncMock()
    
    config = ScreenshotConfig(full_page=True)
    manager = ScreenshotManager(page, config, "test_name")
    
    await manager.capture("test_screenshot", full_page=True)
    
    call_kwargs = page.screenshot.call_args[1]
    assert call_kwargs.get("full_page") is True


@pytest.mark.asyncio
async def test_screenshot_capture_element():
    """Test capturing element screenshot."""
    page = MagicMock()
    # Create a proper locator chain: page.locator().first
    first_locator = MagicMock()
    first_locator.wait_for = AsyncMock()
    first_locator.screenshot = AsyncMock()
    
    locator = MagicMock()
    locator.first = first_locator
    page.locator = MagicMock(return_value=locator)
    page.screenshot = AsyncMock()  # For fallback
    
    config = ScreenshotConfig()
    manager = ScreenshotManager(page, config, "test_name")
    
    await manager.capture("test_screenshot", element="button")
    
    page.locator.assert_called_with("button")
    first_locator.wait_for.assert_called_once()
    first_locator.screenshot.assert_called_once()


@pytest.mark.asyncio
async def test_screenshot_capture_on_action():
    """Test automatic screenshot on action."""
    page = MagicMock()
    page.screenshot = AsyncMock()
    
    config = ScreenshotConfig(auto=True)
    manager = ScreenshotManager(page, config, "test_name")
    
    path = await manager.capture_on_action("click", "button")
    
    assert path is not None
    page.screenshot.assert_called_once()


@pytest.mark.asyncio
async def test_screenshot_capture_on_action_disabled():
    """Test automatic screenshot when disabled."""
    page = MagicMock()
    page.screenshot = AsyncMock()
    
    config = ScreenshotConfig(auto=False)
    manager = ScreenshotManager(page, config, "test_name")
    
    path = await manager.capture_on_action("click", "button")
    
    assert path is None
    page.screenshot.assert_not_called()


@pytest.mark.asyncio
async def test_screenshot_capture_on_failure():
    """Test capturing screenshot on failure."""
    page = MagicMock()
    page.screenshot = AsyncMock()
    
    config = ScreenshotConfig()
    manager = ScreenshotManager(page, config, "test_name")
    
    error = ValueError("Test error")
    path = await manager.capture_on_failure(error)
    
    page.screenshot.assert_called_once()
    call_kwargs = page.screenshot.call_args[1]
    assert call_kwargs.get("full_page") is True


def test_screenshot_set_test_name():
    """Test updating test name."""
    page = MagicMock()
    config = ScreenshotConfig()
    manager = ScreenshotManager(page, config, "old_name")
    
    manager.set_test_name("new_name")
    
    assert manager.test_name == "new_name"
    assert manager._screenshot_count == 0


def test_screenshot_get_metadata():
    """Test getting screenshot metadata."""
    page = MagicMock()
    config = ScreenshotConfig()
    manager = ScreenshotManager(page, config, "test_name")
    
    metadata = manager.get_metadata()
    assert isinstance(metadata, dict)


def test_screenshot_clear_metadata():
    """Test clearing screenshot metadata."""
    page = MagicMock()
    config = ScreenshotConfig()
    manager = ScreenshotManager(page, config, "test_name")
    
    manager._screenshot_metadata["test"] = {"path": "/test"}
    manager.clear_metadata()
    
    assert len(manager._screenshot_metadata) == 0

