#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assertion methods for SimpleTestBase.

Contains methods for asserting element states, text content, attributes, etc.
"""

import logging
from typing import Optional

from .exceptions import ElementNotFoundError

logger = logging.getLogger(__name__)


class AssertionMixin:
    """
    Mixin providing assertion methods for test base classes.
    
    This mixin provides assertion methods for validating element states,
    text content, attributes, and counts. It assumes the base class has:
    - page: Playwright Page instance
    - selector_manager: SelectorManager instance
    - screenshot_manager: ScreenshotManager instance (optional)
    - config: TestConfig instance
    """
    
    async def assert_text(
        self,
        selector: str,
        expected: str,
        description: str = ""
    ) -> 'AssertionMixin':
        """
        Assert element contains expected text.
        
        Args:
            selector: CSS selector of element to check
            expected: Expected text that should be contained in element
            description: Optional description for error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            ElementNotFoundError: If element is not found
            AssertionError: If text assertion fails
            
        Example:
            ```python
            await test.assert_text('.status-message', "Success")
            await test.assert_text('#error', "Error occurred")
            ```
        """
        try:
            element = await self.selector_manager.find_element(selector, description)
            if element is None:
                raise ElementNotFoundError(
                    f"Element not found: {description or selector}"
                )
            
            actual = await element.text_content()
            if expected not in (actual or ""):
                raise AssertionError(
                    f"Text assertion failed for {description or selector}: "
                    f"expected '{expected}' in '{actual}'"
                )
        except AssertionError:
            raise
        except Exception as e:
            logger.error(f"Failed to assert text in '{selector}': {e}")
            raise AssertionError(
                f"Text assertion failed for {description or selector}: {e}"
            ) from e
        
        return self
    
    async def assert_visible(
        self,
        selector: str,
        description: str = ""
    ) -> 'AssertionMixin':
        """
        Assert element is visible.
        
        Args:
            selector: CSS selector of element to check
            description: Optional description for error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            ElementNotFoundError: If element is not found
            AssertionError: If element is not visible
            
        Example:
            ```python
            await test.assert_visible('.modal')
            await test.assert_visible('#submit-button')
            ```
        """
        try:
            element = await self.selector_manager.find_element(selector, description)
            if element is None:
                raise ElementNotFoundError(
                    f"Element not found: {description or selector}"
                )
            
            if not await element.is_visible():
                raise AssertionError(
                    f"Element is not visible: {description or selector}"
                )
        except AssertionError:
            raise
        except Exception as e:
            logger.error(f"Failed to assert visibility of '{selector}': {e}")
            raise AssertionError(
                f"Visibility assertion failed for {description or selector}: {e}"
            ) from e
        
        return self
    
    async def assert_url(self, pattern: str) -> 'AssertionMixin':
        """
        Assert current URL matches pattern.
        
        Args:
            pattern: String pattern that should be contained in current URL
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If URL does not contain pattern
            
        Example:
            ```python
            await test.assert_url("/dashboard")
            await test.assert_url("example.com")
            ```
        """
        try:
            current_url = self.page.url
            if pattern not in current_url:
                raise AssertionError(
                    f"URL assertion failed: expected '{pattern}' in '{current_url}'"
                )
        except Exception as e:
            logger.error(f"Failed to assert URL pattern '{pattern}': {e}")
            raise AssertionError(f"URL assertion failed: {e}") from e
        
        return self
    
    async def assert_count(
        self,
        selector: str,
        expected_count: int,
        description: str = ""
    ) -> 'AssertionMixin':
        """
        Assert number of elements matching selector.
        
        Args:
            selector: CSS selector to count elements
            expected_count: Expected number of elements
            description: Optional description for error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If count does not match expected
            
        Example:
            ```python
            await test.assert_count('.item', 5)
            await test.assert_count('button', 3)
            ```
        """
        try:
            count = await self.page.locator(selector).count()
            if count != expected_count:
                raise AssertionError(
                    f"Count assertion failed for {description or selector}: "
                    f"expected {expected_count}, got {count}"
                )
        except AssertionError:
            raise
        except Exception as e:
            logger.error(f"Failed to assert count for '{selector}': {e}")
            raise AssertionError(
                f"Count assertion failed for {description or selector}: {e}"
            ) from e
        
        return self
    
    async def assert_attr(
        self,
        selector: str,
        attribute: str,
        expected: str,
        description: str = ""
    ) -> 'AssertionMixin':
        """
        Assert element attribute value.
        
        Args:
            selector: CSS selector of element to check
            attribute: Attribute name to check
            expected: Expected attribute value
            description: Optional description for error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            ElementNotFoundError: If element is not found
            AssertionError: If attribute value does not match
            
        Example:
            ```python
            await test.assert_attr('#submit-btn', 'disabled', None)
            await test.assert_attr('.link', 'href', '/dashboard')
            ```
        """
        try:
            element = await self.selector_manager.find_element(selector, description)
            if element is None:
                raise ElementNotFoundError(
                    f"Element not found: {description or selector}"
                )
            
            actual = await element.get_attribute(attribute)
            if actual != expected:
                raise AssertionError(
                    f"Attribute assertion failed for {description or selector}: "
                    f"expected {attribute}='{expected}', got '{actual}'"
                )
        except AssertionError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to assert attribute '{attribute}' of '{selector}': {e}"
            )
            raise AssertionError(
                f"Attribute assertion failed for {description or selector}: {e}"
            ) from e
        
        return self

