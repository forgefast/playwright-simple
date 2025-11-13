#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E-commerce example for playwright-simple.

Demonstrates a complete e-commerce checkout flow.
"""

import asyncio
from playwright_simple import TestRunner, TestConfig


async def test_ecommerce_checkout(page, test):
    """Complete e-commerce checkout flow."""
    # Navigate to homepage
    await test.go_to("/")
    
    # Search for product
    await test.type('.search-input', "laptop", "Search input")
    await test.click('.search-button', "Search button")
    await test.wait(2)
    
    # Select product
    await test.click('.product-card:first-child', "First product")
    await test.wait(1)
    
    # Add to cart
    await test.click('button:has-text("Add to Cart")', "Add to cart button")
    await test.wait(1)
    
    # Go to cart
    await test.click('.cart-icon', "Cart icon")
    await test.wait(1)
    
    # Proceed to checkout
    await test.click('button:has-text("Checkout")', "Checkout button")
    await test.wait(1)
    
    # Fill shipping information
    await test.fill_form({
        'input[name="firstName"]': "John",
        'input[name="lastName"]': "Doe",
        'input[name="email"]': "john@example.com",
        'input[name="address"]': "123 Main St",
        'input[name="city"]': "New York",
        'input[name="zipCode"]': "10001",
    })
    
    # Select shipping method
    await test.click('input[value="standard"]', "Standard shipping")
    
    # Continue to payment
    await test.click('button:has-text("Continue to Payment")', "Continue button")
    await test.wait(1)
    
    # Fill payment information
    await test.fill_form({
        'input[name="cardNumber"]': "4111111111111111",
        'input[name="cardName"]': "John Doe",
        'input[name="expiryDate"]': "12/25",
        'input[name="cvv"]': "123",
    })
    
    # Place order
    await test.click('button:has-text("Place Order")', "Place order button")
    await test.wait(2)
    
    # Assert order confirmation
    await test.assert_text('.order-confirmation', "Thank you for your order!")
    await test.assert_visible('.order-number', "Order number")


async def test_product_filtering(page, test):
    """Test product filtering and sorting."""
    await test.go_to("/products")
    
    # Filter by category
    await test.click('.filter-category[data-category="electronics"]', "Electronics filter")
    await test.wait(1)
    
    # Assert filtered results
    await test.assert_count('.product-item', 5, "Filtered products")
    
    # Sort by price
    await test.select('.sort-select', "price-low-to-high", "Sort dropdown")
    await test.wait(1)
    
    # Assert sorted (check first product price is lower than second)
    first_price = await test.get_text('.product-item:first-child .price')
    second_price = await test.get_text('.product-item:nth-child(2) .price')
    # Note: In real test, you'd parse and compare prices


if __name__ == "__main__":
    config = TestConfig(
        base_url="https://example-store.com",
        cursor_style="circle",
        cursor_color="#28a745",
        video_enabled=True,
        video_quality="high",
        screenshots_auto=True,
        screenshots_on_failure=True,
    )
    
    runner = TestRunner(config=config)
    
    asyncio.run(runner.run_all([
        ("01_checkout_flow", test_ecommerce_checkout),
        ("02_product_filtering", test_product_filtering),
    ]))


