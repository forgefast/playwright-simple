#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Simple - A simple and intuitive library for writing Playwright tests.

Designed for QAs without deep programming knowledge, while maintaining
flexibility for advanced use cases.
"""

__version__ = "0.1.0"

# Import from core to maintain backward compatibility
from .core import (
    TestConfig,
    SimpleTestBase,
    TestRunner,
    CursorManager,
    ScreenshotManager,
    VideoManager,
    SelectorManager,
    YAMLParser,
)

# Optional extensions (import only if available)
try:
    from .forgeerp import ForgeERPTestBase
    __all__ = [
        "TestConfig",
        "SimpleTestBase",
        "TestRunner",
        "CursorManager",
        "ScreenshotManager",
        "VideoManager",
        "SelectorManager",
        "YAMLParser",
        "ForgeERPTestBase",
        "__version__",
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
        "__version__",
    ]

