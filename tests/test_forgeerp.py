#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for ForgeERP extension.
"""

import pytest
from playwright.async_api import async_playwright
from playwright_simple.forgeerp import ForgeERPTestBase, ForgeERPYAMLParser
from playwright_simple import TestConfig
from playwright_simple.forgeerp.selectors import ForgeERPSelectors
from playwright_simple.forgeerp.components import ForgeERPComponents
from playwright_simple.forgeerp.workflows import ForgeERPWorkflows
from playwright_simple.core.htmx import HTMXHelper


@pytest.mark.asyncio
async def test_forgeerp_base_initialization():
    """Test ForgeERPTestBase initialization."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir="videos/test_forgeerp_base_initialization",
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        config = TestConfig(
            base_url="http://localhost:8000",
            video_enabled=True,
            browser_headless=False,
            browser_slow_mo=500
        )
        test = ForgeERPTestBase(page, config, "test_name")
        
        assert test.page == page
        assert test.config == config
        assert test.test_name == "test_name"
        assert test.htmx is not None
        assert test.components is not None
        assert test.workflows is not None
        
        # Check cursor color adaptation to ForgeERP indigo theme
        assert test.config.cursor.color == "#6366f1"
        
        # Navigate to a page to show cursor in action
        await page.goto("data:text/html,<html><body><h1>ForgeERP Test</h1><button>Test Button</button></body></html>")
        await test.wait(1)
        await test.click_button("Test Button")
        await test.wait(1)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_forgeerp_base_cursor_adaptation():
    """Test cursor color adaptation to ForgeERP theme."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir="videos/test_forgeerp_cursor_adaptation",
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Test with default blue color (should be adapted)
        config = TestConfig(
            base_url="http://localhost:8000",
            cursor_color="#007bff",
            video_enabled=True,
            browser_headless=False,
            browser_slow_mo=500
        )
        test = ForgeERPTestBase(page, config)
        assert test.config.cursor.color == "#6366f1"
        assert test.config.cursor.click_effect_color == "#6366f1"
        assert test.config.cursor.hover_effect_color == "#4f46e5"
        
        # Show cursor in action
        await page.goto("data:text/html,<html><body><h1>Cursor Adaptation Test</h1><button id='btn1'>Button 1</button><button id='btn2'>Button 2</button></body></html>")
        await test.wait(0.5)
        await test.click_button("Button 1")
        await test.wait(0.5)
        await test.click_button("Button 2")
        await test.wait(1)
        
        # Test with custom color (should not be adapted)
        config2 = TestConfig(base_url="http://localhost:8000", cursor_color="#ff0000")
        test2 = ForgeERPTestBase(page, config2)
        assert test2.config.cursor.color == "#ff0000"
        
        await context.close()
        await browser.close()


def test_forgeerp_selectors():
    """Test ForgeERPSelectors constants and methods."""
    # Test navigation selectors
    assert ForgeERPSelectors.NAV_HOME == 'a[href="/"]'
    assert ForgeERPSelectors.NAV_SETUP == 'a[href="/setup"]'
    assert ForgeERPSelectors.NAV_PROVISION == 'a[href="/provision"]'
    assert ForgeERPSelectors.NAV_STATUS == 'a[href="/status"]'
    assert ForgeERPSelectors.NAV_DEPLOY == 'a[href="/deploy"]'
    assert ForgeERPSelectors.NAV_DIAGNOSTICS == 'a[href="/diagnostics"]'
    
    # Test form field selectors
    assert ForgeERPSelectors.FIELD_CLIENT_NAME == 'input[name="client_name"]'
    assert ForgeERPSelectors.FIELD_ENVIRONMENT == 'select[name="environment"], input[name="environment"]'
    assert ForgeERPSelectors.FIELD_DATABASE_TYPE == 'select[name="database_type"]'
    assert ForgeERPSelectors.FIELD_NAMESPACE == 'input[name="namespace"]'
    assert ForgeERPSelectors.FIELD_CHART_NAME == 'input[name="chart_name"]'
    assert ForgeERPSelectors.FIELD_CHART_VERSION == 'input[name="chart_version"]'
    
    # Test button selectors
    assert ForgeERPSelectors.BUTTON_SUBMIT == 'button[type="submit"]'
    assert 'Provision' in ForgeERPSelectors.BUTTON_PROVISION
    assert 'Deploy' in ForgeERPSelectors.BUTTON_DEPLOY
    
    # Test HTMX container selectors
    assert ForgeERPSelectors.HTMX_PROVISION_RESULT == '#provision-result'
    assert ForgeERPSelectors.HTMX_DEPLOY_RESULT == '#deploy-result'
    assert ForgeERPSelectors.HTMX_STATUS_RESULT == '#status-result'
    assert ForgeERPSelectors.HTMX_DIAGNOSTICS_SUMMARY == '#diagnostics-summary'
    assert ForgeERPSelectors.HTMX_CLIENT_DIAGNOSTICS == '#client-diagnostics'
    
    # Test modal selectors
    assert '.modal' in ForgeERPSelectors.MODAL
    assert '[role="dialog"]' in ForgeERPSelectors.MODAL
    assert 'Close' in ForgeERPSelectors.MODAL_CLOSE


def test_forgeerp_selectors_helper_methods():
    """Test ForgeERPSelectors helper methods."""
    # Test get_nav_link
    assert ForgeERPSelectors.get_nav_link("home") == ForgeERPSelectors.NAV_HOME
    assert ForgeERPSelectors.get_nav_link("provision") == ForgeERPSelectors.NAV_PROVISION
    assert ForgeERPSelectors.get_nav_link("deploy") == ForgeERPSelectors.NAV_DEPLOY
    assert ForgeERPSelectors.get_nav_link("unknown") == 'a[href="/unknown"]'
    
    # Test get_htmx_result_container
    assert ForgeERPSelectors.get_htmx_result_container("provision") == ForgeERPSelectors.HTMX_PROVISION_RESULT
    assert ForgeERPSelectors.get_htmx_result_container("deploy") == ForgeERPSelectors.HTMX_DEPLOY_RESULT
    assert ForgeERPSelectors.get_htmx_result_container("status") == ForgeERPSelectors.HTMX_STATUS_RESULT
    assert ForgeERPSelectors.get_htmx_result_container("unknown") == '#unknown-result'
    
    # Test get_loading_indicator
    assert ForgeERPSelectors.get_loading_indicator("provision") == ForgeERPSelectors.LOADING_PROVISION
    assert ForgeERPSelectors.get_loading_indicator("deploy") == ForgeERPSelectors.LOADING_DEPLOY
    assert ForgeERPSelectors.get_loading_indicator("unknown") == '#unknown-loading'
    
    # Test get_form_field_selector
    selectors = ForgeERPSelectors.get_form_field_selector("client_name")
    assert len(selectors) > 0
    assert 'input[name="client_name"]' in selectors
    assert 'select[name="client_name"]' in selectors
    assert 'textarea[name="client_name"]' in selectors
    assert '[name="client_name"]' in selectors
    assert '#client_name' in selectors


@pytest.mark.asyncio
async def test_forgeerp_components_initialization():
    """Test ForgeERPComponents initialization."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        htmx = HTMXHelper(page)
        components = ForgeERPComponents(page, htmx)
        
        assert components.page == page
        assert components.htmx == htmx
        
        # Test without providing HTMX (should create one)
        components2 = ForgeERPComponents(page)
        assert components2.htmx is not None
        assert isinstance(components2.htmx, HTMXHelper)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_forgeerp_workflows_initialization():
    """Test ForgeERPWorkflows initialization."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        htmx = HTMXHelper(page)
        components = ForgeERPComponents(page, htmx)
        config = TestConfig(base_url="http://localhost:8000")
        workflows = ForgeERPWorkflows(page, components, htmx, config)
        
        assert workflows.page == page
        assert workflows.components == components
        assert workflows.htmx == htmx
        assert workflows.config == config
        assert workflows.config.base_url == "http://localhost:8000"
        
        await context.close()
        await browser.close()


def test_forgeerp_yaml_parser_class():
    """Test ForgeERPYAMLParser class structure."""
    # Check that it inherits from YAMLParser
    from playwright_simple.core.yaml_parser import YAMLParser
    assert issubclass(ForgeERPYAMLParser, YAMLParser)
    
    # Check that inherited methods are available
    assert hasattr(ForgeERPYAMLParser, 'parse_file')
    assert hasattr(ForgeERPYAMLParser, 'to_python_function')
    assert hasattr(ForgeERPYAMLParser, 'load_test')
    assert hasattr(ForgeERPYAMLParser, 'load_tests')
    
    # Check ForgeERP-specific method
    assert hasattr(ForgeERPYAMLParser, 'parse_forgeerp_action')
    assert callable(ForgeERPYAMLParser.parse_forgeerp_action)


def test_forgeerp_yaml_parser_method_signature():
    """Test parse_forgeerp_action method signature."""
    import inspect
    sig = inspect.signature(ForgeERPYAMLParser.parse_forgeerp_action)
    params = list(sig.parameters.keys())
    
    assert 'action' in params
    assert 'test' in params
    assert len(params) == 2


@pytest.mark.asyncio
async def test_forgeerp_navigation_methods():
    """Test ForgeERP navigation methods."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir="videos/test_forgeerp_navigation",
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Mock page.goto to track calls and show navigation
        called_urls = []
        original_goto = page.goto
        
        async def mock_goto(url, **kwargs):
            called_urls.append(url)
            # Create a simple HTML page showing the current route
            route = url.split("/")[-1] if "/" in url else "home"
            html = f"""
            <html>
                <head><title>ForgeERP - {route}</title></head>
                <body style="font-family: Arial; padding: 50px;">
                    <h1>ForgeERP - {route.upper()}</h1>
                    <p>Current URL: {url}</p>
                    <nav>
                        <a href="/setup">Setup</a> | 
                        <a href="/provision">Provision</a> | 
                        <a href="/status">Status</a> | 
                        <a href="/deploy">Deploy</a> | 
                        <a href="/diagnostics">Diagnostics</a>
                    </nav>
                </body>
            </html>
            """
            return await original_goto(f"data:text/html,{html}")
        
        page.goto = mock_goto
        
        config = TestConfig(
            base_url="http://localhost:8000",
            video_enabled=True,
            browser_headless=False,
            browser_slow_mo=500
        )
        test = ForgeERPTestBase(page, config)
        
        # Test navigation methods with visual feedback
        await test.go_to_setup()
        assert "http://localhost:8000/setup" in called_urls[-1]
        await test.wait(1)
        
        await test.go_to_provision()
        assert "http://localhost:8000/provision" in called_urls[-1]
        await test.wait(1)
        
        await test.go_to_status()
        assert "http://localhost:8000/status" in called_urls[-1]
        await test.wait(1)
        
        await test.go_to_deploy()
        assert "http://localhost:8000/deploy" in called_urls[-1]
        await test.wait(1)
        
        await test.go_to_diagnostics()
        assert "http://localhost:8000/diagnostics" in called_urls[-1]
        await test.wait(1)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_forgeerp_htmx_helper_integration():
    """Test HTMX helper integration in ForgeERPTestBase."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:8000")
        test = ForgeERPTestBase(page, config)
        
        # Verify HTMX helper is properly initialized
        assert isinstance(test.htmx, HTMXHelper)
        assert test.htmx.page == page
        assert test.htmx.timeout == config.browser.timeout
        
        # Verify components use the same HTMX helper
        assert test.components.htmx == test.htmx
        
        # Verify workflows use the same HTMX helper
        assert test.workflows.htmx == test.htmx
        
        await context.close()
        await browser.close()


def test_forgeerp_imports():
    """Test that all ForgeERP modules can be imported."""
    from playwright_simple.forgeerp import ForgeERPTestBase, ForgeERPYAMLParser
    from playwright_simple.forgeerp.selectors import ForgeERPSelectors
    from playwright_simple.forgeerp.components import ForgeERPComponents
    from playwright_simple.forgeerp.workflows import ForgeERPWorkflows
    
    # Verify classes exist
    assert ForgeERPTestBase is not None
    assert ForgeERPYAMLParser is not None
    assert ForgeERPSelectors is not None
    assert ForgeERPComponents is not None
    assert ForgeERPWorkflows is not None


def test_forgeerp_extension_all_exports():
    """Test that __all__ exports are correct."""
    from playwright_simple.forgeerp import __all__
    
    assert "ForgeERPTestBase" in __all__
    assert "ForgeERPYAMLParser" in __all__
    assert len(__all__) == 2
