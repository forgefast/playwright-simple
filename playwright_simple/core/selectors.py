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
    """
    Manages intelligent element selection with fallback strategies.
    
    This class provides smart element finding with automatic fallback to
    alternative selectors and retry logic with exponential backoff. It
    prioritizes reliable selectors (data-testid, aria-label) over less
    reliable ones (CSS, text).
    
    Attributes:
        page: Playwright Page instance
        timeout: Default timeout in milliseconds for element finding
        retry_count: Number of retry attempts with exponential backoff
        SELECTOR_PRIORITY: Priority order for selector strategies (class attribute)
    """
    
    # Priority order for selector strategies (most reliable first)
    SELECTOR_PRIORITY: List[str] = [
        'data-testid',
        'aria-label',
        'role',
        'text',
        'label',
        'css',
    ]
    
    def __init__(self, page: Page, timeout: int = 30000, retry_count: int = 3) -> None:
        """
        Initialize selector manager.
        
        Args:
            page: Playwright page instance
            timeout: Default timeout in milliseconds (default: 30000)
            retry_count: Number of retries with exponential backoff (default: 3)
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
        
        Attempts to find an element using the primary selector. If that fails,
        tries alternative selectors and retries with exponential backoff.
        
        Args:
            selector: Primary CSS selector or text selector
            description: Optional description for logging and error messages
            timeout: Timeout in milliseconds (uses instance default if None)
            state: Element state to wait for: "visible", "hidden", "attached",
                  or "detached" (default: "visible")
            
        Returns:
            Playwright Locator if element is found, None otherwise
            
        Example:
            ```python
            locator = await selector_manager.find_element(
                'button.submit',
                "Submit button",
                timeout=5000
            )
            if locator:
                await locator.click()
            ```
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
            except Exception as e:
                logger.debug(f"Alternative selector '{alt_selector}' failed: {e}")
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
            except Exception as e:
                logger.debug(f"Retry {attempt + 1} with selector '{selector}' failed: {e}")
                continue
        
        logger.warning(f"Element not found after all attempts: {description or selector}")
        return None
    
    def _generate_alternatives(self, selector: str) -> List[str]:
        """
        Generate alternative selectors based on primary selector.
        
        Analyzes the primary selector and generates alternative selectors
        that might match the same element. For example, if the selector
        contains "button", it will also try role-based selectors.
        
        Args:
            selector: Primary selector to analyze
            
        Returns:
            List of alternative selector strings to try
            
        Example:
            ```python
            alternatives = manager._generate_alternatives('button.submit')
            # Might return: ['[role="button"]', 'text="Submit"']
            ```
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
        
        Creates a Playwright text selector that matches elements containing
        the specified text.
        
        Args:
            text: Text content to match
            exact: If True, matches exact text; if False, matches partial text
                  (default: False)
            
        Returns:
            Selector string (e.g., 'text="Submit"' or 'text=Submit')
            
        Example:
            ```python
            selector = manager.by_text("Submit", exact=True)
            # Returns: 'text="Submit"'
            ```
        """
        if exact:
            return f'text="{text}"'
        return f'text={text}'
    
    def by_role(self, role: str, name: Optional[str] = None) -> str:
        """
        Create selector by ARIA role.
        
        Creates a Playwright role selector that matches elements with the
        specified ARIA role, optionally filtered by accessible name.
        
        Args:
            role: ARIA role (e.g., "button", "link", "textbox", "heading")
            name: Optional accessible name to filter by (default: None)
            
        Returns:
            Selector string (e.g., 'role=button' or 'role=button[name="Submit"]')
            
        Example:
            ```python
            selector = manager.by_role("button", name="Submit")
            # Returns: 'role=button[name="Submit"]'
            ```
        """
        if name:
            return f'role={role}[name="{name}"]'
        return f'role={role}'
    
    def by_test_id(self, test_id: str) -> str:
        """
        Create selector by data-testid attribute.
        
        Creates a selector for elements with a specific data-testid attribute.
        This is the most reliable selector strategy as it's specifically
        designed for testing.
        
        Args:
            test_id: Value of the data-testid attribute
            
        Returns:
            Selector string (e.g., '[data-testid="submit-button"]')
            
        Example:
            ```python
            selector = manager.by_test_id("submit-button")
            # Returns: '[data-testid="submit-button"]'
            ```
        """
        return f'[data-testid="{test_id}"]'
    
    def by_label(self, label_text: str) -> str:
        """
        Create selector by label text.
        
        Creates a selector that finds form fields by their associated label
        text. Useful for form interactions where you know the label but not
        the field's name or ID.
        
        Args:
            label_text: Text content of the label element
            
        Returns:
            Selector string (e.g., 'label:has-text("Email")')
            
        Example:
            ```python
            selector = manager.by_label("Email Address")
            # Returns: 'label:has-text("Email Address")'
            ```
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
        
        Similar to find_element, but raises an exception if the element
        is not found within the timeout. This is useful when the element
        is required for the test to continue.
        
        Args:
            selector: CSS selector or text selector to wait for
            description: Optional description for error messages
            timeout: Timeout in milliseconds (uses instance default if None)
            state: Element state to wait for: "visible", "hidden", "attached",
                  or "detached" (default: "visible")
            
        Returns:
            Playwright Locator when element is found
            
        Raises:
            PlaywrightTimeoutError: If element is not found within timeout
            
        Example:
            ```python
            try:
                locator = await selector_manager.wait_for_element(
                    'button.submit',
                    "Submit button",
                    timeout=10000
                )
                await locator.click()
            except PlaywrightTimeoutError:
                print("Submit button did not appear")
            ```
        """
        locator = await self.find_element(selector, description, timeout, state)
        if locator is None:
            raise PlaywrightTimeoutError(
                f"Element not found: {description or selector} "
                f"(timeout: {timeout or self.timeout}ms)"
            )
        return locator


