#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for exceptions module.
"""

import pytest
from playwright_simple.core.exceptions import (
    PlaywrightSimpleError,
    ElementNotFoundError,
    NavigationError,
    VideoProcessingError,
    ConfigurationError,
    TTSGenerationError,
)


def test_base_exception():
    """Test base exception class."""
    error = PlaywrightSimpleError("Test error")
    assert isinstance(error, Exception)
    assert str(error) == "Test error"


def test_exception_hierarchy():
    """Test that all exceptions inherit from PlaywrightSimpleError."""
    assert issubclass(ElementNotFoundError, PlaywrightSimpleError)
    assert issubclass(NavigationError, PlaywrightSimpleError)
    assert issubclass(VideoProcessingError, PlaywrightSimpleError)
    assert issubclass(ConfigurationError, PlaywrightSimpleError)
    assert issubclass(TTSGenerationError, PlaywrightSimpleError)


def test_element_not_found_error():
    """Test ElementNotFoundError."""
    error = ElementNotFoundError("Element not found")
    assert isinstance(error, PlaywrightSimpleError)
    assert str(error) == "Element not found"


def test_navigation_error():
    """Test NavigationError."""
    error = NavigationError("Navigation failed")
    assert isinstance(error, PlaywrightSimpleError)
    assert str(error) == "Navigation failed"


def test_video_processing_error():
    """Test VideoProcessingError."""
    error = VideoProcessingError("Video processing failed")
    assert isinstance(error, PlaywrightSimpleError)
    assert str(error) == "Video processing failed"


def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError("Invalid configuration")
    assert isinstance(error, PlaywrightSimpleError)
    assert str(error) == "Invalid configuration"


def test_tts_generation_error():
    """Test TTSGenerationError."""
    error = TTSGenerationError("TTS generation failed")
    assert isinstance(error, PlaywrightSimpleError)
    assert str(error) == "TTS generation failed"


def test_exception_raising():
    """Test that exceptions can be raised and caught."""
    with pytest.raises(ElementNotFoundError):
        raise ElementNotFoundError("Test")
    
    with pytest.raises(NavigationError):
        raise NavigationError("Test")
    
    with pytest.raises(VideoProcessingError):
        raise VideoProcessingError("Test")
    
    with pytest.raises(ConfigurationError):
        raise ConfigurationError("Test")
    
    with pytest.raises(TTSGenerationError):
        raise TTSGenerationError("Test")


def test_exception_catching_base():
    """Test that catching base exception catches all."""
    try:
        raise ElementNotFoundError("Test")
    except PlaywrightSimpleError:
        pass  # Should catch it
    
    try:
        raise ConfigurationError("Test")
    except PlaywrightSimpleError:
        pass  # Should catch it

