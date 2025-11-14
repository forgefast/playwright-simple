#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Click interaction methods.

Handles single, double, right, middle clicks.
"""

import asyncio
import logging
from typing import Optional

from .base import BaseInteractionMixin
from ..constants import (
    ACTION_DELAY,
    CURSOR_HOVER_DELAY,
    CURSOR_CLICK_EFFECT_DELAY,
)
from ..logger import get_logger

logger = logging.getLogger(__name__)
structured_logger = get_logger()


class ClickInteractionMixin(BaseInteractionMixin):
    """Mixin providing click-related interaction methods."""
    
    async def click(self, text_or_selector: str, description: str = "") -> 'ClickInteractionMixin':
        """
        Click on an element by text (preferred) or selector.
        
        Args:
            text_or_selector: Visible text or CSS selector of element to click
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        try:
            element, x, y = await self._helpers.prepare_element_interaction(text_or_selector, description)
        except Exception as e:
            structured_logger.info(
                f"Elemento não encontrado para clique: '{text_or_selector}'",
                extra={"element": text_or_selector, "action": "click", "selector": text_or_selector, "description": description, "error": str(e)}
            )
            raise
        
        if x is not None and y is not None:
            structured_logger.info(
                f"Elemento encontrado para clique: '{text_or_selector}' em ({x:.0f}, {y:.0f})",
                extra={"element": text_or_selector, "action": "click", "selector": text_or_selector, "description": description, "x": x, "y": y}
            )
        
        state_before = await self._helpers.detect_state_change({})
        
        try:
            await element.click()
            structured_logger.action(
                f"Clique executado com sucesso: '{text_or_selector}'",
                action="click", selector=text_or_selector, description=description
            )
            await asyncio.sleep(ACTION_DELAY * 2)
            
            state_after = await self._helpers.detect_state_change(state_before)
            if state_after.get('state_changed'):
                structured_logger.state(
                    f"Estado da página mudou após clique: '{text_or_selector}'",
                    action="click", selector=text_or_selector, description=description,
                    url_changed=state_after.get('url_changed', False),
                    html_changed=state_after.get('html_changed', False)
                )
        except Exception as e:
            structured_logger.error(
                f"Falha ao clicar no elemento '{text_or_selector}': {e}",
                action="click", selector=text_or_selector, description=description, error=str(e)
            )
            raise
        
        return self
    
    async def double_click(self, selector: str, description: str = "") -> 'ClickInteractionMixin':
        """Double click on an element."""
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        element, x, y = await self._helpers.prepare_element_interaction(selector, description)
        await element.dblclick()
        await asyncio.sleep(ACTION_DELAY * 2)
        structured_logger.action(f"Double click executado: '{selector}'", action="double_click", selector=selector)
        return self
    
    async def right_click(self, selector: str, description: str = "") -> 'ClickInteractionMixin':
        """Right click on an element."""
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        element, x, y = await self._helpers.prepare_element_interaction(selector, description)
        await element.click(button='right')
        await asyncio.sleep(ACTION_DELAY * 2)
        structured_logger.action(f"Right click executado: '{selector}'", action="right_click", selector=selector)
        return self
    
    async def middle_click(self, selector: str, description: str = "") -> 'ClickInteractionMixin':
        """Middle click on an element."""
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        element, x, y = await self._helpers.prepare_element_interaction(selector, description)
        await element.click(button='middle')
        await asyncio.sleep(ACTION_DELAY * 2)
        structured_logger.action(f"Middle click executado: '{selector}'", action="middle_click", selector=selector)
        return self

