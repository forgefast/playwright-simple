#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Navigation methods for SimpleTestBase.

Contains methods for navigating between pages, browser history, and menu navigation.
"""

import asyncio
import logging
from typing import List, Optional, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .cursor import CursorManager
from .screenshot import ScreenshotManager
from .selectors import SelectorManager
from .config import TestConfig
from .exceptions import NavigationError, ElementNotFoundError
from .constants import (
    CURSOR_HOVER_DELAY,
    CURSOR_CLICK_EFFECT_DELAY,
    INVALID_URL_MSG,
)

logger = logging.getLogger(__name__)


class NavigationMixin:
    """
    Mixin providing navigation methods for test base classes.
    
    This mixin provides methods for navigating between pages, browser history,
    and menu navigation. It assumes the base class has:
    - page: Playwright Page instance
    - cursor_manager: CursorManager instance
    - screenshot_manager: ScreenshotManager instance
    - selector_manager: SelectorManager instance
    - config: TestConfig instance
    - _ensure_cursor: Method to ensure cursor is injected
    """
    
    async def _ensure_cursor(self) -> None:
        """
        Ensure cursor is injected.
        
        Must be implemented by base class.
        
        Raises:
            NotImplementedError: If not implemented by base class
        """
        raise NotImplementedError("_ensure_cursor must be implemented by base class")
    
    async def _navigate_with_cursor(
        self,
        navigation_func: Any,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Execute navigation function with cursor management.
        
        Ensures cursor is injected before navigation and re-injects after
        navigation completes.
        
        Args:
            navigation_func: Navigation function to execute
            *args: Positional arguments for navigation function
            **kwargs: Keyword arguments for navigation function
            
        Raises:
            Exception: If navigation or cursor injection fails
        """
        try:
            await self._ensure_cursor()
            await navigation_func(*args, **kwargs)
            await asyncio.sleep(0.05)  # NAVIGATION_DELAY
            
            # Re-inject cursor after navigation
            try:
                await self.cursor_manager.inject(force=True)
            except Exception as e:
                logger.warning(
                    f"Failed to inject cursor after navigation, "
                    f"ensuring cursor exists: {e}"
                )
                await self.cursor_manager._ensure_cursor_exists()
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise
    
    async def go_to(self, url: str) -> 'NavigationMixin':
        """
        Navigate to a URL by clicking on the corresponding link (cursor is the protagonist).
        
        If a link matching the URL is found on the current page, the cursor will:
        1. Move to the link
        2. Show hover effect
        3. Click with visual animation
        4. Navigate
        
        If no link is found, navigates directly but cursor still moves to center first.
        
        Args:
            url: Full URL or relative path
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.go_to("/dashboard")
            await test.go_to("https://example.com")
            ```
        """
        logger.info(f"Iniciando navegação para: {url}")
        current_url = self.page.url
        logger.debug(f"URL atual antes da navegação: {current_url}")
        
        await self._ensure_cursor()
        
        # Validate URL format
        if not url.startswith("http") and not url.startswith("/"):
            logger.error(f"URL inválida: {url}")
            raise NavigationError(INVALID_URL_MSG.format(url=url))
        
        if url.startswith("http"):
            full_url = url
            target_path = None
        else:
            base_url = self.config.base_url.rstrip('/')
            full_url = f"{base_url}{url}"
            target_path = url
        
        # Try to find a link on the current page that matches the target URL
        # This makes the cursor the protagonist - it must click to navigate
        link_found = False
        if target_path and not url.startswith("http"):
            try:
                # Try multiple selectors to find the link
                link_selectors = [
                    f'a[href="{target_path}"]',
                    f'a[href="{url}"]',
                    f'a[href*="{target_path}"]',
                ]
                
                for selector in link_selectors:
                    try:
                        link_element = self.page.locator(selector).first
                        if await link_element.count() > 0:
                            # Found a link! Move cursor to it and click
                            box = await link_element.bounding_box()
                            if box:
                                x = box['x'] + box['width'] / 2
                                y = box['y'] + box['height'] / 2
                                
                                # Move cursor to link
                                await self.cursor_manager.move_to(x, y)
                                
                                # Show hover effect
                                if self.config.cursor.hover_effect:
                                    await self.cursor_manager.show_hover_effect(x, y, True)
                                    await asyncio.sleep(CURSOR_HOVER_DELAY)
                                
                                # Click with visual animation
                                await self.cursor_manager.show_click_effect(x, y)
                                await asyncio.sleep(CURSOR_CLICK_EFFECT_DELAY)
                                
                                # Now click the link
                                await link_element.click()
                                link_found = True
                                break
                    except Exception:
                        continue
            except Exception as e:
                logger.debug(f"Could not find link for {url}, navigating directly: {e}")
        
        # If no link found, navigate directly but keep cursor position
        try:
            if not link_found:
                # Don't reset cursor position - keep it where it is
                # Navigate directly
                logger.debug(f"Navegando diretamente para: {full_url}")
                await self.page.goto(full_url, wait_until="load", timeout=self.config.browser.navigation_timeout)
            else:
                # Wait for navigation to complete after clicking link
                logger.debug(f"Aguardando navegação após clique no link")
                await self.page.wait_for_load_state("load", timeout=self.config.browser.navigation_timeout)
            
            # Check if URL changed
            new_url = self.page.url
            if new_url != current_url:
                logger.info(f"Navegação bem-sucedida: {current_url} -> {new_url}")
            else:
                logger.warning(
                    f"URL não mudou após navegação (pode ser SPA): {url} "
                    f"(URL atual: {new_url})"
                )
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout na navegação para '{url}': {e}")
            raise NavigationError(f"Timeout na navegação para '{url}': {e}") from e
        except Exception as e:
            logger.error(f"Falha na navegação para '{url}': {e}", exc_info=True)
            raise NavigationError(f"Falha na navegação para '{url}': {e}") from e
        
        await asyncio.sleep(0.1)
        
        # After navigation, ensure cursor exists
        try:
            await self.cursor_manager._ensure_cursor_exists()
        except Exception as e:
            logger.warning(f"Failed to ensure cursor exists after navigation, trying injection: {e}")
            try:
                await self.cursor_manager.inject(force=True)
            except Exception as e2:
                logger.error(f"Failed to inject cursor after navigation: {e2}")
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("navigate", url)
        
        return self
    
    async def back(self) -> 'NavigationMixin':
        """
        Navigate back in browser history.
        
        Returns:
            Self for method chaining
            
        Raises:
            NavigationError: If navigation fails
            
        Example:
            ```python
            await test.back()
            ```
        """
        current_url = self.page.url
        logger.info(f"Iniciando navegação para trás (URL atual: {current_url})")
        
        try:
            await self._navigate_with_cursor(
                self.page.go_back,
                wait_until="load",
                timeout=self.config.browser.navigation_timeout
            )
            new_url = self.page.url
            if new_url != current_url:
                logger.info(f"Navegação para trás bem-sucedida: {current_url} -> {new_url}")
            else:
                logger.warning(f"URL não mudou após navegação para trás: {new_url}")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout na navegação para trás: {e}")
            raise NavigationError(f"Timeout na navegação para trás: {e}") from e
        except Exception as e:
            logger.error(f"Falha na navegação para trás: {e}", exc_info=True)
            raise NavigationError(f"Falha na navegação para trás: {e}") from e
        
        return self
    
    async def forward(self) -> 'NavigationMixin':
        """
        Navigate forward in browser history.
        
        Returns:
            Self for method chaining
            
        Raises:
            NavigationError: If navigation fails
            
        Example:
            ```python
            await test.forward()
            ```
        """
        current_url = self.page.url
        logger.info(f"Iniciando navegação para frente (URL atual: {current_url})")
        
        try:
            await self._navigate_with_cursor(
                self.page.go_forward,
                wait_until="load",
                timeout=self.config.browser.navigation_timeout
            )
            new_url = self.page.url
            if new_url != current_url:
                logger.info(f"Navegação para frente bem-sucedida: {current_url} -> {new_url}")
            else:
                logger.warning(f"URL não mudou após navegação para frente: {new_url}")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout na navegação para frente: {e}")
            raise NavigationError(f"Timeout na navegação para frente: {e}") from e
        except Exception as e:
            logger.error(f"Falha na navegação para frente: {e}", exc_info=True)
            raise NavigationError(f"Falha na navegação para frente: {e}") from e
        
        return self
    
    async def refresh(self) -> 'NavigationMixin':
        """
        Refresh the current page.
        
        Returns:
            Self for method chaining
            
        Raises:
            NavigationError: If refresh fails
            
        Example:
            ```python
            await test.refresh()
            ```
        """
        current_url = self.page.url
        logger.info(f"Iniciando refresh da página (URL atual: {current_url})")
        
        try:
            await self._navigate_with_cursor(
                self.page.reload,
                wait_until="load",
                timeout=self.config.browser.navigation_timeout
            )
            logger.info(f"Refresh da página bem-sucedido: {current_url}")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout no refresh da página: {e}")
            raise NavigationError(f"Timeout no refresh da página: {e}") from e
        except Exception as e:
            logger.error(f"Falha no refresh da página: {e}", exc_info=True)
            raise NavigationError(f"Falha no refresh da página: {e}") from e
        
        return self
    
    async def navigate(self, menu_path: List[str]) -> 'NavigationMixin':
        """
        Navigate through a menu path.
        
        Clicks through a series of menu items in sequence. Useful for
        navigating hierarchical menus.
        
        Args:
            menu_path: List of menu items to navigate (e.g., ["Vendas", "Pedidos"])
            
        Returns:
            Self for method chaining
            
        Raises:
            ElementNotFoundError: If any menu item is not found
            NavigationError: If navigation fails
            
        Example:
            ```python
            await test.navigate(["Menu", "Submenu", "Item"])
            await test.navigate(["Vendas", "Pedidos"])
            ```
        """
        if not menu_path:
            raise ValueError("menu_path cannot be empty")
        
        path_str = " > ".join(menu_path)
        logger.info(f"Iniciando navegação pelo menu: {path_str}")
        
        try:
            await self._ensure_cursor()
            
            for i, menu_item in enumerate(menu_path):
                if not menu_item or not menu_item.strip():
                    raise ValueError(f"Menu item at index {i} is empty")
                
                # Try to find and click menu item
                selectors = [
                    f'a:has-text("{menu_item}")',
                    f'button:has-text("{menu_item}")',
                    f'[role="menuitem"]:has-text("{menu_item}")',
                    f'[data-menu="{menu_item}"]',
                ]
                
                clicked = False
                for selector in selectors:
                    try:
                        # Use click method from base class
                        await self.click(selector, f"Menu {menu_item}")
                        clicked = True
                        await asyncio.sleep(0.1)
                        break
                    except (ElementNotFoundError, PlaywrightTimeoutError) as e:
                        logger.debug(f"Menu selector '{selector}' failed: {e}")
                        continue
                    except Exception as e:
                        logger.warning(
                            f"Unexpected error trying menu selector '{selector}': {e}"
                        )
                        continue
                
                if not clicked:
                    logger.error(
                        f"Item de menu não encontrado: '{menu_item}' "
                        f"(caminho até aqui: {' > '.join(menu_path[:i+1])})"
                    )
                    raise ElementNotFoundError(
                        f"Menu item '{menu_item}' not found. "
                        f"Path so far: {' > '.join(menu_path[:i+1])}"
                    )
            
            logger.info(f"Navegação pelo menu concluída com sucesso: {path_str}")
        except ElementNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Falha na navegação pelo menu {path_str}: {e}", exc_info=True)
            raise NavigationError(f"Failed to navigate menu path: {e}") from e
        
        return self

