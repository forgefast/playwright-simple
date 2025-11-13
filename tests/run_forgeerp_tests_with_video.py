#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run ForgeERP tests with video recording.

This script runs ForgeERP tests directly using TestRunner to generate videos.
"""

import asyncio
from pathlib import Path
from playwright_simple import TestRunner, TestConfig
from playwright_simple.forgeerp import ForgeERPTestBase


async def test_forgeerp_initialization(page, test: ForgeERPTestBase):
    """Test ForgeERPTestBase initialization with visual demonstration."""
    # Navigate to a demo page
    await page.goto("data:text/html,<html><head><title>ForgeERP Test - Initialization</title></head><body style='font-family: Arial; padding: 50px;'><h1>ForgeERP Test Base</h1><p>Testing initialization and cursor</p><button id='test-btn'>Test Button</button></body></html>")
    await test.wait(1)
    
    # Show cursor in action
    await test.click_button("Test Button")
    await test.wait(1)
    
    # Verify initialization
    assert test.htmx is not None
    assert test.components is not None
    assert test.workflows is not None
    assert test.config.cursor.color == "#6366f1"


async def test_forgeerp_cursor_adaptation(page, test: ForgeERPTestBase):
    """Test cursor color adaptation to ForgeERP theme."""
    await page.goto("data:text/html,<html><head><title>ForgeERP - Cursor Adaptation</title></head><body style='font-family: Arial; padding: 50px; background: #f0f0f0;'><h1>Cursor Adaptation Test</h1><p>Cursor color: Indigo (#6366f1)</p><button id='btn1' style='margin: 10px; padding: 10px 20px;'>Button 1</button><button id='btn2' style='margin: 10px; padding: 10px 20px;'>Button 2</button><button id='btn3' style='margin: 10px; padding: 10px 20px;'>Button 3</button></body></html>")
    await test.wait(1)
    
    # Show cursor clicking multiple buttons (using selectors since buttons might not be found by text)
    await test.click("#btn1", "Button 1")
    await test.wait(0.5)
    await test.click("#btn2", "Button 2")
    await test.wait(0.5)
    await test.click("#btn3", "Button 3")
    await test.wait(1)
    
    # Verify cursor color
    assert test.config.cursor.color == "#6366f1"


async def test_forgeerp_navigation(page, test: ForgeERPTestBase):
    """Test ForgeERP navigation methods."""
    # Create a mock ForgeERP-like interface
    html = """
    <html>
        <head><title>ForgeERP Navigation</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <nav style="background: #6366f1; color: white; padding: 15px; margin-bottom: 20px;">
                <a href="/setup" style="color: white; margin: 0 15px; text-decoration: none;">Setup</a>
                <a href="/provision" style="color: white; margin: 0 15px; text-decoration: none;">Provision</a>
                <a href="/status" style="color: white; margin: 0 15px; text-decoration: none;">Status</a>
                <a href="/deploy" style="color: white; margin: 0 15px; text-decoration: none;">Deploy</a>
                <a href="/diagnostics" style="color: white; margin: 0 15px; text-decoration: none;">Diagnostics</a>
            </nav>
            <div id="content">
                <h1>ForgeERP Navigation Test</h1>
                <p>Click navigation links to test</p>
            </div>
        </body>
    </html>
    """
    
    # Mock page.goto to show different pages
    original_goto = page.goto
    current_route = "home"
    
    async def mock_goto(url, **kwargs):
        nonlocal current_route
        if "/setup" in url:
            current_route = "setup"
        elif "/provision" in url:
            current_route = "provision"
        elif "/status" in url:
            current_route = "status"
        elif "/deploy" in url:
            current_route = "deploy"
        elif "/diagnostics" in url:
            current_route = "diagnostics"
        
        route_html = f"""
        <html>
            <head><title>ForgeERP - {current_route.upper()}</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <nav style="background: #6366f1; color: white; padding: 15px; margin-bottom: 20px;">
                    <a href="/setup" style="color: white; margin: 0 15px; text-decoration: none;">Setup</a>
                    <a href="/provision" style="color: white; margin: 0 15px; text-decoration: none;">Provision</a>
                    <a href="/status" style="color: white; margin: 0 15px; text-decoration: none;">Status</a>
                    <a href="/deploy" style="color: white; margin: 0 15px; text-decoration: none;">Deploy</a>
                    <a href="/diagnostics" style="color: white; margin: 0 15px; text-decoration: none;">Diagnostics</a>
                </nav>
                <div style="padding: 30px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h1 style="color: #6366f1;">ForgeERP - {current_route.upper()}</h1>
                    <p>Current URL: {url}</p>
                    <p>This is the {current_route} page</p>
                </div>
            </body>
        </html>
        """
        return await original_goto(f"data:text/html,{route_html}")
    
    page.goto = mock_goto
    
    # Start at home
    await page.goto("data:text/html," + html)
    await test.wait(1)
    
    # Navigate through pages
    await test.go_to_setup()
    await test.wait(1.5)
    
    await test.go_to_provision()
    await test.wait(1.5)
    
    await test.go_to_status()
    await test.wait(1.5)
    
    await test.go_to_deploy()
    await test.wait(1.5)
    
    await test.go_to_diagnostics()
    await test.wait(1.5)


async def test_forgeerp_form_interaction(page, test: ForgeERPTestBase):
    """Test ForgeERP form interactions."""
    html = """
    <html>
        <head><title>ForgeERP - Form Interaction</title></head>
        <body style="font-family: Arial; padding: 30px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h1 style="color: #6366f1; margin-bottom: 30px;">Provision Client Form</h1>
                <form>
                    <div style="margin-bottom: 20px;">
                        <label for="client_name" style="display: block; margin-bottom: 5px; font-weight: bold;">Client Name</label>
                        <input type="text" id="client_name" name="client_name" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;" />
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label for="environment" style="display: block; margin-bottom: 5px; font-weight: bold;">Environment</label>
                        <select id="environment" name="environment" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="dev">Development</option>
                            <option value="staging">Staging</option>
                            <option value="prod">Production</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 20px;">
                        <label for="database_type" style="display: block; margin-bottom: 5px; font-weight: bold;">Database Type</label>
                        <select id="database_type" name="database_type" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="postgresql">PostgreSQL</option>
                            <option value="mysql">MySQL</option>
                        </select>
                    </div>
                    <button type="submit" style="background: #6366f1; color: white; padding: 12px 30px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px;">Provision Client</button>
                </form>
            </div>
        </body>
    </html>
    """
    
    await page.goto(f"data:text/html,{html}")
    await test.wait(1)
    
    # Fill form using generic methods from core (labels without colon)
    await test.fill_by_label("Client Name", "test-client-video")
    await test.wait(0.5)
    
    await test.select_by_label("Environment", "dev")
    await test.wait(0.5)
    
    await test.select_by_label("Database Type", "postgresql")
    await test.wait(1)
    
    # Click submit button
    await test.click_button("Provision Client")
    await test.wait(1)


async def main():
    """Run all ForgeERP tests with video recording."""
    config = TestConfig.load(
        base_url="http://localhost:8000",
        cursor_style="arrow",
        cursor_color="#6366f1",  # ForgeERP indigo
        video_enabled=True,
        video_quality="high",
        video_dir="videos",
        browser_headless=True,
        browser_slow_mo=500,
        screenshots_auto=True,
    )
    
    from playwright.async_api import async_playwright
    
    print("=" * 60)
    print("Running ForgeERP Tests with Video Recording")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=500)
        
        # Run each test with its own context for video recording
        tests = [
            ("forgeerp_initialization", test_forgeerp_initialization),
            ("forgeerp_cursor_adaptation", test_forgeerp_cursor_adaptation),
            ("forgeerp_navigation", test_forgeerp_navigation),
            ("forgeerp_form_interaction", test_forgeerp_form_interaction),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🎬 Running test: {test_name}")
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=f"videos/{test_name}",
                record_video_size={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            
            try:
                test = ForgeERPTestBase(page, config, test_name)
                await test_func(page, test)
                print(f"  ✅ {test_name} passed")
            except Exception as e:
                print(f"  ❌ {test_name} failed: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await context.close()
        
        await browser.close()
    
    # List generated videos
    videos_dir = Path("videos")
    if videos_dir.exists():
        print("\n" + "=" * 60)
        print("Generated Videos")
        print("=" * 60)
        for video_file in sorted(videos_dir.rglob("*.webm")):
            if video_file.is_file():
                size = video_file.stat().st_size / 1024 / 1024  # MB
                print(f"  📹 {video_file.relative_to(videos_dir)} ({size:.2f} MB)")


if __name__ == "__main__":
    asyncio.run(main())

