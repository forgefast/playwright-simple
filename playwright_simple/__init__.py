#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Simple - Web automation simplified.

A simple and intuitive library for web automation with Playwright.
Perfect for:
- Automated testing (QA, E2E, regression)
- Task automation (scripts, bots, workflows)
- Monitoring and data collection
- System integration
- Web scraping
- Automated reporting

Designed for QAs and developers without deep programming knowledge,
while maintaining flexibility for advanced use cases.
"""

__version__ = "0.1.0"

# Import from core to maintain backward compatibility
from .core import (
    TestConfig,
    SimpleTestBase,
    TestRunner,
    CursorManager,
    ScreenshotManager,
    SelectorManager,
    YAMLParser,
)
# VideoManager moved to extensions/video

# Optional extensions (import only if available)
try:
    from .forgeerp import ForgeERPTestBase
    __all__ = [
        "TestConfig",
        "SimpleTestBase",
        "TestRunner",
        "CursorManager",
        "ScreenshotManager",
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
        "SelectorManager",
        "YAMLParser",
        "__version__",
    ]

