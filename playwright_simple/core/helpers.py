#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper functions and mixins for SimpleTestBase.

Contains reusable code extracted from base.py to improve maintainability.
"""

import asyncio
import logging
from typing import Optional, Tuple, Dict, Any
from playwright.async_api import Page, Locator

from .cursor import CursorManager
from .config import TestConfig
from .constants import (
    CURSOR_HOVER_DELAY,
    CURSOR_CLICK_EFFECT_DELAY,
    ACTION_DELAY,
)

logger = logging.getLogger(__name__)


class TestBaseHelpers:
    """
    Helper methods for test base classes.
    
    This class provides reusable helper methods that are used by mixins
    and the base test class. It encapsulates common operations like cursor
    management, element preparation, and navigation.
    
    Attributes:
        page: Playwright Page instance
        cursor_manager: CursorManager instance for visual cursor effects
        config: TestConfig instance with test configuration
        selector_manager: SelectorManager instance for element finding
        _cursor_injected: Internal flag tracking cursor injection state
    """
    
    def __init__(
        self,
        page: Page,
        cursor_manager: CursorManager,
        config: TestConfig,
        selector_manager: 'SelectorManager'
    ) -> None:
        """
        Initialize helpers.
        
        Args:
            page: Playwright page instance
            cursor_manager: Cursor manager instance for visual effects
            config: Test configuration
            selector_manager: Selector manager instance for element finding
        """
        self.page = page
        self.cursor_manager = cursor_manager
        self.config = config
        self.selector_manager = selector_manager
        self._cursor_injected = False
    
    async def ensure_cursor(self) -> None:
        """
        Ensure cursor is injected into the page.
        
        Injects the visual cursor overlay if it hasn't been injected yet.
        This is called before any interaction that requires cursor visualization.
        
        Raises:
            Exception: If cursor injection fails
        """
        if not self._cursor_injected:
            await self.cursor_manager.inject()
            self._cursor_injected = True
    
    async def prepare_element_interaction(
        self, 
        selector: str, 
        description: str = ""
    ) -> Tuple[Locator, Optional[float], Optional[float]]:
        """
        Prepare element for interaction, getting element and coordinates.
        
        Finds the element using the selector manager and calculates its
        center coordinates for cursor movement. If coordinates cannot be
        determined, returns None for x and y.
        
        Args:
            selector: CSS selector or text to find element
            description: Optional description for error messages and logging
            
        Returns:
            Tuple of (element, x, y) where:
            - element: Playwright Locator for the element
            - x: X coordinate of element center, or None if unavailable
            - y: Y coordinate of element center, or None if unavailable
            
        Raises:
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            element, x, y = await helpers.prepare_element_interaction(
                'button.submit',
                "Submit button"
            )
            if x is not None and y is not None:
                await helpers.move_cursor_to_element(x, y)
            ```
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            from .exceptions import ElementNotFoundError
            raise ElementNotFoundError(
                f"Element not found: {description or selector}"
            )
        
        # Get element position for cursor movement
        try:
            box = await element.bounding_box()
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                return element, x, y
        except Exception as e:
            logger.debug(f"Could not get bounding box for {selector}: {e}")
        
        return element, None, None
    
    async def detect_state_change(
        self,
        state_before: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect changes in page state after an action.
        
        Captures current page state (URL, title) and compares with previous state
        to detect if page changed after an action.
        
        Args:
            state_before: Optional previous state to compare against
            
        Returns:
            Dictionary with current state and change detection:
            - url: Current page URL
            - title: Current page title
            - url_changed: Whether URL changed (if state_before provided)
            - state_changed: Whether any state changed (if state_before provided)
        """
        state = {}
        try:
            state['url'] = self.page.url
            state['title'] = await self.page.title()
            
            if state_before:
                state['url_changed'] = state_before.get('url') != state['url']
                state['state_changed'] = (
                    state['url_changed'] or
                    state_before.get('title') != state['title']
                )
        except Exception as e:
            logger.debug(f"Erro ao capturar estado da página: {e}")
        
        return state
    
    async def move_cursor_to_element(
        self, 
        x: float, 
        y: float, 
        show_hover: bool = True, 
        show_click_effect: bool = True, 
        click_count: int = 1
    ) -> None:
        """
        Move cursor to element position with visual effects.
        
        Moves the visual cursor overlay to the specified coordinates and
        optionally shows hover and click effects. The click effect can be
        shown multiple times (e.g., for double-click).
        
        Args:
            x: X coordinate (pixels from left edge of viewport)
            y: Y coordinate (pixels from top edge of viewport)
            show_hover: Whether to show hover effect (currently disabled)
            show_click_effect: Whether to show click effect animation
            click_count: Number of click effects to show (1 for single click,
                       2 for double-click, etc.)
            
        Raises:
            Exception: If cursor movement or effect display fails
        """
        # Move cursor to element
        await self.cursor_manager.move_to(x, y)
        
        # Hover effect is disabled - skip it completely
        # Show click effect(s) only
        if show_click_effect:
            for _ in range(click_count):
                await self.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(CURSOR_CLICK_EFFECT_DELAY)
    
    async def navigate_with_cursor(
        self, 
        navigation_func, 
        *args, 
        **kwargs
    ) -> None:
        """
        Execute navigation function with cursor management.
        
        Ensures cursor is injected before navigation and re-injects it
        after navigation completes, as navigation can sometimes remove
        the cursor overlay.
        
        Args:
            navigation_func: Navigation function to call (e.g., page.goto,
                           page.go_back, page.reload)
            *args: Positional arguments for navigation function
            **kwargs: Keyword arguments for navigation function
            
        Raises:
            Exception: If navigation or cursor injection fails
        """
        await self.ensure_cursor()
        await navigation_func(*args, **kwargs)
        await asyncio.sleep(0.05)  # NAVIGATION_DELAY
        
        # Re-inject cursor after navigation
        try:
            await self.cursor_manager.inject(force=True)
        except Exception as e:
            logger.warning(f"Failed to inject cursor after navigation, ensuring cursor exists: {e}")
            await self.cursor_manager._ensure_cursor_exists()

