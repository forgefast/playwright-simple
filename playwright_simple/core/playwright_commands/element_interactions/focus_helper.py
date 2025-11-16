#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focus Helper Module.

Handles focus checking and management for elements.
"""

import logging
from typing import Optional
from playwright.async_api import Page, ElementHandle

logger = logging.getLogger(__name__)

DEBUG_CLICKS = True  # Set to False to disable click debug logs


class FocusHelper:
    """Helper class for checking and managing element focus."""
    
    def __init__(self, page: Page):
        """
        Initialize focus helper.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
    
    async def is_focused(self, element: ElementHandle) -> bool:
        """
        Check if an element is currently focused.
        
        Args:
            element: ElementHandle to check
            
        Returns:
            True if element is focused, False otherwise
        """
        try:
            is_focused = await element.evaluate("""
                (el) => {
                    return document.activeElement === el;
                }
            """)
            if DEBUG_CLICKS:
                logger.info(f"🖱️  [DEBUG] Element focus check: is_focused={is_focused}")
            return is_focused
        except Exception as e:
            logger.debug(f"Error checking focus: {e}")
            return False
    
    async def focus_element(self, element: ElementHandle) -> bool:
        """
        Focus an element.
        
        Args:
            element: ElementHandle to focus
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await element.focus()
            return True
        except Exception as e:
            logger.debug(f"Error focusing element: {e}")
            return False

