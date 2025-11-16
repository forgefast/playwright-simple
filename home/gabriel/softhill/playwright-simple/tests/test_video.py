#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for video module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from playwright_simple.core.video import VideoManager
from playwright_simple.core.config import VideoConfig


def test_video_manager_init():
    """Test VideoManager initialization."""
    config = VideoConfig()
    manager = VideoManager(config)
    
    assert manager.config == config
    assert manager.video_dir == Path(config.dir)
    assert manager.video_dir.exists()


def test_video_manager_get_context_options():
    """Test getting context options."""
    config = VideoConfig(enabled=True, quality="high")
    manager = VideoManager(config)
    
    options = manager.get_context_options()
    assert "record_video_dir" in options
    assert "record_video_size" in options
    assert options["record_video_size"]["width"] == 1920
    assert options["record_video_size"]["height"] == 1080


def test_video_manager_get_context_options_disabled():
    """Test getting context options when disabled."""
    config = VideoConfig(enabled=False)
    manager = VideoManager(config)
    
    options = manager.get_context_options()
    assert options == {}


def test_video_manager_get_context_options_with_viewport():
    """Test getting context options with custom viewport."""
    config = VideoConfig(enabled=True)
    manager = VideoManager(config)
    
    viewport = {"width": 1280, "height": 720}
    options = manager.get_context_options(viewport=viewport)
    assert options["record_video_size"] == viewport


def test_video_manager_register_context():
    """Test registering browser context."""
    config = VideoConfig()
    manager = VideoManager(config)
    
    context = MagicMock()
    manager.register_context(context, "test_name")
    
    assert "test_name" in manager._recording_contexts
    assert manager._recording_contexts["test_name"] == context


@pytest.mark.asyncio
async def test_video_manager_pause():
    """Test pausing video recording."""
    config = VideoConfig(enabled=True)
    manager = VideoManager(config)
    
    context = MagicMock()
    manager.register_context(context, "test_name")
    
    await manager.pause("test_name")
    assert manager.is_paused("test_name") is True


@pytest.mark.asyncio
async def test_video_manager_pause_all():
    """Test pausing all video recordings."""
    config = VideoConfig(enabled=True)
    manager = VideoManager(config)
    
    context1 = MagicMock()
    context2 = MagicMock()
    manager.register_context(context1, "test1")
    manager.register_context(context2, "test2")
    
    await manager.pause()
    assert manager.is_paused() is True


@pytest.mark.asyncio
async def test_video_manager_resume():
    """Test resuming video recording."""
    config = VideoConfig(enabled=True)
    manager = VideoManager(config)
    
    context = MagicMock()
    manager.register_context(context, "test_name")
    manager._paused_contexts.add("test_name")
    
    await manager.resume("test_name")
    assert manager.is_paused("test_name") is False


@pytest.mark.asyncio
async def test_video_manager_resume_all():
    """Test resuming all video recordings."""
    config = VideoConfig(enabled=True)
    manager = VideoManager(config)
    
    context1 = MagicMock()
    context2 = MagicMock()
    manager.register_context(context1, "test1")
    manager.register_context(context2, "test2")
    manager._paused_contexts.update(["test1", "test2"])
    
    await manager.resume()
    assert manager.is_paused() is False


def test_video_manager_is_paused():
    """Test checking if recording is paused."""
    config = VideoConfig()
    manager = VideoManager(config)
    
    assert manager.is_paused() is False
    assert manager.is_paused("test_name") is False
    
    manager._paused_contexts.add("test_name")
    assert manager.is_paused("test_name") is True
    assert manager.is_paused() is True


@pytest.mark.asyncio
async def test_video_manager_stop_all():
    """Test stopping all video recordings."""
    config = VideoConfig()
    manager = VideoManager(config)
    
    context1 = MagicMock()
    context1.close = AsyncMock()
    context2 = MagicMock()
    context2.close = AsyncMock()
    
    manager.register_context(context1, "test1")
    manager.register_context(context2, "test2")
    manager._paused_contexts.add("test1")
    
    await manager.stop_all()
    
    context1.close.assert_called_once()
    context2.close.assert_called_once()
    assert len(manager._recording_contexts) == 0
    assert len(manager._paused_contexts) == 0


def test_video_manager_get_video_path():
    """Test getting video path."""
    config = VideoConfig(enabled=True, dir="videos")
    manager = VideoManager(config)
    
    # Create test video file
    test_video = manager.video_dir / "test_name.webm"
    test_video.parent.mkdir(parents=True, exist_ok=True)
    test_video.touch()
    
    try:
        path = manager.get_video_path("test_name")
        assert path == test_video
    finally:
        test_video.unlink()


def test_video_manager_get_video_path_not_found():
    """Test getting video path when file doesn't exist."""
    config = VideoConfig(enabled=True)
    manager = VideoManager(config)
    
    path = manager.get_video_path("nonexistent")
    assert path is None


def test_video_manager_get_video_path_disabled():
    """Test getting video path when disabled."""
    config = VideoConfig(enabled=False)
    manager = VideoManager(config)
    
    path = manager.get_video_path("test_name")
    assert path is None

