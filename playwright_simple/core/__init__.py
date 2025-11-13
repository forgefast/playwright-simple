#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core modules for playwright-simple.

This package contains the core functionality of playwright-simple.
"""

from .config import TestConfig
from .base import SimpleTestBase
from .runner import TestRunner
from .cursor import CursorManager
from .screenshot import ScreenshotManager
from .video import VideoManager
from .selectors import SelectorManager
from .yaml_parser import YAMLParser
from .tts import TTSManager
from .exceptions import (
    PlaywrightSimpleError,
    ElementNotFoundError,
    NavigationError,
    VideoProcessingError,
    ConfigurationError,
    TTSGenerationError,
)

# Optional HTMX helper (for apps using HTMX)
try:
    from .htmx import HTMXHelper
    __all__ = [
        "TestConfig",
        "SimpleTestBase",
        "TestRunner",
        "CursorManager",
        "ScreenshotManager",
        "VideoManager",
        "SelectorManager",
        "YAMLParser",
        "TTSManager",
        "HTMXHelper",
        "PlaywrightSimpleError",
        "ElementNotFoundError",
        "NavigationError",
        "VideoProcessingError",
        "ConfigurationError",
        "TTSGenerationError",
    ]
except ImportError:
    __all__ = [
        "TestConfig",
        "SimpleTestBase",
        "TestRunner",
        "CursorManager",
        "ScreenshotManager",
        "VideoManager",
        "SelectorManager",
        "YAMLParser",
        "TTSManager",
        "PlaywrightSimpleError",
        "ElementNotFoundError",
        "NavigationError",
        "VideoProcessingError",
        "ConfigurationError",
        "TTSGenerationError",
    ]

