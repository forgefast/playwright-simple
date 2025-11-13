#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for YAMLParser class.
"""

import pytest
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_simple import YAMLParser, SimpleTestBase, TestConfig


def test_yaml_parser_parse_file():
    """Test parsing YAML file."""
    yaml_content = """
name: test_example
steps:
  - action: go_to
    url: /test
  - action: click
    selector: button
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        yaml_path = Path(f.name)
    
    try:
        data = YAMLParser.parse_file(yaml_path)
        assert data['name'] == 'test_example'
        assert len(data['steps']) == 2
        assert data['steps'][0]['action'] == 'go_to'
    finally:
        yaml_path.unlink()


def test_yaml_parser_parse_file_not_found():
    """Test parsing non-existent YAML file."""
    with pytest.raises(FileNotFoundError):
        YAMLParser.parse_file(Path("nonexistent.yaml"))


def test_yaml_parser_load_test():
    """Test loading test from YAML file."""
    yaml_content = """
name: test_example
steps:
  - action: go_to
    url: /test
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        yaml_path = Path(f.name)
    
    try:
        test_name, test_func = YAMLParser.load_test(yaml_path)
        assert test_name == 'test_example'
        assert callable(test_func)
    finally:
        yaml_path.unlink()


def test_yaml_parser_load_tests():
    """Test loading multiple tests from directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = Path(tmpdir)
        
        # Create test files
        test1 = yaml_dir / "test1.yaml"
        test1.write_text("""
name: test1
steps:
  - action: go_to
    url: /test1
""")
        
        test2 = yaml_dir / "test2.yaml"
        test2.write_text("""
name: test2
steps:
  - action: go_to
    url: /test2
""")
        
        tests = YAMLParser.load_tests(yaml_dir)
        assert len(tests) == 2
        # Order may vary, so check both names exist
        test_names = [t[0] for t in tests]
        assert 'test1' in test_names
        assert 'test2' in test_names


def test_yaml_parser_load_tests_empty_dir():
    """Test loading tests from empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = Path(tmpdir)
        tests = YAMLParser.load_tests(yaml_dir)
        assert tests == []


def test_yaml_parser_load_tests_invalid_yaml():
    """Test loading tests with invalid YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yaml_dir = Path(tmpdir)
        
        # Create invalid YAML file
        invalid_file = yaml_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content: [")
        
        # Should not raise, but skip invalid files
        tests = YAMLParser.load_tests(yaml_dir)
        # Should handle gracefully (either skip or return empty)
        assert isinstance(tests, list)


@pytest.mark.asyncio
async def test_yaml_parser_to_python_function():
    """Test converting YAML to Python function."""
    yaml_data = {
        'name': 'test_example',
        'steps': [
            {'action': 'go_to', 'url': '/test'},
        ]
    }
    
    test_func = YAMLParser.to_python_function(yaml_data)
    assert callable(test_func)
    assert test_func.__name__ == 'test_example'
    
    # Test function should be async
    import inspect
    assert inspect.iscoroutinefunction(test_func)


@pytest.mark.asyncio
async def test_yaml_parser_execute_step_go_to():
    """Test executing go_to step."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        step = {
            'action': 'go_to',
            'url': '/test'
        }
        
        # Mock go_to to avoid actual navigation
        original_go_to = test.go_to
        called_url = None
        
        async def mock_go_to(url):
            nonlocal called_url
            called_url = url
            return test
        
        test.go_to = mock_go_to
        
        await YAMLParser._execute_step(step, test)
        assert called_url == '/test'
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_yaml_parser_execute_step_click():
    """Test executing click step."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<button>Click me</button>')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        step = {
            'action': 'click',
            'selector': 'button'
        }
        
        await YAMLParser._execute_step(step, test)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_yaml_parser_execute_step_type():
    """Test executing type step."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<input type="text" />')
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        step = {
            'action': 'type',
            'selector': 'input',
            'text': 'test text'
        }
        
        await YAMLParser._execute_step(step, test)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_yaml_parser_execute_step_wait():
    """Test executing wait step."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        step = {
            'action': 'wait',
            'seconds': 0.1
        }
        
        await YAMLParser._execute_step(step, test)
        
        await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_yaml_parser_execute_step_unknown():
    """Test executing unknown action."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        config = TestConfig()
        test = SimpleTestBase(page, config)
        
        step = {
            'action': 'unknown_action'
        }
        
        # Should not raise, just print warning
        await YAMLParser._execute_step(step, test)
        
        await context.close()
        await browser.close()


def test_yaml_parser_inheritance():
    """Test YAML inheritance."""
    base_yaml = """
name: base_test
steps:
  - action: go_to
    url: /base
"""
    
    child_yaml = """
extends: base.yaml
steps:
  - action: click
    selector: button
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "base.yaml"
        base_path.write_text(base_yaml)
        
        child_path = Path(tmpdir) / "child.yaml"
        child_path.write_text(child_yaml)
        
        # Test inheritance resolution
        data = YAMLParser.parse_file(child_path)
        # Should merge base and child steps
        assert 'steps' in data


def test_yaml_parser_includes():
    """Test YAML includes."""
    included_yaml = """
steps:
  - action: wait
    seconds: 1
"""
    
    main_yaml = """
name: main_test
includes:
  - included.yaml
steps:
  - action: go_to
    url: /test
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        included_path = Path(tmpdir) / "included.yaml"
        included_path.write_text(included_yaml)
        
        main_path = Path(tmpdir) / "main.yaml"
        main_path.write_text(main_yaml)
        
        # Test includes resolution
        data = YAMLParser.parse_file(main_path)
        assert 'steps' in data

