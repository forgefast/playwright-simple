#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor customization system for playwright-simple.

Provides visual cursor overlay with customizable style, color, size, and animations.
"""

from playwright.async_api import Page

from .config import CursorConfig
from .cursor_styles import CursorStyles
from .cursor_elements import CursorElements
from .cursor_movement import CursorMovement
from .cursor_effects import CursorEffects
from .cursor_injection import CursorInjection


class CursorManager:
    """Manages cursor visualization and effects."""
    
    def __init__(self, page: Page, config: CursorConfig):
        """
        Initialize cursor manager.
        
        Args:
            page: Playwright page instance
            config: Cursor configuration
        """
        self.page = page
        self.config = config
        self._injected = False
        self._init_script_added = False  # Track if init script was added to this page
        
        # Initialize helper classes
        self._elements = CursorElements(page, config)
        self._movement = CursorMovement(page, config)
        self._effects = CursorEffects(page, config)
        self._injection = CursorInjection(page, config)
    
    async def inject(self, force: bool = False):
        """
        Inject cursor CSS and JavaScript into the page.
        
        Args:
            force: Force re-injection even if already injected
        """
        # Add init script only once per page (it persists across navigations)
        if not self._init_script_added:
            await self._injection.add_init_script()
            self._init_script_added = True
        
        # Ensure cursor exists on current page
        await self._elements.ensure_cursor_exists()
        
        # Remove hover effect if disabled
        await self._elements.remove_hover_effect_if_disabled()
        
        # Ensure click effect is hidden at start
        await self._elements.ensure_click_effect_hidden()
        
        self._injected = True
    
    async def _ensure_cursor_exists(self):
        """Ensure cursor elements exist on current page."""
        await self._elements.ensure_cursor_exists()
        
        # Remove hover effect if disabled
        await self._elements.remove_hover_effect_if_disabled()
        
        # Ensure click effect is hidden
        await self._elements.ensure_click_effect_hidden()
    
    async def move_to(self, x: float, y: float):
        """
        Move cursor to position with smooth animation.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        # Ensure cursor exists
        cursor_exists = await self._elements.cursor_exists()
        if not cursor_exists:
            await self._ensure_cursor_exists()
        
        # Move cursor with animation
        await self._movement.move_to(x, y)
    
    async def show_click_effect(self, x: float, y: float):
        """
        Show click effect at position and wait for animation to complete.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        await self._effects.show_click_effect(x, y)
    
    async def show_hover_effect(self, x: float, y: float, show: bool = True):
        """
        Show or hide hover effect at position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            show: Whether to show or hide
        """
        await self._effects.show_hover_effect(x, y, show)
