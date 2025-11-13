#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow helpers for ForgeERP.

Provides complete workflows for common ForgeERP operations like provisioning,
deployment, diagnostics, and status checking.
"""

import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import Page

from ..core.config import TestConfig
from ..core.htmx import HTMXHelper
from .components import ForgeERPComponents
from .selectors import ForgeERPSelectors


class ForgeERPWorkflows:
    """Complete workflows for ForgeERP operations."""
    
    def __init__(
        self,
        page: Page,
        components: ForgeERPComponents,
        htmx: HTMXHelper,
        config: Optional[TestConfig] = None
    ):
        """
        Initialize workflow helper.
        
        Args:
            page: Playwright page instance
            components: Component helper instance
            htmx: HTMX helper instance
            config: Test configuration (for base_url)
        """
        self.page = page
        self.components = components
        self.htmx = htmx
        self.config = config or TestConfig()
    
    async def provision_client(
        self,
        client_name: str,
        environment: str = "dev",
        **options
    ) -> None:
        """
        Execute complete provisioning workflow.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
            **options: Additional options:
                - database_type: Database type (postgresql, mysql)
                - namespace: Kubernetes namespace
                - wait_for_result: Wait for HTMX response (default: True)
                - check_errors: Check for errors after provisioning (default: True)
        """
        # Navigate to provision page
        base_url = self.config.base_url.rstrip('/')
        await self.page.goto(f"{base_url}/provision")
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.5)
        
        # Fill form
        await self.components.fill_provision_form(
            client_name,
            environment,
            database_type=options.get("database_type"),
            namespace=options.get("namespace"),
            **{k: v for k, v in options.items() if k not in ["database_type", "namespace", "wait_for_result", "check_errors"]}
        )
        
        # Submit form
        wait_for_result = options.get("wait_for_result", True)
        check_errors = options.get("check_errors", True)
        
        await self.components.submit_form(
            wait_for_response=wait_for_result,
            container_selector=ForgeERPSelectors.HTMX_PROVISION_RESULT
        )
        
        # Check for errors if requested
        if check_errors and wait_for_result:
            error_msg = await self.htmx.detect_htmx_error(ForgeERPSelectors.HTMX_PROVISION_RESULT)
            if error_msg:
                raise AssertionError(f"Provisioning failed: {error_msg}")
    
    async def deploy_application(
        self,
        client_name: str,
        environment: str = "dev",
        chart_name: str = "generic",
        **options
    ) -> None:
        """
        Execute complete deployment workflow.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
            chart_name: Helm chart name (required)
            **options: Additional options:
                - chart_version: Chart version
                - wait_for_result: Wait for HTMX response (default: True)
                - check_errors: Check for errors after deployment (default: True)
        """
        # Navigate to deploy page
        base_url = self.config.base_url.rstrip('/')
        await self.page.goto(f"{base_url}/deploy")
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.5)
        
        # Fill form
        await self.components.fill_deploy_form(
            client_name,
            environment,
            chart_name,
            chart_version=options.get("chart_version"),
            **{k: v for k, v in options.items() if k not in ["chart_version", "wait_for_result", "check_errors"]}
        )
        
        # Submit form
        wait_for_result = options.get("wait_for_result", True)
        check_errors = options.get("check_errors", True)
        
        await self.components.submit_form(
            wait_for_response=wait_for_result,
            container_selector=ForgeERPSelectors.HTMX_DEPLOY_RESULT
        )
        
        # Check for errors if requested
        if check_errors and wait_for_result:
            error_msg = await self.htmx.detect_htmx_error(ForgeERPSelectors.HTMX_DEPLOY_RESULT)
            if error_msg:
                raise AssertionError(f"Deployment failed: {error_msg}")
    
    async def check_status(
        self,
        client_name: str,
        environment: str = "dev"
    ) -> str:
        """
        Check status of a provisioned client.
        
        Args:
            client_name: Client name (required)
            environment: Environment (dev, staging, prod) - default: dev
            
        Returns:
            Status result text
        """
        # Navigate to status page
        base_url = self.config.base_url.rstrip('/')
        await self.page.goto(f"{base_url}/status")
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.5)
        
        # Fill form
        await self.components.fill_diagnostics_form(client_name, environment)
        
        # Submit form
        await self.components.submit_form(
            button_selector=ForgeERPSelectors.BUTTON_CHECK_STATUS,
            wait_for_response=True,
            container_selector=ForgeERPSelectors.HTMX_STATUS_RESULT
        )
        
        # Get result
        result = await self.htmx.get_htmx_result(
            ForgeERPSelectors.HTMX_STATUS_RESULT,
            wait_for_swap=False
        )
        
        return result
    
    async def run_diagnostics(
        self,
        client_name: Optional[str] = None,
        environment: Optional[str] = None
    ) -> str:
        """
        Run diagnostics.
        
        Args:
            client_name: Optional client name (for client-specific diagnostics)
            environment: Optional environment (requires client_name)
            
        Returns:
            Diagnostics result text
        """
        # Navigate to diagnostics page
        base_url = self.config.base_url.rstrip('/')
        await self.page.goto(f"{base_url}/diagnostics")
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(0.5)
        
        if client_name and environment:
            # Client-specific diagnostics
            await self.components.fill_diagnostics_form(client_name, environment)
            
            # Submit form
            await self.components.submit_form(
                button_selector=ForgeERPSelectors.BUTTON_RUN_DIAGNOSTICS,
                wait_for_response=True,
                container_selector=ForgeERPSelectors.HTMX_CLIENT_DIAGNOSTICS
            )
            
            # Get result
            result = await self.htmx.get_htmx_result(
                ForgeERPSelectors.HTMX_CLIENT_DIAGNOSTICS,
                wait_for_swap=False
            )
        else:
            # Summary diagnostics
            summary_button = self.page.locator(ForgeERPSelectors.BUTTON_RUN_DIAGNOSTICS).first
            await summary_button.wait_for(state="visible", timeout=10000)
            await summary_button.click()
            await asyncio.sleep(0.2)
            
            # Wait for result
            await self.htmx.wait_for_htmx_response(ForgeERPSelectors.HTMX_DIAGNOSTICS_SUMMARY)
            
            # Get result
            result = await self.htmx.get_htmx_result(
                ForgeERPSelectors.HTMX_DIAGNOSTICS_SUMMARY,
                wait_for_swap=False
            )
        
        return result

