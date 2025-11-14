#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main PlaywrightCommands class.

Coordinates all command modules.
"""

from typing import Optional
from playwright.async_api import Page

from .element_finder import ElementFinder
from .element_interactions import ElementInteractions
from .page_operations import PageOperations
from .visual_feedback import VisualFeedback


class PlaywrightCommands:
    """Interface for direct Playwright commands."""
    
    def __init__(self, page: Page, fast_mode: bool = False, enable_animations: bool = True):
        """
        Initialize Playwright commands interface.
        
        Args:
            page: Playwright Page instance
            fast_mode: Enable fast mode (reduce delays, but animations can still be enabled)
            enable_animations: Whether to show animations (default: True, even in fast_mode for recording)
        """
        self.page = page
        self.fast_mode = fast_mode
        self._element_finder = ElementFinder(page)
        self._element_interactions = ElementInteractions(page, fast_mode=fast_mode)
        self._page_operations = PageOperations(page)
        self._visual_feedback = VisualFeedback(page, fast_mode=fast_mode, enable_animations=enable_animations)
    
    # Delegate to element finder
    async def find_element(self, *args, **kwargs):
        """Find an element on the page."""
        return await self._element_finder.find_element(*args, **kwargs)
    
    async def find_all_elements(self, *args, **kwargs):
        """Find all elements matching criteria."""
        return await self._element_finder.find_all_elements(*args, **kwargs)
    
    # Delegate to element interactions
    async def click(self, *args, cursor_controller=None, description="", **kwargs):
        """Click on an element."""
        return await self._element_interactions.click(
            *args,
            cursor_controller=cursor_controller,
            visual_feedback=self._visual_feedback,
            description=description,
            **kwargs
        )
    
    async def type_text(self, *args, cursor_controller=None, **kwargs):
        """Type text into an input field."""
        return await self._element_interactions.type_text(
            *args,
            cursor_controller=cursor_controller,
            visual_feedback=self._visual_feedback,
            **kwargs
        )
    
    async def submit_form(self, *args, cursor_controller=None, **kwargs):
        """Submit a form by clicking the submit button."""
        return await self._element_interactions.submit_form(
            *args,
            cursor_controller=cursor_controller,
            visual_feedback=self._visual_feedback,
            **kwargs
        )
    
    # Delegate to page operations
    async def wait_for_element(self, *args, **kwargs):
        """Wait for an element to appear on the page."""
        return await self._page_operations.wait_for_element(*args, **kwargs)
    
    async def get_page_info(self, *args, **kwargs):
        """Get current page information."""
        return await self._page_operations.get_page_info(*args, **kwargs)
    
    async def navigate(self, *args, **kwargs):
        """Navigate to a URL."""
        return await self._page_operations.navigate(*args, **kwargs)
    
    async def take_screenshot(self, *args, **kwargs):
        """Take a screenshot."""
        return await self._page_operations.take_screenshot(*args, **kwargs)
    
    async def get_html(self, *args, **kwargs):
        """Get HTML content of the page or a specific element."""
        return await self._page_operations.get_html(*args, **kwargs)


# Convenience functions for easy access
async def create_commands(page: Page) -> PlaywrightCommands:
    """Create a PlaywrightCommands instance from a page."""
    return PlaywrightCommands(page)

