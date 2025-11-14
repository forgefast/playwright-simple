#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Submit Handler Module.

Handles form submission by clicking submit buttons.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

from .element_finder import ElementFinder

logger = logging.getLogger(__name__)


class SubmitHandler:
    """Handles form submission."""
    
    def __init__(self, page: Page, fast_mode: bool = False):
        """
        Initialize submit handler.
        
        Args:
            page: Playwright Page instance
            fast_mode: Enable fast mode
        """
        self.page = page
        self.fast_mode = fast_mode
        self.element_finder = ElementFinder(page)
    
    async def submit_form(
        self,
        button_text: Optional[str] = None,
        cursor_controller = None,
        visual_feedback = None
    ) -> bool:
        """
        Submit a form by clicking the submit button.
        
        Args:
            button_text: Optional text to identify specific submit button
            cursor_controller: Optional CursorController instance for visual feedback
            visual_feedback: Optional VisualFeedback instance
        
        Returns:
            True if form was submitted successfully, False otherwise
        """
        try:
            # Find submit button
            result = await self.element_finder.find_submit_button(button_text)
            
            if not result:
                logger.warning(f"Submit button not found (button_text: {button_text})")
                return False
            
            x = result.get('x')
            y = result.get('y')
            button_text_found = result.get('text', '')
            logger.debug(f"[SUBMIT] Submit button found at ({x}, {y}), button_text='{button_text}', found_text='{button_text_found}'")
            
            # Show visual feedback
            if visual_feedback and cursor_controller:
                logger.debug(f"[SUBMIT] Showing visual feedback at ({x}, {y})")
                await visual_feedback.show_click_feedback(x, y, cursor_controller)
            
            # Use mouse click directly - this will trigger DOM events that event_capture can catch
            logger.debug(f"[CLICK] Executing mouse.click at ({x}, {y}) [submit form, button_text='{button_text}']")
            await self.page.mouse.click(x, y)
            logger.debug(f"[CLICK] Mouse click completed at ({x}, {y}) [submit form]")
            
            # Small delay to ensure click event is captured (reduced in fast mode)
            await asyncio.sleep(0.05 if self.fast_mode else 0.15)
            
            logger.info(f"Form submitted (button: '{button_text_found}')")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting form: {e}")
            return False

