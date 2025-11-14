#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication methods for SimpleTestBase.

Contains generic login method for web applications.
"""

import asyncio
import logging
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .exceptions import ElementNotFoundError

logger = logging.getLogger(__name__)


class AuthMixin:
    """
    Mixin providing authentication methods for test base classes.
    
    NOTE: The generic login() method has been removed. Each application-specific
    extension should implement its own login as a YAML file (e.g., odoo/login.yaml).
    
    This mixin is kept for future authentication-related methods.
    It assumes the base class has:
    - page: Playwright Page instance
    - config: TestConfig instance
    - type: Method to type text into fields
    - click: Method to click elements
    - _ensure_cursor: Method to ensure cursor is injected
    """
    
    # Login method removed - use YAML composition instead
    # Example: action: login (searches for login.yaml in examples/)

