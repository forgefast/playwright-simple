#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart selector system for playwright-simple.

Provides intelligent element location with automatic fallback and retry logic.
"""

import asyncio
import logging
from typing import List, Optional, Tuple
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class SelectorManager:
    """Manages intelligent element selection with fallback strategies."""
    
    # Priority order for selector strategies
    SELECTOR_PRIORITY = [
        'data-testid',
        'aria-label',
        'role',
        'text',
        'label',
        'css',
    ]
    
    def __init__(self, page: Page, timeout: int = 30000, retry_count: int = 3):
        """
        Initialize selector manager.
        
        Args:
            page: Playwright page instance
            timeout: Default timeout in milliseconds
            retry_count: Number of retries with backoff
        """
        self.page = page
        self.timeout = timeout
        self.retry_count = retry_count
    
    async def find_element(
        self,
        selector: str,
        description: str = "",
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> Optional[Locator]:
        """
        Find element using intelligent fallback strategies.
        
        Args:
            selector: Primary selector
            description: Description for logging
            timeout: Timeout in milliseconds (uses default if None)
            state: Element state to wait for (visible, hidden, attached, detached)
            
        Returns:
            Locator if found, None otherwise
        """
        timeout = timeout or self.timeout
        
        # Try primary selector first
        try:
            locator = self.page.locator(selector).first
            await locator.wait_for(state=state, timeout=timeout)
            if await locator.count() > 0:
                logger.debug(f"Found element with selector '{selector}': {description}")
                return locator
        except Exception as e:
            logger.debug(f"Primary selector '{selector}' failed: {e}")
        
        # Try alternative selectors
        alternatives = self._generate_alternatives(selector)
        for alt_selector in alternatives:
            try:
                locator = self.page.locator(alt_selector).first
                await locator.wait_for(state=state, timeout=min(timeout, 5000))
                if await locator.count() > 0:
                    logger.info(f"Found element with alternative selector '{alt_selector}': {description}")
                    return locator
            except Exception:
                continue
        
        # Retry with exponential backoff
        for attempt in range(self.retry_count):
            wait_time = (2 ** attempt) * 100  # Exponential backoff: 100ms, 200ms, 400ms
            await asyncio.sleep(wait_time / 1000)
            
            try:
                locator = self.page.locator(selector).first
                await locator.wait_for(state=state, timeout=timeout)
                if await locator.count() > 0:
                    logger.info(f"Found element on retry {attempt + 1}: {description}")
                    return locator
            except Exception:
                continue
        
        logger.warning(f"Element not found after all attempts: {description or selector}")
        return None
    
    def _generate_alternatives(self, selector: str) -> List[str]:
        """
        Generate alternative selectors based on primary selector.
        
        Args:
            selector: Primary selector
            
        Returns:
            List of alternative selectors
        """
        alternatives = []
        
        # If it's a CSS selector, try variations
        if selector.startswith(('#', '.', '[')):
            # Try as text selector
            if ':' in selector:
                # Extract text if it's a :has-text() selector
                if ':has-text(' in selector:
                    import re
                    match = re.search(r':has-text\(["\']([^"\']+)["\']\)', selector)
                    if match:
                        text = match.group(1)
                        alternatives.append(f'text="{text}"')
                        alternatives.append(f'text={text}')
        
        # Try role-based if it looks like a button/link
        if 'button' in selector.lower() or 'btn' in selector.lower():
            alternatives.append('[role="button"]')
        
        if 'link' in selector.lower() or 'a[' in selector:
            alternatives.append('[role="link"]')
        
        return alternatives
    
    def by_text(self, text: str, exact: bool = False) -> str:
        """
        Create selector by text content.
        
        Args:
            text: Text to match
            exact: Whether to match exactly
            
        Returns:
            Selector string
        """
        if exact:
            return f'text="{text}"'
        return f'text={text}'
    
    def by_role(self, role: str, name: Optional[str] = None) -> str:
        """
        Create selector by ARIA role.
        
        Args:
            role: ARIA role (button, link, textbox, etc.)
            name: Optional name/accessible name
            
        Returns:
            Selector string
        """
        if name:
            return f'role={role}[name="{name}"]'
        return f'role={role}'
    
    def by_test_id(self, test_id: str) -> str:
        """
        Create selector by data-testid attribute.
        
        Args:
            test_id: Value of data-testid attribute
            
        Returns:
            Selector string
        """
        return f'[data-testid="{test_id}"]'
    
    def by_label(self, label_text: str) -> str:
        """
        Create selector by label text.
        
        Args:
            label_text: Label text
            
        Returns:
            Selector string
        """
        return f'label:has-text("{label_text}")'
    
    async def wait_for_element(
        self,
        selector: str,
        description: str = "",
        timeout: Optional[int] = None,
        state: str = "visible"
    ) -> Locator:
        """
        Wait for element to appear with intelligent fallback.
        
        Args:
            selector: Selector to wait for
            description: Description for error messages
            timeout: Timeout in milliseconds
            state: Element state to wait for
            
        Returns:
            Locator when found
            
        Raises:
            TimeoutError: If element not found within timeout
        """
        locator = await self.find_element(selector, description, timeout, state)
        if locator is None:
            raise PlaywrightTimeoutError(
                f"Element not found: {description or selector} "
                f"(timeout: {timeout or self.timeout}ms)"
            )
        return locator


