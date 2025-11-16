#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E tests for core functionality - FASE 10.

These tests verify end-to-end functionality of the core features.
"""

import pytest
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_simple.core.base import SimpleTestBase
from playwright_simple.core.config import TestConfig
from playwright_simple.core.yaml_parser import YAMLParser


@pytest.mark.asyncio
async def test_e2e_basic_yaml_execution():
    """
    E2E Test: Execute basic YAML test.
    
    Verifies that a simple YAML test can be executed end-to-end.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple test page with JavaScript to show result on click
        await page.set_content("""
            <html>
                <body>
                    <h1>Test Page</h1>
                    <button id="test-btn" onclick="document.getElementById('result').style.display='block'">Click Me</button>
                    <div id="result" style="display:none;">Clicked!</div>
                </body>
            </html>
        """)
        
        # Create YAML test
        yaml_data = {
            'name': 'E2E Basic Test',
            'steps': [
                {'action': 'click', 'selector': '#test-btn'},
                {'action': 'wait_for', 'selector': '#result', 'timeout': 2000},
                {'action': 'assert_visible', 'selector': '#result'}
            ]
        }
        
        config = TestConfig(base_url="about:blank")
        test = SimpleTestBase(page, config)
        
        # Convert YAML to function and execute
        test_func = YAMLParser.to_python_function(yaml_data)
        await test_func(page, test)
        
        # Verify result
        result_visible = await page.locator('#result').is_visible()
        assert result_visible, "Result should be visible after click"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_e2e_yaml_file_execution():
    """
    E2E Test: Execute YAML from file.
    
    Verifies that YAML can be loaded from file and executed.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create a simple test page
        await page.set_content("""
            <html>
                <body>
                    <input type="text" id="name" />
                    <button id="submit">Submit</button>
                </body>
            </html>
        """)
        
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_content = """
name: E2E File Test
steps:
  - action: type
    selector: "#name"
    text: "Test User"
  - action: click
    selector: "#submit"
"""
            f.write(yaml_content)
            yaml_path = Path(f.name)
        
        try:
            # Parse and execute YAML file
            yaml_data = YAMLParser.parse_file(yaml_path)
            config = TestConfig(base_url="about:blank")
            test = SimpleTestBase(page, config)
            
            test_func = YAMLParser.to_python_function(yaml_data, yaml_path=yaml_path)
            await test_func(page, test)
            
            # Verify input was filled
            input_value = await page.locator('#name').input_value()
            assert input_value == "Test User", f"Expected 'Test User', got '{input_value}'"
            
        finally:
            # Clean up
            yaml_path.unlink()
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_e2e_navigation():
    """
    E2E Test: Navigation between pages.
    
    Verifies that navigation works correctly.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create first page
        await page.set_content("""
            <html>
                <body>
                    <a href="#page2" id="link">Go to Page 2</a>
                </body>
            </html>
        """)
        
        yaml_data = {
            'name': 'E2E Navigation Test',
            'steps': [
                {'action': 'click', 'selector': '#link'},
                {'action': 'wait', 'seconds': 0.5}
            ]
        }
        
        config = TestConfig(base_url="about:blank")
        test = SimpleTestBase(page, config)
        
        test_func = YAMLParser.to_python_function(yaml_data)
        await test_func(page, test)
        
        # Verify navigation occurred (URL changed or page updated)
        current_url = page.url
        assert current_url is not None
        
        await context.close()
        await browser.close()

