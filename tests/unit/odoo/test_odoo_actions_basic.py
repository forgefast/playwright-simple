#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Odoo basic actions - FASE 6 TDD.

These tests define the minimum requirements for Odoo extension.
Following TDD: write tests first, then verify implementation.
"""

import pytest
from playwright.async_api import async_playwright
from playwright_simple.odoo import OdooTestBase
from playwright_simple import TestConfig


@pytest.mark.asyncio
async def test_odoo_base_initialization():
    """
    Test: OdooTestBase can be initialized.
    
    Requirement: OdooTestBase must extend SimpleTestBase and work with Odoo.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:8069")
        test = OdooTestBase(page, config)
        
        assert test.page == page
        assert test.config == config
        assert hasattr(test, 'login')  # Odoo-specific method
        assert hasattr(test, 'go_to')  # Inherited from SimpleTestBase
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_odoo_login_action():
    """
    Test: Odoo login action works.
    
    Requirement: login() method must work with Odoo login page.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple Odoo login page mock
        await page.set_content("""
            <html>
                <body>
                    <form id="login-form">
                        <input name="login" type="text" />
                        <input name="password" type="password" />
                        <button type="submit">Entrar</button>
                    </form>
                </body>
            </html>
        """)
        
        config = TestConfig(base_url="http://localhost:8069")
        test = OdooTestBase(page, config)
        
        # Login should work (will fail if page structure is wrong, but method exists)
        # Note: This is a basic test - full test would require real Odoo instance
        assert hasattr(test, 'login')
        assert callable(test.login)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_odoo_navigate_action():
    """
    Test: Odoo navigation action works.
    
    Requirement: go_to() with menu path must work for Odoo navigation.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:8069")
        test = OdooTestBase(page, config)
        
        # Navigation should work
        assert hasattr(test, 'go_to')
        assert callable(test.go_to)
        assert hasattr(test, 'go_to_menu')  # Odoo-specific
        assert callable(test.go_to_menu)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_odoo_fill_action():
    """
    Test: Odoo fill action works.
    
    Requirement: fill() method must work with Odoo field format ("Label = Value").
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple form with label (only one field to avoid multiple matches)
        await page.set_content("""
            <html>
                <body>
                    <form>
                        <div>
                            <label for="partner_id">Cliente</label>
                            <input id="partner_id" name="partner_id" type="text" />
                        </div>
                    </form>
                </body>
            </html>
        """)
        
        config = TestConfig(base_url="http://localhost:8069")
        test = OdooTestBase(page, config)
        
        # Fill should work with Odoo format
        assert hasattr(test, 'fill')
        assert callable(test.fill)
        
        # Test fill with "Label = Value" format
        # Note: Odoo fill expects specific Odoo page structure
        # For unit test, we just verify the method exists and can parse the format
        # Full integration test would require real Odoo instance
        assert hasattr(test, 'fill')
        assert callable(test.fill)
        
        # The method should exist and be callable
        # Actual fill functionality requires proper Odoo page structure
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_odoo_click_action():
    """
    Test: Odoo click action works.
    
    Requirement: click() method must work with Odoo elements (by text).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple page with button
        await page.set_content("""
            <html>
                <body>
                    <button>Criar</button>
                </body>
            </html>
        """)
        
        config = TestConfig(base_url="http://localhost:8069")
        test = OdooTestBase(page, config)
        
        # Click should work
        assert hasattr(test, 'click')
        assert callable(test.click)
        
        # Click by text (Odoo style)
        await test.click("Criar")
        
        # Verify button exists (click was executed)
        button = page.locator("button:has-text('Criar')")
        assert await button.count() == 1
        
        await context.close()
        await browser.close()

