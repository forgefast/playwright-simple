#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text-based interaction methods for OdooTestBase.

Contains methods that accept text instead of CSS selectors, making them
more user-friendly for QAs.
"""

from typing import Optional


class OdooTextInteractionMixin:
    """Mixin providing text-based interaction methods.
    
    Assumes base class has: page, hover, double_click, right_click, drag (from parent)
    """
    
    async def hover(self, text: str, context: Optional[str] = None) -> 'OdooTextInteractionMixin':
        """
        Hover over an element by visible text.
        
        Args:
            text: Visible text of element
            context: Optional context for disambiguation
            
        Returns:
            Self for method chaining
        """
        # Try to find element by text
        selectors = [
            f':has-text("{text}")',
            f'[title*="{text}"]',
            f'[aria-label*="{text}"]',
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    await super().hover(selector, f"Hover: {text}")
                    return self
            except Exception:
                continue
        
        raise Exception(f"Element with text '{text}' not found for hover")
    
    async def double_click(self, text: str, context: Optional[str] = None) -> 'OdooTextInteractionMixin':
        """
        Double-click on an element by visible text.
        
        Args:
            text: Visible text of element
            context: Optional context for disambiguation
            
        Returns:
            Self for method chaining
        """
        # Try to find element by text
        selectors = [
            f':has-text("{text}")',
            f'button:has-text("{text}")',
            f'a:has-text("{text}")',
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    await super().double_click(selector, f"Double-click: {text}")
                    return self
            except Exception:
                continue
        
        raise Exception(f"Element with text '{text}' not found for double-click")
    
    async def right_click(self, text: str, context: Optional[str] = None) -> 'OdooTextInteractionMixin':
        """
        Right-click on an element by visible text.
        
        Args:
            text: Visible text of element
            context: Optional context for disambiguation
            
        Returns:
            Self for method chaining
        """
        # Try to find element by text
        selectors = [
            f':has-text("{text}")',
            f'button:has-text("{text}")',
            f'a:has-text("{text}")',
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    await super().right_click(selector, f"Right-click: {text}")
                    return self
            except Exception:
                continue
        
        raise Exception(f"Element with text '{text}' not found for right-click")
    
    async def drag_and_drop(self, from_text: str, to_text: str) -> 'OdooTextInteractionMixin':
        """
        Drag and drop from one element to another by visible text.
        
        Args:
            from_text: Visible text of source element
            to_text: Visible text of target element
            
        Returns:
            Self for method chaining
        """
        # Find source element
        from_selectors = [
            f':has-text("{from_text}")',
            f'[title*="{from_text}"]',
        ]
        
        source_element = None
        for selector in from_selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    source_element = selector
                    break
            except Exception:
                continue
        
        if not source_element:
            raise Exception(f"Source element with text '{from_text}' not found")
        
        # Find target element
        to_selectors = [
            f':has-text("{to_text}")',
            f'[title*="{to_text}"]',
        ]
        
        target_element = None
        for selector in to_selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    target_element = selector
                    break
            except Exception:
                continue
        
        if not target_element:
            raise Exception(f"Target element with text '{to_text}' not found")
        
        await super().drag(source_element, target_element, f"Drag {from_text} to {to_text}")
        return self
    
    async def scroll_down(self, amount: int = 500) -> 'OdooTextInteractionMixin':
        """
        Scroll down the page.
        
        Args:
            amount: Pixels to scroll (default: 500)
            
        Returns:
            Self for method chaining
        """
        await super().scroll(direction="down", amount=amount)
        return self
    
    async def scroll_up(self, amount: int = 500) -> 'OdooTextInteractionMixin':
        """
        Scroll up the page.
        
        Args:
            amount: Pixels to scroll (default: 500)
            
        Returns:
            Self for method chaining
        """
        await super().scroll(direction="up", amount=amount)
        return self

