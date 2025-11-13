#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo logo navigation.

Handles clicking the Odoo logo in the top-left corner to navigate to dashboard.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

from ...core.constants import ACTION_DELAY

logger = logging.getLogger(__name__)


class LogoNavigator:
    """Helper for navigating via Odoo logo."""
    
    def __init__(self, page: Page, cursor_manager=None):
        """
        Initialize logo navigator.
        
        Args:
            page: Playwright page instance
            cursor_manager: Optional cursor manager for visual cursor movement
        """
        self.page = page
        self.cursor_manager = cursor_manager
    
    async def click_logo(self) -> bool:
        """
        Click the Odoo logo in the top-left corner to navigate to dashboard.
        
        Specifically targets the Odoo logo, avoiding other clickable elements
        like "Discussões" or "Mensagens".
        
        Returns:
            True if logo was clicked successfully, False otherwise
        """
        # Priority 1: Odoo logo/brand in top-left corner (most specific)
        # These selectors target the actual logo, not other menu items
        logo_selectors = [
            # Odoo logo/brand element (most specific - top-left corner)
            '.o_main_navbar .o_menu_brand:first-child',
            '.o_main_navbar > .o_menu_brand',
            'a.o_menu_brand:first-child',
            '.o_main_navbar a.o_menu_brand[href*="#home"]',
            '.o_main_navbar a.o_menu_brand[href="#"]',
            # Fallback: any logo/brand in navbar
            '.o_main_navbar .o_menu_brand',
            'a.o_menu_brand',
        ]
        
        for selector in logo_selectors:
            try:
                logo_link = self.page.locator(selector).first
                if await logo_link.count() > 0:
                    # Verify it's actually visible
                    is_visible = await logo_link.is_visible()
                    if not is_visible:
                        continue
                    
                    # Verify it's in the navbar and is one of the first children (logo position)
                    is_in_navbar = await logo_link.evaluate("""
                        (el) => {
                            const navbar = el.closest('.o_main_navbar');
                            if (!navbar) return false;
                            
                            // Check if it's the first child or early in the navbar (logo position)
                            const children = Array.from(navbar.children);
                            const index = children.indexOf(el);
                            return index < 3; // Logo should be in first 3 children
                        }
                    """)
                    
                    if not is_in_navbar:
                        continue
                    
                    # Get text content to exclude "Discuss" or "Mensagens"
                    text_content = await logo_link.text_content() or ""
                    text_lower = text_content.lower()
                    
                    # Exclude elements that contain "Discuss" or "Mensagens" text
                    if "discuss" in text_lower or "mensagens" in text_lower:
                        continue
                    
                    # Move cursor to logo if cursor_manager is available
                    if self.cursor_manager:
                        try:
                            box = await logo_link.bounding_box()
                            if box:
                                x = box['x'] + box['width'] / 2
                                y = box['y'] + box['height'] / 2
                                await self.cursor_manager.move_to(x, y)
                                await asyncio.sleep(ACTION_DELAY * 2)
                                await self.cursor_manager.show_click_effect(x, y)
                                await asyncio.sleep(0.05)
                        except Exception as e:
                            logger.debug(f"Failed to move cursor to logo: {e}")
                    
                    # Click the logo
                    await logo_link.click()
                    await asyncio.sleep(ACTION_DELAY * 2)
                    return True
            except Exception as e:
                logger.debug(f"Logo selector '{selector}' failed: {e}")
                continue
        
        # Fallback: try home link selectors
        home_selectors = [
            'a[href="#home"]',
            'a[href="/web"]',
            '.o_main_navbar a[href*="home"]',
        ]
        
        for selector in home_selectors:
            try:
                home_link = self.page.locator(selector).first
                if await home_link.count() > 0:
                    # Verify it's in navbar and not a menu item
                    is_menu_item = await home_link.evaluate("""
                        (el) => {
                            return el.closest('.o_menu_item, .dropdown-menu') !== null;
                        }
                    """)
                    if not is_menu_item:
                        if self.cursor_manager:
                            try:
                                box = await home_link.bounding_box()
                                if box:
                                    x = box['x'] + box['width'] / 2
                                    y = box['y'] + box['height'] / 2
                                    await self.cursor_manager.move_to(x, y)
                                    await asyncio.sleep(ACTION_DELAY * 2)
                                    await self.cursor_manager.show_click_effect(x, y)
                                    await asyncio.sleep(0.05)
                            except Exception:
                                pass
                        await home_link.click()
                        await asyncio.sleep(ACTION_DELAY * 2)
                        return True
            except Exception:
                continue
        
        logger.warning("Odoo logo not found. Cannot navigate to dashboard.")
        return False

