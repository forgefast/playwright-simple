#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo menu navigation module.

Handles navigation through Odoo menus for both Community and Enterprise editions.
"""

import asyncio
from typing import Optional, List
from playwright.async_api import Page

from .selectors import get_menu_selectors, get_selector_list
from .version_detector import detect_version, detect_edition
from .specific.logo import LogoNavigator
from ..core.constants import ACTION_DELAY


class MenuNavigator:
    """Helper class for navigating Odoo menus."""
    
    def __init__(self, page: Page, version: Optional[str] = None, cursor_manager=None):
        """
        Initialize menu navigator.
        
        Args:
            page: Playwright page instance
            version: Odoo version (auto-detected if None)
            cursor_manager: Optional cursor manager for visual cursor movement
        """
        self.page = page
        self._version = version
        self._edition = None
        self.cursor_manager = cursor_manager
    
    async def _get_version(self) -> str:
        """Get Odoo version (cached)."""
        if not self._version:
            self._version = await detect_version(self.page) or "18.0"
        return self._version
    
    async def _get_edition(self) -> str:
        """Get Odoo edition (cached)."""
        if not self._edition:
            self._edition = await detect_edition(self.page)
        return self._edition
    
    async def open_apps_menu(self) -> bool:
        """
        Open the Apps menu.
        
        Returns:
            True if menu was opened, False otherwise
        """
        # Try multiple approaches to open apps menu
        selectors = [
            'button.o_menu_toggle',
            'button[aria-label*="Menu"]',
            'button[title*="Apps"]',
            'button[title*="Menu"]',
            '.o_menu_toggle',
            '[data-bs-toggle="offcanvas"]',
            'button:has-text("Apps")',
        ]
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    is_visible = await btn.is_visible()
                    if is_visible:
                        # Move cursor to button if cursor_manager is available
                        if self.cursor_manager:
                            try:
                                box = await btn.bounding_box()
                                if box:
                                    x = box['x'] + box['width'] / 2
                                    y = box['y'] + box['height'] / 2
                                    await self.cursor_manager.move_to(x, y)
                                    await asyncio.sleep(ACTION_DELAY * 2)  # Minimal pause
                                    await self.cursor_manager.show_click_effect(x, y)
                                    await asyncio.sleep(0.05)  # Minimal pause
                            except Exception:
                                pass
                        await btn.click()
                        await asyncio.sleep(ACTION_DELAY * 2)  # Minimal delay
                        return True
            except Exception:
                continue
        
        # Try pressing Alt key (common shortcut for apps menu)
        try:
            await self.page.keyboard.press("Alt")
            await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.5s
            # Check if menu opened
            menu_visible = await self.page.locator('.o_apps_menu, .o_main_navbar').is_visible()
            if menu_visible:
                return True
        except Exception:
            pass
        
        return False
    
    async def close_apps_menu(self) -> bool:
        """Close the Apps menu."""
        try:
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.3s
            return True
        except Exception:
            return False
    
    async def _is_current_app(self, app_name: str) -> bool:
        """
        Check if already in the specified app.
        
        Args:
            app_name: Name of the app to check
            
        Returns:
            True if already in the app
        """
        try:
            # Check URL for app indicators
            current_url = self.page.url.lower()
            app_name_lower = app_name.lower().strip()
            
            # Check if URL contains app name or related keywords
            url_indicators = {
                "vendas": ["sale", "sales"],
                "contatos": ["contact", "partner", "res.partner"],
                "crm": ["crm"],
                "projetos": ["project"],
                "inventário": ["stock", "inventory"],
                "compras": ["purchase"],
                "contabilidade": ["account"],
                "recursos humanos": ["hr", "employee"],
                "hr": ["hr", "employee"],
                "website": ["website"],
                "ecommerce": ["shop", "ecommerce"],
            }
            
            if app_name_lower in url_indicators:
                for indicator in url_indicators[app_name_lower]:
                    if indicator in current_url:
                        return True
            
            # Check breadcrumbs or menu title
            breadcrumb_selectors = [
                '.breadcrumb',
                '.o_breadcrumb',
                '[data-breadcrumb]',
                '.o_main_navbar',
            ]
            
            for selector in breadcrumb_selectors:
                try:
                    breadcrumb = self.page.locator(selector).first
                    if await breadcrumb.count() > 0:
                        text = await breadcrumb.text_content()
                        if text and app_name_lower in text.lower():
                            return True
                except Exception:
                    continue
            
            # Check if main menu button shows the app name
            menu_button_selectors = [
                'button.o_menu_toggle',
                '.o_main_navbar .o_menu_toggle',
                '[data-bs-toggle="offcanvas"]',
            ]
            
            for selector in menu_button_selectors:
                try:
                    button = self.page.locator(selector).first
                    if await button.count() > 0:
                        # Check aria-label or title
                        aria_label = await button.get_attribute('aria-label') or ''
                        title = await button.get_attribute('title') or ''
                        if app_name_lower in aria_label.lower() or app_name_lower in title.lower():
                            return True
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return False
    
    async def go_to_app(self, app_name: str) -> bool:
        """
        Navigate to a specific app.
        
        Args:
            app_name: Name of the app (e.g., "Vendas", "Contatos")
            
        Returns:
            True if navigation was successful
        """
        # Check if already in the app - if so, skip navigation
        if await self._is_current_app(app_name):
            return True
        
        # Translation mapping for common menu names (Portuguese -> English)
        translations = {
            "vendas": "Sales",
            "contatos": "Contacts",
            "crm": "CRM",
            "projetos": "Project",
            "inventário": "Inventory",
            "compras": "Purchases",
            "contabilidade": "Accounting",
            "recursos humanos": "Human Resources",
            "hr": "Human Resources",
            "website": "Website",
            "ecommerce": "eCommerce",
            "vendas online": "Online Sales",
        }
        
        # Try both original name and translation
        names_to_try = [app_name]
        app_name_lower = app_name.lower().strip()
        if app_name_lower in translations:
            names_to_try.append(translations[app_name_lower])
        
        # Try to open apps menu first
        menu_opened = await self.open_apps_menu()
        
        # Wait a bit for menu to appear (increased delay for visibility)
        if menu_opened:
            await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show menu opening clearly
        else:
            # If menu didn't open, try searching in the page directly
            print(f"    ⚠️  Menu de apps não abriu, tentando buscar '{app_name}' diretamente na página...")
            await asyncio.sleep(ACTION_DELAY * 1)  # Delay even if menu didn't open
        
        # Try each name variant
        for name_variant in names_to_try:
            # Try multiple selectors to find the app
            app_selectors = [
                f'a:has-text("{name_variant}")',
                f'a:has-text("{name_variant}"):visible',
                f'[data-menu-xmlid*="{name_variant.lower()}"]',
                f'a[title*="{name_variant}"]',
                f'.o_app[data-menu-xmlid*="{name_variant.lower()}"]',
                f'.o_menu_item:has-text("{name_variant}")',
                f'.o_apps_menu_item:has-text("{name_variant}")',
                f'.o_app:has-text("{name_variant}")',
                f'[aria-label*="{name_variant}"]',
                f'text="{name_variant}"',
            ]
            
            for selector in app_selectors:
                try:
                    element = self.page.locator(selector).first
                    count = await element.count()
                    if count > 0:
                        try:
                            # Try to find visible element
                            for i in range(count):
                                elem = element.nth(i)
                                is_visible = await elem.is_visible()
                                if is_visible:
                                    try:
                                        # Get element position for cursor movement
                                        try:
                                            box = await elem.bounding_box()
                                            if box and self.cursor_manager:
                                                x = box['x'] + box['width'] / 2
                                                y = box['y'] + box['height'] / 2
                                                
                                                # Move cursor to element (with human-like speed - slower for visibility)
                                                await self.cursor_manager.move_to(x, y)
                                                await asyncio.sleep(ACTION_DELAY * 2)  # Increased pause after movement to show cursor position clearly
                                                
                                                # Show click effect BEFORE clicking (so it's visible)
                                                await self.cursor_manager.show_click_effect(x, y)
                                                await asyncio.sleep(0.05)  # Increased pause to show effect before click
                                        except Exception:
                                            pass
                                        
                                        await elem.click()
                                        await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation result
                                        await self.close_apps_menu()
                                        await asyncio.sleep(ACTION_DELAY * 1)  # Increased delay after closing menu
                                        return True
                                    except Exception:
                                        continue
                        except Exception as e:
                            # Try clicking first element anyway
                            try:
                                # Try to move cursor to element if cursor_manager is available
                                try:
                                    box = await element.first.bounding_box()
                                    if box and self.cursor_manager:
                                        x = box['x'] + box['width'] / 2
                                        y = box['y'] + box['height'] / 2
                                        
                                        # Move cursor to element (with human-like speed - slower for visibility)
                                        await self.cursor_manager.move_to(x, y)
                                        await asyncio.sleep(ACTION_DELAY * 2)  # Increased pause after movement to show cursor position clearly
                                        
                                        # Show click effect BEFORE clicking (so it's visible)
                                        await self.cursor_manager.show_click_effect(x, y)
                                        await asyncio.sleep(0.05)  # Increased pause to show effect before click
                                except Exception:
                                    pass
                                
                                await element.first.click()
                                await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation result
                                await self.close_apps_menu()
                                await asyncio.sleep(ACTION_DELAY * 1)  # Increased delay after closing menu
                                print(f"    ✅ App '{name_variant}' clicado (com exceção: {e})")
                                return True
                            except Exception:
                                continue
                except Exception:
                    continue
        
        # Close menu if opened
        if menu_opened:
            await self.close_apps_menu()
        
        # Debug: try to get page content to understand what's available
        try:
            # Try using Odoo's search menu feature
            search_success = await self.search_menu(app_name)
            if search_success:
                print(f"    ✅ App '{app_name}' encontrado via busca")
                return True
        except Exception as e:
            print(f"    ⚠️  Busca de menu falhou: {e}")
        
        # Debug: list available menu items
        try:
            menu_items = await self.page.evaluate("""
                () => {
                    const items = [];
                    document.querySelectorAll('.o_app, .o_menu_item, a[data-menu-xmlid]').forEach(el => {
                        const text = el.textContent?.trim() || el.getAttribute('title') || el.getAttribute('aria-label') || '';
                        if (text) items.push(text);
                    });
                    return items.slice(0, 20); // First 20 items
                }
            """)
            if menu_items:
                print(f"    📋 Menus disponíveis (primeiros 20): {', '.join(menu_items[:10])}")
        except Exception:
            pass
        
        print(f"    ❌ App '{app_name}' não encontrado")
        return False
    
    async def go_to_menu(
        self, 
        menu: str, 
        submenu: Optional[str] = None
    ) -> bool:
        """
        Navigate to a menu and optionally a submenu.
        
        Supports two formats:
        1. `go_to_menu("Vendas", "Pedidos")` - separate arguments
        2. `go_to_menu("Vendas > Pedidos")` - single string with separator
        
        Args:
            menu: Main menu name or full path (e.g., "Vendas" or "Vendas > Pedidos")
            submenu: Submenu name (optional, ignored if menu contains '>')
            
        Returns:
            True if navigation was successful
        """
        # Check if menu contains separator (format: "Vendas > Pedidos")
        if '>' in menu:
            parts = [p.strip() for p in menu.split('>')]
            if len(parts) >= 2:
                menu = parts[0]
                submenu = parts[1]
            elif len(parts) == 1:
                menu = parts[0]
                submenu = None
        
        # Navigate to main menu
        success = await self.go_to_app(menu)
        if not success:
            return False
        
        # If submenu is specified, navigate to it
        if submenu:
            await asyncio.sleep(ACTION_DELAY * 1)  # Wait for menu to load and show cursor position
            
            submenu_selectors = [
                f'a:has-text("{submenu}")',
                f'a:has-text("{submenu}"):visible',
                f'a[title*="{submenu}"]',
                f'.o_menu_item:has-text("{submenu}")',
                f'text={submenu}',
                f'[data-menu-xmlid*="{submenu.lower()}"]',
            ]
            
            for selector in submenu_selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.count() > 0:
                        try:
                            if await element.is_visible():
                                # Get element position for cursor movement
                                try:
                                    box = await element.bounding_box()
                                    if box:
                                        x = box['x'] + box['width'] / 2
                                        y = box['y'] + box['height'] / 2
                                        
                                        # Move cursor to element if cursor_manager is available (with human-like speed)
                                        if self.cursor_manager:
                                            await self.cursor_manager.move_to(x, y)
                                            await asyncio.sleep(ACTION_DELAY * 2)  # Increased pause after movement to show cursor position clearly
                                            
                                            # Show click effect BEFORE clicking (so it's visible)
                                            await self.cursor_manager.show_click_effect(x, y)
                                            await asyncio.sleep(0.05)  # Increased pause to show effect before click
                                        else:
                                            # No cursor manager, just add delay
                                            await asyncio.sleep(ACTION_DELAY * 2)
                                except Exception:
                                    pass
                                
                                await element.click()
                                await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation result
                                return True
                        except Exception:
                            await element.click()
                            await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation result
                            return True
                except Exception:
                    continue
            
            # If submenu not found, try with translation (Portuguese -> English)
            translations = {
                "categorias": "Categories",
                "pedidos": "Orders",
                "clientes": "Customers",
                "produtos": "Products",
                "badges": "Badges",
                "desafios": "Challenges",
                "cursos": "Courses",
            }
            
            submenu_lower = submenu.lower().strip()
            if submenu_lower in translations:
                translated_submenu = translations[submenu_lower]
                # Try again with translated name
                for selector in submenu_selectors:
                    try:
                        # Replace submenu in selector with translated version
                        translated_selector = selector.replace(f'"{submenu}"', f'"{translated_submenu}"')
                        element = self.page.locator(translated_selector).first
                        if await element.count() > 0:
                            try:
                                if await element.is_visible():
                                    await element.click()
                                    await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation
                                    return True
                            except Exception:
                                await element.click()
                                await asyncio.sleep(ACTION_DELAY * 2)  # Increased delay to show navigation
                                return True
                    except Exception:
                        continue
            
            # If still not found, return False (don't use URL navigation)
            return False
        
        return True
    
    async def search_menu(self, search_text: str) -> bool:
        """
        Search for a menu item.
        
        Args:
            search_text: Text to search for
            
        Returns:
            True if search was successful
        """
        # Open apps menu first
        await self.open_apps_menu()
        await asyncio.sleep(0.02)
        
        # Look for search input in apps menu
        search_selectors = [
            'input[placeholder*="Buscar"], input[placeholder*="Search"]',
            '.o_apps_menu input',
            '.o_searchview_input',
        ]
        
        for selector in search_selectors:
            try:
                search_input = self.page.locator(selector).first
                if await search_input.count() > 0:
                    await search_input.fill(search_text)
                    await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.5s
                    
                    # Try to click first result
                    result_selectors = [
                        '.o_apps_menu .o_app:first-child',
                        '.o_menu_item:first-child',
                    ]
                    
                    for result_sel in result_selectors:
                        try:
                            result = self.page.locator(result_sel).first
                            if await result.count() > 0:
                                await result.click()
                                await asyncio.sleep(ACTION_DELAY * 2)  # Reduced from 0.8s
                                await self.close_apps_menu()
                                return True
                        except Exception:
                            continue
                    break
            except Exception:
                continue
        
        await self.close_apps_menu()
        return False
    
    async def go_to_dashboard(self) -> bool:
        """
        Navigate to Odoo dashboard/home page.
        
        Uses LogoNavigator to click the Odoo logo in the top-left corner.
        
        Returns:
            True if navigation was successful, False otherwise
        """
        logo_navigator = LogoNavigator(self.page, self.cursor_manager)
        return await logo_navigator.click_logo()
    
    async def go_to_home(self) -> bool:
        """
        Navigate to home page (alias for go_to_dashboard).
        
        Returns:
            True if navigation was successful
        """
        return await self.go_to_dashboard()

