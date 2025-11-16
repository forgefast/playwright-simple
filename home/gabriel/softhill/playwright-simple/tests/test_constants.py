#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for constants module.
"""

import pytest
from playwright_simple.core import constants


def test_timing_constants_defined():
    """Test that all timing constants are defined and positive."""
    assert hasattr(constants, 'CURSOR_ANIMATION_MIN_DURATION')
    assert constants.CURSOR_ANIMATION_MIN_DURATION > 0
    
    assert hasattr(constants, 'CURSOR_HOVER_DELAY')
    assert constants.CURSOR_HOVER_DELAY > 0
    
    assert hasattr(constants, 'CURSOR_CLICK_EFFECT_DELAY')
    assert constants.CURSOR_CLICK_EFFECT_DELAY > 0
    
    assert hasattr(constants, 'CURSOR_AFTER_MOVE_DELAY')
    assert constants.CURSOR_AFTER_MOVE_DELAY > 0
    
    assert hasattr(constants, 'NAVIGATION_DELAY')
    assert constants.NAVIGATION_DELAY > 0
    
    assert hasattr(constants, 'ACTION_DELAY')
    assert constants.ACTION_DELAY > 0
    
    assert hasattr(constants, 'TYPE_DELAY')
    assert constants.TYPE_DELAY > 0
    
    assert hasattr(constants, 'TYPE_CHAR_DELAY')
    assert constants.TYPE_CHAR_DELAY > 0
    
    assert hasattr(constants, 'CLEANUP_DELAY')
    assert constants.CLEANUP_DELAY > 0
    
    assert hasattr(constants, 'VIDEO_FINALIZATION_DELAY')
    assert constants.VIDEO_FINALIZATION_DELAY > 0


def test_cursor_constants_defined():
    """Test that all cursor constants are defined."""
    assert hasattr(constants, 'CURSOR_ELEMENT_ID')
    assert isinstance(constants.CURSOR_ELEMENT_ID, str)
    assert len(constants.CURSOR_ELEMENT_ID) > 0
    
    assert hasattr(constants, 'CLICK_EFFECT_ELEMENT_ID')
    assert isinstance(constants.CLICK_EFFECT_ELEMENT_ID, str)
    assert len(constants.CLICK_EFFECT_ELEMENT_ID) > 0
    
    assert hasattr(constants, 'HOVER_EFFECT_ELEMENT_ID')
    assert isinstance(constants.HOVER_EFFECT_ELEMENT_ID, str)
    assert len(constants.HOVER_EFFECT_ELEMENT_ID) > 0
    
    assert hasattr(constants, 'CURSOR_Z_INDEX')
    assert isinstance(constants.CURSOR_Z_INDEX, int)
    assert constants.CURSOR_Z_INDEX > 0
    
    assert hasattr(constants, 'CLICK_EFFECT_Z_INDEX')
    assert isinstance(constants.CLICK_EFFECT_Z_INDEX, int)
    assert constants.CLICK_EFFECT_Z_INDEX > 0
    
    assert hasattr(constants, 'HOVER_EFFECT_Z_INDEX')
    assert isinstance(constants.HOVER_EFFECT_Z_INDEX, int)
    assert constants.HOVER_EFFECT_Z_INDEX > 0


def test_viewport_constants_defined():
    """Test that viewport constants are defined and valid."""
    assert hasattr(constants, 'DEFAULT_VIEWPORT_WIDTH')
    assert isinstance(constants.DEFAULT_VIEWPORT_WIDTH, int)
    assert constants.DEFAULT_VIEWPORT_WIDTH > 0
    
    assert hasattr(constants, 'DEFAULT_VIEWPORT_HEIGHT')
    assert isinstance(constants.DEFAULT_VIEWPORT_HEIGHT, int)
    assert constants.DEFAULT_VIEWPORT_HEIGHT > 0


def test_video_constants_defined():
    """Test that video processing constants are defined."""
    assert hasattr(constants, 'FFMPEG_TIMEOUT')
    assert isinstance(constants.FFMPEG_TIMEOUT, int)
    assert constants.FFMPEG_TIMEOUT > 0
    
    assert hasattr(constants, 'FFMPEG_VERSION_CHECK_TIMEOUT')
    assert isinstance(constants.FFMPEG_VERSION_CHECK_TIMEOUT, int)
    assert constants.FFMPEG_VERSION_CHECK_TIMEOUT > 0


def test_subtitle_constants_defined():
    """Test that subtitle constants are defined."""
    assert hasattr(constants, 'SUBTITLE_FONT_SIZE')
    assert isinstance(constants.SUBTITLE_FONT_SIZE, int)
    assert constants.SUBTITLE_FONT_SIZE > 0
    
    assert hasattr(constants, 'SUBTITLE_MIN_DURATION')
    assert isinstance(constants.SUBTITLE_MIN_DURATION, (int, float))
    assert constants.SUBTITLE_MIN_DURATION > 0


def test_error_messages_defined():
    """Test that error message constants are defined and formatable."""
    assert hasattr(constants, 'ELEMENT_NOT_FOUND_MSG')
    assert isinstance(constants.ELEMENT_NOT_FOUND_MSG, str)
    # Test formatting
    formatted = constants.ELEMENT_NOT_FOUND_MSG.format(description="test")
    assert "test" in formatted
    
    assert hasattr(constants, 'INVALID_URL_MSG')
    assert isinstance(constants.INVALID_URL_MSG, str)
    # Test formatting
    formatted = constants.INVALID_URL_MSG.format(url="test")
    assert "test" in formatted


def test_z_index_ordering():
    """Test that z-index values are ordered correctly."""
    assert constants.CURSOR_Z_INDEX > constants.CLICK_EFFECT_Z_INDEX
    assert constants.CLICK_EFFECT_Z_INDEX > constants.HOVER_EFFECT_Z_INDEX

