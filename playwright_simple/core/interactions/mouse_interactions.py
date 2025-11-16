#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse interaction methods.

Handles hover, drag, scroll.
"""

import asyncio
import logging
from typing import Optional

from .base import BaseInteractionMixin
from ..constants import (
    ACTION_DELAY,
    CURSOR_HOVER_DELAY,
)
from ..logger import get_logger

logger = logging.getLogger(__name__)
structured_logger = get_logger()


class MouseInteractionMixin(BaseInteractionMixin):
    """Mixin providing mouse-related interaction methods."""
    
    async def hover(self, selector: str, description: str = "") -> 'MouseInteractionMixin':
        """Hover over an element."""
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        element, x, y = await self._helpers.prepare_element_interaction(selector, description)
        await element.hover()
        await asyncio.sleep(CURSOR_HOVER_DELAY)
        structured_logger.action(f"Hover executado: '{selector}'", action="hover", selector=selector)
        return self
    
    async def drag(self, source: str, target: str, description: str = "") -> 'MouseInteractionMixin':
        """Drag an element from source to target."""
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        source_element, sx, sy = await self._helpers.prepare_element_interaction(source, description)
        target_element, tx, ty = await self._helpers.prepare_element_interaction(target, description)
        
        await source_element.drag_to(target_element)
        await asyncio.sleep(ACTION_DELAY * 2)
        structured_logger.action(
            f"Drag executado: '{source}' -> '{target}'",
            action="drag", source=source, target=target
        )
        return self
    
    async def scroll(
        self,
        selector: Optional[str] = None,
        direction: str = 'down',
        amount: int = 500,
        description: str = ""
    ) -> 'MouseInteractionMixin':
        """
        Scroll the page or an element.
        
        Args:
            selector: Optional selector for element to scroll (if None, scrolls page)
            direction: 'up', 'down', 'left', 'right'
            amount: Pixels to scroll
            description: Optional description
        """
        scroll_amount = amount if direction in ['down', 'right'] else -amount
        
        if selector:
            element, x, y = await self._helpers.prepare_element_interaction(selector, description)
            if direction in ['up', 'down']:
                await element.evaluate(f"element => element.scrollBy(0, {scroll_amount})")
            else:
                await element.evaluate(f"element => element.scrollBy({scroll_amount}, 0)")
        else:
            if direction in ['up', 'down']:
                await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            else:
                await self.page.evaluate(f"window.scrollBy({scroll_amount}, 0)")
        
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action(
            f"Scroll executado: {direction} {amount}px",
            action="scroll", direction=direction, amount=amount
        )
        return self

