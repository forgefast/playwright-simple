#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OdooTestBase - Main class for Odoo testing.

Extends SimpleTestBase with Odoo-specific functionality.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page

from ..core.base import SimpleTestBase
from ..core.config import TestConfig
from ..core.constants import ACTION_DELAY
from .version_detector import detect_version, detect_edition, get_version_info
from .menus import MenuNavigator
from .fields import FieldHelper
from .views import ViewHelper
from .wizards import WizardHelper
from .workflows import WorkflowHelper
from .auth import OdooAuthMixin
from .wait import OdooWaitMixin
from .navigation import OdooNavigationMixin
from .text_interactions import OdooTextInteractionMixin
from .crud import OdooCRUDMixin
from .forms import OdooFormsMixin

logger = logging.getLogger(__name__)


class OdooTestBase(
    SimpleTestBase,
    OdooAuthMixin,
    OdooWaitMixin,
    OdooNavigationMixin,
    OdooTextInteractionMixin,
    OdooCRUDMixin,
    OdooFormsMixin
):
    """
    Base class for Odoo tests.
    
    Extends SimpleTestBase with Odoo-specific methods for:
    - Login/logout
    - Menu navigation
    - Field interaction
    - View manipulation
    - Wizard handling
    - Workflow execution
    
    Uses composition with specialized mixins for better code organization:
    - OdooAuthMixin: login, logout
    - OdooWaitMixin: wait_until_ready
    - OdooNavigationMixin: go_to_menu, go_to_dashboard, go_to_model
    - OdooTextInteractionMixin: hover, double_click, right_click, drag_and_drop, scroll_down, scroll_up
    - OdooCRUDMixin: create_record, search_and_open, assert_record_exists, open_record, add_line
    - OdooFormsMixin: fill, click_button, click (with text support)
    
    Example:
        ```python
        from playwright_simple.odoo import OdooTestBase
        
        async def test_sale_order(page, test: OdooTestBase):
            await test.login("admin", "admin", database="devel")
            await test.go_to_menu("Vendas", "Pedidos")
            await test.create_record("sale.order", {
                "partner_id": "Cliente Teste",
                "order_line": [{"product_id": "Produto 1", "quantity": 10}]
            })
        ```
    """
    
    def __init__(
        self,
        page: Page,
        config: Optional[TestConfig] = None,
        test_name: Optional[str] = None,
        cursor_manager=None,
        screenshot_manager=None,
        selector_manager=None,
        session_manager=None,
        helpers=None
    ):
        """
        Initialize Odoo test base.
        
        Uses Dependency Injection to allow customization of managers and helpers.
        Passes dependencies to SimpleTestBase.
        
        Args:
            page: Playwright page instance
            config: Test configuration
            test_name: Name of current test
            cursor_manager: Optional CursorManager instance (passed to SimpleTestBase)
            screenshot_manager: Optional ScreenshotManager instance (passed to SimpleTestBase)
            selector_manager: Optional SelectorManager instance (passed to SimpleTestBase)
            session_manager: Optional SessionManager instance (passed to SimpleTestBase)
            helpers: Optional TestBaseHelpers instance (passed to SimpleTestBase)
        """
        # Call SimpleTestBase.__init__ with Dependency Injection
        SimpleTestBase.__init__(
            self,
            page,
            config,
            test_name,
            cursor_manager=cursor_manager,
            screenshot_manager=screenshot_manager,
            selector_manager=selector_manager,
            session_manager=session_manager,
            helpers=helpers
        )
        
        # Initialize helpers
        self._version = None
        self._edition = None
        self._menu_navigator = None
        self._field_helper = None
        self._view_helper = None
        self._wizard_helper = None
        self._workflow_helper = None
        
        # Ensure _helpers is set (should be set by SimpleTestBase, but double-check)
        if not hasattr(self, '_helpers') or self._helpers is None:
            from ..core.helpers import TestBaseHelpers
            self._helpers = TestBaseHelpers(
                page,
                self.cursor_manager,
                self.config,
                self.selector_manager
            )
            # Also set it on InteractionMixin
            from ..core.interactions import InteractionMixin
            InteractionMixin._set_helpers(self, self._helpers)
    
    async def login(self, username: str, password: str, database: Optional[str] = None) -> 'OdooTestBase':
        """
        Login to Odoo - overrides generic login() to use Odoo-specific implementation.
        
        This method explicitly implements Odoo login to ensure it's used instead
        of the generic AuthMixin.login().
        
        Args:
            username: Username
            password: Password
            database: Database name (optional, for multi-db setups)
            
        Returns:
            Self for method chaining
        """
        import asyncio
        from ..core.constants import ACTION_DELAY
        
        # Ensure cursor is injected and visible
        await self._ensure_cursor()
        
        # Navigate to login page
        base_url = self.config.base_url.rstrip('/')
        login_url = f"{base_url}/web/login"
        await self.go_to(login_url)
        await asyncio.sleep(ACTION_DELAY * 2)
        
        # After navigation, just ensure cursor exists (init script handles creation)
        await self.cursor_manager._ensure_cursor_exists()
        await asyncio.sleep(ACTION_DELAY)
        
        # Fill database if needed (with cursor movement)
        if database:
            db_input = self.page.locator('input[name="db"]').first
            if await db_input.count() > 0:
                await self.type('input[name="db"]', database, "Campo Database")
        
        # Fill login (with cursor movement)
        await self.type('input[name="login"]', username, "Campo Login")
        
        # Fill password (with cursor movement)
        await self.type('input[name="password"]', password, "Campo Senha")
        await asyncio.sleep(ACTION_DELAY * 2)
        
        # Find submit button - try multiple selectors
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Entrar")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'input[type="submit"]',
            'button.btn-primary',
            'button.o_primary',
            'form button[type="submit"]',
            '.o_login_form button[type="submit"]',
        ]
        
        submit_btn = None
        for selector in submit_selectors:
            try:
                btn = self.page.locator(selector).first
                count = await btn.count()
                if count > 0:
                    is_visible = await btn.is_visible()
                    if is_visible:
                        submit_btn = btn
                        break
            except Exception:
                continue
        
        if not submit_btn:
            # Last resort: try to find ANY submit button
            all_buttons = self.page.locator('button, input[type="submit"]')
            count = await all_buttons.count()
            
            for i in range(min(count, 10)):
                btn = all_buttons.nth(i)
                try:
                    btn_type = await btn.get_attribute("type")
                    is_visible = await btn.is_visible()
                    if btn_type == "submit" and is_visible:
                        submit_btn = btn
                        break
                except Exception:
                    continue
        
        if not submit_btn:
            raise ValueError("Botão de login não encontrado após preencher senha")
        
        # Get button position for cursor movement
        try:
            box = await submit_btn.bounding_box()
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                
                # Move cursor to button (optimized for speed)
                await self.cursor_manager.move_to(x, y)
                await asyncio.sleep(ACTION_DELAY * 1)  # Minimal pause
                
                # Show click effect BEFORE clicking (so it's visible)
                await self.cursor_manager.show_click_effect(x, y)
                # Wait for click effect animation to complete
                await asyncio.sleep(0.02)  # Minimal pause
                
                # Click the button directly
                await submit_btn.click()
            else:
                await submit_btn.click()
        except Exception:
            await submit_btn.click()
        
        await asyncio.sleep(ACTION_DELAY * 1)  # Minimal delay after click
        
        # Wait for page to load
        await self.page.wait_for_load_state("load", timeout=10000)
        await asyncio.sleep(ACTION_DELAY * 1)  # Minimal delay
        
        # After login, ensure cursor exists
        await self.cursor_manager._ensure_cursor_exists()
        
        # Wait for Odoo to be ready
        await self.wait_until_ready(timeout=2000)  # Reduced timeout
        await asyncio.sleep(ACTION_DELAY * 1)  # Minimal delay
        return self
    
    async def _check_current_state(self, destination: str) -> bool:
        """
        Check if we're already at the destination (state machine check).
        
        Args:
            destination: Destination to check (e.g., "Dashboard", "Contatos", "Portal")
            
        Returns:
            True if already at destination, False otherwise
        """
        try:
            destination_lower = destination.lower().strip()
            current_url = self.page.url.lower()
            
            # Dashboard check
            if destination_lower in ["dashboard", "menu principal", "home", "início", "página inicial"]:
                from ..odoo.specific.logo import LogoNavigator
                logo_nav = LogoNavigator(self.page, self.cursor_manager)
                return await logo_nav._is_on_dashboard()
            
            # Portal check
            elif destination_lower in ["portal", "meu portal", "portal do cliente"]:
                return '/my' in current_url
            
            # Shop check
            elif destination_lower in ["loja", "e-commerce", "shop", "compras"]:
                return '/shop' in current_url
            
            # Menu/app check - use _is_current_app
            else:
                # Parse menu path (e.g., "Vendas > Pedidos" -> app="Vendas")
                menu_parts = destination.split('>')
                app_name = menu_parts[0].strip() if menu_parts else destination.strip()
                
                if hasattr(self, 'menu') and hasattr(self.menu, '_is_current_app'):
                    is_current = await self.menu._is_current_app(app_name)
                    if is_current:
                        # If submenu specified, check if we're on the submenu
                        if len(menu_parts) > 1:
                            submenu = menu_parts[1].strip().lower()
                            page_title = (await self.page.title()).lower()
                            # Check if submenu is in title or URL
                            return submenu in page_title or submenu.replace(' ', '') in current_url.replace(' ', '')
                        return True
                
                return False
        except Exception as e:
            logger.debug(f"Erro ao verificar estado atual: {e}")
            return False
    
    async def go_to(self, menu_path_or_url: str) -> 'OdooTestBase':
        """
        Navigate to a menu, URL, or user-friendly location - overrides generic go_to().
        
        This method implements Odoo-specific navigation to ensure it's used instead
        of the generic NavigationMixin.go_to().
        
        Uses state machine: checks current state before navigating.
        If already at destination, skips navigation.
        
        Args:
            menu_path_or_url: Menu path, user-friendly text, or URL
            
        Returns:
            Self for method chaining
        """
        # State machine: check if we're already at the destination
        if not menu_path_or_url.startswith("/") and not menu_path_or_url.startswith("http"):
            is_already_there = await self._check_current_state(menu_path_or_url)
            logger.info(f"Verificação de estado para '{menu_path_or_url}': {is_already_there}")
            if is_already_there:
                logger.info(f"✅ Já estamos em '{menu_path_or_url}' - não precisa navegar (máquina de estado)")
                print(f"  ✅ Já estamos em '{menu_path_or_url}' - não precisa navegar")
                return self
            else:
                logger.info(f"🔄 Não estamos em '{menu_path_or_url}' - precisa navegar")
                print(f"  🔄 Navegando para '{menu_path_or_url}'...")
        # First check if it's a URL (starts with / or http)
        # BUT: For Odoo, we should NEVER use direct URL navigation to avoid "Missing Action" errors
        # Only allow direct navigation for external URLs (http/https) that are not Odoo URLs
        if menu_path_or_url.startswith("http"):
            # External URL - check if it's the Odoo base URL
            if self.config.base_url in menu_path_or_url or menu_path_or_url.startswith(self.config.base_url):
                # It's an Odoo URL - try to find a link to click instead
                # Extract the path part
                from urllib.parse import urlparse
                parsed = urlparse(menu_path_or_url)
                path = parsed.path + (parsed.fragment if parsed.fragment else "")
                # Try to find a link with this path
                try:
                    link = self.page.locator(f'a[href*="{path}"]').first
                    if await link.count() > 0 and await link.is_visible():
                        box = await link.bounding_box()
                        if box:
                            x = box['x'] + box['width'] / 2
                            y = box['y'] + box['height'] / 2
                            await self.cursor_manager.move_to(x, y)
                            await asyncio.sleep(ACTION_DELAY * 1)
                            await self.cursor_manager.show_click_effect(x, y)
                            await asyncio.sleep(0.01)
                            await link.click()
                            await asyncio.sleep(ACTION_DELAY * 1)
                            await self.wait_until_ready(timeout=5000)
                            await asyncio.sleep(ACTION_DELAY * 2)
                            return self
                except Exception:
                    pass
                # If no link found, use parent's go_to (but this should be rare)
                await super(SimpleTestBase, self).go_to(menu_path_or_url)
            else:
                # External non-Odoo URL - use parent's go_to
                await super(SimpleTestBase, self).go_to(menu_path_or_url)
            return self
        
        # For relative URLs starting with /, try to find a link first
        if menu_path_or_url.startswith("/"):
            # Try to find a link with this path
            try:
                link = self.page.locator(f'a[href*="{menu_path_or_url}"]').first
                if await link.count() > 0 and await link.is_visible():
                    box = await link.bounding_box()
                    if box:
                        x = box['x'] + box['width'] / 2
                        y = box['y'] + box['height'] / 2
                        await self.cursor_manager.move_to(x, y)
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.cursor_manager.show_click_effect(x, y)
                        await asyncio.sleep(0.01)
                        await link.click()
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.wait_until_ready(timeout=5000)
                        await asyncio.sleep(ACTION_DELAY * 2)
                        return self
            except Exception:
                pass
            # If no link found, DON'T use direct navigation - it causes "Missing Action" errors
            # Instead, try to navigate via menu or return error
            raise ValueError(
                f"Não foi possível encontrar um link para '{menu_path_or_url}'. "
                f"Use navegação por menu (ex: 'Vendas > Pedidos') ou verifique se o link existe na página."
            )
        
        # Resolve user-friendly URLs using OdooNavigationMixin logic
        text_lower = menu_path_or_url.lower().strip()
        
        # Dashboard/Home mappings - usa navegação via cursor
        if text_lower in ["dashboard", "menu principal", "home", "início", "página inicial"]:
            # State check already done above - se já está no dashboard, retorna
            # Se não está, navega usando cursor (sem navegação direta)
            success = await self.menu.go_to_dashboard()
            if not success:
                raise ValueError("Não foi possível navegar para o Dashboard - cursor não conseguiu clicar no elemento necessário")
        # Portal mappings - try to find links first, avoid direct URL navigation
        elif text_lower in ["portal", "meu portal", "portal do cliente"]:
            # State check already done above, proceed with navigation
            # Try to find portal link
            try:
                portal_link = self.page.locator('a[href*="/my"], a:has-text("Portal"), a:has-text("Meu Portal")').first
                if await portal_link.count() > 0 and await portal_link.is_visible():
                    box = await portal_link.bounding_box()
                    if box:
                        x = box['x'] + box['width'] / 2
                        y = box['y'] + box['height'] / 2
                        await self.cursor_manager.move_to(x, y)
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.cursor_manager.show_click_effect(x, y)
                        await asyncio.sleep(0.01)
                        await portal_link.click()
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.wait_until_ready(timeout=5000)
                        await asyncio.sleep(ACTION_DELAY * 2)
                        return self
            except Exception:
                pass
            # Don't use direct navigation - cursor must be the protagonist
            # If portal link not found, we should fail rather than navigate without cursor
            logger.warning("Link do Portal não encontrado - não é possível navegar sem cursor visual")
            raise ValueError("Não foi possível encontrar link do Portal para navegação com cursor visual")
        # E-commerce/Shop mappings - try to find links first
        elif text_lower in ["loja", "e-commerce", "shop", "compras"]:
            try:
                shop_link = self.page.locator('a[href*="/shop"], a:has-text("Loja"), a:has-text("Shop")').first
                if await shop_link.count() > 0 and await shop_link.is_visible():
                    box = await shop_link.bounding_box()
                    if box:
                        x = box['x'] + box['width'] / 2
                        y = box['y'] + box['height'] / 2
                        await self.cursor_manager.move_to(x, y)
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.cursor_manager.show_click_effect(x, y)
                        await asyncio.sleep(0.01)
                        await shop_link.click()
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.wait_until_ready(timeout=5000)
                        await asyncio.sleep(ACTION_DELAY * 2)
                        return self
            except Exception:
                pass
            # Fallback: try direct navigation only if link not found
            await super(SimpleTestBase, self).go_to("/shop")
        # Common portal pages - try to find links first
        elif text_lower in ["meus pedidos", "pedidos", "orders"]:
            try:
                orders_link = self.page.locator('a[href*="/my/orders"], a:has-text("Pedidos"), a:has-text("Orders")').first
                if await orders_link.count() > 0 and await orders_link.is_visible():
                    box = await orders_link.bounding_box()
                    if box:
                        x = box['x'] + box['width'] / 2
                        y = box['y'] + box['height'] / 2
                        await self.cursor_manager.move_to(x, y)
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.cursor_manager.show_click_effect(x, y)
                        await asyncio.sleep(0.01)
                        await orders_link.click()
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.wait_until_ready(timeout=5000)
                        await asyncio.sleep(ACTION_DELAY * 2)
                        return self
            except Exception:
                pass
            # Fallback: try direct navigation only if link not found
            await super(SimpleTestBase, self).go_to("/my/orders")
        elif text_lower in ["meu perfil", "perfil", "profile"]:
            try:
                profile_link = self.page.locator('a[href*="/my/profile"], a:has-text("Perfil"), a:has-text("Profile")').first
                if await profile_link.count() > 0 and await profile_link.is_visible():
                    box = await profile_link.bounding_box()
                    if box:
                        x = box['x'] + box['width'] / 2
                        y = box['y'] + box['height'] / 2
                        await self.cursor_manager.move_to(x, y)
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.cursor_manager.show_click_effect(x, y)
                        await asyncio.sleep(0.01)
                        await profile_link.click()
                        await asyncio.sleep(ACTION_DELAY * 1)
                        await self.wait_until_ready(timeout=5000)
                        await asyncio.sleep(ACTION_DELAY * 2)
                        return self
            except Exception:
                pass
            # Fallback: try direct navigation only if link not found
            await super(SimpleTestBase, self).go_to("/my/profile")
        else:
            # Not a special URL, treat as menu path (e.g., "Vendas", "Contatos")
            # State check already done above, proceed with navigation
            # Log navigation attempt
            logger.info(f"Attempting to navigate to menu: {menu_path_or_url}")
            try:
                current_url = self.page.url
                page_title = await self.page.title()
                logger.debug(f"Current page: {current_url}, title: {page_title}")
            except Exception:
                pass
            
            success = await self.menu.go_to_menu(menu_path_or_url)
            if not success:
                # Log failure details
                try:
                    final_url = self.page.url
                    page_title = await self.page.title()
                    # Try to get visible menu items for debugging
                    menu_items = await self.page.locator('.o_menu_apps, .o_main_menu, [role="menubar"]').count()
                    logger.error(
                        f"Failed to navigate to menu '{menu_path_or_url}'. "
                        f"Current URL: {final_url}, Title: {page_title}, "
                        f"Menu items found: {menu_items}"
                    )
                except Exception as log_error:
                    logger.error(f"Failed to navigate to menu '{menu_path_or_url}': {log_error}")
                
                raise ValueError(
                    f"Não foi possível navegar para o menu '{menu_path_or_url}'. "
                    f"Verifique se o menu existe e está acessível."
                )
            else:
                # Log success
                try:
                    final_url = self.page.url
                    page_title = await self.page.title()
                    logger.info(f"Successfully navigated to menu '{menu_path_or_url}'. URL: {final_url}, Title: {page_title}")
                except Exception:
                    logger.info(f"Successfully navigated to menu '{menu_path_or_url}'")
        
        # Wait for Odoo to be ready after navigation
        # This automatically waits until page is fully loaded and ready
        await self.wait_until_ready(timeout=5000)
        # Minimal visual delay - automatic wait handles actual readiness
        await asyncio.sleep(0.1)  # Small delay just for visual smoothness
        return self
    
    @property
    def menu(self) -> MenuNavigator:
        """Get menu navigator."""
        if not self._menu_navigator:
            self._menu_navigator = MenuNavigator(self.page, self._version, self.cursor_manager)
        return self._menu_navigator
    
    @property
    def field(self) -> FieldHelper:
        """Get field helper."""
        if not self._field_helper:
            self._field_helper = FieldHelper(self.page, self._version)
        return self._field_helper
    
    @property
    def view(self) -> ViewHelper:
        """Get view helper."""
        if not self._view_helper:
            self._view_helper = ViewHelper(self.page)
        return self._view_helper
    
    @property
    def wizard(self) -> WizardHelper:
        """Get wizard helper."""
        if not self._wizard_helper:
            self._wizard_helper = WizardHelper(self.page)
        return self._wizard_helper
    
    @property
    def workflow(self) -> WorkflowHelper:
        """Get workflow helper."""
        if not self._workflow_helper:
            self._workflow_helper = WorkflowHelper(self.page)
        return self._workflow_helper
    
    async def detect_odoo_version(self) -> Optional[str]:
        """
        Detect Odoo version automatically.
        
        Returns:
            Version string (e.g., "14.0", "15.0") or None
        """
        if not self._version:
            self._version = await detect_version(self.page)
        return self._version
    
    async def detect_odoo_edition(self) -> str:
        """
        Detect Odoo edition (Community or Enterprise).
        
        Returns:
            "community" or "enterprise"
        """
        if not self._edition:
            self._edition = await detect_edition(self.page)
        return self._edition
