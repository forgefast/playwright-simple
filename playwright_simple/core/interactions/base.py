#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base class for interaction mixins.

Provides common functionality shared by all interaction types.
"""

import logging
from typing import Optional, TYPE_CHECKING, Any

from ..helpers import TestBaseHelpers
from ..logger import get_logger

if TYPE_CHECKING:
    from playwright.async_api import Page, Locator

logger = logging.getLogger(__name__)
structured_logger = get_logger()


class BaseInteractionMixin:
    """
    Base mixin providing common functionality for interaction mixins.
    
    This mixin provides:
    - Helpers management
    - Common logging
    - Shared initialization
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize mixin."""
        super().__init__(*args, **kwargs)
        self._helpers: Optional[TestBaseHelpers] = None
    
    def _set_helpers(self, helpers: TestBaseHelpers) -> None:
        """
        Set helpers instance.
        
        Called by base class after creating TestBaseHelpers instance.
        
        Args:
            helpers: TestBaseHelpers instance to use
        """
        self._helpers = helpers

