#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test context management module.

Handles creation of test instances based on test function type.
"""

import inspect
import logging
from typing import Callable
from playwright.async_api import Page

from ..config import TestConfig
from ..base import SimpleTestBase

logger = logging.getLogger(__name__)

# Try to import OdooTestBase (optional dependency)
try:
    from ...odoo.base import OdooTestBase
    ODOO_AVAILABLE = True
except ImportError:
    OdooTestBase = None
    ODOO_AVAILABLE = False

# Try to import ForgeERPTestBase (optional dependency)
try:
    from ...forgeerp.base import ForgeERPTestBase
    FORGEERP_AVAILABLE = True
except ImportError:
    ForgeERPTestBase = None
    FORGEERP_AVAILABLE = False


class TestContextManager:
    """Manages test context and instance creation."""
    
    def __init__(self, config: TestConfig):
        """
        Initialize test context manager.
        
        Args:
            config: Test configuration
        """
        self.config = config
    
    def create_instance(self, page: Page, test_name: str, test_func: Callable) -> SimpleTestBase:
        """
        Create appropriate test instance based on test function type.
        
        Args:
            page: Playwright page instance
            test_name: Name of the test
            test_func: Test function
            
        Returns:
            Test base instance (SimpleTestBase, OdooTestBase, or ForgeERPTestBase)
        """
        # Check if test function expects specific test base
        # Check function signature
        sig = inspect.signature(test_func)
        params = list(sig.parameters.values())
        
        # If second parameter is annotated, check which type it expects
        if len(params) >= 2:
            param = params[1]  # Second parameter is usually 'test'
            if param.annotation != inspect.Parameter.empty:
                annotation_str = str(param.annotation)
                # Check for ForgeERPTestBase first (more specific)
                if 'ForgeERPTestBase' in annotation_str and FORGEERP_AVAILABLE:
                    return ForgeERPTestBase(page, self.config, test_name)
                # Check for OdooTestBase
                if 'OdooTestBase' in annotation_str and ODOO_AVAILABLE:
                    return OdooTestBase(page, self.config, test_name)
        
        # Check if test function module is from forgeerp
        if hasattr(test_func, '__module__'):
            if 'forgeerp' in test_func.__module__ and FORGEERP_AVAILABLE:
                return ForgeERPTestBase(page, self.config, test_name)
            # Check if test function module is from odoo
            if 'odoo' in test_func.__module__ and ODOO_AVAILABLE:
                return OdooTestBase(page, self.config, test_name)
        
        # Default to SimpleTestBase
        return SimpleTestBase(page, self.config, test_name)

