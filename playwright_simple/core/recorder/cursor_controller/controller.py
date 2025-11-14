#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main CursorController class.

Coordinates all cursor modules.
"""

from typing import Optional
from playwright.async_api import Page

from .visual import CursorVisual
from .movement import CursorMovement
from .interaction import CursorInteraction


class CursorController:
    """Controls a visual cursor overlay in the browser."""
    
    def __init__(self, page: Page):
        """Initialize cursor controller."""
        self.page = page
        self.is_active = False
        self.current_x = 0
        self.current_y = 0
        
        # Initialize modules
        self._visual = CursorVisual(page)
        self._movement = CursorMovement(page, self)
        self._interaction = CursorInteraction(page, self)
    
    async def start(self, force: bool = False, initial_x: int = None, initial_y: int = None):
        """
        Start cursor controller and inject cursor overlay.
        
        Args:
            force: Force reinjection even if already active
            initial_x: Initial X position (None = center or last position)
            initial_y: Initial Y position (None = center or last position)
        """
        await self._visual.start(force, initial_x, initial_y)
        self.is_active = self._visual.is_active
        # Update current position from movement module
        if self._movement.current_x == 0 and self._movement.current_y == 0:
            # Get position from page if available
            position = await self.page.evaluate("""
                () => {
                    return window.__playwright_cursor_last_position || null;
                }
            """)
            if position:
                self.current_x = position.get('x', 0)
                self.current_y = position.get('y', 0)
                self._movement.current_x = self.current_x
                self._movement.current_y = self.current_y
    
    async def show(self):
        """Show cursor overlay."""
        await self._visual.show()
    
    async def hide(self):
        """Hide cursor overlay."""
        await self._visual.hide()
    
    async def move(self, x: int, y: int, smooth: bool = True):
        """Move cursor to position."""
        await self._movement.move(x, y, smooth)
        self.current_x = self._movement.current_x
        self.current_y = self._movement.current_y
    
    async def click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Click at cursor position or specified coordinates."""
        await self._interaction.click(x, y)
        # Update position if coordinates provided
        if x is not None and y is not None:
            self.current_x = x
            self.current_y = y
    
    async def click_by_text(self, text: str) -> bool:
        """Click on element by text."""
        return await self._interaction.click_by_text(text)
    
    async def type_text(self, text: str, field_selector: Optional[str] = None) -> bool:
        """Type text into a field."""
        return await self._interaction.type_text(text, field_selector)
    
    async def press_key(self, key: str):
        """Press a key."""
        await self._interaction.press_key(key)
    
    async def get_element_at(self, x: int, y: int) -> Optional[dict]:
        """Get element information at cursor position."""
        return await self._interaction.get_element_at(x, y)
    
    async def stop(self):
        """Stop cursor controller."""
        await self._visual.stop()
        self.is_active = False

