#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E tests for Odoo extension - FASE 10.

These tests verify end-to-end functionality of the Odoo extension.
Note: These tests require a running Odoo instance or mock.
"""

import pytest
from playwright.async_api import async_playwright
from playwright_simple.odoo import OdooTestBase
from playwright_simple.core.config import TestConfig


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires running Odoo instance")
async def test_e2e_odoo_login():
    """
    E2E Test: Odoo login.
    
    Verifies that Odoo login works end-to-end.
    Requires running Odoo instance.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:8069")
        test = OdooTestBase(page, config)
        
        # Login
        await test.login("admin", "admin", database="devel")
        
        # Verify login (check for dashboard or user menu)
        # This would require actual Odoo instance
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_e2e_odoo_base_initialization():
    """
    E2E Test: Odoo base initialization.
    
    Verifies that OdooTestBase can be initialized correctly.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:8069")
        test = OdooTestBase(page, config)
        
        # Verify test base has required attributes
        assert hasattr(test, 'page')
        assert hasattr(test, 'config')
        assert hasattr(test, 'login')
        assert hasattr(test, 'go_to')
        assert hasattr(test, 'fill')
        assert hasattr(test, 'click')
        
        await context.close()
        await browser.close()

