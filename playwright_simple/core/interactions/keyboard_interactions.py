#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyboard interaction methods.

Handles typing, key presses, clipboard operations.
"""

import asyncio
import logging
from typing import Optional

from .base import BaseInteractionMixin
from ..constants import (
    ACTION_DELAY,
    TYPE_DELAY,
    TYPE_CHAR_DELAY,
)
from ..logger import get_logger

logger = logging.getLogger(__name__)
structured_logger = get_logger()


class KeyboardInteractionMixin(BaseInteractionMixin):
    """Mixin providing keyboard-related interaction methods."""
    
    async def type(self, text: str, selector: Optional[str] = None, description: str = "") -> 'KeyboardInteractionMixin':
        """
        Type text into an element.
        
        If no selector is provided, tries to find the focused field or first visible text input.
        
        Args:
            text: Text to type
            selector: Optional selector for the element (if None, uses focused field)
            description: Optional description for logging
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        try:
            if selector:
                element, x, y = await self._helpers.prepare_element_interaction(selector, description)
            else:
                # Try to find focused field or first visible text input
                try:
                    # Check if there's a focused element
                    focused_element = await self.page.evaluate("() => document.activeElement")
                    if focused_element and focused_element.get('tagName', '').lower() in ['input', 'textarea']:
                        element = self.page.locator(':focus')
                        x, y = None, None
                    else:
                        # Find first visible text input
                        element = self.page.locator('input[type="text"], input[type="email"], input[type="password"], textarea').first
                        x, y = None, None
                except Exception:
                    # Fallback: use first input
                    element = self.page.locator('input, textarea').first
                    x, y = None, None
            
            structured_logger.info(
                f"Elemento encontrado para digitação: '{selector or 'auto'}'",
                element=selector or 'auto',
                action="type", selector=selector, description=description
            )
            
            await element.fill('')  # Clear first
            await element.type(text, delay=TYPE_CHAR_DELAY)
            await asyncio.sleep(TYPE_DELAY)
            
            structured_logger.action(
                f"Texto digitado com sucesso: '{text[:50]}...'",
                action="type", selector=selector, description=description
            )
        except Exception as e:
            structured_logger.error(
                f"Falha ao digitar texto: {e}",
                action="type", selector=selector, description=description, error=str(e)
            )
            raise
        
        return self
    
    async def press(self, key: str, description: str = "") -> 'KeyboardInteractionMixin':
        """Press a key."""
        await self.page.keyboard.press(key)
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action(f"Tecla pressionada: '{key}'", action="press", key=key)
        return self
    
    async def keydown(self, key: str, description: str = "") -> 'KeyboardInteractionMixin':
        """Press and hold a key."""
        await self.page.keyboard.down(key)
        structured_logger.action(f"Tecla pressionada (hold): '{key}'", action="keydown", key=key)
        return self
    
    async def keyup(self, key: str, description: str = "") -> 'KeyboardInteractionMixin':
        """Release a key."""
        await self.page.keyboard.up(key)
        structured_logger.action(f"Tecla solta: '{key}'", action="keyup", key=key)
        return self
    
    async def keypress(self, key: str, description: str = "") -> 'KeyboardInteractionMixin':
        """Press and release a key (alias for press)."""
        return await self.press(key, description)
    
    async def insert_text(self, text: str, description: str = "") -> 'KeyboardInteractionMixin':
        """Insert text without triggering input events."""
        await self.page.keyboard.insert_text(text)
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action(f"Texto inserido: '{text[:50]}...'", action="insert_text")
        return self
    
    async def select_all(self, description: str = "") -> 'KeyboardInteractionMixin':
        """Select all text in the focused element."""
        import platform
        is_mac = platform.system() == 'Darwin'
        await self.page.keyboard.press('Meta+a' if is_mac else 'Control+a')
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action("Selecionar tudo executado", action="select_all")
        return self
    
    async def copy(self, description: str = "") -> 'KeyboardInteractionMixin':
        """Copy selected text to clipboard."""
        import platform
        is_mac = platform.system() == 'Darwin'
        await self.page.keyboard.press('Meta+c' if is_mac else 'Control+c')
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action("Copiar executado", action="copy")
        return self
    
    async def paste(self, description: str = "") -> 'KeyboardInteractionMixin':
        """Paste text from clipboard."""
        import platform
        is_mac = platform.system() == 'Darwin'
        await self.page.keyboard.press('Meta+v' if is_mac else 'Control+v')
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action("Colar executado", action="paste")
        return self
    
    async def clear(self, selector: str, description: str = "") -> 'KeyboardInteractionMixin':
        """Clear text from an element."""
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        element, x, y = await self._helpers.prepare_element_interaction(selector, description)
        await element.fill('')
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action(f"Campo limpo: '{selector}'", action="clear", selector=selector)
        return self
    
    async def focus(self, selector: str, description: str = "") -> 'KeyboardInteractionMixin':
        """Focus on an element."""
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        element, x, y = await self._helpers.prepare_element_interaction(selector, description)
        await element.focus()
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action(f"Foco definido: '{selector}'", action="focus", selector=selector)
        return self
    
    async def blur(self, selector: str, description: str = "") -> 'KeyboardInteractionMixin':
        """Remove focus from an element."""
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        element, x, y = await self._helpers.prepare_element_interaction(selector, description)
        await element.blur()
        await asyncio.sleep(ACTION_DELAY)
        structured_logger.action(f"Foco removido: '{selector}'", action="blur", selector=selector)
        return self

