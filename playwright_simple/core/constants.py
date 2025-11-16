#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Constants for playwright-simple core module.

Centralizes magic numbers and strings to improve maintainability.
"""

# Timing constants (in seconds) - Optimized for speed
CURSOR_ANIMATION_MIN_DURATION = 0.05  # Reduced for faster execution
CURSOR_HOVER_DELAY = 0.01  # Minimal delay
CURSOR_CLICK_EFFECT_DELAY = 0.05  # Reduced for faster execution
CURSOR_AFTER_MOVE_DELAY = 0.01  # Minimal delay
NAVIGATION_DELAY = 0.01  # Minimal delay
ACTION_DELAY = 0.01  # Reduced for faster execution
TYPE_DELAY = 0.005  # Minimal delay
TYPE_CHAR_DELAY = 5  # Reduced milliseconds
CLEANUP_DELAY = 0.05  # Reduced
VIDEO_FINALIZATION_DELAY = 0.1  # Reduced

# Cursor constants
CURSOR_ELEMENT_ID = 'playwright-cursor'
CLICK_EFFECT_ELEMENT_ID = 'playwright-click-effect'
HOVER_EFFECT_ELEMENT_ID = 'playwright-hover-effect'
CURSOR_Z_INDEX = 2147483647
CLICK_EFFECT_Z_INDEX = 2147483646
HOVER_EFFECT_Z_INDEX = 2147483645

# Default viewport
DEFAULT_VIEWPORT_WIDTH = 1920
DEFAULT_VIEWPORT_HEIGHT = 1080

# Video processing
FFMPEG_TIMEOUT = 300  # seconds
FFMPEG_VERSION_CHECK_TIMEOUT = 5  # seconds

# Subtitle constants
SUBTITLE_FONT_SIZE = 24
SUBTITLE_MIN_DURATION = 1.0  # Minimum duration for subtitle visibility

# Error messages
ELEMENT_NOT_FOUND_MSG = "Element not found: {description}"
INVALID_URL_MSG = (
    "URL inválida: '{url}'. "
    "URLs devem começar com 'http' ou '/'. "
    "Para navegação por menu, use o método apropriado da subclasse."
)

