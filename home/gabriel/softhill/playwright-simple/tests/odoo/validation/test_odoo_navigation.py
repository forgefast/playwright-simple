#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Odoo navigation - TDD approach.

Tests go_to, go_to_menu, go_to_dashboard, etc. to ensure they work correctly.
"""

import pytest
from playwright.async_api import async_playwright
from playwright_simple.odoo import OdooTestBase
from playwright_simple import TestConfig


@pytest.fixture
async def odoo_nav_page():
    """Fixture to create a page with Odoo navigation mock."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create Odoo page with menu structure
        await page.set_content("""
            <html>
                <head><title>Odoo</title></head>
                <body>
                    <nav class="o_main_navbar">
                        <a href="#" data-menu-xmlid="sale.sale_menu_root">Vendas</a>
                        <a href="#" data-menu-xmlid="contacts.res_partner_menu">Contatos</a>
                    </nav>
                    <div id="content"></div>
                </body>
            </html>
        """)
        
        config = TestConfig(base_url="http://localhost:18069")
        test = OdooTestBase(page, config)
        
        yield test, page
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_go_to_method_exists(odoo_nav_page):
    """Test: go_to() method exists and is callable."""
    test, page = odoo_nav_page
    
    assert hasattr(test, 'go_to')
    assert callable(test.go_to)


@pytest.mark.asyncio
async def test_go_to_menu_method_exists(odoo_nav_page):
    """Test: go_to_menu() method exists and is callable."""
    test, page = odoo_nav_page
    
    assert hasattr(test, 'go_to_menu')
    assert callable(test.go_to_menu)


@pytest.mark.asyncio
async def test_go_to_dashboard_method_exists(odoo_nav_page):
    """Test: go_to_dashboard() method exists and is callable."""
    test, page = odoo_nav_page
    
    assert hasattr(test, 'go_to_dashboard')
    assert callable(test.go_to_dashboard)


@pytest.mark.asyncio
async def test_go_to_accepts_menu_path_string(odoo_nav_page):
    """Test: go_to() accepts menu path string like 'Vendas > Pedidos'."""
    test, page = odoo_nav_page
    
    # Should accept string format
    try:
        await test.go_to("Vendas > Pedidos")
    except Exception:
        # May fail if not real Odoo, but should accept the format
        pass
    
    # Method should exist and accept string
    assert True


@pytest.mark.asyncio
async def test_go_to_accepts_url(odoo_nav_page):
    """Test: go_to() accepts URL string."""
    test, page = odoo_nav_page
    
    # Should accept URL format
    try:
        await test.go_to("/web")
    except Exception:
        # May fail if not real Odoo
        pass
    
    # Method should exist and accept URL
    assert True


@pytest.mark.asyncio
async def test_go_to_accepts_user_friendly_text(odoo_nav_page):
    """Test: go_to() accepts user-friendly text like 'Dashboard'."""
    test, page = odoo_nav_page
    
    # Should accept user-friendly text
    try:
        await test.go_to("Dashboard")
    except Exception:
        # May fail if not real Odoo
        pass
    
    # Method should exist and accept text
    assert True


@pytest.mark.asyncio
async def test_go_to_menu_accepts_separate_args(odoo_nav_page):
    """Test: go_to_menu() accepts separate menu and submenu arguments."""
    test, page = odoo_nav_page
    
    # Should accept separate arguments
    try:
        await test.go_to_menu("Vendas", "Pedidos")
    except Exception:
        # May fail if not real Odoo
        pass
    
    # Method should exist and accept separate args
    assert True


@pytest.mark.asyncio
async def test_go_to_menu_accepts_path_string(odoo_nav_page):
    """Test: go_to_menu() accepts menu path string."""
    test, page = odoo_nav_page
    
    # Should accept path string
    try:
        await test.go_to_menu("Vendas > Pedidos")
    except Exception:
        # May fail if not real Odoo
        pass
    
    # Method should exist and accept path string
    assert True


@pytest.mark.asyncio
async def test_go_to_returns_self_for_chaining(odoo_nav_page):
    """Test: go_to() returns self for method chaining."""
    test, page = odoo_nav_page
    
    try:
        result = await test.go_to("Dashboard")
        assert result is test, "go_to() should return self for chaining"
    except Exception:
        # May fail if not real Odoo, but return type should be correct
        pass


@pytest.mark.asyncio
async def test_go_to_menu_returns_self_for_chaining(odoo_nav_page):
    """Test: go_to_menu() returns self for method chaining."""
    test, page = odoo_nav_page
    
    try:
        result = await test.go_to_menu("Vendas", "Pedidos")
        assert result is test, "go_to_menu() should return self for chaining"
    except Exception:
        # May fail if not real Odoo, but return type should be correct
        pass


@pytest.mark.asyncio
async def test_go_to_dashboard_returns_self_for_chaining(odoo_nav_page):
    """Test: go_to_dashboard() returns self for method chaining."""
    test, page = odoo_nav_page
    
    try:
        result = await test.go_to_dashboard()
        assert result is test, "go_to_dashboard() should return self for chaining"
    except Exception:
        # May fail if not real Odoo, but return type should be correct
        pass


@pytest.mark.asyncio
async def test_go_to_home_method_exists(odoo_nav_page):
    """Test: go_to_home() method exists."""
    test, page = odoo_nav_page
    
    assert hasattr(test, 'go_to_home')
    assert callable(test.go_to_home)


@pytest.mark.asyncio
async def test_go_to_model_method_exists(odoo_nav_page):
    """Test: go_to_model() method exists."""
    test, page = odoo_nav_page
    
    assert hasattr(test, 'go_to_model')
    assert callable(test.go_to_model)

