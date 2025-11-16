#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo filter menu interactions.

Handles opening and interacting with Odoo filter dropdown menus.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class FilterHelper:
    """Helper for Odoo filter menu interactions."""
    
    def __init__(self, page: Page):
        """
        Initialize filter helper.
        
        Args:
            page: Playwright page instance
        """
        self.page = page
    
    async def open_filter_menu(self) -> bool:
        """
        Open the Odoo filter dropdown menu by clicking on the filter dropdown arrow.
        
        Returns:
            True if filter menu was opened successfully
        """
        # Try to find the filter dropdown button/arrow
        # Odoo uses a dropdown toggle button with a caret/arrow icon
        filter_dropdown_selectors = [
            # Search view dropdown toggler (most specific - the actual filter button)
            'button.o_searchview_dropdown_toggler',
            'button.o_searchview_dropdown_toggler.dropdown-toggle',
            '.o_searchview_dropdown_toggler',
            # Filter dropdown button with caret (alternative)
            '.o_filters_menu .dropdown-toggle',
            '.o_filters_menu button.dropdown-toggle',
            'button.o_filters_menu_button.dropdown-toggle',
            # Filter button with caret icon
            '.o_filters_menu button:has(.fa-caret-down)',
            '.o_filters_menu button:has(.fa-chevron-down)',
            '.o_filters_menu button:has(.dropdown-caret)',
            # Generic filter menu button
            '.o_filters_menu button',
            'button.o_filters_menu_button',
            # Filter button in control panel
            '.o_control_panel .o_filters_menu button',
            '.o_control_panel button[title*="Filtros"]',
            '.o_control_panel button[title*="Filters"]',
            # Search view filter button
            '.o_searchview .o_filters_menu button',
            '.o_searchview_facet button',
            # Generic dropdown toggle in search area
            '.o_searchview button.dropdown-toggle',
            'button[title*="Ativar/Desativar painel de pesquisa"]',
        ]
        
        for selector in filter_dropdown_selectors:
            try:
                filter_btn = self.page.locator(selector).first
                if await filter_btn.count() > 0 and await filter_btn.is_visible():
                    # Click the filter dropdown button using cursor system
                    # Get the test instance from page context if available
                    test_instance = getattr(self.page, '_test_instance', None)
                    if test_instance and hasattr(test_instance, 'click'):
                        # Use test.click() which handles cursor movement
                        await test_instance.click(selector, "Botão de filtros")
                    else:
                        # Fallback: use cursor manager directly if available
                        cursor_manager = getattr(self.page, '_cursor_manager', None)
                        if cursor_manager:
                            box = await filter_btn.bounding_box()
                            if box:
                                x = box['x'] + box['width'] / 2
                                y = box['y'] + box['height'] / 2
                                await cursor_manager.move_to(x, y)
                                await asyncio.sleep(0.2)
                                await cursor_manager.show_click_effect(x, y)
                                await asyncio.sleep(0.05)
                                # Click using page.mouse to ensure cursor is at position
                                await self.page.mouse.click(x, y)
                        else:
                            # Last resort: direct click (no cursor)
                            logger.warning(
                                "DEPRECATED: filter_btn.click() usado sem cursor_manager. "
                                "Esta ação será removida em versão futura. "
                                "Certifique-se de que cursor_manager está disponível."
                            )
                            await filter_btn.click()
                    await asyncio.sleep(0.3)  # Wait for dropdown menu to open
                    
                    # Verify menu opened by checking if dropdown menu is visible
                    # Check multiple possible dropdown menu selectors
                    dropdown_menu_selectors = [
                        '.o_searchview_dropdown_menu',
                        '.o_filters_menu .dropdown-menu',
                        '.o_filters_menu_menu',
                        '.o_dropdown_menu',
                        '.dropdown-menu.show',
                        '.o_searchview .dropdown-menu',
                    ]
                    for menu_selector in dropdown_menu_selectors:
                        dropdown_menu = self.page.locator(menu_selector).first
                        if await dropdown_menu.count() > 0:
                            is_visible = await dropdown_menu.is_visible()
                            if is_visible:
                                return True
                    
                    # Also check if button aria-expanded changed to true
                    aria_expanded = await filter_btn.get_attribute('aria-expanded')
                    if aria_expanded == 'true':
                        return True
            except Exception:
                continue
        
        # Fallback: try to find filter button by title/aria-label
        filter_title_selectors = [
            'button[title*="Filtros"]',
            'button[title*="Filters"]',
            'button[aria-label*="Filtros"]',
            'button[aria-label*="Filters"]',
        ]
        
        for selector in filter_title_selectors:
            try:
                filter_btn = self.page.locator(selector).first
                if await filter_btn.count() > 0 and await filter_btn.is_visible():
                    # Check if it's in the control panel/search area (not in a menu)
                    is_in_control_panel = await filter_btn.evaluate("""
                        (el) => {
                            return el.closest('.o_control_panel, .o_searchview, .o_cp_searchview') !== null;
                        }
                    """)
                    if is_in_control_panel:
                        logger.warning(
                            "DEPRECATED: filter_btn.click() usado sem cursor. "
                            "Esta ação será removida em versão futura. "
                            "Use test.click() que utiliza cursor_manager."
                        )
                        await filter_btn.click()
                        await asyncio.sleep(0.3)
                        return True
            except Exception:
                continue
        
        return False
    
    async def select_filter(self, filter_name: str) -> bool:
        """
        Select a filter option from the opened filter menu.
        
        Args:
            filter_name: Name of the filter to apply (e.g., "Consumidor", "Revendedor")
            
        Returns:
            True if filter was selected successfully
        """
        # Try multiple strategies to find and click the filter option
        filter_found = False
        
        # Strategy 1: Look in filter dropdown menu (most specific)
        filter_dropdown_selectors = [
            '.o_filters_menu .dropdown-menu',
            '.o_filters_menu_menu',
            '.o_dropdown_menu',
            '.o_filters_menu ul',
            '[role="menu"]',
        ]
        
        for dropdown_selector in filter_dropdown_selectors:
            try:
                dropdown_menu = self.page.locator(dropdown_selector).first
                if await dropdown_menu.count() > 0 and await dropdown_menu.is_visible():
                    # Look for filter option within dropdown
                    filter_option = dropdown_menu.locator(f'text={filter_name}').first
                    if await filter_option.count() > 0:
                        logger.warning(
                            "DEPRECATED: filter_option.click() usado sem cursor. "
                            "Esta ação será removida em versão futura. "
                            "Use test.click() que utiliza cursor_manager."
                        )
                        await filter_option.click()
                        filter_found = True
                        break
                    
                    # Try with partial match
                    filter_option = dropdown_menu.locator(f'text=/{filter_name}/i').first
                    if await filter_option.count() > 0:
                        logger.warning(
                            "DEPRECATED: filter_option.click() usado sem cursor. "
                            "Esta ação será removida em versão futura. "
                            "Use test.click() que utiliza cursor_manager."
                        )
                        await filter_option.click()
                        filter_found = True
                        break
                    
                    # Try with contains
                    filter_option = dropdown_menu.locator(f':has-text("{filter_name}")').first
                    if await filter_option.count() > 0:
                        logger.warning(
                            "DEPRECATED: filter_option.click() usado sem cursor. "
                            "Esta ação será removida em versão futura. "
                            "Use test.click() que utiliza cursor_manager."
                        )
                        await filter_option.click()
                        filter_found = True
                        break
            except Exception:
                continue
        
        # Strategy 2: Direct text match in page (fallback)
        if not filter_found:
            filter_option = self.page.locator(f'text={filter_name}').first
            if await filter_option.count() > 0:
                # Verify it's in a dropdown menu
                is_in_dropdown = await filter_option.evaluate("""
                    (el) => {
                        return el.closest('.dropdown-menu, .o_filters_menu_menu, [role="menu"]') !== null;
                    }
                """)
                if is_in_dropdown:
                    logger.warning(
                        "DEPRECATED: filter_option.click() usado sem cursor. "
                        "Esta ação será removida em versão futura. "
                        "Use test.click() que utiliza cursor_manager."
                    )
                    await filter_option.click()
                    filter_found = True
        
        if filter_found:
            await asyncio.sleep(0.2)  # Wait for filter to be applied
            return True
        else:
            # If filter not found, try to close the menu and return False
            logger.warning(
                "DEPRECATED: page.keyboard.press() usado sem cursor. "
                "Esta ação será removida em versão futura."
            )
            await self.page.keyboard.press('Escape')
            logger.warning(f"Filter '{filter_name}' not found in dropdown menu")
            return False

