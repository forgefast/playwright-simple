#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI helper methods for SimpleTestBase.

Contains methods for modals, buttons, and generic UI interactions.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .exceptions import ElementNotFoundError

logger = logging.getLogger(__name__)


class UIHelpersMixin:
    """
    Mixin providing UI helper methods for test base classes.
    
    This mixin provides methods for interacting with common UI elements like
    modals, buttons, and cards. It assumes the base class has:
    - page: Playwright Page instance
    - config: TestConfig instance
    - screenshot_manager: ScreenshotManager instance
    - _ensure_cursor: Method to ensure cursor is injected
    """
    
    async def wait_for_modal(
        self,
        modal_selector: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> 'UIHelpersMixin':
        """
        Wait for a modal dialog to appear.
        
        Uses common modal selectors: .modal, [role="dialog"], .dialog
        
        Args:
            modal_selector: Optional custom selector for the modal.
                          Defaults to common modal patterns.
            timeout: Timeout in milliseconds
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.wait_for_modal()
            await test.close_modal()
            ```
        """
        try:
            timeout = timeout or self.config.browser.timeout
            
            if modal_selector is None:
                # Common modal selectors
                modal_selector = '.modal, [role="dialog"], .dialog, .modal-dialog'
            
            modal = self.page.locator(modal_selector).first
            await modal.wait_for(state="visible", timeout=timeout)
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("wait_for_modal")
        except Exception as e:
            logger.error(f"Failed to wait for modal '{modal_selector}': {e}")
            raise
        
        return self
    
    async def close_modal(
        self,
        close_button_selector: Optional[str] = None
    ) -> 'UIHelpersMixin':
        """
        Close any open modal dialog.
        
        Uses common close button selectors: button[aria-label*="Close"],
        button:has-text("Close"), .close, .modal-close
        
        Args:
            close_button_selector: Optional custom selector for close button.
                                 Defaults to common close button patterns.
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.wait_for_modal()
            await test.close_modal()
            ```
        """
        if close_button_selector is None:
            # Common close button selectors
            close_button_selector = (
                'button[aria-label*="Close"], '
                'button:has-text("Close"), '
                '.close, '
                '.modal-close, '
                '[data-dismiss="modal"]'
            )
        
        try:
            close_button = self.page.locator(close_button_selector).first
            if await close_button.count() > 0:
                await close_button.click()
                await asyncio.sleep(0.3)
                
                if self.config.screenshots.auto:
                    await self.screenshot_manager.capture_on_action("close_modal")
            else:
                logger.warning(
                    f"Close button not found with selector: {close_button_selector}"
                )
        except Exception as e:
            logger.error(f"Failed to close modal: {e}")
            raise
        
        return self
    
    async def click_button(
        self,
        text: str,
        context: Optional[str] = None,
        description: str = ""
    ) -> 'UIHelpersMixin':
        """
        Click a button by its visible text using CursorController.
        
        Args:
            text: Button text to match
            context: Optional context selector to narrow search
            description: Description for error messages
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.click_button("Submit")
            await test.click_button("Save", context=".form-container")
            ```
        """
        if not text or not text.strip():
            raise ValueError("Button text cannot be empty")
        
        # Get CursorController from test base
        cursor_controller = None
        if hasattr(self, '_get_cursor_controller'):
            cursor_controller = self._get_cursor_controller()
        
        if cursor_controller:
            # Use CursorController
            if not cursor_controller.is_active:
                await cursor_controller.start()
            
            success = await cursor_controller.click_by_text(text)
            if not success:
                raise ElementNotFoundError(
                    f"Button with text '{text}' not found{f' in context {context}' if context else ''}"
                )
            return self
        
        # Fallback to old method
        try:
            await self._ensure_cursor()
            
            button_selector = (
                f'button:has-text("{text}"), '
                f'a:has-text("{text}"), '
                f'[role="button"]:has-text("{text}")'
            )
            
            if context:
                context_locator = self.page.locator(context)
                button = context_locator.locator(button_selector).first
            else:
                button = self.page.locator(button_selector).first
            
            await button.wait_for(
                state="visible",
                timeout=self.config.browser.timeout
            )
            await button.click()
            await asyncio.sleep(0.2)
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("click_button", text)
        except Exception as e:
            logger.error(f"Failed to click button with text '{text}': {e}")
            raise ElementNotFoundError(
                f"Button with text '{text}' not found or not clickable: {e}"
            ) from e
        
        return self
    
    async def get_card_content(self, card_selector: str, description: str = "") -> str:
        """
        Get text content from a card or container element.
        
        Args:
            card_selector: CSS selector for the card/container
            description: Description for error messages
            
        Returns:
            Text content of the card, or empty string if not found
            
        Example:
            ```python
            content = await test.get_card_content(".status-card")
            print(f"Card content: {content}")
            ```
        """
        try:
            card = self.page.locator(card_selector).first
            if await card.count() == 0:
                if description:
                    print(f"  ⚠️  Card not found: {description}")
                return ""
            
            return (await card.text_content()) or ""
        except (ElementNotFoundError, PlaywrightTimeoutError) as e:
            if description:
                logger.warning(f"Error getting card content ({description}): {e}")
            return ""
        except Exception as e:
            if description:
                logger.error(f"Unexpected error getting card content ({description}): {e}")
            return ""

