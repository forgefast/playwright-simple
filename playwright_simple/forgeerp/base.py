#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ForgeERPTestBase - Main class for ForgeERP testing.

Extends SimpleTestBase with ForgeERP-specific functionality for HTMX,
Tailwind CSS, and Alpine.js interactions.
"""

import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import Page

from ..core.base import SimpleTestBase
from ..core.config import TestConfig
from ..core.htmx import HTMXHelper
from .selectors import ForgeERPSelectors
from .components import ForgeERPComponents
from .workflows import ForgeERPWorkflows


class ForgeERPTestBase(SimpleTestBase):
    """
    Base class for ForgeERP tests.
    
    Extends SimpleTestBase with ForgeERP-specific methods for:
    - Navigation (setup, provision, status, deploy, diagnostics)
    - Form interactions (provision, deploy, diagnostics)
    - HTMX interactions (waiting for swaps, detecting errors)
    - Component helpers (modals, cards, buttons)
    - Workflows (provision, deploy, diagnostics)
    
    Example:
        ```python
        from playwright_simple.forgeerp import ForgeERPTestBase
        
        async def test_provision(page, test: ForgeERPTestBase):
            await test.go_to_provision()
            await test.fill_provision_form("my-client", "dev")
            await test.submit_form()
            await test.assert_no_errors()
        ```
    """
    
    def __init__(self, page: Page, config: Optional[TestConfig] = None, test_name: Optional[str] = None):
        """
        Initialize ForgeERP test base.
        
        Args:
            page: Playwright page instance
            config: Test configuration
            test_name: Name of current test
        """
        super().__init__(page, config, test_name)
        
        # Initialize ForgeERP-specific helpers
        self.htmx = HTMXHelper(page, self.config.browser.timeout)
        self.components = ForgeERPComponents(page, self.htmx)
        self.workflows = ForgeERPWorkflows(page, self.components, self.htmx, self.config)
        
        # Adapt cursor color to ForgeERP theme (indigo)
        if self.config.cursor.color == "#007bff":  # Default blue
            self.config.cursor.color = "#6366f1"  # ForgeERP indigo-500
            self.config.cursor.click_effect_color = "#6366f1"
            self.config.cursor.hover_effect_color = "#4f46e5"  # indigo-600
    
    # ==================== Navigation Methods ====================
    
    async def go_to_setup(self) -> 'ForgeERPTestBase':
        """
        Navigate to setup page.
        
        Returns:
            Self for method chaining
        """
        await self.go_to("/setup")
        return self
    
    async def go_to_provision(self) -> 'ForgeERPTestBase':
        """
        Navigate to provisioning page.
        
        Returns:
            Self for method chaining
        """
        await self.go_to("/provision")
        return self
    
    async def go_to_status(
        self,
        client_name: Optional[str] = None,
        environment: Optional[str] = None
    ) -> 'ForgeERPTestBase':
        """
        Navigate to status page.
        
        Args:
            client_name: Optional client name (navigates to specific status)
            environment: Optional environment (requires client_name)
            
        Returns:
            Self for method chaining
        """
        if client_name and environment:
            await self.go_to(f"/status/{client_name}/{environment}")
        else:
            await self.go_to("/status")
        return self
    
    async def go_to_deploy(self) -> 'ForgeERPTestBase':
        """
        Navigate to deployment page.
        
        Returns:
            Self for method chaining
        """
        await self.go_to("/deploy")
        return self
    
    async def go_to_diagnostics(self) -> 'ForgeERPTestBase':
        """
        Navigate to diagnostics page.
        
        Returns:
            Self for method chaining
        """
        await self.go_to("/diagnostics")
        return self
    
    async def navigate_menu(self, menu_text: str) -> 'ForgeERPTestBase':
        """
        Navigate using the main menu.
        
        Args:
            menu_text: Menu item text (Home, Setup, Provision, Status, Deploy, Diagnostics)
            
        Returns:
            Self for method chaining
        """
        menu_map = {
            'home': ForgeERPSelectors.NAV_HOME,
            'setup': ForgeERPSelectors.NAV_SETUP,
            'provision': ForgeERPSelectors.NAV_PROVISION,
            'status': ForgeERPSelectors.NAV_STATUS,
            'deploy': ForgeERPSelectors.NAV_DEPLOY,
            'diagnostics': ForgeERPSelectors.NAV_DIAGNOSTICS,
        }
        
        menu_text_lower = menu_text.lower()
        selector = menu_map.get(menu_text_lower)
        
        if selector:
            await self.click(selector, f"Menu: {menu_text}")
        else:
            # Try direct navigation
            await self.go_to(f"/{menu_text_lower}")
        
        return self
    
    # ==================== Form Methods ====================
    
    async def fill_provision_form(
        self,
        client_name: str,
        environment: str = "dev",
        database_type: Optional[str] = None,
        namespace: Optional[str] = None,
        **kwargs
    ) -> 'ForgeERPTestBase':
        """
        Fill the provisioning form.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
            database_type: Database type (postgresql, mysql) - optional
            namespace: Kubernetes namespace - optional
            **kwargs: Additional field values
            
        Returns:
            Self for method chaining
        """
        await self.components.fill_provision_form(
            client_name, environment, database_type, namespace, **kwargs
        )
        return self
    
    async def fill_deploy_form(
        self,
        client_name: str,
        environment: str = "dev",
        chart_name: str = "generic",
        chart_version: Optional[str] = None,
        **kwargs
    ) -> 'ForgeERPTestBase':
        """
        Fill the deployment form.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
            chart_name: Helm chart name (required)
            chart_version: Chart version (optional)
            **kwargs: Additional field values
            
        Returns:
            Self for method chaining
        """
        await self.components.fill_deploy_form(
            client_name, environment, chart_name, chart_version, **kwargs
        )
        return self
    
    async def fill_diagnostics_form(
        self,
        client_name: str,
        environment: str = "dev"
    ) -> 'ForgeERPTestBase':
        """
        Fill the diagnostics form.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
            
        Returns:
            Self for method chaining
        """
        await self.components.fill_diagnostics_form(client_name, environment)
        return self
    
    async def submit_form(
        self,
        button_selector: Optional[str] = None,
        wait_for_response: bool = True,
        container_selector: Optional[str] = None
    ) -> 'ForgeERPTestBase':
        """
        Submit a form and wait for HTMX response.
        
        Args:
            button_selector: Selector for submit button
            wait_for_response: Whether to wait for HTMX response
            container_selector: Selector for result container
            
        Returns:
            Self for method chaining
        """
        await self.components.submit_form(button_selector, wait_for_response, container_selector)
        return self
    
    async def wait_for_htmx_response(
        self,
        container_selector: str,
        timeout: Optional[int] = None,
        check_for_errors: bool = True
    ) -> 'ForgeERPTestBase':
        """
        Wait for HTMX response.
        
        Args:
            container_selector: Selector for HTMX target container
            timeout: Timeout in milliseconds
            check_for_errors: Whether to check for errors
            
        Returns:
            Self for method chaining
        """
        await self.htmx.wait_for_htmx_response(container_selector, timeout, check_for_errors)
        return self
    
    # ==================== Component Methods ====================
    
    # Note: Generic methods are now available from SimpleTestBase:
    # - click_button() - Click button by text
    # - fill_by_label() - Fill field by label
    # - select_by_label() - Select option by label
    # - wait_for_modal() - Wait for modal
    # - close_modal() - Close modal
    # - get_card_content() - Get card content
    
    # ==================== HTMX Methods ====================
    
    async def wait_for_htmx_swap(
        self,
        container_selector: str,
        timeout: Optional[int] = None
    ) -> 'ForgeERPTestBase':
        """
        Wait for HTMX swap to complete.
        
        Args:
            container_selector: Selector for container
            timeout: Timeout in milliseconds
            
        Returns:
            Self for method chaining
        """
        await self.htmx.wait_for_htmx_swap(container_selector, timeout)
        return self
    
    async def wait_for_htmx_loading(
        self,
        indicator_selector: str,
        timeout: Optional[int] = None,
        wait_for_hidden: bool = True
    ) -> 'ForgeERPTestBase':
        """
        Wait for HTMX loading indicator.
        
        Args:
            indicator_selector: Selector for loading indicator
            timeout: Timeout in milliseconds
            wait_for_hidden: Wait for hidden (default) or visible
            
        Returns:
            Self for method chaining
        """
        await self.htmx.wait_for_htmx_loading(indicator_selector, timeout, wait_for_hidden)
        return self
    
    async def detect_htmx_error(self, container_selector: str) -> Optional[str]:
        """
        Detect error messages in HTMX response.
        
        Args:
            container_selector: Selector for container
            
        Returns:
            Error message if found, None otherwise
        """
        return await self.htmx.detect_htmx_error(container_selector)
    
    async def get_htmx_result(
        self,
        container_id: str,
        wait_for_swap: bool = True,
        timeout: Optional[int] = None
    ) -> str:
        """
        Get text content from HTMX result container.
        
        Args:
            container_id: ID of container
            wait_for_swap: Whether to wait for swap first
            timeout: Timeout in milliseconds
            
        Returns:
            Text content
        """
        return await self.htmx.get_htmx_result(container_id, wait_for_swap, timeout)
    
    # ==================== Validation Methods ====================
    
    async def assert_no_errors(self) -> 'ForgeERPTestBase':
        """
        Assert that no errors are displayed on the page.
        
        Checks for:
        - Error toasts
        - Error messages in HTMX results
        - Error classes in UI
        
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If errors are detected
        """
        # Check for error toasts
        error_toast = self.page.locator(ForgeERPSelectors.TOAST_ERROR)
        toast_count = await error_toast.count()
        
        if toast_count > 0:
            error_texts = []
            for i in range(min(toast_count, 3)):
                try:
                    text = await error_toast.nth(i).text_content()
                    if text:
                        error_texts.append(text.strip())
                except Exception:
                    pass
            
            if error_texts:
                raise AssertionError(f"Error toasts detected: {', '.join(error_texts)}")
        
        # Check common HTMX result containers for errors
        containers = [
            ForgeERPSelectors.HTMX_PROVISION_RESULT,
            ForgeERPSelectors.HTMX_DEPLOY_RESULT,
            ForgeERPSelectors.HTMX_STATUS_RESULT,
            ForgeERPSelectors.HTMX_DIAGNOSTICS_SUMMARY,
            ForgeERPSelectors.HTMX_CLIENT_DIAGNOSTICS,
        ]
        
        for container in containers:
            error_msg = await self.htmx.detect_htmx_error(container)
            if error_msg:
                raise AssertionError(f"HTMX error detected in {container}: {error_msg}")
        
        return self
    
    async def assert_success_message(self, expected_text: str) -> 'ForgeERPTestBase':
        """
        Assert that a success message is displayed.
        
        Args:
            expected_text: Expected text in success message
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If success message not found
        """
        success_toast = self.page.locator(ForgeERPSelectors.TOAST_SUCCESS)
        if await success_toast.count() == 0:
            # Check for success in HTMX results
            containers = [
                ForgeERPSelectors.HTMX_PROVISION_RESULT,
                ForgeERPSelectors.HTMX_DEPLOY_RESULT,
            ]
            
            found = False
            for container in containers:
                result = await self.htmx.get_htmx_result(container, wait_for_swap=False)
                if expected_text.lower() in result.lower():
                    found = True
                    break
            
            if not found:
                raise AssertionError(f"Success message '{expected_text}' not found")
        else:
            toast_text = await success_toast.first.text_content()
            if expected_text.lower() not in (toast_text or "").lower():
                raise AssertionError(
                    f"Success message mismatch: expected '{expected_text}', "
                    f"got '{toast_text}'"
                )
        
        return self
    
    async def assert_status_display(
        self,
        client_name: str,
        environment: str
    ) -> 'ForgeERPTestBase':
        """
        Assert that status is displayed for a client.
        
        Args:
            client_name: Client name
            environment: Environment
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If status not found
        """
        # Navigate to status page if not already there
        current_url = self.page.url
        if f"/status/{client_name}/{environment}" not in current_url:
            await self.go_to_status(client_name, environment)
        
        # Check for status content
        status_result = self.page.locator(ForgeERPSelectors.HTMX_STATUS_RESULT)
        if await status_result.count() == 0:
            raise AssertionError("Status result container not found")
        
        result_text = await status_result.text_content()
        if not result_text or client_name.lower() not in result_text.lower():
            raise AssertionError(
                f"Status for {client_name}/{environment} not found or invalid"
            )
        
        return self
    
    async def assert_provision_success(self, client_name: str) -> 'ForgeERPTestBase':
        """
        Assert that provisioning was successful.
        
        Args:
            client_name: Client name that was provisioned
            
        Returns:
            Self for method chaining
            
        Raises:
            AssertionError: If provisioning failed
        """
        # Check provision result
        result = await self.htmx.get_htmx_result(
            ForgeERPSelectors.HTMX_PROVISION_RESULT,
            wait_for_swap=True
        )
        
        # Check for success indicators
        success_indicators = ["success", "created", "provisioned", "completed"]
        result_lower = result.lower()
        
        if not any(indicator in result_lower for indicator in success_indicators):
            # Check for errors
            error_msg = await self.htmx.detect_htmx_error(ForgeERPSelectors.HTMX_PROVISION_RESULT)
            if error_msg:
                raise AssertionError(f"Provisioning failed: {error_msg}")
            else:
                raise AssertionError(
                    f"Provisioning result unclear for {client_name}. "
                    f"Result: {result[:200]}"
                )
        
        return self
    
    # ==================== Workflow Methods ====================
    
    async def provision_client(
        self,
        client_name: str,
        environment: str = "dev",
        **options
    ) -> 'ForgeERPTestBase':
        """
        Execute complete provisioning workflow.
        
        Args:
            client_name: Client name
            environment: Environment (dev, staging, prod)
            **options: Additional provisioning options
            
        Returns:
            Self for method chaining
        """
        await self.workflows.provision_client(client_name, environment, **options)
        return self
    
    async def deploy_application(
        self,
        client_name: str,
        environment: str = "dev",
        chart_name: str = "generic",
        **options
    ) -> 'ForgeERPTestBase':
        """
        Execute complete deployment workflow.
        
        Args:
            client_name: Client name
            environment: Environment
            chart_name: Helm chart name
            **options: Additional deployment options
            
        Returns:
            Self for method chaining
        """
        await self.workflows.deploy_application(client_name, environment, chart_name, **options)
        return self
    
    async def check_status(
        self,
        client_name: str,
        environment: str = "dev"
    ) -> 'ForgeERPTestBase':
        """
        Check status of a provisioned client.
        
        Args:
            client_name: Client name
            environment: Environment
            
        Returns:
            Self for method chaining
        """
        await self.workflows.check_status(client_name, environment)
        return self
    
    async def run_diagnostics(
        self,
        client_name: Optional[str] = None,
        environment: Optional[str] = None
    ) -> 'ForgeERPTestBase':
        """
        Run diagnostics.
        
        Args:
            client_name: Optional client name (for client-specific diagnostics)
            environment: Optional environment (requires client_name)
            
        Returns:
            Self for method chaining
        """
        await self.workflows.run_diagnostics(client_name, environment)
        return self

