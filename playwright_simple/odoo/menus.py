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


class MenuNavigator:
    """Helper class for navigating Odoo menus."""
    
    def __init__(self, page: Page, version: Optional[str] = None):
        """
        Initialize menu navigator.
        
        Args:
            page: Playwright page instance
            version: Odoo version (auto-detected if None)
        """
        self.page = page
        self._version = version
        self._edition = None
    
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
                        await btn.click()
                        await asyncio.sleep(0.8)
                        return True
            except Exception:
                continue
        
        # Try pressing Alt key (common shortcut for apps menu)
        try:
            await self.page.keyboard.press("Alt")
            await asyncio.sleep(0.5)
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
            await asyncio.sleep(0.3)
            return True
        except Exception:
            return False
    
    async def go_to_app(self, app_name: str) -> bool:
        """
        Navigate to a specific app.
        
        Args:
            app_name: Name of the app (e.g., "Vendas", "Contatos")
            
        Returns:
            True if navigation was successful
        """
        # Try to open apps menu first
        menu_opened = await self.open_apps_menu()
        
        # Wait a bit for menu to appear
        if menu_opened:
            await asyncio.sleep(1)
        else:
            # If menu didn't open, try searching in the page directly
            print(f"    ⚠️  Menu de apps não abriu, tentando buscar '{app_name}' diretamente na página...")
        
        # Try multiple selectors to find the app
        app_selectors = [
            f'a:has-text("{app_name}")',
            f'a:has-text("{app_name}"):visible',
            f'[data-menu-xmlid*="{app_name.lower()}"]',
            f'a[title*="{app_name}"]',
            f'.o_app[data-menu-xmlid*="{app_name.lower()}"]',
            f'.o_menu_item:has-text("{app_name}")',
            f'.o_apps_menu_item:has-text("{app_name}")',
            f'.o_app:has-text("{app_name}")',
            f'[aria-label*="{app_name}"]',
            f'text="{app_name}"',
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
                            if await elem.is_visible():
                                await elem.click()
                                await asyncio.sleep(1)
                                await self.close_apps_menu()
                                print(f"    ✅ App '{app_name}' encontrado e clicado")
                                return True
                    except Exception as e:
                        # Try clicking first element anyway
                        try:
                            await element.first.click()
                            await asyncio.sleep(1)
                            await self.close_apps_menu()
                            print(f"    ✅ App '{app_name}' clicado (com exceção: {e})")
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
            await asyncio.sleep(0.8)  # Wait for menu to load
            
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
                                await element.click()
                                await asyncio.sleep(0.8)
                                return True
                        except Exception:
                            await element.click()
                            await asyncio.sleep(0.8)
                            return True
                except Exception:
                    continue
            
            # If submenu not found, try direct URL navigation
            return await self._go_to_menu_by_url(menu, submenu)
        
        return True
    
    async def _go_to_menu_by_url(self, menu: str, submenu: Optional[str] = None) -> bool:
        """
        Navigate to menu by URL (fallback).
        
        Args:
            menu: Main menu name
            submenu: Submenu name (optional)
            
        Returns:
            True if navigation was successful
        """
        # Common menu URLs (can be extended)
        menu_urls = {
            ("Vendas", "Pedidos"): "/web#action=sale.action_orders&model=sale.order&view_type=list",
            ("Vendas", "Clientes"): "/web#action=sale.action_partner_form&model=res.partner&view_type=list",
            ("Vendas", "Produtos"): "/web#action=product.action_product_template&model=product.template&view_type=list",
            ("Contatos", "Clientes"): "/web#action=contacts.action_contacts&model=res.partner&view_type=list",
            ("Contatos", "Categorias"): "/web#action=contacts.action_contacts_category&model=res.partner.category&view_type=list",
            ("Website", "Cursos"): "/web#action=website_slides.slide_channel_action&model=slide.channel&view_type=list",
            ("Gamificação", "Badges"): "/web#action=gamification.action_gamification_badge&model=gamification.badge&view_type=list",
            ("Gamificação", "Desafios"): "/web#action=gamification.action_gamification_challenge&model=gamification.challenge&view_type=list",
        }
        
        key = (menu, submenu) if submenu else (menu, None)
        if key in menu_urls:
            try:
                base_url = self.page.url.split('/web')[0]
                await self.page.goto(f"{base_url}{menu_urls[key]}", wait_until="networkidle", timeout=30000)
                await asyncio.sleep(0.5)
                return True
            except Exception:
                pass
        
        return False
    
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
        await asyncio.sleep(0.3)
        
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
                    await asyncio.sleep(0.5)
                    
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
                                await asyncio.sleep(0.8)
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
        
        Returns:
            True if navigation was successful
        """
        try:
            base_url = self.page.url.split('/web')[0]
            # Try /web#home first (Odoo 14+)
            url = f"{base_url}/web#home"
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(0.5)
            return True
        except Exception:
            try:
                # Fallback to /web
                base_url = self.page.url.split('/web')[0]
                url = f"{base_url}/web"
                await self.page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(0.5)
                return True
            except Exception:
                return False
    
    async def go_to_home(self) -> bool:
        """
        Navigate to home page (alias for go_to_dashboard).
        
        Returns:
            True if navigation was successful
        """
        return await self.go_to_dashboard()

