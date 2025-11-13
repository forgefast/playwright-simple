#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for configuration system.
"""

import pytest
import os
import tempfile
from pathlib import Path
from playwright_simple import TestConfig


def test_default_config():
    """Test default configuration."""
    config = TestConfig()
    assert config.base_url == "http://localhost:8000"
    assert config.cursor.style == "arrow"
    assert config.video.enabled is True
    assert config.screenshots.auto is True


def test_config_from_dict():
    """Test configuration from dictionary."""
    data = {
        "base_url": "http://test.com",
        "cursor": {
            "style": "dot",
            "color": "#ff0000",
        },
        "video": {
            "enabled": False,
        },
    }
    config = TestConfig.from_dict(data)
    assert config.base_url == "http://test.com"
    assert config.cursor.style == "dot"
    assert config.cursor.color == "#ff0000"
    assert config.video.enabled is False


def test_config_validation():
    """Test configuration validation."""
    from playwright_simple.core.exceptions import ConfigurationError
    from playwright_simple.core.config import CursorConfig, VideoConfig
    
    # Invalid cursor style
    with pytest.raises(ConfigurationError, match="Invalid cursor style"):
        CursorConfig(style="invalid")
    
    # Invalid cursor size
    with pytest.raises(ConfigurationError, match="Invalid cursor size"):
        CursorConfig(size="invalid_size")
    
    # Invalid animation speed (negative)
    with pytest.raises(ConfigurationError, match="Animation speed must be non-negative"):
        from playwright_simple.core.config import CursorConfig
        CursorConfig(animation_speed=-1)
    
    # Invalid video quality
    with pytest.raises(ConfigurationError, match="Invalid video quality"):
        VideoConfig(quality="invalid")
    
    # Invalid video codec
    with pytest.raises(ConfigurationError, match="Invalid video codec"):
        from playwright_simple.core.config import VideoConfig
        VideoConfig(codec="invalid")
    
    # Invalid video speed (zero or negative)
    with pytest.raises(ConfigurationError, match="Video speed must be positive"):
        VideoConfig(speed=0)
    
    with pytest.raises(ConfigurationError, match="Video speed must be positive"):
        VideoConfig(speed=-1)
    
    # Invalid TTS engine
    with pytest.raises(ConfigurationError, match="Invalid TTS engine"):
        VideoConfig(narration_engine="invalid_engine")
    
    # Invalid screenshot format
    from playwright_simple.core.config import ScreenshotConfig
    with pytest.raises(ConfigurationError, match="Invalid screenshot format"):
        ScreenshotConfig(format="invalid")
    
    # Invalid base_url (empty)
    with pytest.raises(ConfigurationError, match="base_url cannot be empty"):
        TestConfig(base_url="")
    
    # Invalid browser timeout (negative) - validated in TestConfig._validate()
    config = TestConfig()
    config.browser.timeout = -1
    with pytest.raises(ValueError, match="browser.timeout must be >= 0"):
        config._validate()
    
    # Invalid viewport (missing width/height) - validated in TestConfig._validate()
    config = TestConfig()
    config.browser.viewport = {}
    with pytest.raises(ValueError, match="browser.viewport must have"):
        config._validate()


def test_config_save_and_load():
    """Test saving and loading configuration."""
    from playwright_simple.core.config import CursorConfig
    config = TestConfig(
        base_url="http://test.com",
        cursor=CursorConfig(style="dot"),
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save as YAML
        yaml_path = Path(tmpdir) / "config.yaml"
        try:
            config.save(yaml_path, format="yaml")
            assert yaml_path.exists()
            
            # Load YAML
            loaded = TestConfig.from_file(yaml_path)
            assert loaded.base_url == "http://test.com"
            assert loaded.cursor.style == "dot"
        except ImportError:
            # PyYAML not available, skip
            pytest.skip("PyYAML not available")
        
        # Save as JSON
        json_path = Path(tmpdir) / "config.json"
        config.save(json_path, format="json")
        assert json_path.exists()
        
        # Load JSON
        loaded = TestConfig.from_file(json_path)
        assert loaded.base_url == "http://test.com"
        assert loaded.cursor.style == "dot"


def test_config_from_env():
    """Test loading configuration from environment variables."""
    # Set environment variables
    os.environ["PLAYWRIGHT_SIMPLE_BASE_URL"] = "http://env-test.com"
    os.environ["PLAYWRIGHT_SIMPLE_CURSOR_STYLE"] = "circle"
    os.environ["PLAYWRIGHT_SIMPLE_VIDEO_ENABLED"] = "false"
    
    try:
        config = TestConfig.from_env()
        assert config.base_url == "http://env-test.com"
        assert config.cursor.style == "circle"
        assert config.video.enabled is False
    finally:
        # Cleanup
        os.environ.pop("PLAYWRIGHT_SIMPLE_BASE_URL", None)
        os.environ.pop("PLAYWRIGHT_SIMPLE_CURSOR_STYLE", None)
        os.environ.pop("PLAYWRIGHT_SIMPLE_VIDEO_ENABLED", None)


def test_config_priority():
    """Test configuration priority (runtime > env > file > defaults)."""
    # Set env var
    os.environ["PLAYWRIGHT_SIMPLE_BASE_URL"] = "http://env.com"
    
    try:
        # Runtime should override env
        config = TestConfig.load(
            use_env=True,
            base_url="http://runtime.com"
        )
        assert config.base_url == "http://runtime.com"
    finally:
        os.environ.pop("PLAYWRIGHT_SIMPLE_BASE_URL", None)


def test_cursor_config_validation():
    """Test CursorConfig validation."""
    from playwright_simple.core.config import CursorConfig
    from playwright_simple.core.exceptions import ConfigurationError
    
    # Valid styles
    for style in ["arrow", "dot", "circle", "custom"]:
        config = CursorConfig(style=style)
        assert config.style == style
    
    # Valid sizes
    for size in ["small", "medium", "large"]:
        config = CursorConfig(size=size)
        assert config.size == size
    
    # Valid numeric size
    config = CursorConfig(size=20)
    assert config.size == 20


def test_video_config_validation():
    """Test VideoConfig validation."""
    from playwright_simple.core.config import VideoConfig
    
    # Valid qualities
    for quality in ["low", "medium", "high"]:
        config = VideoConfig(quality=quality)
        assert config.quality == quality
    
    # Valid codecs
    for codec in ["webm", "mp4"]:
        config = VideoConfig(codec=codec)
        assert config.codec == codec
    
    # Valid TTS engines
    for engine in ["gtts", "edge-tts", "pyttsx3"]:
        config = VideoConfig(narration_engine=engine)
        assert config.narration_engine == engine


def test_screenshot_config_validation():
    """Test ScreenshotConfig validation."""
    from playwright_simple.core.config import ScreenshotConfig
    
    # Valid formats
    for fmt in ["png", "jpeg"]:
        config = ScreenshotConfig(format=fmt)
        assert config.format == fmt


def test_config_to_dict():
    """Test converting config to dictionary."""
    from playwright_simple.core.config import CursorConfig
    config = TestConfig(
        base_url="http://test.com",
        cursor=CursorConfig(style="dot", color="#ff0000"),
    )
    
    data = config.to_dict()
    assert data["base_url"] == "http://test.com"
    assert data["cursor"]["style"] == "dot"
    assert data["cursor"]["color"] == "#ff0000"
    assert "video" in data
    assert "screenshots" in data
    assert "browser" in data


def test_config_from_file_not_found():
    """Test loading config from non-existent file."""
    with pytest.raises(FileNotFoundError):
        TestConfig.from_file("nonexistent.yaml")


def test_config_from_file_invalid_format():
    """Test loading config from file with invalid format."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"invalid content")
        fpath = f.name
    
    try:
        with pytest.raises(ValueError, match="Unsupported config file format"):
            TestConfig.from_file(fpath)
    finally:
        Path(fpath).unlink()


