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

# CursorManager removed - using CursorController instead
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
        config: TestConfig,
        selector_manager: 'SelectorManager'
    ) -> None:
        """
        Initialize helpers.
        
        Args:
            page: Playwright page instance
            config: Test configuration
            selector_manager: Selector manager instance for element finding
        """
        self.page = page
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
        # CursorController is the single source of truth for cursor visualization
        # This method is kept for backward compatibility but does nothing when CursorController is used
        # The actual cursor injection is handled by CursorController when actions are executed
        pass
    
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
        logger.debug(f"[HELPERS] prepare_element_interaction: selector='{selector}', description='{description}'")
        try:
            element = await self.selector_manager.find_element(selector, description)
            logger.debug(f"[HELPERS] Element encontrado: {element}")
            if element is None:
                logger.error(f"[HELPERS] Element não encontrado: {selector}")
                from .exceptions import ElementNotFoundError
                raise ElementNotFoundError(
                    f"Element not found: {description or selector}"
                )
            
            # Get element position for cursor movement
            try:
                logger.debug(f"[HELPERS] Obtendo bounding box do elemento...")
                box = await element.bounding_box()
                logger.debug(f"[HELPERS] Bounding box: {box}")
                if box:
                    x = box['x'] + box['width'] / 2
                    y = box['y'] + box['height'] / 2
                    logger.debug(f"[HELPERS] Coordenadas calculadas: x={x}, y={y}")
                    return element, x, y
            except Exception as e:
                logger.debug(f"[HELPERS] Erro ao obter bounding box para {selector}: {e}")
            
            logger.debug(f"[HELPERS] Retornando elemento sem coordenadas")
            return element, None, None
        except Exception as e:
            logger.error(f"[HELPERS] Erro em prepare_element_interaction: {e}", exc_info=True)
            raise
    
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
        # CursorController will handle cursor movement when actions are executed
        # No need to use CursorManager
        
        # Hover effect is disabled - skip it completely
        # Show click effect(s) only
        if show_click_effect:
            for _ in range(click_count):
                # CursorController will handle click effects when actions are executed
                # No need to use CursorManager
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
        
        # CursorController will handle cursor restoration after navigation
        # No need to use CursorManager

