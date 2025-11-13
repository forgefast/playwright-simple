#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interaction methods for SimpleTestBase.

Contains click, type, select, hover, drag, and scroll methods.
"""

import asyncio
import logging
from typing import Optional, TYPE_CHECKING, Any

from .helpers import TestBaseHelpers
from .constants import (
    ACTION_DELAY,
    TYPE_DELAY,
    TYPE_CHAR_DELAY,
    CURSOR_HOVER_DELAY,
    CURSOR_CLICK_EFFECT_DELAY,
)

if TYPE_CHECKING:
    from playwright.async_api import Page, Locator

logger = logging.getLogger(__name__)


class InteractionMixin:
    """
    Mixin providing interaction methods for test base classes.
    
    This mixin provides common interaction methods like click, type, select,
    hover, drag, and scroll. It assumes the base class has the following
    attributes:
    - page: Playwright Page instance
    - cursor_manager: CursorManager instance
    - screenshot_manager: ScreenshotManager instance
    - selector_manager: SelectorManager instance
    - config: TestConfig instance
    - _helpers: TestBaseHelpers instance (set via _set_helpers)
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize mixin.
        
        Must be called after parent class initialization.
        The base class should call _set_helpers() after creating helpers.
        
        Args:
            *args: Positional arguments passed to parent
            **kwargs: Keyword arguments passed to parent
        """
        super().__init__(*args, **kwargs)
        # Helpers will be set by the base class
        self._helpers: Optional[TestBaseHelpers] = None
    
    def _set_helpers(self, helpers: TestBaseHelpers) -> None:
        """
        Set helpers instance.
        
        Called by base class after creating TestBaseHelpers instance.
        
        Args:
            helpers: TestBaseHelpers instance to use
        """
        self._helpers = helpers
    
    async def click(self, selector: str, description: str = "") -> 'InteractionMixin':
        """
        Click on an element.
        
        Moves cursor to element, shows visual click effect, and clicks.
        Takes screenshot if auto-screenshots are enabled.
        
        Args:
            selector: CSS selector or text of element to click
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            RuntimeError: If helpers are not initialized
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            await test.click('button:has-text("Submit")')
            await test.click('#submit-btn', description="Submit button")
            ```
        """
        if self._helpers is None:
            raise RuntimeError(
                "_helpers not initialized. "
                "Make sure base class calls _set_helpers() after creating helpers."
            )
        
        try:
            await self._helpers.ensure_cursor()
            
            try:
                element, x, y = await self._helpers.prepare_element_interaction(selector, description)
            except Exception as e:
                logger.warning(
                    f"Elemento não encontrado para clique: '{selector}' "
                    f"(descrição: '{description}'). Erro: {e}"
                )
                raise
            
            # Log coordinates when element is found
            if x is not None and y is not None:
                logger.debug(
                    f"Elemento encontrado para clique: '{selector}' "
                    f"em coordenadas ({x:.0f}, {y:.0f})"
                )
            else:
                logger.debug(
                    f"Elemento encontrado para clique: '{selector}' "
                    f"(coordenadas não disponíveis)"
                )
            
            # Move cursor and show effects
            if x is not None and y is not None:
                # Move cursor first (with human-like speed)
                await self._helpers.move_cursor_to_element(
                    x, y,
                    show_hover=False,
                    show_click_effect=False,
                    click_count=1
                )
                await asyncio.sleep(ACTION_DELAY * 3)  # Pause after movement
                
                # Show click effect BEFORE clicking (so it's visible)
                await self.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(0.1)  # Small pause to show effect
            
            # Capture state before click
            state_before = await self._helpers.detect_state_change()
            
            # Execute click
            await element.click()
            logger.info(
                f"Clique executado com sucesso: '{selector}' "
                f"(descrição: '{description}')"
            )
            await asyncio.sleep(ACTION_DELAY * 2)  # Pause after click
            
            # Detect state change after click
            state_after = await self._helpers.detect_state_change(state_before)
            if state_after.get('state_changed'):
                logger.info(
                    f"Estado da página mudou após clique: '{selector}' "
                    f"(URL mudou: {state_after.get('url_changed', False)})"
                )
            else:
                logger.debug(
                    f"Estado da página não mudou após clique: '{selector}' "
                    f"(pode ser ação que não causa navegação)"
                )
            
            # Screenshot
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("click", selector)
        except Exception as e:
            logger.error(
                f"Falha ao clicar no elemento '{selector}' "
                f"(descrição: '{description}'): {e}",
                exc_info=True
            )
            raise
        
        return self
    
    async def double_click(self, selector: str, description: str = "") -> 'InteractionMixin':
        """
        Double-click on an element.
        
        Moves cursor to element, shows visual click effects (2 clicks),
        and performs double-click.
        
        Args:
            selector: CSS selector or text of element to double-click
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            RuntimeError: If helpers are not initialized
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            await test.double_click('.editable-field')
            ```
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        try:
            await self._helpers.ensure_cursor()
            
            try:
                element, x, y = await self._helpers.prepare_element_interaction(selector, description)
            except Exception as e:
                logger.warning(
                    f"Elemento não encontrado para duplo-clique: '{selector}' "
                    f"(descrição: '{description}'). Erro: {e}"
                )
                raise
            
            if x is not None and y is not None:
                logger.debug(
                    f"Elemento encontrado para duplo-clique: '{selector}' "
                    f"em coordenadas ({x:.0f}, {y:.0f})"
                )
            
            # Move cursor and show effects (2 clicks for double-click)
            if x is not None and y is not None:
                await self._helpers.move_cursor_to_element(
                    x, y,
                    show_hover=True,
                    show_click_effect=True,
                    click_count=2
                )
            
            # Execute double-click
            await element.dblclick()
            logger.info(
                f"Duplo-clique executado com sucesso: '{selector}' "
                f"(descrição: '{description}')"
            )
            await asyncio.sleep(ACTION_DELAY)
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("double_click", selector)
        except Exception as e:
            logger.error(
                f"Falha ao executar duplo-clique no elemento '{selector}' "
                f"(descrição: '{description}'): {e}",
                exc_info=True
            )
            raise
        
        return self
    
    async def right_click(self, selector: str, description: str = "") -> 'InteractionMixin':
        """
        Right-click on an element.
        
        Moves cursor to element, shows visual click effect, and performs
        right-click (context menu).
        
        Args:
            selector: CSS selector or text of element to right-click
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            RuntimeError: If helpers are not initialized
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            await test.right_click('.context-menu-trigger')
            ```
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        try:
            await self._helpers.ensure_cursor()
            
            try:
                element, x, y = await self._helpers.prepare_element_interaction(selector, description)
            except Exception as e:
                logger.warning(
                    f"Elemento não encontrado para clique direito: '{selector}' "
                    f"(descrição: '{description}'). Erro: {e}"
                )
                raise
            
            if x is not None and y is not None:
                logger.debug(
                    f"Elemento encontrado para clique direito: '{selector}' "
                    f"em coordenadas ({x:.0f}, {y:.0f})"
                )
            
            # Move cursor and show effects
            if x is not None and y is not None:
                await self._helpers.move_cursor_to_element(
                    x, y,
                    show_hover=False,
                    show_click_effect=True,
                    click_count=1
                )
            
            # Execute right-click
            await element.click(button="right")
            logger.info(
                f"Clique direito executado com sucesso: '{selector}' "
                f"(descrição: '{description}')"
            )
            await asyncio.sleep(ACTION_DELAY)
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("right_click", selector)
        except Exception as e:
            logger.error(
                f"Falha ao executar clique direito no elemento '{selector}' "
                f"(descrição: '{description}'): {e}",
                exc_info=True
            )
            raise
        
        return self
    
    async def type(self, selector: str, text: str, description: str = "") -> 'InteractionMixin':
        """
        Type text into a field.
        
        Moves cursor to field, clicks to focus, clears existing content,
        and types text character by character for visual effect.
        
        Args:
            selector: CSS selector of input/textarea field
            text: Text to type into the field
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            RuntimeError: If helpers are not initialized
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            await test.type('input[name="email"]', "user@example.com")
            await test.type('#message', "Hello world")
            ```
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        try:
            await self._helpers.ensure_cursor()
            
            element, x, y = await self._helpers.prepare_element_interaction(selector, description)
            
            # Move cursor to element and click first
            if x is not None and y is not None:
                # Move cursor to field (with human-like speed)
                await self.cursor_manager.move_to(x, y)
                await asyncio.sleep(ACTION_DELAY * 3)  # Pause after movement
                
                # Show click effect BEFORE clicking (so it's visible)
                await self.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(0.1)  # Small pause to show effect
                
                # Click the element to focus it
                await element.click()
                await asyncio.sleep(TYPE_DELAY)
            else:
                # No coordinates available, but still need to click to focus
                await element.click()
                await asyncio.sleep(TYPE_DELAY)
            
            # Capture state before typing
            state_before = await self._helpers.detect_state_change()
            
            # Clear and type
            await element.clear()
            await asyncio.sleep(ACTION_DELAY)
            
            # Type character by character for visual effect
            for char in text:
                await element.type(char, delay=TYPE_CHAR_DELAY)
            
            await asyncio.sleep(ACTION_DELAY)
            
            # Verify field was filled correctly
            try:
                field_value = await element.input_value()
                if field_value == text:
                    logger.info(
                        f"Campo preenchido com sucesso: '{selector}' "
                        f"(valor: '{text[:50]}...' se muito longo)"
                    )
                else:
                    logger.warning(
                        f"Campo preenchido mas valor não corresponde: '{selector}' "
                        f"(esperado: '{text[:30]}...', obtido: '{field_value[:30]}...')"
                    )
            except Exception as e:
                logger.debug(f"Não foi possível verificar valor do campo '{selector}': {e}")
            
            # Detect state change after typing
            state_after = await self._helpers.detect_state_change(state_before)
            if state_after.get('state_changed'):
                logger.info(
                    f"Estado da página mudou após digitação: '{selector}' "
                    f"(URL mudou: {state_after.get('url_changed', False)})"
                )
            
            # Screenshot
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("type", selector)
        except Exception as e:
            logger.error(f"Failed to type into element '{selector}': {e}")
            raise
        
        return self
    
    async def select(self, selector: str, option: str, description: str = "") -> 'InteractionMixin':
        """
        Select an option in a dropdown.
        
        Moves cursor to dropdown, shows visual effects, and selects option.
        
        Args:
            selector: CSS selector of select/dropdown element
            option: Option value or label to select
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            RuntimeError: If helpers are not initialized
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            await test.select('select[name="country"]', "Brazil")
            await test.select('#status-dropdown', "Active")
            ```
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        try:
            await self._helpers.ensure_cursor()
            
            element, x, y = await self._helpers.prepare_element_interaction(selector, description)
            
            # Move cursor to element and click first
            if x is not None and y is not None:
                await self._helpers.move_cursor_to_element(
                    x, y,
                    show_hover=True,
                    show_click_effect=True,
                    click_count=1
                )
            
            # Capture state before selection
            state_before = await self._helpers.detect_state_change()
            
            await element.select_option(option)
            logger.info(
                f"Opção selecionada com sucesso: '{option}' em '{selector}' "
                f"(descrição: '{description}')"
            )
            await asyncio.sleep(ACTION_DELAY * 2)
            
            # Verify option was selected
            try:
                selected_value = await element.input_value()
                logger.debug(
                    f"Valor selecionado em '{selector}': '{selected_value}' "
                    f"(esperado: '{option}')"
                )
            except Exception as e:
                logger.debug(f"Não foi possível verificar opção selecionada em '{selector}': {e}")
            
            # Detect state change after selection
            state_after = await self._helpers.detect_state_change(state_before)
            if state_after.get('state_changed'):
                logger.info(
                    f"Estado da página mudou após seleção: '{selector}' "
                    f"(URL mudou: {state_after.get('url_changed', False)})"
                )
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("select", selector)
        except Exception as e:
            logger.error(f"Failed to select option '{option}' in '{selector}': {e}")
            raise
        
        return self
    
    async def hover(self, selector: str, description: str = "") -> 'InteractionMixin':
        """
        Hover over an element.
        
        Moves cursor to element and shows hover effect. Useful for triggering
        tooltips, dropdowns, or hover states.
        
        Args:
            selector: CSS selector or text of element to hover
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            RuntimeError: If helpers are not initialized
            ElementNotFoundError: If element is not found
            
        Example:
            ```python
            await test.hover('.tooltip-trigger')
            ```
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        try:
            await self._helpers.ensure_cursor()
            
            element, x, y = await self._helpers.prepare_element_interaction(selector, description)
            
            # Move cursor and show hover effect
            if x is not None and y is not None:
                await self._helpers.move_cursor_to_element(
                    x, y,
                    show_hover=True,
                    show_click_effect=False,
                    click_count=0
                )
            
            await element.hover()
            await asyncio.sleep(ACTION_DELAY)
        except Exception as e:
            logger.error(f"Failed to hover over element '{selector}': {e}")
            raise
        
        return self
    
    async def drag(self, source: str, target: str, description: str = "") -> 'InteractionMixin':
        """
        Drag and drop from source to target.
        
        Performs drag and drop operation from source element to target element.
        
        Args:
            source: CSS selector of source element to drag
            target: CSS selector of target element to drop on
            description: Optional description for logging and error messages
            
        Returns:
            Self for method chaining
            
        Raises:
            RuntimeError: If helpers are not initialized
            ElementNotFoundError: If source or target element is not found
            
        Example:
            ```python
            await test.drag('.draggable-item', '.drop-zone')
            ```
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        try:
            await self._helpers.ensure_cursor()
            
            source_element = await self.selector_manager.find_element(
                source,
                f"Source: {description}"
            )
            target_element = await self.selector_manager.find_element(
                target,
                f"Target: {description}"
            )
            
            if source_element is None or target_element is None:
                from .exceptions import ElementNotFoundError
                raise ElementNotFoundError(
                    f"Source or target element not found: {description}"
                )
            
            await source_element.drag_to(target_element)
            await asyncio.sleep(0.1)
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action(
                    "drag",
                    f"{source}->{target}"
                )
        except Exception as e:
            logger.error(f"Failed to drag from '{source}' to '{target}': {e}")
            raise
        
        return self
    
    async def scroll(
        self,
        selector: Optional[str] = None,
        direction: str = "down",
        amount: int = 500
    ) -> 'InteractionMixin':
        """
        Scroll page or element.
        
        Scrolls the page or a specific element in the specified direction.
        
        Args:
            selector: Optional CSS selector of element to scroll.
                     If None, scrolls the page.
            direction: Scroll direction: "down", "up", "right", or "left"
            amount: Number of pixels to scroll (default: 500)
            
        Returns:
            Self for method chaining
            
        Raises:
            RuntimeError: If helpers are not initialized
            ElementNotFoundError: If selector is provided but element not found
            ValueError: If direction is invalid
            
        Example:
            ```python
            await test.scroll()  # Scroll page down
            await test.scroll('.scrollable-container', direction="up", amount=200)
            ```
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        valid_directions = {"down", "up", "right", "left"}
        if direction not in valid_directions:
            raise ValueError(
                f"Invalid direction '{direction}'. "
                f"Must be one of: {', '.join(valid_directions)}"
            )
        
        try:
            await self._helpers.ensure_cursor()
            
            if selector:
                element = await self.selector_manager.find_element(
                    selector,
                    "Scroll target"
                )
                if element is None:
                    from .exceptions import ElementNotFoundError
                    raise ElementNotFoundError(
                        f"Element not found for scrolling: {selector}"
                    )
                
                scroll_map = {
                    "down": f"element => element.scrollBy(0, {amount})",
                    "up": f"element => element.scrollBy(0, -{amount})",
                    "right": f"element => element.scrollBy({amount}, 0)",
                    "left": f"element => element.scrollBy(-{amount}, 0)",
                }
                await element.evaluate(scroll_map[direction])
            else:
                scroll_map = {
                    "down": f"window.scrollBy(0, {amount})",
                    "up": f"window.scrollBy(0, -{amount})",
                    "right": f"window.scrollBy({amount}, 0)",
                    "left": f"window.scrollBy(-{amount}, 0)",
                }
                await self.page.evaluate(scroll_map[direction])
            
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to scroll '{direction}' on '{selector or 'page'}': {e}")
            raise
        
        return self

