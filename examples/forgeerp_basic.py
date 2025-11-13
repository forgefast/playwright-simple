#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic example of using playwright-simple with ForgeERP extension.

This example demonstrates basic navigation and form interactions.
"""

import asyncio
from playwright.async_api import async_playwright
from playwright_simple.forgeerp import ForgeERPTestBase
from playwright_simple import TestConfig


async def test_basic_navigation(page, test: ForgeERPTestBase):
    """Test basic navigation in ForgeERP."""
    # Navigate to different pages
    await test.go_to("/")  # Home
    await test.go_to_setup()
    await test.go_to_provision()
    await test.go_to_status()
    await test.go_to_deploy()
    await test.go_to_diagnostics()


async def test_provision_workflow(page, test: ForgeERPTestBase):
    """Test complete provisioning workflow."""
    # Navigate to provision page
    await test.go_to_provision()
    
    # Fill provisioning form
    await test.fill_provision_form(
        client_name="test-client",
        environment="dev",
        database_type="postgresql"
    )
    
    # Submit form
    await test.submit_form()
    
    # Check for errors
    await test.assert_no_errors()
    
    # Optionally check for success message
    # await test.assert_success_message("provisioned")


async def test_deploy_workflow(page, test: ForgeERPTestBase):
    """Test complete deployment workflow."""
    # Navigate to deploy page
    await test.go_to_deploy()
    
    # Fill deployment form
    await test.fill_deploy_form(
        client_name="test-client",
        environment="dev",
        chart_name="generic"
    )
    
    # Submit form
    await test.submit_form()
    
    # Check for errors
    await test.assert_no_errors()


async def test_status_check(page, test: ForgeERPTestBase):
    """Test status checking."""
    # Navigate to status page
    await test.go_to_status()
    
    # Fill status form
    await test.fill_diagnostics_form("test-client", "dev")
    
    # Submit and check status
    await test.submit_form()
    await test.assert_no_errors()


async def test_diagnostics(page, test: ForgeERPTestBase):
    """Test diagnostics."""
    # Navigate to diagnostics page
    await test.go_to_diagnostics()
    
    # Run summary diagnostics
    await test.run_diagnostics()
    
    # Or run client-specific diagnostics
    # await test.run_diagnostics("test-client", "dev")


async def main():
    """Run examples."""
    config = TestConfig(
        base_url="http://localhost:8000",
        cursor_style="arrow",
        cursor_color="#6366f1",  # ForgeERP indigo
    )
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Create test instance
        test = ForgeERPTestBase(page, config, "basic_test")
        
        try:
            # Run tests
            await test_basic_navigation(page, test)
            # await test_provision_workflow(page, test)
            # await test_deploy_workflow(page, test)
            # await test_status_check(page, test)
            # await test_diagnostics(page, test)
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

