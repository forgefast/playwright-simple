#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML parser for playwright-simple.

Converts YAML test definitions to executable Python functions.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from playwright.async_api import Page

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .base import SimpleTestBase


class YAMLParser:
    """Parser for YAML test definitions."""
    
    @staticmethod
    def parse_file(yaml_path: Path) -> Dict[str, Any]:
        """
        Parse YAML test file with support for inheritance and composition.
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Dictionary with test definition (with resolved inheritance/composition)
        """
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")
        
        yaml_path = Path(yaml_path)
        base_dir = yaml_path.parent
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Resolve inheritance and composition
        data = YAMLParser._resolve_inheritance(data, base_dir)
        data = YAMLParser._resolve_includes(data, base_dir)
        
        return data
    
    @staticmethod
    def _resolve_inheritance(data: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """
        Resolve extends (inheritance) in YAML data.
        
        Args:
            data: YAML data dictionary
            base_dir: Base directory for resolving relative paths
            
        Returns:
            Resolved YAML data with parent steps merged
        """
        if 'extends' not in data:
            return data
        
        extends_path = data['extends']
        if not extends_path:
            return data
        
        # Resolve path
        if not Path(extends_path).is_absolute():
            extends_path = base_dir / extends_path
        else:
            extends_path = Path(extends_path)
        
        if not extends_path.exists():
            raise FileNotFoundError(f"Extended YAML file not found: {extends_path}")
        
        # Load parent data
        with open(extends_path, 'r', encoding='utf-8') as f:
            parent_data = yaml.safe_load(f)
        
        # Recursively resolve parent's inheritance
        parent_data = YAMLParser._resolve_inheritance(parent_data, extends_path.parent)
        parent_data = YAMLParser._resolve_includes(parent_data, extends_path.parent)
        
        # Merge: child overrides parent
        merged = parent_data.copy()
        
        # Merge config (child overrides parent)
        if 'config' in data:
            if 'config' in merged:
                # Deep merge config
                merged_config = merged['config'].copy()
                merged_config.update(data['config'])
                merged['config'] = merged_config
            else:
                merged['config'] = data['config']
        
        # Merge steps: parent steps come first, then child steps (inheritance)
        parent_steps = merged.get('steps', [])
        child_steps = data.get('steps', [])
        merged['steps'] = parent_steps + child_steps  # Parent first, then child
        
        # Merge setup: parent setup first, then child setup
        parent_setup = merged.get('setup', [])
        child_setup = data.get('setup', [])
        if parent_setup or child_setup:
            merged['setup'] = parent_setup + child_setup
        
        # Merge teardown: child teardown first, then parent teardown (reverse order)
        parent_teardown = merged.get('teardown', [])
        child_teardown = data.get('teardown', [])
        if parent_teardown or child_teardown:
            merged['teardown'] = child_teardown + parent_teardown
        
        # Merge other fields (child overrides)
        for key in data:
            if key not in ['extends', 'config', 'steps', 'setup', 'teardown']:
                merged[key] = data[key]
        
        # Remove extends after resolution
        if 'extends' in merged:
            del merged['extends']
        
        return merged
    
    @staticmethod
    def _resolve_includes(data: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
        """
        Resolve include (composition) in YAML data.
        
        Args:
            data: YAML data dictionary
            base_dir: Base directory for resolving relative paths
            
        Returns:
            Resolved YAML data with included steps added
        """
        if 'include' not in data:
            return data
        
        include_paths = data['include']
        if not include_paths:
            return data
        
        # Support both single include and list of includes
        if isinstance(include_paths, str):
            include_paths = [include_paths]
        
        # Get base steps
        steps = data.get('steps', [])
        
        # Process each include
        for include_path in include_paths:
            # Resolve path
            if not Path(include_path).is_absolute():
                include_path = base_dir / include_path
            else:
                include_path = Path(include_path)
            
            if not include_path.exists():
                raise FileNotFoundError(f"Included YAML file not found: {include_path}")
            
            # Load included data
            with open(include_path, 'r', encoding='utf-8') as f:
                included_data = yaml.safe_load(f)
            
            # Recursively resolve included file's inheritance/includes
            included_data = YAMLParser._resolve_inheritance(included_data, include_path.parent)
            included_data = YAMLParser._resolve_includes(included_data, include_path.parent)
            
            # Add included steps to beginning (composition)
            included_steps = included_data.get('steps', [])
            steps = included_steps + steps
        
        # Update steps
        data['steps'] = steps
        
        # Remove include after resolution
        if 'include' in data:
            del data['include']
        
        return data
    
    @staticmethod
    def to_python_function(yaml_data: Dict[str, Any]) -> Callable:
        """
        Convert YAML test definition to Python function.
        
        Args:
            yaml_data: YAML test data
            
        Returns:
            Python async function (page, test) -> None
        """
        test_name = yaml_data.get('name', 'yaml_test')
        steps = yaml_data.get('steps', [])
        setup_steps = yaml_data.get('setup', [])
        teardown_steps = yaml_data.get('teardown', [])
        base_url = yaml_data.get('base_url')
        config_data = yaml_data.get('config', {})
        save_session = yaml_data.get('save_session', False)
        load_session = yaml_data.get('load_session')
        
        async def test_function(page: Page, test: SimpleTestBase) -> None:
            """Generated test function from YAML."""
            # Apply configuration from YAML if provided
            if config_data:
                from .config import TestConfig
                # Merge config with existing config
                if 'cursor' in config_data:
                    cursor_data = config_data['cursor']
                    if 'style' in cursor_data:
                        test.config.cursor.style = cursor_data['style']
                    if 'color' in cursor_data:
                        test.config.cursor.color = cursor_data['color']
                    if 'size' in cursor_data:
                        test.config.cursor.size = cursor_data['size']
                    if 'click_effect' in cursor_data:
                        test.config.cursor.click_effect = cursor_data['click_effect']
                    if 'animation_speed' in cursor_data:
                        test.config.cursor.animation_speed = cursor_data['animation_speed']
                
                if 'video' in config_data:
                    video_data = config_data['video']
                    if 'enabled' in video_data:
                        test.config.video.enabled = video_data['enabled']
                    if 'quality' in video_data:
                        test.config.video.quality = video_data['quality']
                    if 'codec' in video_data:
                        test.config.video.codec = video_data['codec']
                
                if 'browser' in config_data:
                    browser_data = config_data['browser']
                    if 'headless' in browser_data:
                        test.config.browser.headless = browser_data['headless']
                    if 'slow_mo' in browser_data:
                        test.config.browser.slow_mo = browser_data['slow_mo']
            
            # Set base URL if provided
            if base_url:
                test.config.base_url = base_url
            
            # Execute setup steps first
            if setup_steps:
                for step in setup_steps:
                    action = step.get('action')
                    if not action:
                        continue
                    await YAMLParser._execute_step(step, test)
            
            # Execute main steps
            try:
                for step in steps:
                    action = step.get('action')
                    if not action:
                        continue
                    await YAMLParser._execute_step(step, test)
            finally:
                # Execute teardown steps (always, even on error)
                if teardown_steps:
                    for step in teardown_steps:
                        try:
                            action = step.get('action')
                            if not action:
                                continue
                            await YAMLParser._execute_step(step, test)
                        except Exception as e:
                            # Log but don't fail on teardown errors
                            print(f"  ⚠️  Teardown step failed: {e}")
        
        # Set function attributes for session management
        test_function.save_session = save_session if save_session else None
        test_function.load_session = load_session if load_session else None
        
        # Set function name for debugging
        test_function.__name__ = test_name
        return test_function
    
    @staticmethod
    async def _execute_step(step: Dict[str, Any], test: SimpleTestBase) -> None:
        """
        Execute a single step from YAML.
        
        Args:
            step: Step dictionary
            test: Test base instance
        """
        action = step.get('action')
        if not action:
            return
        
        # Map action to method
        if action == 'login':
            username = step.get('username', '')
            password = step.get('password', '')
            login_url = step.get('login_url', '/login')
            show_process = step.get('show_process', False)
            await test.login(username, password, login_url, show_process)
        
        elif action == 'go_to':
            url = step.get('url', '/')
            await test.go_to(url)
        
        elif action == 'click':
            selector = step.get('selector', '')
            description = step.get('description', '')
            await test.click(selector, description)
        
        elif action == 'type':
            selector = step.get('selector', '')
            text = step.get('text', '')
            description = step.get('description', '')
            await test.type(selector, text, description)
        
        elif action == 'select':
            selector = step.get('selector', '')
            option = step.get('option', '')
            description = step.get('description', '')
            await test.select(selector, option, description)
        
        elif action == 'hover':
            selector = step.get('selector', '')
            description = step.get('description', '')
            await test.hover(selector, description)
        
        elif action == 'drag':
            source = step.get('source', '')
            target = step.get('target', '')
            description = step.get('description', '')
            await test.drag(source, target, description)
        
        elif action == 'scroll':
            selector = step.get('selector')
            direction = step.get('direction', 'down')
            amount = step.get('amount', 500)
            await test.scroll(selector, direction, amount)
        
        elif action == 'wait':
            seconds = step.get('seconds', 1.0)
            await test.wait(seconds)
        
        elif action == 'wait_for':
            selector = step.get('selector', '')
            state = step.get('state', 'visible')
            timeout = step.get('timeout')
            description = step.get('description', '')
            await test.wait_for(selector, state, timeout, description)
        
        elif action == 'wait_for_url':
            url_pattern = step.get('url_pattern', '')
            timeout = step.get('timeout')
            await test.wait_for_url(url_pattern, timeout)
        
        elif action == 'wait_for_text':
            selector = step.get('selector', '')
            text = step.get('text', '')
            timeout = step.get('timeout')
            description = step.get('description', '')
            await test.wait_for_text(selector, text, timeout, description)
        
        elif action == 'assert_text':
            selector = step.get('selector', '')
            expected = step.get('expected', '')
            description = step.get('description', '')
            await test.assert_text(selector, expected, description)
        
        elif action == 'assert_visible':
            selector = step.get('selector', '')
            description = step.get('description', '')
            await test.assert_visible(selector, description)
        
        elif action == 'assert_url':
            pattern = step.get('pattern', '')
            await test.assert_url(pattern)
        
        elif action == 'assert_count':
            selector = step.get('selector', '')
            expected_count = step.get('expected_count', 0)
            description = step.get('description', '')
            await test.assert_count(selector, expected_count, description)
        
        elif action == 'assert_attr':
            selector = step.get('selector', '')
            attribute = step.get('attribute', '')
            expected = step.get('expected', '')
            description = step.get('description', '')
            await test.assert_attr(selector, attribute, expected, description)
        
        elif action == 'fill_form':
            fields = step.get('fields', {})
            await test.fill_form(fields)
        
        elif action == 'screenshot':
            name = step.get('name')
            full_page = step.get('full_page')
            element = step.get('element')
            await test.screenshot(name, full_page, element)
        
        elif action == 'navigate':
            menu_path = step.get('menu_path', [])
            await test.navigate(menu_path)
        
        else:
            print(f"  ⚠️  Unknown action: {action}")
                
    
    @staticmethod
    def load_test(yaml_path: Path) -> tuple[str, Callable]:
        """
        Load test from YAML file.
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Tuple of (test_name, test_function)
        """
        data = YAMLParser.parse_file(yaml_path)
        test_name = data.get('name', yaml_path.stem)
        test_function = YAMLParser.to_python_function(data)
        return (test_name, test_function)
    
    @staticmethod
    def load_tests(yaml_dir: Path) -> List[tuple[str, Callable]]:
        """
        Load all tests from YAML directory.
        
        Args:
            yaml_dir: Directory containing YAML test files
            
        Returns:
            List of tuples (test_name, test_function)
        """
        tests = []
        yaml_dir = Path(yaml_dir)
        
        if not yaml_dir.exists():
            return tests
        
        for yaml_file in yaml_dir.glob("*.yaml"):
            try:
                test_name, test_func = YAMLParser.load_test(yaml_file)
                tests.append((test_name, test_func))
            except Exception as e:
                print(f"  ⚠️  Error loading {yaml_file}: {e}")
        
        for yaml_file in yaml_dir.glob("*.yml"):
            try:
                test_name, test_func = YAMLParser.load_test(yaml_file)
                tests.append((test_name, test_func))
            except Exception as e:
                print(f"  ⚠️  Error loading {yaml_file}: {e}")
        
        return tests


