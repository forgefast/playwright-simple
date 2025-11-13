#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Component helpers for ForgeERP.

Provides helpers for interacting with ForgeERP UI components like forms,
modals, cards, and status displays.
"""

import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import Page, Locator

from ..core.htmx import HTMXHelper
from .selectors import ForgeERPSelectors


class ForgeERPComponents:
    """Helpers for ForgeERP UI components."""
    
    def __init__(self, page: Page, htmx: Optional[HTMXHelper] = None):
        """
        Initialize component helper.
        
        Args:
            page: Playwright page instance
            htmx: Optional HTMX helper instance (creates one if not provided)
        """
        self.page = page
        self.htmx = htmx or HTMXHelper(page)
    
    async def fill_provision_form(
        self,
        client_name: str,
        environment: str = "dev",
        database_type: Optional[str] = None,
        namespace: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Fill the provisioning form.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
            database_type: Database type (postgresql, mysql) - optional
            namespace: Kubernetes namespace - optional (auto-generated if empty)
            **kwargs: Additional field values
        """
        # Fill client name
        client_input = self.page.locator(ForgeERPSelectors.FIELD_CLIENT_NAME).first
        await client_input.wait_for(state="visible", timeout=10000)
        await client_input.fill(client_name)
        await asyncio.sleep(0.2)
        
        # Fill environment
        env_input = self.page.locator(ForgeERPSelectors.FIELD_ENVIRONMENT).first
        await env_input.wait_for(state="visible", timeout=10000)
        tag_name = await env_input.evaluate("el => el.tagName.toLowerCase()")
        if tag_name == "select":
            await env_input.select_option(environment)
        else:
            await env_input.fill(environment)
        await asyncio.sleep(0.2)
        
        # Fill database type if provided
        if database_type:
            db_input = self.page.locator(ForgeERPSelectors.FIELD_DATABASE_TYPE).first
            if await db_input.count() > 0:
                await db_input.wait_for(state="visible", timeout=10000)
                await db_input.select_option(database_type)
                await asyncio.sleep(0.2)
        
        # Fill namespace if provided
        if namespace:
            ns_input = self.page.locator(ForgeERPSelectors.FIELD_NAMESPACE).first
            if await ns_input.count() > 0:
                await ns_input.wait_for(state="visible", timeout=10000)
                await ns_input.fill(namespace)
                await asyncio.sleep(0.2)
        
        # Fill any additional fields
        for field_name, value in kwargs.items():
            selectors = ForgeERPSelectors.get_form_field_selector(field_name)
            for selector in selectors:
                field = self.page.locator(selector).first
                if await field.count() > 0:
                    await field.wait_for(state="visible", timeout=5000)
                    tag_name = await field.evaluate("el => el.tagName.toLowerCase()")
                    if tag_name == "select":
                        await field.select_option(str(value))
                    else:
                        await field.fill(str(value))
                    await asyncio.sleep(0.1)
                    break
    
    async def fill_deploy_form(
        self,
        client_name: str,
        environment: str = "dev",
        chart_name: str = "generic",
        chart_version: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Fill the deployment form.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
            chart_name: Helm chart name (required)
            chart_version: Chart version (optional)
            **kwargs: Additional field values
        """
        # Fill client name
        client_input = self.page.locator(ForgeERPSelectors.FIELD_CLIENT_NAME).first
        await client_input.wait_for(state="visible", timeout=10000)
        await client_input.fill(client_name)
        await asyncio.sleep(0.2)
        
        # Fill environment
        env_input = self.page.locator(ForgeERPSelectors.FIELD_ENVIRONMENT).first
        await env_input.wait_for(state="visible", timeout=10000)
        tag_name = await env_input.evaluate("el => el.tagName.toLowerCase()")
        if tag_name == "select":
            await env_input.select_option(environment)
        else:
            await env_input.fill(environment)
        await asyncio.sleep(0.2)
        
        # Fill chart name
        chart_input = self.page.locator(ForgeERPSelectors.FIELD_CHART_NAME).first
        await chart_input.wait_for(state="visible", timeout=10000)
        await chart_input.fill(chart_name)
        await asyncio.sleep(0.2)
        
        # Fill chart version if provided
        if chart_version:
            version_input = self.page.locator(ForgeERPSelectors.FIELD_CHART_VERSION).first
            if await version_input.count() > 0:
                await version_input.wait_for(state="visible", timeout=10000)
                await version_input.fill(chart_version)
                await asyncio.sleep(0.2)
        
        # Fill any additional fields
        for field_name, value in kwargs.items():
            selectors = ForgeERPSelectors.get_form_field_selector(field_name)
            for selector in selectors:
                field = self.page.locator(selector).first
                if await field.count() > 0:
                    await field.wait_for(state="visible", timeout=5000)
                    tag_name = await field.evaluate("el => el.tagName.toLowerCase()")
                    if tag_name == "select":
                        await field.select_option(str(value))
                    else:
                        await field.fill(str(value))
                    await asyncio.sleep(0.1)
                    break
    
    async def fill_diagnostics_form(
        self,
        client_name: str,
        environment: str = "dev"
    ) -> None:
        """
        Fill the diagnostics form.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
        """
        # Fill client name
        client_input = self.page.locator(ForgeERPSelectors.FIELD_CLIENT_NAME).first
        await client_input.wait_for(state="visible", timeout=10000)
        await client_input.fill(client_name)
        await asyncio.sleep(0.2)
        
        # Fill environment
        env_input = self.page.locator(ForgeERPSelectors.FIELD_ENVIRONMENT).first
        await env_input.wait_for(state="visible", timeout=10000)
        tag_name = await env_input.evaluate("el => el.tagName.toLowerCase()")
        if tag_name == "select":
            await env_input.select_option(environment)
        else:
            await env_input.fill(environment)
        await asyncio.sleep(0.2)
    
    async def submit_form(
        self,
        button_selector: Optional[str] = None,
        wait_for_response: bool = True,
        container_selector: Optional[str] = None
    ) -> None:
        """
        Submit a form and wait for HTMX response.
        
        Args:
            button_selector: Selector for submit button (defaults to button[type="submit"])
            wait_for_response: Whether to wait for HTMX response
            container_selector: Selector for result container (auto-detected if None)
        """
        if button_selector is None:
            button_selector = ForgeERPSelectors.BUTTON_SUBMIT
        
        submit_button = self.page.locator(button_selector).first
        await submit_button.wait_for(state="visible", timeout=10000)
        # Use click method from SimpleTestBase to ensure cursor animation
        # We need to get the test instance to use its click method
        # For now, click directly but this should be refactored to use test.click()
        await submit_button.click()
        await asyncio.sleep(0.2)
        
        if wait_for_response:
            # Try to detect container from current page context
            if container_selector is None:
                # Check common result containers
                common_containers = [
                    ForgeERPSelectors.HTMX_PROVISION_RESULT,
                    ForgeERPSelectors.HTMX_DEPLOY_RESULT,
                    ForgeERPSelectors.HTMX_STATUS_RESULT,
                    ForgeERPSelectors.HTMX_DIAGNOSTICS_SUMMARY,
                    ForgeERPSelectors.HTMX_CLIENT_DIAGNOSTICS,
                    ForgeERPSelectors.HTMX_SETUP_RESULT,
                ]
                
                for container in common_containers:
                    if await self.page.locator(container).count() > 0:
                        container_selector = container
                        break
            
            if container_selector:
                await self.htmx.wait_for_htmx_response(container_selector)
            else:
                # Fallback: wait for network idle
                await self.page.wait_for_load_state("networkidle", timeout=30000)
                await asyncio.sleep(0.5)
    

