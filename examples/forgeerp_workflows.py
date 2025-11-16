#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example of using ForgeERP workflows.

This example demonstrates using high-level workflow methods
for complete operations.
"""

import asyncio
from playwright.async_api import async_playwright
from playwright_simple.forgeerp import ForgeERPTestBase
from playwright_simple import TestConfig


async def test_provision_workflow(page, test: ForgeERPTestBase):
    """Test provisioning using workflow method."""
    # Complete provisioning workflow in one call
    await test.provision_client(
        client_name="test-client",
        environment="dev",
        database_type="postgresql"
    )
    
    # Assert provisioning was successful
    await test.assert_provision_success("test-client")


async def test_deploy_workflow(page, test: ForgeERPTestBase):
    """Test deployment using workflow method."""
    # Complete deployment workflow in one call
    await test.deploy_application(
        client_name="test-client",
        environment="dev",
        chart_name="generic",
        chart_version="1.0.0"
    )
    
    # Check for errors
    await test.assert_no_errors()


async def test_status_workflow(page, test: ForgeERPTestBase):
    """Test status checking using workflow method."""
    # Check status
    status = await test.check_status("test-client", "dev")
    print(f"Status result: {status[:200]}...")
    
    # Assert status is displayed
    await test.assert_status_display("test-client", "dev")


async def test_diagnostics_workflow(page, test: ForgeERPTestBase):
    """Test diagnostics using workflow method."""
    # Run summary diagnostics
    summary = await test.run_diagnostics()
    print(f"Summary diagnostics: {summary[:200]}...")
    
    # Run client-specific diagnostics
    client_diag = await test.run_diagnostics("test-client", "dev")
    print(f"Client diagnostics: {client_diag[:200]}...")


async def test_complete_workflow(page, test: ForgeERPTestBase):
    """Test complete workflow: provision -> deploy -> check status."""
    # Step 1: Provision client
    await test.provision_client("test-client", "dev")
    await test.assert_provision_success("test-client")
    
    # Step 2: Deploy application
    await test.deploy_application("test-client", "dev", "generic")
    await test.assert_no_errors()
    
    # Step 3: Check status
    await test.check_status("test-client", "dev")
    await test.assert_status_display("test-client", "dev")
    
    # Step 4: Run diagnostics
    await test.run_diagnostics("test-client", "dev")


async def main():
    """Run workflow examples."""
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
        test = ForgeERPTestBase(page, config, "workflow_test")
        
        try:
            # Run workflow tests
            # await test_provision_workflow(page, test)
            # await test_deploy_workflow(page, test)
            # await test_status_workflow(page, test)
            # await test_diagnostics_workflow(page, test)
            await test_complete_workflow(page, test)
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

