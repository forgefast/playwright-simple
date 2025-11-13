#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OdooTestBase - Main class for Odoo testing.

Extends SimpleTestBase with Odoo-specific functionality.
"""

import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import Page

from ..core.base import SimpleTestBase
from ..core.config import TestConfig
from .version_detector import detect_version, detect_edition, get_version_info
from .menus import MenuNavigator
from .fields import FieldHelper
from .views import ViewHelper
from .wizards import WizardHelper
from .workflows import WorkflowHelper


class OdooTestBase(SimpleTestBase):
    """
    Base class for Odoo tests.
    
    Extends SimpleTestBase with Odoo-specific methods for:
    - Login/logout
    - Menu navigation
    - Field interaction
    - View manipulation
    - Wizard handling
    - Workflow execution
    
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
    
    def __init__(self, page: Page, config: Optional[TestConfig] = None, test_name: Optional[str] = None):
        """
        Initialize Odoo test base.
        
        Args:
            page: Playwright page instance
            config: Test configuration
            test_name: Name of current test
        """
        super().__init__(page, config, test_name)
        
        # Initialize helpers
        self._version = None
        self._edition = None
        self._menu_navigator = None
        self._field_helper = None
        self._view_helper = None
        self._wizard_helper = None
        self._workflow_helper = None
    
    @property
    def menu(self) -> MenuNavigator:
        """Get menu navigator."""
        if not self._menu_navigator:
            self._menu_navigator = MenuNavigator(self.page, self._version)
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
    
    async def login(self, username: str, password: str, database: Optional[str] = None) -> 'OdooTestBase':
        """
        Login to Odoo with visible cursor movement.
        
        Args:
            username: Username
            password: Password
            database: Database name (optional, for multi-db setups)
            
        Returns:
            Self for method chaining
        """
        # Ensure cursor is injected and visible
        await self._ensure_cursor()
        
        # Navigate to login page
        base_url = self.config.base_url.rstrip('/')
        await self.go_to(f"{base_url}/web/login")
        await asyncio.sleep(1)  # Wait for page to fully load
        
        # Re-inject cursor after navigation to ensure it's visible
        await self.cursor_manager.inject(force=True)
        await asyncio.sleep(0.5)
        
        # Fill database if needed (with cursor movement)
        if database:
            db_input = self.page.locator('input[name="db"]').first
            if await db_input.count() > 0:
                await self.type('input[name="db"]', database, "Campo Database")
                await asyncio.sleep(0.3)
        
        # Fill login (with cursor movement)
        await self.type('input[name="login"]', username, "Campo Login")
        await asyncio.sleep(0.3)
        
        # Fill password (with cursor movement)
        await self.type('input[name="password"]', password, "Campo Senha")
        await asyncio.sleep(0.3)
        
        # Click submit (with cursor movement)
        await self.click('button[type="submit"], button:has-text("Entrar"), button:has-text("Log in")', "Botão Entrar")
        await asyncio.sleep(1)
        
        # Wait for page to load
        await self.page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(0.5)
        
        # Re-inject cursor after login to ensure it's visible on dashboard
        await self.cursor_manager.inject(force=True)
        await asyncio.sleep(0.3)
        
        # Detect version after login
        await self.detect_odoo_version()
        
        return self
    
    async def logout(self) -> 'OdooTestBase':
        """Logout from Odoo."""
        try:
            # Look for user menu
            user_menu_selectors = [
                '.o_user_menu',
                '.o_main_navbar .o_user_menu',
                'button[title*="Usuário"], button[title*="User"]',
            ]
            
            for selector in user_menu_selectors:
                try:
                    user_menu = self.page.locator(selector).first
                    if await user_menu.count() > 0:
                        await user_menu.click()
                        await asyncio.sleep(0.5)
                        
                        # Click logout
                        logout_btn = self.page.locator('a:has-text("Sair"), a:has-text("Log out")').first
                        if await logout_btn.count() > 0:
                            await logout_btn.click()
                            await asyncio.sleep(1)
                            return self
                except Exception:
                    continue
        except Exception:
            pass
        
        return self
    
    async def go_to_menu(self, menu: str, submenu: Optional[str] = None) -> 'OdooTestBase':
        """
        Navigate to a menu.
        
        Supports two formats:
        1. `go_to_menu("Vendas", "Pedidos")` - separate arguments
        2. `go_to_menu("Vendas > Pedidos")` - single string with separator
        
        Args:
            menu: Main menu name or full path (e.g., "Vendas" or "Vendas > Pedidos")
            submenu: Submenu name (optional, ignored if menu contains '>')
            
        Returns:
            Self for method chaining
        """
        await self.menu.go_to_menu(menu, submenu)
        return self
    
    def _resolve_user_friendly_url(self, text: str) -> Optional[str]:
        """
        Resolve user-friendly text to URL or action.
        
        Args:
            text: User-friendly text (e.g., "Dashboard", "Portal", "Loja")
            
        Returns:
            URL string or None if should use menu navigation
        """
        text_lower = text.lower().strip()
        
        # Dashboard/Home mappings
        if text_lower in ["dashboard", "menu principal", "home", "início", "página inicial"]:
            return "DASHBOARD"  # Special marker for dashboard navigation
        
        # Portal mappings
        if text_lower in ["portal", "meu portal", "portal do cliente"]:
            return "/my"
        
        # E-commerce/Shop mappings
        if text_lower in ["loja", "e-commerce", "shop", "compras"]:
            return "/shop"
        
        # Common portal pages
        if text_lower in ["meus pedidos", "pedidos", "orders"]:
            return "/my/orders"
        
        if text_lower in ["meu perfil", "perfil", "profile"]:
            return "/my/profile"
        
        # If it looks like a URL, return as-is
        if text.startswith("/") or text.startswith("http"):
            return text
        
        # Otherwise, treat as menu path
        return None
    
    async def go_to(self, menu_path_or_url: str) -> 'OdooTestBase':
        """
        Navigate to a menu, URL, or user-friendly location.
        
        Supports multiple formats:
        1. Menu path: "Vendas > Pedidos"
        2. User-friendly: "Dashboard", "Portal", "Loja", "Menu principal"
        3. URL: "/web", "/my", "/shop"
        
        Args:
            menu_path_or_url: Menu path, user-friendly text, or URL
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.go_to("Vendas > Pedidos")
            await test.go_to("Dashboard")
            await test.go_to("Portal")
            await test.go_to("/web")
            ```
        """
        # First check if it's a URL (starts with / or http)
        if menu_path_or_url.startswith("/") or menu_path_or_url.startswith("http"):
            # It's a URL, use parent's go_to
            await super().go_to(menu_path_or_url)
            return self
        
        # Resolve user-friendly URLs
        resolved = self._resolve_user_friendly_url(menu_path_or_url)
        
        if resolved == "DASHBOARD":
            # Navigate to dashboard
            await self.menu.go_to_dashboard()
        elif resolved and resolved.startswith("/"):
            # It's a URL, use parent's go_to
            await super().go_to(resolved)
        elif resolved and resolved.startswith("http"):
            # It's a full URL, use parent's go_to
            await super().go_to(resolved)
        else:
            # Not a special URL, treat as menu path (e.g., "Vendas", "Contatos")
            # This includes when resolved is None
            success = await self.menu.go_to_menu(menu_path_or_url)
            if not success:
                # If menu navigation failed, raise error
                raise ValueError(
                    f"Não foi possível navegar para o menu '{menu_path_or_url}'. "
                    f"Verifique se o menu existe e está acessível."
                )
        
        return self
    
    async def go_to_dashboard(self) -> 'OdooTestBase':
        """
        Navigate to Odoo dashboard/home page.
        
        Returns:
            Self for method chaining
        """
        await self.menu.go_to_dashboard()
        return self
    
    async def go_to_home(self) -> 'OdooTestBase':
        """
        Navigate to home page (alias for go_to_dashboard).
        
        Returns:
            Self for method chaining
        """
        await self.menu.go_to_home()
        return self
    
    async def go_to_model(self, model_name: str, view_type: str = "list") -> 'OdooTestBase':
        """
        Navigate directly to a model.
        
        Args:
            model_name: Odoo model name (e.g., "sale.order", "res.partner")
            view_type: View type ("list", "kanban", "form")
            
        Returns:
            Self for method chaining
        """
        base_url = self.config.base_url.rstrip('/')
        url = f"{base_url}/web#model={model_name}&view_type={view_type}"
        await self.go_to(url)
        await asyncio.sleep(0.5)
        return self
    
    async def create_record(self, model_name: Optional[str] = None, fields: Optional[Dict[str, Any]] = None) -> 'OdooTestBase':
        """
        Create a new record.
        
        Args:
            model_name: Model name (optional, if already on the model page)
            fields: Dictionary of field names and values
            
        Returns:
            Self for method chaining
        """
        # Navigate to model if specified
        if model_name:
            await self.go_to_model(model_name, "list")
        
        # Click create button
        await self.view.create_record()
        
        # Fill fields if provided
        if fields:
            for field_name, value in fields.items():
                if isinstance(value, dict) and 'type' in value:
                    field_type = value['type']
                    field_value = value['value']
                    
                    if field_type == 'many2one':
                        await self.field.fill_many2one(field_name, field_value)
                    elif field_type == 'one2many':
                        await self.field.fill_one2many(field_name, field_value)
                    elif field_type == 'char':
                        await self.field.fill_char(field_name, field_value)
                    elif field_type == 'integer':
                        await self.field.fill_integer(field_name, field_value)
                    elif field_type == 'float':
                        await self.field.fill_float(field_name, field_value)
                    elif field_type == 'boolean':
                        await self.field.toggle_boolean(field_name)
                    elif field_type == 'date':
                        await self.field.fill_date(field_name, field_value)
                    elif field_type == 'datetime':
                        await self.field.fill_datetime(field_name, field_value)
                else:
                    # Default to char
                    await self.field.fill_char(field_name, str(value))
        
        return self
    
    async def search_and_open(self, model_name: str, search_text: str) -> 'OdooTestBase':
        """
        Search for a record and open it.
        
        Args:
            model_name: Model name
            search_text: Text to search for
            
        Returns:
            Self for method chaining
        """
        await self.go_to_model(model_name, "list")
        await self.view.search_records(search_text)
        await self.view.open_record(0)
        return self
    
    async def assert_record_exists(self, model_name: str, search_text: str) -> 'OdooTestBase':
        """
        Assert that a record exists.
        
        Args:
            model_name: Model name
            search_text: Text to search for
            
        Returns:
            Self for method chaining
        """
        await self.go_to_model(model_name, "list")
        await self.view.search_records(search_text)
        
        # Check if any results found
        results = self.page.locator('tr.o_data_row, .o_kanban_record')
        count = await results.count()
        assert count > 0, f"Record with '{search_text}' not found in {model_name}"
        
        return self
    
    async def open_record(
        self,
        search_text: str,
        position: Optional[str] = None
    ) -> 'OdooTestBase':
        """
        Search for a record by text and open it.
        
        Args:
            search_text: Text to search for (visible in the record)
            position: Position to select if multiple results ('primeiro', 'segundo', 'último', '1', '2', 'last')
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If no records found or position invalid
            
        Example:
            ```python
            await test.open_record("João Silva")
            await test.open_record("João Silva", position="primeiro")
            await test.open_record("João", position="segundo")
            ```
        """
        await self.view.find_and_open_record(search_text, position)
        return self
    
    async def add_line(self, button_text: Optional[str] = None) -> 'OdooTestBase':
        """
        Add a line to a One2many table (e.g., add product to sale order).
        
        Args:
            button_text: Optional button text (e.g., "Adicionar linha", "Add a line").
                        If not provided, auto-detects the button.
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.add_line()
            await test.add_line("Adicionar linha")
            ```
        """
        await self.view.add_line(button_text)
        return self
    
    async def fill(
        self,
        label_or_assignment: str,
        value: Optional[Any] = None,
        context: Optional[str] = None
    ) -> 'OdooTestBase':
        """
        Fill a field by its visible label. Supports two syntaxes:
        
        1. `await test.fill("Cliente", "João Silva")`
        2. `await test.fill("Cliente = João Silva")`
        
        Uses Odoo-specific field detection for many2one, one2many, etc.
        Falls back to generic fill_by_label for simple fields.
        
        Args:
            label_or_assignment: Field label or assignment string (e.g., "Cliente = João Silva")
            value: Value to fill (if label_or_assignment is just the label)
            context: Optional context to narrow search (e.g., "Seção Cliente")
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.fill("Cliente", "João Silva")
            await test.fill("Cliente = João Silva")
            await test.fill("Data", "01/01/2024", context="Seção Datas")
            ```
        """
        # Parse assignment syntax if value is None
        if value is None and '=' in label_or_assignment:
            parts = label_or_assignment.split('=', 1)
            label = parts[0].strip()
            value = parts[1].strip()
        else:
            label = label_or_assignment
        
        # Use Odoo field helper (which handles Odoo-specific field types)
        # It will use generic methods from core when appropriate
        await self.field.fill_field(label, value, context)
        return self
    
    async def click_button(
        self,
        text: str,
        context: Optional[str] = None
    ) -> 'OdooTestBase':
        """
        Click a button by its visible text. Automatically detects if button is in wizard or form.
        
        Args:
            text: Button text (e.g., "Salvar", "Confirmar", "Criar")
            context: Optional context ("wizard" or "form"). If not specified, auto-detects.
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If button not found
            
        Example:
            ```python
            await test.click_button("Salvar")
            await test.click_button("Confirmar", context="wizard")
            ```
        """
        # Check if wizard is visible
        wizard_visible = await self.wizard.is_wizard_visible()
        
        # Determine search scope
        if context == "wizard":
            # Search only in wizard
            wizard_loc = await self.wizard.get_wizard_locator()
            if not wizard_loc:
                raise ValueError(f"Wizard não encontrado. Botão '{text}' não pode ser clicado.")
            search_scope = wizard_loc
        elif context == "form":
            # Search only in form (not in wizard)
            search_scope = self.page
            # Exclude wizard areas
            wizard_loc = await self.wizard.get_wizard_locator()
            if wizard_loc:
                # We'll search in page but exclude wizard
                pass
        else:
            # Auto-detect: if wizard visible, search there first, else search in form
            if wizard_visible:
                wizard_loc = await self.wizard.get_wizard_locator()
                search_scope = wizard_loc if wizard_loc else self.page
            else:
                search_scope = self.page
        
        # Build button selectors
        button_selectors = [
            f'button:has-text("{text}")',
            f'button:has-text("{text}"):visible',
            f'a:has-text("{text}")',
            f'a:has-text("{text}"):visible',
            f'button[title*="{text}"]',
            f'button[aria-label*="{text}"]',
            f'[role="button"]:has-text("{text}")',
        ]
        
        # Try to find and click button
        for selector in button_selectors:
            try:
                if context == "wizard" and wizard_visible:
                    # Search within wizard
                    wizard_loc = await self.wizard.get_wizard_locator()
                    if wizard_loc:
                        buttons = wizard_loc.locator(selector)
                    else:
                        buttons = self.page.locator(selector)
                elif context == "form":
                    # Search in page but exclude wizard
                    buttons = self.page.locator(selector)
                    # Filter out buttons inside wizard
                    count = await buttons.count()
                    for i in range(count):
                        btn = buttons.nth(i)
                        is_in_wizard = await btn.evaluate("""
                            (el) => {
                                let wizard = el.closest('.modal, .o_dialog, [role="dialog"], .o_popup');
                                return wizard !== null;
                            }
                        """)
                        if not is_in_wizard and await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(0.3)
                            await self.wizard.is_wizard_visible()
                            return self
                    continue
                else:
                    # Auto-detect: search in wizard first if visible, else in page
                    if wizard_visible:
                        wizard_loc = await self.wizard.get_wizard_locator()
                        if wizard_loc:
                            buttons = wizard_loc.locator(selector)
                        else:
                            buttons = self.page.locator(selector)
                    else:
                        buttons = self.page.locator(selector)
                
                count = await buttons.count()
                
                if count > 0:
                    button = buttons.first
                    if await button.is_visible():
                        await button.click()
                        await asyncio.sleep(0.3)
                        
                        # Update wizard state
                        await self.wizard.is_wizard_visible()
                        
                        return self
            except Exception:
                continue
        
        # If not found, provide helpful error
        location = "wizard" if (wizard_visible and context != "form") else "formulário"
        raise ValueError(
            f"Botão '{text}' não encontrado no {location}. "
            f"Verifique se o texto está correto e se está na tela correta."
        )
    
    async def click(
        self,
        selector_or_text: str,
        description: Optional[str] = None
    ) -> 'OdooTestBase':
        """
        Click an element. If selector looks like a CSS selector, uses it directly.
        Otherwise, treats as button text and uses click_button().
        
        Args:
            selector_or_text: CSS selector or button text
            description: Description for logging (optional)
            
        Returns:
            Self for method chaining
        """
        # Check if it looks like a CSS selector (contains special chars)
        is_css_selector = any(char in selector_or_text for char in ['.', '#', '[', ':', '>', ' ', '(', ')'])
        
        if is_css_selector:
            # Use parent class method (from SimpleTestBase)
            await super().click(selector_or_text, description or selector_or_text)
        else:
            # Treat as button text
            await self.click_button(selector_or_text)
        
        return self
    
    async def scroll_down(self, amount: int = 500) -> 'OdooTestBase':
        """
        Scroll down the page.
        
        Args:
            amount: Pixels to scroll (default: 500)
            
        Returns:
            Self for method chaining
        """
        await super().scroll(direction="down", amount=amount)
        return self
    
    async def scroll_up(self, amount: int = 500) -> 'OdooTestBase':
        """
        Scroll up the page.
        
        Args:
            amount: Pixels to scroll (default: 500)
            
        Returns:
            Self for method chaining
        """
        await super().scroll(direction="up", amount=amount)
        return self
    
    async def hover(self, text: str, context: Optional[str] = None) -> 'OdooTestBase':
        """
        Hover over an element by visible text.
        
        Args:
            text: Visible text of element
            context: Optional context for disambiguation
            
        Returns:
            Self for method chaining
        """
        # Try to find element by text
        selectors = [
            f':has-text("{text}")',
            f'[title*="{text}"]',
            f'[aria-label*="{text}"]',
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    await super().hover(selector, f"Hover: {text}")
                    return self
            except Exception:
                continue
        
        raise Exception(f"Element with text '{text}' not found for hover")
    
    async def double_click(self, text: str, context: Optional[str] = None) -> 'OdooTestBase':
        """
        Double-click on an element by visible text.
        
        Args:
            text: Visible text of element
            context: Optional context for disambiguation
            
        Returns:
            Self for method chaining
        """
        # Try to find element by text
        selectors = [
            f':has-text("{text}")',
            f'button:has-text("{text}")',
            f'a:has-text("{text}")',
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    await super().double_click(selector, f"Double-click: {text}")
                    return self
            except Exception:
                continue
        
        raise Exception(f"Element with text '{text}' not found for double-click")
    
    async def right_click(self, text: str, context: Optional[str] = None) -> 'OdooTestBase':
        """
        Right-click on an element by visible text.
        
        Args:
            text: Visible text of element
            context: Optional context for disambiguation
            
        Returns:
            Self for method chaining
        """
        # Try to find element by text
        selectors = [
            f':has-text("{text}")',
            f'button:has-text("{text}")',
            f'a:has-text("{text}")',
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    await super().right_click(selector, f"Right-click: {text}")
                    return self
            except Exception:
                continue
        
        raise Exception(f"Element with text '{text}' not found for right-click")
    
    async def drag_and_drop(self, from_text: str, to_text: str) -> 'OdooTestBase':
        """
        Drag and drop from one element to another by visible text.
        
        Args:
            from_text: Visible text of source element
            to_text: Visible text of target element
            
        Returns:
            Self for method chaining
        """
        # Find source element
        from_selectors = [
            f':has-text("{from_text}")',
            f'[title*="{from_text}"]',
        ]
        
        source_element = None
        for selector in from_selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    source_element = selector
                    break
            except Exception:
                continue
        
        if not source_element:
            raise Exception(f"Source element with text '{from_text}' not found")
        
        # Find target element
        to_selectors = [
            f':has-text("{to_text}")',
            f'[title*="{to_text}"]',
        ]
        
        target_element = None
        for selector in to_selectors:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0 and await element.is_visible():
                    target_element = selector
                    break
            except Exception:
                continue
        
        if not target_element:
            raise Exception(f"Target element with text '{to_text}' not found")
        
        await super().drag(source_element, target_element, f"Drag {from_text} to {to_text}")
        return self

