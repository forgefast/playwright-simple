#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo integration example for playwright-simple.

Demonstrates how to use the library with Odoo ERP system.
"""

import asyncio
from playwright_simple import TestRunner, TestConfig


async def test_odoo_sale_flow(page, test):
    """Test Odoo sales flow."""
    # Login to Odoo
    await test.login("admin", "admin", login_url="/web/login")
    
    # Navigate to Sales menu
    await test.navigate(["Vendas", "Pedidos"])
    
    # Create new sale order
    await test.click('button:has-text("Criar")', "Create button")
    await test.wait(1)
    
    # Fill customer
    await test.click('.o_field_char[name="partner_id"]', "Customer field")
    await test.type('.o_field_char[name="partner_id"] input', "Customer Test")
    await test.wait(0.5)
    await test.click('.ui-menu-item:first-child', "First customer option")
    
    # Add product line
    await test.click('.o_field_x2many_list_row_add a', "Add line")
    await test.wait(0.5)
    await test.click('.o_field_many2one[name="product_id"]', "Product field")
    await test.type('.o_field_many2one[name="product_id"] input', "Product Test")
    await test.wait(0.5)
    await test.click('.ui-menu-item:first-child', "First product option")
    
    # Confirm order
    await test.click('button:has-text("Confirmar")', "Confirm button")
    await test.wait(2)
    
    # Assert order created
    await test.assert_text('.o_notification', "Pedido confirmado", "Confirmation message")


async def test_odoo_inventory(page, test):
    """Test Odoo inventory management."""
    await test.login("admin", "admin")
    
    # Navigate to Inventory
    await test.navigate(["Inventário", "Produtos"])
    
    # Search for product
    await test.type('.o_searchview_input', "Test Product", "Search field")
    await test.wait(1)
    
    # Open product
    await test.click('.o_kanban_record:first-child', "First product")
    await test.wait(1)
    
    # Check product details
    await test.assert_visible('.o_form_view', "Product form")


if __name__ == "__main__":
    config = TestConfig(
        base_url="http://localhost:8069",
        cursor_style="arrow",
        cursor_color="#007bff",
        video_enabled=True,
        screenshots_auto=True,
        browser_headless=False,  # Show browser for Odoo tests
        browser_slow_mo=50,  # Slow down for visibility
    )
    
    runner = TestRunner(config=config)
    
    asyncio.run(runner.run_all([
        ("01_sale_flow", test_odoo_sale_flow),
        ("02_inventory", test_odoo_inventory),
    ]))


