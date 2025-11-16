#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wait methods for SimpleTestBase.

Contains methods for waiting for elements, URLs, text, etc.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WaitMixin:
    """
    Mixin providing wait methods for test base classes.
    
    This mixin provides methods for waiting for elements, URLs, text content,
    etc. It assumes the base class has:
    - page: Playwright Page instance
    - selector_manager: SelectorManager instance
    - config: TestConfig instance
    """
    
    async def wait(self, seconds: float = 1.0) -> 'WaitMixin':
        """
        Wait for a specified time.
        
        Args:
            seconds: Number of seconds to wait (default: 1.0)
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.wait(2.5)  # Wait 2.5 seconds
            ```
        """
        if seconds < 0:
            raise ValueError(f"Wait time must be non-negative, got {seconds}")
        
        await asyncio.sleep(seconds)
        return self
    
    async def wait_for(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = None,
        description: str = ""
    ) -> 'WaitMixin':
        """
        Wait for element to appear with specified state.
        
        Args:
            selector: CSS selector of element to wait for
            state: Element state to wait for: "visible", "hidden", "attached", "detached"
            timeout: Maximum time to wait in milliseconds (uses config default if None)
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            TimeoutError: If element does not appear within timeout
            
        Example:
            ```python
            await test.wait_for('.modal')
            await test.wait_for('#loading', state="hidden")
            ```
        """
        try:
            await self.selector_manager.wait_for_element(
                selector,
                description,
                timeout,
                state
            )
        except Exception as e:
            logger.error(
                f"Failed to wait for element '{selector}' (state={state}): {e}"
            )
            raise
        
        return self
    
    async def wait_for_url(
        self,
        url_pattern: str,
        timeout: Optional[int] = None
    ) -> 'WaitMixin':
        """
        Wait for URL to match pattern.
        
        Args:
            url_pattern: URL pattern to wait for (can be regex or string)
            timeout: Maximum time to wait in milliseconds (uses config default if None)
            
        Returns:
            Self for method chaining
            
        Raises:
            TimeoutError: If URL does not match pattern within timeout
            
        Example:
            ```python
            await test.wait_for_url("/dashboard")
            await test.wait_for_url(".*example.com.*")
            ```
        """
        try:
            timeout = timeout or self.config.browser.timeout
            await self.page.wait_for_url(url_pattern, timeout=timeout)
        except Exception as e:
            logger.error(f"Failed to wait for URL pattern '{url_pattern}': {e}")
            raise
        
        return self
    
    async def wait_for_text(
        self,
        selector: str,
        text: str,
        timeout: Optional[int] = None,
        description: str = ""
    ) -> 'WaitMixin':
        """
        Wait for element to contain text.
        
        Args:
            selector: CSS selector of element to check
            text: Text that should appear in element
            timeout: Maximum time to wait in milliseconds (uses config default if None)
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            TimeoutError: If text does not appear within timeout
            
        Example:
            ```python
            await test.wait_for_text('.status', "Success")
            await test.wait_for_text('#message', "Loading complete")
            ```
        """
        try:
            timeout = timeout or self.config.browser.timeout
            element = await self.selector_manager.wait_for_element(
                selector,
                description,
                timeout
            )
            await element.wait_for(state="visible", timeout=timeout)
            
            # Escape text for use in JavaScript
            escaped_text = text.replace("'", "\\'").replace('"', '\\"')
            await self.page.wait_for_function(
                f"document.querySelector('{selector}')?.textContent?.includes('{escaped_text}')",
                timeout=timeout
            )
        except Exception as e:
            logger.error(
                f"Failed to wait for text '{text}' in '{selector}': {e}"
            )
            raise
        
        return self

