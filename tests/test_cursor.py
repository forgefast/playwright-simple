#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for cursor module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from playwright_simple.core.cursor import CursorManager
from playwright_simple.core.config import CursorConfig, TestConfig


@pytest.mark.asyncio
async def test_cursor_manager_init():
    """Test CursorManager initialization."""
    page = MagicMock()
    config = CursorConfig()
    
    manager = CursorManager(page, config)
    assert manager.page == page
    assert manager.config == config
    assert manager._injected is False
    assert manager._init_script_added is False


@pytest.mark.asyncio
async def test_cursor_inject():
    """Test cursor injection."""
    page = MagicMock()
    page.viewport_size = {"width": 1920, "height": 1080}
    page.add_init_script = AsyncMock()
    page.evaluate = AsyncMock(return_value=None)
    
    config = CursorConfig()
    manager = CursorManager(page, config)
    
    await manager.inject()
    
    assert manager._injected is True
    assert manager._init_script_added is True
    page.add_init_script.assert_called_once()
    assert page.evaluate.call_count >= 1


@pytest.mark.asyncio
async def test_cursor_inject_force():
    """Test cursor injection with force flag."""
    page = MagicMock()
    page.viewport_size = {"width": 1920, "height": 1080}
    page.add_init_script = AsyncMock()
    page.evaluate = AsyncMock(return_value=None)
    
    config = CursorConfig()
    manager = CursorManager(page, config)
    manager._injected = True
    manager._init_script_added = True
    
    await manager.inject(force=True)
    
    # Should still call evaluate even if already injected
    assert page.evaluate.call_count >= 1


@pytest.mark.asyncio
async def test_cursor_move_to():
    """Test cursor movement."""
    page = MagicMock()
    page.viewport_size = {"width": 1920, "height": 1080}
    page.evaluate = AsyncMock(return_value={"x": 100, "y": 200, "exists": True})
    
    config = CursorConfig()
    manager = CursorManager(page, config)
    manager._injected = True
    
    await manager.move_to(500, 600)
    
    # Should call evaluate for getting position and moving
    assert page.evaluate.call_count >= 2


@pytest.mark.asyncio
async def test_cursor_move_to_no_existing_cursor():
    """Test cursor movement when cursor doesn't exist."""
    page = MagicMock()
    page.viewport_size = {"width": 1920, "height": 1080}
    page.evaluate = AsyncMock(return_value={"x": 0, "y": 0, "exists": False})
    
    config = CursorConfig()
    manager = CursorManager(page, config)
    manager._injected = True
    
    await manager.move_to(500, 600)
    
    # Should still move cursor
    assert page.evaluate.call_count >= 2


@pytest.mark.asyncio
async def test_cursor_show_click_effect():
    """Test click effect display."""
    page = MagicMock()
    page.viewport_size = {"width": 1920, "height": 1080}
    page.evaluate = AsyncMock(return_value={"success": True})
    
    config = CursorConfig(click_effect=True)
    manager = CursorManager(page, config)
    manager._injected = True
    
    await manager.show_click_effect(100, 200)
    
    page.evaluate.assert_called()


@pytest.mark.asyncio
async def test_cursor_show_click_effect_disabled():
    """Test click effect when disabled."""
    page = MagicMock()
    page.evaluate = AsyncMock()
    
    config = CursorConfig(click_effect=False)
    manager = CursorManager(page, config)
    
    await manager.show_click_effect(100, 200)
    
    # Should not call evaluate when disabled
    page.evaluate.assert_not_called()


@pytest.mark.asyncio
async def test_cursor_show_hover_effect():
    """Test hover effect display."""
    page = MagicMock()
    page.viewport_size = {"width": 1920, "height": 1080}
    page.evaluate = AsyncMock()
    
    config = CursorConfig(hover_effect=True)
    manager = CursorManager(page, config)
    manager._injected = True
    
    await manager.show_hover_effect(100, 200, show=True)
    
    page.evaluate.assert_called()


@pytest.mark.asyncio
async def test_cursor_show_hover_effect_disabled():
    """Test hover effect when disabled."""
    page = MagicMock()
    page.evaluate = AsyncMock()
    
    config = CursorConfig(hover_effect=False)
    manager = CursorManager(page, config)
    
    await manager.show_hover_effect(100, 200, show=True)
    
    # Should not call evaluate when disabled
    page.evaluate.assert_not_called()


@pytest.mark.asyncio
async def test_cursor_get_cursor_css_arrow():
    """Test CSS generation for arrow style."""
    page = MagicMock()
    config = CursorConfig(style="arrow", color="#ff0000", size="medium")
    manager = CursorManager(page, config)
    
    css = manager._get_cursor_css()
    assert "border-left" in css
    assert "border-right" in css
    assert "border-top" in css
    assert "#ff0000" in css


@pytest.mark.asyncio
async def test_cursor_get_cursor_css_dot():
    """Test CSS generation for dot style."""
    page = MagicMock()
    config = CursorConfig(style="dot", color="#00ff00", size="large")
    manager = CursorManager(page, config)
    
    css = manager._get_cursor_css()
    assert "border-radius: 50%" in css
    assert "#00ff00" in css


@pytest.mark.asyncio
async def test_cursor_get_cursor_css_circle():
    """Test CSS generation for circle style."""
    page = MagicMock()
    config = CursorConfig(style="circle", color="#0000ff", size="small")
    manager = CursorManager(page, config)
    
    css = manager._get_cursor_css()
    assert "border-radius: 50%" in css
    assert "background: transparent" in css
    assert "#0000ff" in css


@pytest.mark.asyncio
async def test_cursor_get_cursor_css_custom():
    """Test CSS generation for custom style."""
    page = MagicMock()
    config = CursorConfig(style="custom", color="#ffff00", size=30)
    manager = CursorManager(page, config)
    
    css = manager._get_cursor_css()
    assert "#ffff00" in css


def test_cursor_get_size_pixels():
    """Test size conversion to pixels."""
    page = MagicMock()
    config = CursorConfig(size="small")
    manager = CursorManager(page, config)
    
    assert manager._get_size_pixels() == 12
    
    config.size = "medium"
    assert manager._get_size_pixels() == 20
    
    config.size = "large"
    assert manager._get_size_pixels() == 32
    
    config.size = 25
    assert manager._get_size_pixels() == 25


@pytest.mark.asyncio
async def test_cursor_get_click_effect_css():
    """Test click effect CSS generation."""
    page = MagicMock()
    config = CursorConfig(click_effect_color="#ff00ff")
    manager = CursorManager(page, config)
    
    css = manager._get_click_effect_css()
    assert "#ff00ff" in css
    assert "border-radius: 50%" in css


@pytest.mark.asyncio
async def test_cursor_ensure_cursor_exists():
    """Test ensuring cursor exists."""
    page = MagicMock()
    page.viewport_size = {"width": 1920, "height": 1080}
    page.evaluate = AsyncMock(return_value=None)
    
    config = CursorConfig()
    manager = CursorManager(page, config)
    
    await manager._ensure_cursor_exists()
    
    page.evaluate.assert_called()


@pytest.mark.asyncio
async def test_cursor_ensure_cursor_exists_no_viewport():
    """Test ensuring cursor exists without viewport."""
    page = MagicMock()
    page.viewport_size = None
    page.evaluate = AsyncMock(return_value=None)
    
    config = CursorConfig()
    manager = CursorManager(page, config)
    
    await manager._ensure_cursor_exists()
    
    page.evaluate.assert_called()

