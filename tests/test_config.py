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
    # Invalid cursor style
    with pytest.raises(ValueError, match="Invalid cursor style"):
        TestConfig(cursor_style="invalid")
    
    # Invalid video quality
    with pytest.raises(ValueError, match="Invalid video quality"):
        TestConfig(video_quality="invalid")
    
    # Invalid screenshot format
    with pytest.raises(ValueError, match="Invalid screenshot format"):
        TestConfig(screenshots_format="invalid")


def test_config_save_and_load():
    """Test saving and loading configuration."""
    config = TestConfig(
        base_url="http://test.com",
        cursor_style="dot",
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


