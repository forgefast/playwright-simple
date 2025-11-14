#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base class for simple Playwright tests.

Provides easy-to-use methods for common actions, designed for QAs
without deep programming knowledge while maintaining flexibility for advanced use cases.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from .config import TestConfig
from .cursor import CursorManager
from .screenshot import ScreenshotManager
from .selectors import SelectorManager
from .session import SessionManager
from .helpers import TestBaseHelpers
from ..extensions import ExtensionRegistry, Extension
from .interactions import InteractionMixin
from .assertions import AssertionMixin
from .wait import WaitMixin
from .navigation import NavigationMixin
from .forms import FormsMixin
from .queries import QueryMixin
from .ui_helpers import UIHelpersMixin
from .auth import AuthMixin
from .exceptions import (
    ElementNotFoundError,
    NavigationError,
)
from .constants import (
    CURSOR_HOVER_DELAY,
    CURSOR_CLICK_EFFECT_DELAY,
    NAVIGATION_DELAY,
    ACTION_DELAY,
    TYPE_DELAY,
    TYPE_CHAR_DELAY,
    ELEMENT_NOT_FOUND_MSG,
    INVALID_URL_MSG,
)

logger = logging.getLogger(__name__)


class SimpleTestBase(
    InteractionMixin,
    AssertionMixin,
    WaitMixin,
    NavigationMixin,
    FormsMixin,
    QueryMixin,
    UIHelpersMixin,
    AuthMixin
):
    """
    Base class for simple visual tests.
    
    Provides easy-to-use methods for common actions with automatic
    cursor visualization, screenshots, and smart element selection.
    
    Uses composition with specialized mixins for better code organization:
    - InteractionMixin: click, type, select, hover, drag, scroll
    - AssertionMixin: assert_text, assert_visible, assert_url, etc.
    - WaitMixin: wait, wait_for, wait_for_url, wait_for_text
    - NavigationMixin: go_to, back, forward, refresh, navigate
    - FormsMixin: fill_form, fill_by_label, select_by_label
    - QueryMixin: get_text, get_attr, is_visible, is_enabled
    - UIHelpersMixin: wait_for_modal, close_modal, click_button, get_card_content
    - AuthMixin: login (generic)
    
    Example:
        ```python
        async def test_example(page, test):
            await test.login("admin", "senha123")
            await test.go_to("/dashboard")
            await test.click('button:has-text("Criar")')
            await test.type('input[name="name"]', "Item Teste")
            await test.assert_text(".success-message", "Item criado")
        ```
    """
    
    def __init__(
        self,
        page: Page,
        config: Optional[TestConfig] = None,
        test_name: Optional[str] = None,
        cursor_manager: Optional[CursorManager] = None,
        screenshot_manager: Optional[ScreenshotManager] = None,
        selector_manager: Optional[SelectorManager] = None,
        session_manager: Optional[SessionManager] = None,
        helpers: Optional[TestBaseHelpers] = None
    ):
        """
        Initialize test base.
        
        Uses Dependency Injection to allow customization of managers and helpers.
        If not provided, creates default instances.
        
        Args:
            page: Playwright page instance
            config: Test configuration (uses defaults if not provided)
            test_name: Name of current test (for organization)
            cursor_manager: Optional CursorManager instance (creates default if None)
            screenshot_manager: Optional ScreenshotManager instance (creates default if None)
            selector_manager: Optional SelectorManager instance (creates default if None)
            session_manager: Optional SessionManager instance (creates default if None)
            helpers: Optional TestBaseHelpers instance (creates default if None)
        """
        self.page = page
        self.config = config or TestConfig()
        self.test_name = test_name or "default"
        
        # Initialize managers with Dependency Injection
        self.cursor_manager = cursor_manager or CursorManager(page, self.config.cursor)
        self.screenshot_manager = screenshot_manager or ScreenshotManager(page, self.config.screenshots, test_name)
        self.selector_manager = selector_manager or SelectorManager(page, self.config.browser.timeout)
        self.session_manager = session_manager or SessionManager()
        
        # Initialize helpers with Dependency Injection
        helpers_instance = helpers or TestBaseHelpers(
            page,
            self.cursor_manager,
            self.config,
            self.selector_manager
        )
        
        # Initialize mixins (they access attributes directly via inheritance)
        # IMPORTANT: Initialize mixins AFTER creating helpers, and set helpers immediately
        # Call parent __init__ first (which calls InteractionMixin.__init__)
        # This will set self._helpers = None, so we need to set it again after
        super().__init__()
        
        # Now set the helpers instance (this overrides the None set by InteractionMixin.__init__)
        self._helpers = helpers_instance
        # Also call _set_helpers to ensure it's properly set on the mixin
        if hasattr(self, '_set_helpers'):
            self._set_helpers(helpers_instance)
        
        # Also set helpers on other mixins that might need it (they inherit from InteractionMixin)
        # But most mixins access attributes directly, so this should be sufficient
        
        # Inject cursor on first action
        self._cursor_injected = False
        
        # Initialize extension registry
        self.extensions = ExtensionRegistry()
        # Initialize extensions with this test instance
        # (will be called when extensions are registered)
    
    async def register_extension(self, extension: Extension) -> None:
        """
        Register an extension.
        
        Args:
            extension: Extension instance to register
        """
        self.extensions.register(extension)
        await extension.initialize(self)
    
    async def cleanup_extensions(self) -> None:
        """Cleanup all registered extensions."""
        await self.extensions.cleanup_all()
    
    async def _ensure_cursor(self) -> None:
        """Ensure cursor is injected."""
        if not self._cursor_injected:
            await self.cursor_manager.inject()
            self._cursor_injected = True
    
    async def _prepare_element_interaction(
        self, 
        selector: str, 
        description: str = ""
    ) -> Tuple[Locator, Optional[float], Optional[float]]:
        """
        Prepare element for interaction: find element and get position.
        
        Args:
            selector: CSS selector or text of element
            description: Description of element
            
        Returns:
            Tuple of (element, x, y) or (element, None, None) if no bounding box
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            from .exceptions import ElementNotFoundError
            raise ElementNotFoundError(
                ELEMENT_NOT_FOUND_MSG.format(description=description or selector)
            )
        
        box = await element.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            return element, x, y
        return element, None, None
    
    async def _move_cursor_to_element(
        self, 
        x: float, 
        y: float, 
        show_hover: bool = True, 
        show_click_effect: bool = True, 
        click_count: int = 1
    ) -> None:
        """
        Move cursor to element position with visual effects.
        
        Args:
            x: X coordinate
            y: Y coordinate
            show_hover: Whether to show hover effect
            show_click_effect: Whether to show click effect
            click_count: Number of click effects to show (for double-click)
        """
        # Move cursor to element
        await self.cursor_manager.move_to(x, y)
        
        # Hover effect is disabled - skip it completely
        # Show click effect(s) only
        if show_click_effect:
            for _ in range(click_count):
                await self.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(CURSOR_CLICK_EFFECT_DELAY)
    
    # ==================== Screenshot Methods ====================
    
    async def screenshot(self, name: Optional[str] = None, full_page: Optional[bool] = None, element: Optional[str] = None, description: Optional[str] = None) -> Path:
        """
        Take a screenshot.
        
        Args:
            name: Name for screenshot file
            full_page: Whether to capture full page
            element: Selector for element to screenshot
            description: Optional description for documentation
            
        Returns:
            Path to saved screenshot
            
        Example:
            ```python
            path = await test.screenshot("after_login", description="Dashboard após login")
            path = await test.screenshot(element='.dashboard')
            ```
        """
        return await self.screenshot_manager.capture(name, full_page, element, description=description)
    
    def set_test_name(self, test_name: str):
        """
        Update test name for organization.
        
        Args:
            test_name: New test name
        """
        self.test_name = test_name
        self.screenshot_manager.set_test_name(test_name)
    
    # ==================== Session Methods ====================
    
    async def save_session(self, session_name: Optional[str] = None, include_storage: bool = True) -> Path:
        """
        Save current browser session state (cookies, localStorage, sessionStorage).
        
        Args:
            session_name: Name to save session as (defaults to test_name)
            include_storage: Whether to include localStorage/sessionStorage
            
        Returns:
            Path to saved session file
            
        Example:
            ```python
            await test.save_session("login_session")
            ```
        """
        if session_name is None:
            session_name = self.test_name
        
        context = self.page.context
        return await self.session_manager.save_session(context, session_name, include_storage)
    
    async def load_session(self, session_name: str, apply_storage: bool = True) -> bool:
        """
        Load browser session state from a previously saved session.
        
        Args:
            session_name: Name of session to load
            apply_storage: Whether to apply localStorage/sessionStorage
            
        Returns:
            True if session was loaded, False if not found
            
        Example:
            ```python
            await test.load_session("login_session")
            ```
        """
        context = self.page.context
        return await self.session_manager.load_session(context, session_name, apply_storage)
    
    # ==================== Wait Methods ====================
    
    async def wait_until_ready(self, timeout: Optional[int] = None) -> 'SimpleTestBase':
        """
        Wait until page is ready (loaded and stable).
        
        This is a generic method that works for any web application.
        It waits for the page to reach the configured load state.
        
        Args:
            timeout: Maximum time to wait in milliseconds (default: from config)
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.wait_until_ready()
            ```
        """
        timeout = timeout or self.config.browser.wait_timeout
        load_state = self.config.browser.wait_for_load
        
        try:
            # Wait for the configured load state
            if load_state in ["load", "domcontentloaded", "networkidle"]:
                await self.page.wait_for_load_state(load_state, timeout=timeout)
            else:
                # Default to load if invalid value
                await self.page.wait_for_load_state("load", timeout=timeout)
        except Exception as e:
            # Don't fail if wait times out - just log
            logger.debug(f"wait_until_ready timeout or error: {e}")
        
        return self