#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query methods for SimpleTestBase.

Contains methods for getting element information: text, attributes, visibility, etc.
"""

import logging
from typing import Optional

from .exceptions import ElementNotFoundError
from .constants import ELEMENT_NOT_FOUND_MSG

logger = logging.getLogger(__name__)


class QueryMixin:
    """
    Mixin providing query methods for test base classes.
    
    This mixin provides methods for querying element information like text
    content, attributes, visibility, and enabled state. It assumes the
    base class has:
    - selector_manager: SelectorManager instance
    """
    
    async def get_text(self, selector: str, description: str = "") -> str:
        """
        Get text content of element.
        
        Args:
            selector: CSS selector of element
            description: Optional description for logging and error messages
            
        Returns:
            Text content of element, or empty string if element has no text
            
        Raises:
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            text = await test.get_text('.status-message')
            title = await test.get_text('h1')
            ```
        """
        try:
            element = await self.selector_manager.find_element(selector, description)
            if element is None:
                raise ElementNotFoundError(
                    ELEMENT_NOT_FOUND_MSG.format(
                        description=description or selector
                    )
                )
            return (await element.text_content()) or ""
        except ElementNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get text from '{selector}': {e}")
            raise ElementNotFoundError(
                f"Failed to get text from '{description or selector}': {e}"
            ) from e
    
    async def get_attr(
        self,
        selector: str,
        attribute: str,
        description: str = ""
    ) -> Optional[str]:
        """
        Get attribute value of element.
        
        Args:
            selector: CSS selector of element
            attribute: Attribute name to get
            description: Optional description for logging and error messages
            
        Returns:
            Attribute value, or None if attribute doesn't exist or element not found
            
        Raises:
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            href = await test.get_attr('a.link', 'href')
            disabled = await test.get_attr('#submit-btn', 'disabled')
            ```
        """
        try:
            element = await self.selector_manager.find_element(selector, description)
            if element is None:
                raise ElementNotFoundError(
                    ELEMENT_NOT_FOUND_MSG.format(
                        description=description or selector
                    )
                )
            return await element.get_attribute(attribute)
        except ElementNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to get attribute '{attribute}' from '{selector}': {e}"
            )
            raise ElementNotFoundError(
                f"Failed to get attribute from '{description or selector}': {e}"
            ) from e
    
    async def is_visible(self, selector: str, description: str = "") -> bool:
        """
        Check if element is visible.
        
        Args:
            selector: CSS selector of element
            description: Optional description for logging
            
        Returns:
            True if element is visible, False if not found or not visible
            
        Example:
            ```python
            if await test.is_visible('.modal'):
                await test.close_modal()
            ```
        """
        try:
            element = await self.selector_manager.find_element(selector, description)
            if element is None:
                return False
            return await element.is_visible()
        except Exception as e:
            logger.debug(f"Failed to check visibility of '{selector}': {e}")
            return False
    
    async def is_enabled(self, selector: str, description: str = "") -> bool:
        """
        Check if element is enabled.
        
        Args:
            selector: CSS selector of element
            description: Optional description for logging
            
        Returns:
            True if element is enabled, False if not found or disabled
            
        Example:
            ```python
            if await test.is_enabled('#submit-btn'):
                await test.click('#submit-btn')
            ```
        """
        try:
            element = await self.selector_manager.find_element(selector, description)
            if element is None:
                return False
            return await element.is_enabled()
        except Exception as e:
            logger.debug(f"Failed to check enabled state of '{selector}': {e}")
            return False

