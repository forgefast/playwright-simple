#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base class for simple Playwright tests.

Provides easy-to-use methods for common actions, designed for QAs
without deep programming knowledge while maintaining flexibility for advanced use cases.
"""

import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .config import TestConfig
from .cursor import CursorManager
from .screenshot import ScreenshotManager
from .selectors import SelectorManager
from .session import SessionManager


class SimpleTestBase:
    """
    Base class for simple visual tests.
    
    Provides easy-to-use methods for common actions with automatic
    cursor visualization, screenshots, and smart element selection.
    
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
    
    def __init__(self, page: Page, config: Optional[TestConfig] = None, test_name: Optional[str] = None):
        """
        Initialize test base.
        
        Args:
            page: Playwright page instance
            config: Test configuration (uses defaults if not provided)
            test_name: Name of current test (for organization)
        """
        self.page = page
        self.config = config or TestConfig()
        self.test_name = test_name or "default"
        
        # Initialize managers
        self.cursor_manager = CursorManager(page, self.config.cursor)
        self.screenshot_manager = ScreenshotManager(page, self.config.screenshots, test_name)
        self.selector_manager = SelectorManager(page, self.config.browser.timeout)
        self.session_manager = SessionManager()
        
        # Inject cursor on first action
        self._cursor_injected = False
    
    async def _ensure_cursor(self):
        """Ensure cursor is injected."""
        if not self._cursor_injected:
            await self.cursor_manager.inject()
            self._cursor_injected = True
    
    # ==================== Navigation Methods ====================
    
    async def go_to(self, url: str) -> 'SimpleTestBase':
        """
        Navigate to a URL.
        
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
        await self._ensure_cursor()
        
        # Validate URL format
        if not url.startswith("http") and not url.startswith("/"):
            # If it doesn't look like a URL, it might be a menu path
            # This should be handled by subclasses, but as a safety check:
            raise ValueError(
                f"URL inválida: '{url}'. "
                f"URLs devem começar com 'http' ou '/'. "
                f"Para navegação por menu, use o método apropriado da subclasse."
            )
        
        if url.startswith("http"):
            full_url = url
        else:
            base_url = self.config.base_url.rstrip('/')
            full_url = f"{base_url}{url}"
        
        await self.page.goto(full_url, wait_until="networkidle", timeout=self.config.browser.navigation_timeout)
        await asyncio.sleep(0.5)
        
        # Re-inject cursor after navigation to ensure it's visible
        try:
            await self.cursor_manager.inject(force=True)
        except Exception:
            # If injection fails, try to ensure cursor exists
            await self.cursor_manager._ensure_cursor_exists()
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("navigate", url)
        
        return self
    
    async def back(self) -> 'SimpleTestBase':
        """
        Navigate back in browser history.
        
        Returns:
            Self for method chaining
        """
        await self._ensure_cursor()
        await self.page.go_back(wait_until="networkidle", timeout=self.config.browser.navigation_timeout)
        await asyncio.sleep(0.5)
        return self
    
    async def forward(self) -> 'SimpleTestBase':
        """
        Navigate forward in browser history.
        
        Returns:
            Self for method chaining
        """
        await self._ensure_cursor()
        await self.page.go_forward(wait_until="networkidle", timeout=self.config.browser.navigation_timeout)
        await asyncio.sleep(0.5)
        return self
    
    async def refresh(self) -> 'SimpleTestBase':
        """
        Refresh the current page.
        
        Returns:
            Self for method chaining
        """
        await self._ensure_cursor()
        await self.page.reload(wait_until="networkidle", timeout=self.config.browser.navigation_timeout)
        await asyncio.sleep(0.5)
        return self
    
    async def navigate(self, menu_path: List[str]) -> 'SimpleTestBase':
        """
        Navigate through a menu path.
        
        Args:
            menu_path: List of menu items to navigate (e.g., ["Vendas", "Pedidos"])
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.navigate(["Menu", "Submenu", "Item"])
            ```
        """
        await self._ensure_cursor()
        
        for menu_item in menu_path:
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
                    await self.click(selector, f"Menu {menu_item}")
                    clicked = True
                    await asyncio.sleep(0.5)
                    break
                except Exception:
                    continue
            
            if not clicked:
                raise Exception(f"Menu item '{menu_item}' not found")
        
        return self
    
    # ==================== Interaction Methods ====================
    
    async def click(self, selector: str, description: str = "") -> 'SimpleTestBase':
        """
        Click on an element.
        
        Args:
            selector: CSS selector or text of element
            description: Description of element (for logs)
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.click('button:has-text("Submit")')
            await test.click('[data-testid="login-button"]', "Login Button")
            ```
        """
        await self._ensure_cursor()
        
        # Find element with smart selector
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise Exception(f"Element not found: {description or selector}")
        
        # Get element position
        box = await element.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            
            # Move cursor to element (waits for animation to complete)
            await self.cursor_manager.move_to(x, y)
            
            # Show hover effect
            if self.config.cursor.hover_effect:
                await self.cursor_manager.show_hover_effect(x, y, True)
                await asyncio.sleep(0.2)  # Brief pause to show hover
            
            # Show click effect (waits for animation to complete)
            await self.cursor_manager.show_click_effect(x, y)
            await asyncio.sleep(0.1)  # Brief pause after click effect
        
        # NOW click - cursor has moved, hovered, and clicked visually
        await element.click()
        await asyncio.sleep(0.15)
        
        # Screenshot
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("click", selector)
        
        return self
    
    async def double_click(self, selector: str, description: str = "") -> 'SimpleTestBase':
        """
        Double-click on an element.
        
        Args:
            selector: CSS selector or text of element
            description: Description of element (for logs)
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.double_click('button:has-text("Edit")')
            ```
        """
        await self._ensure_cursor()
        
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise Exception(f"Element not found: {description or selector}")
        
        box = await element.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            
            # Move cursor to element (waits for animation to complete)
            await self.cursor_manager.move_to(x, y)
            
            # Show hover effect
            if self.config.cursor.hover_effect:
                await self.cursor_manager.show_hover_effect(x, y, True)
                await asyncio.sleep(0.2)
            
            # Show first click effect
            await self.cursor_manager.show_click_effect(x, y)
            await asyncio.sleep(0.15)
            
            # Show second click effect (for double click)
            await self.cursor_manager.show_click_effect(x, y)
            await asyncio.sleep(0.1)
        
        # NOW double-click - cursor has moved, hovered, and clicked visually twice
        await element.dblclick()
        await asyncio.sleep(0.15)
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("double_click", selector)
        
        return self
    
    async def right_click(self, selector: str, description: str = "") -> 'SimpleTestBase':
        """
        Right-click on an element.
        
        Args:
            selector: CSS selector or text of element
            description: Description of element (for logs)
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.right_click('div:has-text("Item")')
            ```
        """
        await self._ensure_cursor()
        
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise Exception(f"Element not found: {description or selector}")
        
        box = await element.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            await self.cursor_manager.move_to(x, y)
            await asyncio.sleep(0.1)
            await self.cursor_manager.show_click_effect(x, y)
            await asyncio.sleep(0.1)
        
        await element.click(button="right")
        await asyncio.sleep(0.15)
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("right_click", selector)
        
        return self
    
    async def type(self, selector: str, text: str, description: str = "") -> 'SimpleTestBase':
        """
        Type text into a field.
        
        Args:
            selector: Selector of field
            text: Text to type
            description: Description of field (for logs)
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.type('input[name="username"]', "admin")
            await test.type('#password', "secret123", "Password Field")
            ```
        """
        await self._ensure_cursor()
        
        # Find element
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise Exception(f"Element not found: {description or selector}")
        
        # Get element position
        box = await element.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            
            print(f"🖱️  DEBUG type: Element found at ({x}, {y}), moving cursor...")
            
            await self.cursor_manager.move_to(x, y)
            await asyncio.sleep(0.1)
            
            print(f"🖱️  DEBUG type: Cursor moved, typing...")
        
        # Clear and type
        await element.clear()
        await asyncio.sleep(0.05)
        
        # Type character by character for visual effect
        for char in text:
            await element.type(char, delay=20)
        
        await asyncio.sleep(0.1)
        
        # Screenshot
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("type", selector)
        
        return self
    
    async def select(self, selector: str, option: str, description: str = "") -> 'SimpleTestBase':
        """
        Select an option in a dropdown.
        
        Args:
            selector: Selector of dropdown
            option: Option text or value to select
            description: Description of dropdown (for logs)
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.select('select[name="country"]', "Brazil")
            ```
        """
        await self._ensure_cursor()
        
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise Exception(f"Element not found: {description or selector}")
        
        await element.select_option(option)
        await asyncio.sleep(0.2)
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("select", selector)
        
        return self
    
    async def hover(self, selector: str, description: str = "") -> 'SimpleTestBase':
        """
        Hover over an element.
        
        Args:
            selector: Selector of element
            description: Description of element (for logs)
            
        Returns:
            Self for method chaining
        """
        await self._ensure_cursor()
        
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise Exception(f"Element not found: {description or selector}")
        
        box = await element.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            await self.cursor_manager.move_to(x, y)
            await self.cursor_manager.show_hover_effect(x, y, True)
            await asyncio.sleep(0.1)
        
        await element.hover()
        await asyncio.sleep(0.2)
        
        return self
    
    async def drag(self, source: str, target: str, description: str = "") -> 'SimpleTestBase':
        """
        Drag and drop from source to target.
        
        Args:
            source: Selector of source element
            target: Selector of target element
            description: Description (for logs)
            
        Returns:
            Self for method chaining
        """
        await self._ensure_cursor()
        
        source_element = await self.selector_manager.find_element(source, f"Source: {description}")
        target_element = await self.selector_manager.find_element(target, f"Target: {description}")
        
        if source_element is None or target_element is None:
            raise Exception(f"Source or target element not found: {description}")
        
        await source_element.drag_to(target_element)
        await asyncio.sleep(0.3)
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("drag", f"{source}->{target}")
        
        return self
    
    async def scroll(self, selector: Optional[str] = None, direction: str = "down", amount: int = 500) -> 'SimpleTestBase':
        """
        Scroll page or element.
        
        Args:
            selector: Selector of element to scroll (None for page)
            direction: "down", "up", "left", "right"
            amount: Pixels to scroll
            
        Returns:
            Self for method chaining
        """
        await self._ensure_cursor()
        
        if selector:
            element = await self.selector_manager.find_element(selector, "Scroll target")
            if element is None:
                raise Exception(f"Element not found for scrolling: {selector}")
            
            if direction == "down":
                await element.evaluate(f"element => element.scrollBy(0, {amount})")
            elif direction == "up":
                await element.evaluate(f"element => element.scrollBy(0, -{amount})")
            elif direction == "right":
                await element.evaluate(f"element => element.scrollBy({amount}, 0)")
            elif direction == "left":
                await element.evaluate(f"element => element.scrollBy(-{amount}, 0)")
        else:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "right":
                await self.page.evaluate(f"window.scrollBy({amount}, 0)")
            elif direction == "left":
                await self.page.evaluate(f"window.scrollBy(-{amount}, 0)")
        
        await asyncio.sleep(0.3)
        return self
    
    # ==================== Wait Methods ====================
    
    async def wait(self, seconds: float = 1.0) -> 'SimpleTestBase':
        """
        Wait for a specified time.
        
        Args:
            seconds: Seconds to wait
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.wait(2.5)  # Wait 2.5 seconds
            ```
        """
        await asyncio.sleep(seconds)
        return self
    
    async def wait_for(self, selector: str, state: str = "visible", timeout: Optional[int] = None, description: str = "") -> 'SimpleTestBase':
        """
        Wait for element to appear.
        
        Args:
            selector: Selector of element
            state: State to wait for (visible, hidden, attached, detached)
            timeout: Timeout in milliseconds
            description: Description (for logs)
            
        Returns:
            Self for method chaining
        """
        await self.selector_manager.wait_for_element(selector, description, timeout, state)
        return self
    
    async def wait_for_url(self, url_pattern: str, timeout: Optional[int] = None) -> 'SimpleTestBase':
        """
        Wait for URL to match pattern.
        
        Args:
            url_pattern: URL pattern to wait for
            timeout: Timeout in milliseconds
            
        Returns:
            Self for method chaining
        """
        timeout = timeout or self.config.browser.timeout
        await self.page.wait_for_url(url_pattern, timeout=timeout)
        return self
    
    async def wait_for_text(self, selector: str, text: str, timeout: Optional[int] = None, description: str = "") -> 'SimpleTestBase':
        """
        Wait for element to contain text.
        
        Args:
            selector: Selector of element
            text: Text to wait for
            timeout: Timeout in milliseconds
            description: Description (for logs)
            
        Returns:
            Self for method chaining
        """
        timeout = timeout or self.config.browser.timeout
        element = await self.selector_manager.wait_for_element(selector, description, timeout)
        await element.wait_for(state="visible", timeout=timeout)
        await self.page.wait_for_function(
            f"document.querySelector('{selector}')?.textContent?.includes('{text}')",
            timeout=timeout
        )
        return self
    
    # ==================== Assertion Methods ====================
    
    async def assert_text(self, selector: str, expected: str, description: str = "") -> 'SimpleTestBase':
        """
        Assert element contains expected text.
        
        Args:
            selector: Selector of element
            expected: Expected text
            description: Description (for error messages)
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If text doesn't match
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise AssertionError(f"Element not found: {description or selector}")
        
        actual = await element.text_content()
        if expected not in (actual or ""):
            raise AssertionError(
                f"Text assertion failed for {description or selector}: "
                f"expected '{expected}' in '{actual}'"
            )
        return self
    
    async def assert_visible(self, selector: str, description: str = "") -> 'SimpleTestBase':
        """
        Assert element is visible.
        
        Args:
            selector: Selector of element
            description: Description (for error messages)
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If element is not visible
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise AssertionError(f"Element not found: {description or selector}")
        
        if not await element.is_visible():
            raise AssertionError(f"Element is not visible: {description or selector}")
        return self
    
    async def assert_url(self, pattern: str) -> 'SimpleTestBase':
        """
        Assert current URL matches pattern.
        
        Args:
            pattern: URL pattern to match
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If URL doesn't match
        """
        current_url = self.page.url
        if pattern not in current_url:
            raise AssertionError(f"URL assertion failed: expected '{pattern}' in '{current_url}'")
        return self
    
    async def assert_count(self, selector: str, expected_count: int, description: str = "") -> 'SimpleTestBase':
        """
        Assert number of elements matching selector.
        
        Args:
            selector: Selector of elements
            expected_count: Expected number of elements
            description: Description (for error messages)
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If count doesn't match
        """
        count = await self.page.locator(selector).count()
        if count != expected_count:
            raise AssertionError(
                f"Count assertion failed for {description or selector}: "
                f"expected {expected_count}, got {count}"
            )
        return self
    
    async def assert_attr(self, selector: str, attribute: str, expected: str, description: str = "") -> 'SimpleTestBase':
        """
        Assert element attribute value.
        
        Args:
            selector: Selector of element
            attribute: Attribute name
            expected: Expected attribute value
            description: Description (for error messages)
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If attribute doesn't match
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise AssertionError(f"Element not found: {description or selector}")
        
        actual = await element.get_attribute(attribute)
        if actual != expected:
            raise AssertionError(
                f"Attribute assertion failed for {description or selector}: "
                f"expected {attribute}='{expected}', got '{actual}'"
            )
        return self
    
    # ==================== Helper Methods ====================
    
    async def login(self, username: str, password: str, login_url: str = "/login", show_process: bool = False) -> 'SimpleTestBase':
        """
        Login to system with common selectors.
        
        Args:
            username: Username
            password: Password
            login_url: URL of login page
            show_process: Show login process in logs
            
        Returns:
            Self for method chaining
        """
        if show_process:
            print(f"  🔐 Logging in as {username}...")
        
        await self.go_to(login_url)
        await asyncio.sleep(0.3)
        
        # Try common login field selectors
        login_selectors = [
            'input[name="username"]',
            'input[name="login"]',
            'input[name="email"]',
            'input[type="text"]',
            'input[type="email"]',
            '#username',
            '#login',
            '#email',
        ]
        
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            '#password',
        ]
        
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Entrar")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'input[type="submit"]',
        ]
        
        # Fill username
        for selector in login_selectors:
            try:
                await self.type(selector, username, "Username field")
                break
            except Exception:
                continue
        
        await asyncio.sleep(0.2)
        
        # Fill password
        for selector in password_selectors:
            try:
                await self.type(selector, password, "Password field")
                break
            except Exception:
                continue
        
        await asyncio.sleep(0.2)
        
        # Submit
        for selector in submit_selectors:
            try:
                await self.click(selector, "Login button")
                break
            except Exception:
                continue
        
        await asyncio.sleep(1)
        await self.page.wait_for_load_state("networkidle", timeout=self.config.browser.timeout)
        await asyncio.sleep(0.5)
        
        return self
    
    async def fill_form(self, fields: Dict[str, str]) -> 'SimpleTestBase':
        """
        Fill a form with multiple fields.
        
        Args:
            fields: Dictionary mapping selectors to values
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.fill_form({
                'input[name="name"]': "John",
                'input[name="email"]': "john@example.com",
            })
            ```
        """
        for selector, value in fields.items():
            await self.type(selector, value, f"Form field: {selector}")
            await asyncio.sleep(0.1)
        return self
    
    async def fill_by_label(
        self,
        label: str,
        value: str,
        context: Optional[str] = None
    ) -> 'SimpleTestBase':
        """
        Fill a field by its visible label (generic web application support).
        
        Args:
            label: Visible label text (e.g., "Email", "Name", "Password")
            value: Value to fill
            context: Optional context to narrow search (e.g., "Section Name")
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If field not found or multiple fields found without context
            
        Example:
            ```python
            await test.fill_by_label("Email", "user@example.com")
            await test.fill_by_label("Name", "John", context="Personal Info")
            ```
        """
        await self._ensure_cursor()
        
        label_normalized = label.strip()
        
        # Build selectors to find label
        label_selectors = [
            f'label:has-text("{label_normalized}")',
            f'label:has-text("{label_normalized}"):visible',
            f'[for*="{label_normalized.lower()}"]',
            f'text="{label_normalized}"',
        ]
        
        found_fields = []
        
        for label_sel in label_selectors:
            try:
                labels = self.page.locator(label_sel)
                count = await labels.count()
                
                for i in range(count):
                    label_elem = labels.nth(i)
                    if not await label_elem.is_visible():
                        continue
                    
                    # Check context if provided
                    if context:
                        parent_text = await label_elem.evaluate("""
                            (el) => {
                                let parent = el.closest('fieldset, section, .form-group, .field-group');
                                return parent ? parent.textContent : '';
                            }
                        """)
                        if context.lower() not in parent_text.lower():
                            continue
                    
                    # Find associated field
                    field_name = await label_elem.get_attribute("for")
                    
                    if field_name:
                        # Find input/field by name
                        field_selectors = [
                            f'input[name="{field_name}"]',
                            f'textarea[name="{field_name}"]',
                            f'select[name="{field_name}"]',
                            f'[name="{field_name}"]',
                        ]
                    else:
                        # Try to find field near the label
                        field_selectors = [
                            'input',
                            'textarea',
                            'select',
                        ]
                    
                    # Find field
                    for field_sel in field_selectors:
                        try:
                            if field_name:
                                field = self.page.locator(field_sel).first
                            else:
                                # Find field near label (next sibling or in same container)
                                field = label_elem.locator('xpath=following::*[self::input or self::textarea or self::select][1]')
                            
                            if await field.count() > 0 and await field.is_visible():
                                found_fields.append(field)
                                break
                        except Exception:
                            continue
            except Exception:
                continue
        
        if not found_fields:
            raise ValueError(f"Campo com label '{label}' não encontrado. Verifique se o label está correto e visível na tela.")
        
        if len(found_fields) > 1 and not context:
            raise ValueError(
                f"Múltiplos campos '{label}' encontrados. "
                f"Use context para especificar (ex: context='Seção Nome'). "
                f"Campos encontrados: {len(found_fields)}"
            )
        
        # Fill the first matching field
        field = found_fields[0]
        
        # Check if it's a select dropdown
        tag_name = await field.evaluate("(el) => el.tagName.toLowerCase()")
        if tag_name == "select":
            await field.select_option(label=value)
        else:
            await field.fill(value)
        
        await asyncio.sleep(0.2)
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("fill_by_label", label)
        
        return self
    
    async def select_by_label(
        self,
        label: str,
        option: str,
        context: Optional[str] = None
    ) -> 'SimpleTestBase':
        """
        Select an option in a dropdown by its visible label.
        
        Args:
            label: Visible label text
            option: Option text or value to select
            context: Optional context to narrow search
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.select_by_label("Country", "Brazil")
            ```
        """
        await self._ensure_cursor()
        
        label_normalized = label.strip()
        
        # Find label
        label_selectors = [
            f'label:has-text("{label_normalized}")',
            f'label:has-text("{label_normalized}"):visible',
            f'[for*="{label_normalized.lower()}"]',
        ]
        
        field = None
        for label_sel in label_selectors:
            try:
                label_elem = self.page.locator(label_sel).first
                if await label_elem.count() > 0 and await label_elem.is_visible():
                    # Check context if provided
                    if context:
                        parent_text = await label_elem.evaluate("""
                            (el) => {
                                let parent = el.closest('fieldset, section, .form-group');
                                return parent ? parent.textContent : '';
                            }
                        """)
                        if context.lower() not in parent_text.lower():
                            continue
                    
                    # Find associated select
                    field_name = await label_elem.get_attribute("for")
                    if field_name:
                        field = self.page.locator(f'select[name="{field_name}"]').first
                    else:
                        field = label_elem.locator('xpath=following::select[1]')
                    
                    if await field.count() > 0:
                        break
            except Exception:
                continue
        
        if not field or await field.count() == 0:
            raise ValueError(f"Dropdown com label '{label}' não encontrado.")
        
        await field.select_option(label=option)
        await asyncio.sleep(0.2)
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("select_by_label", label)
        
        return self
    
    async def get_text(self, selector: str, description: str = "") -> str:
        """
        Get text content of element.
        
        Args:
            selector: Selector of element
            description: Description (for logs)
            
        Returns:
            Text content
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise Exception(f"Element not found: {description or selector}")
        return (await element.text_content()) or ""
    
    async def get_attr(self, selector: str, attribute: str, description: str = "") -> Optional[str]:
        """
        Get attribute value of element.
        
        Args:
            selector: Selector of element
            attribute: Attribute name
            description: Description (for logs)
            
        Returns:
            Attribute value or None
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            raise Exception(f"Element not found: {description or selector}")
        return await element.get_attribute(attribute)
    
    async def is_visible(self, selector: str, description: str = "") -> bool:
        """
        Check if element is visible.
        
        Args:
            selector: Selector of element
            description: Description (for logs)
            
        Returns:
            True if visible, False otherwise
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            return False
        return await element.is_visible()
    
    async def is_enabled(self, selector: str, description: str = "") -> bool:
        """
        Check if element is enabled.
        
        Args:
            selector: Selector of element
            description: Description (for logs)
            
        Returns:
            True if enabled, False otherwise
        """
        element = await self.selector_manager.find_element(selector, description)
        if element is None:
            return False
        return await element.is_enabled()
    
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
    
    # ==================== Generic UI Helpers ====================
    
    async def wait_for_modal(
        self,
        modal_selector: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> 'SimpleTestBase':
        """
        Wait for a modal dialog to appear.
        
        Uses common modal selectors: .modal, [role="dialog"], .dialog
        
        Args:
            modal_selector: Optional custom selector for the modal.
                          Defaults to common modal patterns.
            timeout: Timeout in milliseconds
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.wait_for_modal()
            await test.close_modal()
            ```
        """
        timeout = timeout or self.config.browser.timeout
        
        if modal_selector is None:
            # Common modal selectors
            modal_selector = '.modal, [role="dialog"], .dialog, .modal-dialog'
        
        modal = self.page.locator(modal_selector).first
        await modal.wait_for(state="visible", timeout=timeout)
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("wait_for_modal")
        
        return self
    
    async def close_modal(
        self,
        close_button_selector: Optional[str] = None
    ) -> 'SimpleTestBase':
        """
        Close any open modal dialog.
        
        Uses common close button selectors: button[aria-label*="Close"],
        button:has-text("Close"), .close, .modal-close
        
        Args:
            close_button_selector: Optional custom selector for close button.
                                 Defaults to common close button patterns.
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.wait_for_modal()
            await test.close_modal()
            ```
        """
        if close_button_selector is None:
            # Common close button selectors
            close_button_selector = (
                'button[aria-label*="Close"], '
                'button:has-text("Close"), '
                '.close, '
                '.modal-close, '
                '[data-dismiss="modal"]'
            )
        
        close_button = self.page.locator(close_button_selector).first
        if await close_button.count() > 0:
            await close_button.click()
            await asyncio.sleep(0.3)
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("close_modal")
        
        return self
    
    async def click_button(
        self,
        text: str,
        context: Optional[str] = None,
        description: str = ""
    ) -> 'SimpleTestBase':
        """
        Click a button by its visible text.
        
        Args:
            text: Button text to match
            context: Optional context selector to narrow search
            description: Description for error messages
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.click_button("Submit")
            await test.click_button("Save", context=".form-container")
            ```
        """
        await self._ensure_cursor()
        
        if context:
            context_locator = self.page.locator(context)
            button = context_locator.locator(f'button:has-text("{text}"), a:has-text("{text}"), [role="button"]:has-text("{text}")').first
        else:
            button = self.page.locator(f'button:has-text("{text}"), a:has-text("{text}"), [role="button"]:has-text("{text}")').first
        
        await button.wait_for(state="visible", timeout=self.config.browser.timeout)
        await button.click()
        await asyncio.sleep(0.2)
        
        if self.config.screenshots.auto:
            await self.screenshot_manager.capture_on_action("click_button", text)
        
        return self
    
    async def get_card_content(self, card_selector: str, description: str = "") -> str:
        """
        Get text content from a card or container element.
        
        Args:
            card_selector: CSS selector for the card/container
            description: Description for error messages
            
        Returns:
            Text content of the card, or empty string if not found
            
        Example:
            ```python
            content = await test.get_card_content(".status-card")
            print(f"Card content: {content}")
            ```
        """
        try:
            card = self.page.locator(card_selector).first
            if await card.count() == 0:
                if description:
                    print(f"  ⚠️  Card not found: {description}")
                return ""
            
            return (await card.text_content()) or ""
        except Exception as e:
            if description:
                print(f"  ⚠️  Error getting card content ({description}): {e}")
            return ""


