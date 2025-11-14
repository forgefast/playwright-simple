#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal tests for YAML Parser - FASE 0 TDD.

These tests define the minimum requirements for YAML parser.
Following TDD: write tests first, then implement.
"""

import pytest
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_simple.core.yaml_parser import YAMLParser


def test_parse_simple_yaml():
    """
    Test: YAMLParser can parse a simple YAML file.
    
    Requirement: Parser must read and parse basic YAML structure.
    """
    yaml_content = """
name: Simple Test
base_url: http://test.com
steps:
  - action: go_to
    url: /home
  - action: click
    selector: button
"""
    
    # Create temporary YAML file
    test_file = Path("/tmp/test_simple.yaml")
    test_file.write_text(yaml_content)
    
    try:
        data = YAMLParser.parse_file(test_file)
        
        assert data['name'] == "Simple Test"
        assert data['base_url'] == "http://test.com"
        assert len(data['steps']) == 2
        assert data['steps'][0]['action'] == "go_to"
        assert data['steps'][1]['action'] == "click"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_parse_yaml_with_steps():
    """
    Test: YAMLParser can parse YAML with multiple steps.
    
    Requirement: Parser must handle multiple steps correctly.
    """
    yaml_content = """
name: Multi Step Test
steps:
  - action: go_to
    url: /page1
  - action: click
    selector: #button1
  - action: type
    selector: input
    text: Hello
"""
    
    test_file = Path("/tmp/test_multi_step.yaml")
    test_file.write_text(yaml_content)
    
    try:
        data = YAMLParser.parse_file(test_file)
        
        assert len(data['steps']) == 3
        assert data['steps'][0]['action'] == "go_to"
        assert data['steps'][1]['action'] == "click"
        assert data['steps'][2]['action'] == "type"
        assert data['steps'][2]['text'] == "Hello"
    finally:
        if test_file.exists():
            test_file.unlink()


@pytest.mark.asyncio
async def test_yaml_to_python_function():
    """
    Test: YAMLParser can convert YAML to executable Python function.
    
    Requirement: Parser must generate a callable function from YAML.
    """
    yaml_content = """
name: Executable Test
base_url: http://test.com
steps:
  - action: go_to
    url: /test
"""
    
    test_file = Path("/tmp/test_executable.yaml")
    test_file.write_text(yaml_content)
    
    try:
        data = YAMLParser.parse_file(test_file)
        test_function = YAMLParser.to_python_function(data)
        
        # Function should be callable
        assert callable(test_function)
        assert test_function.__name__ == "Executable Test"
        
        # Function should have attributes
        assert hasattr(test_function, 'save_session') or test_function.save_session is None
        
    finally:
        if test_file.exists():
            test_file.unlink()


@pytest.mark.asyncio
async def test_execute_simple_yaml():
    """
    Test: Can execute a simple YAML test end-to-end.
    
    Requirement: Full flow from YAML to execution must work.
    """
    yaml_content = """
name: E2E Test
steps:
  - action: go_to
    url: data:text/html,<html><body><button id="btn">Click</button></body></html>
  - action: click
    selector: #btn
"""
    
    test_file = Path("/tmp/test_e2e.yaml")
    test_file.write_text(yaml_content)
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Load and convert YAML
            data = YAMLParser.parse_file(test_file)
            test_function = YAMLParser.to_python_function(data)
            
            # Create a simple test base for execution
            from playwright_simple import SimpleTestBase, TestConfig
            test = SimpleTestBase(page, TestConfig())
            
            # Execute the function
            await test_function(page, test)
            
            # Verify execution (button should exist)
            button = page.locator("#btn")
            assert await button.count() == 1
            
            await context.close()
            await browser.close()
    finally:
        if test_file.exists():
            test_file.unlink()

