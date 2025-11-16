#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core modules for playwright-simple.

This package contains the core functionality of playwright-simple.
"""

from .config import TestConfig
# Lazy imports to avoid circular dependencies
try:
    from .base import SimpleTestBase
except (ImportError, SyntaxError) as e:
    SimpleTestBase = None  # type: ignore
try:
    from .runner import TestRunner
except (ImportError, SyntaxError) as e:
    TestRunner = None  # type: ignore
from .logging_config import FrameworkLogger, log_action, log_mouse_action, log_keyboard_action, log_cursor_action, log_element_action, log_error
from .cursor import CursorManager
from .screenshot import ScreenshotManager
from .selectors import SelectorManager
# YAMLParser removed - use Recorder for playback or parse_yaml_file from yaml_resolver for parsing
# VideoManager and TTSManager moved to extensions
from .exceptions import (
    PlaywrightSimpleError,
    ElementNotFoundError,
    NavigationError,
    ConfigurationError,
)
# VideoProcessingError and TTSGenerationError moved to extensions

# Optional HTMX helper (for apps using HTMX)
try:
    from .htmx import HTMXHelper
    __all__ = [
        "TestConfig",
        "SimpleTestBase",
        "TestRunner",
        "CursorManager",
        "ScreenshotManager",
        "SelectorManager",
        "HTMXHelper",
        "PlaywrightSimpleError",
        "ElementNotFoundError",
        "NavigationError",
        "ConfigurationError",
    ]
except ImportError:
    __all__ = [
        "TestConfig",
        "SimpleTestBase",
        "TestRunner",
        "CursorManager",
        "ScreenshotManager",
        "SelectorManager",
        "PlaywrightSimpleError",
        "ElementNotFoundError",
        "NavigationError",
        "ConfigurationError",
    ]

