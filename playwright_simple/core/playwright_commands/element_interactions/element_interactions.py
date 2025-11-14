#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Element Interactions Module.

Main interface for element interactions (click, type, submit).
Refactored to delegate to specialized handlers.
"""

import logging
from typing import Optional
from playwright.async_api import Page

from .click_handler import ClickHandler
from .type_handler import TypeHandler
from .submit_handler import SubmitHandler

logger = logging.getLogger(__name__)


class ElementInteractions:
    """Handles interactions with elements."""
    
    def __init__(self, page: Page, fast_mode: bool = False):
        """Initialize element interactions."""
        self.page = page
        self.fast_mode = fast_mode
        
        # Initialize handlers
        self.click_handler = ClickHandler(page, fast_mode)
        self.type_handler = TypeHandler(page, fast_mode)
        self.submit_handler = SubmitHandler(page, fast_mode)
    
    async def click(
        self,
        text: Optional[str] = None,
        selector: Optional[str] = None,
        role: Optional[str] = None,
        index: int = 0,
        cursor_controller = None,
        visual_feedback = None,
        description: str = ""
    ) -> bool:
        """
        Click on an element.
        
        Delegates to ClickHandler.
        """
        return await self.click_handler.click(
            text=text,
            selector=selector,
            role=role,
            index=index,
            cursor_controller=cursor_controller,
            visual_feedback=visual_feedback,
            description=description
        )
    
    async def type_text(
        self,
        text: str,
        into: Optional[str] = None,
        selector: Optional[str] = None,
        clear: bool = True,
        cursor_controller = None,
        visual_feedback = None
    ) -> bool:
        """
        Type text into an input field.
        
        Delegates to TypeHandler.
        """
        return await self.type_handler.type_text(
            text=text,
            into=into,
            selector=selector,
            clear=clear,
            cursor_controller=cursor_controller,
            visual_feedback=visual_feedback
        )
    
    async def submit_form(
        self,
        button_text: Optional[str] = None,
        cursor_controller = None,
        visual_feedback = None
    ) -> bool:
        """
        Submit a form by clicking the submit button.
        
        Delegates to SubmitHandler.
        """
        return await self.submit_handler.submit_form(
            button_text=button_text,
            cursor_controller=cursor_controller,
            visual_feedback=visual_feedback
        )