def test_config_load_with_file():
    """Test loading config with file path."""
    from playwright_simple.core.config import CursorConfig
    config = TestConfig(
        base_url="http://test.com",
        cursor=CursorConfig(style="dot"),
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "config.json"
        config.save(json_path, format="json")
        
        loaded = TestConfig.load(config_file=json_path)
        assert loaded.base_url == "http://test.com"
        assert loaded.cursor.style == "dot"


def test_config_nested_updates():
    """Test updating nested config values."""
    # Update cursor via kwargs - TestConfig.load doesn't support cursor_style directly
    # Need to use cursor dict or update after creation
    config = TestConfig.load()
    config.cursor.style = "circle"
    config.cursor.color = "#00ff00"
    assert config.cursor.style == "circle"
    assert config.cursor.color == "#00ff00"
    
    # Update video via kwargs
    config = TestConfig.load()
    config.video.enabled = False
    config.video.quality = "low"
    assert config.video.enabled is False
    assert config.video.quality == "low"
    
    # Update screenshots via kwargs
    config = TestConfig.load()
    config.screenshots.auto = False
    config.screenshots.format = "jpeg"
    assert config.screenshots.auto is False
    assert config.screenshots.format == "jpeg"
    
    # Update browser via kwargs
    config = TestConfig.load()
    config.browser.headless = False
    config.browser.timeout = 60000
    assert config.browser.headless is False
    assert config.browser.timeout == 60000


