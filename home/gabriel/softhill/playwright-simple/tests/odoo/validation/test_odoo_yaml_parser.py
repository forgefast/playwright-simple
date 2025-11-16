#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Odoo YAML parser - TDD approach.

Tests ActionParser, ActionValidator, and StepExecutor.
"""

import pytest
from playwright.async_api import async_playwright
from playwright_simple.odoo import OdooTestBase
from playwright_simple.odoo.yaml_parser import OdooYAMLParser
from playwright_simple import TestConfig


@pytest.mark.asyncio
async def test_odoo_yaml_parser_exists():
    """Test: OdooYAMLParser class exists and can be instantiated."""
    parser = OdooYAMLParser()
    assert parser is not None
    assert hasattr(parser, 'action_parser')
    assert hasattr(parser, 'action_validator')


@pytest.mark.asyncio
async def test_action_parser_exists():
    """Test: ActionParser exists and can parse actions."""
    from playwright_simple.odoo.yaml_parser.action_parser import ActionParser
    
    parser = ActionParser()
    assert parser is not None
    assert hasattr(parser, 'parse_odoo_action')


@pytest.mark.asyncio
async def test_action_validator_exists():
    """Test: ActionValidator exists."""
    from playwright_simple.odoo.yaml_parser.action_validator import ActionValidator
    
    validator = ActionValidator()
    assert validator is not None
    assert hasattr(validator, 'validate')


@pytest.mark.asyncio
async def test_step_executor_exists():
    """Test: StepExecutor exists."""
    from playwright_simple.odoo.yaml_parser.step_executor import StepExecutor
    
    executor = StepExecutor()
    assert executor is not None


@pytest.mark.asyncio
async def test_parse_login_action():
    """Test: ActionParser can parse login action."""
    from playwright_simple.odoo.yaml_parser.action_parser import ActionParser
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:18069")
        test = OdooTestBase(page, config)
        
        parser = ActionParser()
        
        # Parse login action
        action = {"login": "admin", "password": "admin", "database": "devel"}
        action_func = parser.parse_odoo_action(action, test)
        
        assert callable(action_func), "parse_odoo_action() should return callable"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_parse_go_to_action():
    """Test: ActionParser can parse go_to action."""
    from playwright_simple.odoo.yaml_parser.action_parser import ActionParser
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:18069")
        test = OdooTestBase(page, config)
        
        parser = ActionParser()
        
        # Parse go_to action
        action = {"go_to": "Vendas > Pedidos"}
        action_func = parser.parse_odoo_action(action, test)
        
        assert callable(action_func), "parse_odoo_action() should return callable"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_parse_click_action():
    """Test: ActionParser can parse click action."""
    from playwright_simple.odoo.yaml_parser.action_parser import ActionParser
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:18069")
        test = OdooTestBase(page, config)
        
        parser = ActionParser()
        
        # Parse click action
        action = {"click": "Criar"}
        action_func = parser.parse_odoo_action(action, test)
        
        assert callable(action_func), "parse_odoo_action() should return callable"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_parse_fill_action():
    """Test: ActionParser can parse fill action."""
    from playwright_simple.odoo.yaml_parser.action_parser import ActionParser
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig(base_url="http://localhost:18069")
        test = OdooTestBase(page, config)
        
        parser = ActionParser()
        
        # Parse fill action
        action = {"fill": "Cliente = João Silva"}
        action_func = parser.parse_odoo_action(action, test)
        
        assert callable(action_func), "parse_odoo_action() should return callable"
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_to_python_function():
    """Test: OdooYAMLParser.to_python_function() converts YAML to Python function."""
    yaml_data = {
        'name': 'Test YAML',
        'steps': [
            {'login': 'admin', 'password': 'admin'},
            {'go_to': 'Vendas > Pedidos'},
            {'click': 'Criar'},
        ]
    }
    
    test_function = OdooYAMLParser.to_python_function(yaml_data)
    
    assert callable(test_function), "to_python_function() should return callable"
    assert hasattr(test_function, 'yaml_steps_count'), "Function should have yaml_steps_count attribute"


@pytest.mark.asyncio
async def test_yaml_with_setup_teardown():
    """Test: OdooYAMLParser handles setup and teardown."""
    yaml_data = {
        'name': 'Test with Setup',
        'setup': [
            {'login': 'admin', 'password': 'admin'},
        ],
        'steps': [
            {'go_to': 'Dashboard'},
        ],
        'teardown': [
            {'logout': None},
        ]
    }
    
    test_function = OdooYAMLParser.to_python_function(yaml_data)
    
    assert callable(test_function), "to_python_function() should handle setup/teardown"
    assert test_function.yaml_steps_count == 3, "Should count setup, steps, and teardown"

