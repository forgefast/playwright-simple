#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML parser for ForgeERP tests - User-friendly version.

Supports simple, intuitive YAML syntax for QAs without programming experience.
"""

from pathlib import Path
from typing import Dict, Any, Callable, TYPE_CHECKING, Optional
from playwright.async_api import Page

from ..core.yaml_resolver import parse_yaml_file

if TYPE_CHECKING:
    from .base import ForgeERPTestBase


class ForgeERPYAMLParser:
    """YAML parser with ForgeERP-specific actions - User-friendly syntax."""
    
    @staticmethod
    def parse_forgeerp_action(action: Dict[str, Any], test: 'ForgeERPTestBase') -> Callable:
        """
        Parse a ForgeERP-specific action from YAML (user-friendly syntax).
        
        Supports actions like:
        - go_to_provision: Navigate to provision page
        - fill_provision_form: Fill provisioning form
        - provision_client: Complete provisioning workflow
        - deploy_application: Complete deployment workflow
        - check_status: Check client status
        - run_diagnostics: Run diagnostics
        
        Args:
            action: Action dictionary from YAML
            test: ForgeERPTestBase instance
            
        Returns:
            Async function to execute the action
        """
        async def execute_action():
            # Navigation actions
            if "go_to_setup" in action:
                await test.go_to_setup()
            
            elif "go_to_provision" in action:
                await test.go_to_provision()
            
            elif "go_to_status" in action:
                client_name = action.get("client_name")
                environment = action.get("environment")
                await test.go_to_status(client_name, environment)
            
            elif "go_to_deploy" in action:
                await test.go_to_deploy()
            
            elif "go_to_diagnostics" in action:
                await test.go_to_diagnostics()
            
            # Form filling actions
            elif "fill_provision_form" in action:
                form_data = action["fill_provision_form"]
                if isinstance(form_data, dict):
                    await test.fill_provision_form(
                        client_name=form_data.get("client_name", ""),
                        environment=form_data.get("environment", "dev"),
                        database_type=form_data.get("database_type"),
                        namespace=form_data.get("namespace")
                    )
                else:
                    # Simple format: just client_name
                    await test.fill_provision_form(client_name=str(form_data))
            
            elif "fill_deploy_form" in action:
                form_data = action["fill_deploy_form"]
                if isinstance(form_data, dict):
                    await test.fill_deploy_form(
                        client_name=form_data.get("client_name", ""),
                        environment=form_data.get("environment", "dev"),
                        chart_name=form_data.get("chart_name", "generic"),
                        chart_version=form_data.get("chart_version"),
                        **{k: v for k, v in form_data.items() 
                           if k not in ["client_name", "environment", "chart_name", "chart_version"]}
                    )
                else:
                    # Simple format: just client_name
                    await test.fill_deploy_form(client_name=str(form_data))
            
            elif "fill_diagnostics_form" in action:
                form_data = action["fill_diagnostics_form"]
                if isinstance(form_data, dict):
                    await test.fill_diagnostics_form(
                        client_name=form_data.get("client_name", ""),
                        environment=form_data.get("environment", "dev")
                    )
                else:
                    # Simple format: just client_name
                    await test.fill_diagnostics_form(client_name=str(form_data), environment="dev")
            
            # Form submission
            elif "submit_form" in action:
                submit_data = action.get("submit_form", {})
                if isinstance(submit_data, dict):
                    await test.submit_form(
                        button_selector=submit_data.get("button_selector"),
                        wait_for_response=submit_data.get("wait_for_response", True),
                        container_selector=submit_data.get("container_selector")
                    )
                else:
                    # Simple format: just submit
                    await test.submit_form()
            
            # Workflow actions
            elif "provision_client" in action:
                workflow_data = action["provision_client"]
                if isinstance(workflow_data, dict):
                    await test.provision_client(
                        client_name=workflow_data.get("client_name", ""),
                        environment=workflow_data.get("environment", "dev"),
                        database_type=workflow_data.get("database_type"),
                        namespace=workflow_data.get("namespace"),
                        **{k: v for k, v in workflow_data.items() 
                           if k not in ["client_name", "environment", "database_type", "namespace"]}
                    )
                else:
                    # Simple format: just client_name
                    await test.provision_client(client_name=str(workflow_data))
            
            elif "deploy_application" in action:
                workflow_data = action["deploy_application"]
                if isinstance(workflow_data, dict):
                    await test.deploy_application(
                        client_name=workflow_data.get("client_name", ""),
                        environment=workflow_data.get("environment", "dev"),
                        chart_name=workflow_data.get("chart_name", "generic"),
                        chart_version=workflow_data.get("chart_version"),
                        **{k: v for k, v in workflow_data.items() 
                           if k not in ["client_name", "environment", "chart_name", "chart_version"]}
                    )
                else:
                    # Simple format: just client_name
                    await test.deploy_application(client_name=str(workflow_data))
            
            elif "check_status" in action:
                status_data = action["check_status"]
                if isinstance(status_data, dict):
                    await test.check_status(
                        client_name=status_data.get("client_name", ""),
                        environment=status_data.get("environment", "dev")
                    )
                else:
                    # Simple format: just client_name
                    await test.check_status(client_name=str(status_data))
            
            elif "run_diagnostics" in action:
                diagnostics_data = action.get("run_diagnostics", {})
                if isinstance(diagnostics_data, dict):
                    await test.run_diagnostics(
                        client_name=diagnostics_data.get("client_name"),
                        environment=diagnostics_data.get("environment")
                    )
                elif diagnostics_data:
                    # Simple format: client_name string
                    await test.run_diagnostics(client_name=str(diagnostics_data))
                else:
                    # No data: run summary diagnostics
                    await test.run_diagnostics()
            
            # HTMX actions (via test.htmx)
            elif "wait_for_htmx_swap" in action:
                container = action["wait_for_htmx_swap"]
                timeout = action.get("timeout")
                await test.htmx.wait_for_htmx_swap(container, timeout)
            
            elif "wait_for_htmx_loading" in action:
                indicator = action.get("wait_for_htmx_loading", ".htmx-indicator")
                timeout = action.get("timeout")
                wait_for_hidden = action.get("wait_for_hidden", True)
                await test.htmx.wait_for_htmx_loading(indicator, timeout, wait_for_hidden)
            
            elif "get_htmx_result" in action:
                container_id = action["get_htmx_result"]
                wait_for_swap = action.get("wait_for_swap", True)
                timeout = action.get("timeout")
                result = await test.htmx.get_htmx_result(container_id, wait_for_swap, timeout)
                # Store result in test context for later use
                if not hasattr(test, '_yaml_results'):
                    test._yaml_results = {}
                test._yaml_results[container_id] = result
            
            # Validation actions
            elif "assert_no_errors" in action:
                # assert_no_errors() doesn't accept parameters in current implementation
                # Just call it without parameters
                await test.assert_no_errors()
            
            # Generic actions (fallback to core parser)
            # Check if it's a core action format (with 'action' key)
            elif "action" in action:
                # Convert to core format and execute
                await YAMLParser._execute_step(action, test)
            
            # Generic actions without 'action' key (user-friendly format)
            # Try common generic actions
            elif "go_to" in action:
                url = action["go_to"]
                await test.go_to(url)
            
            elif "click" in action:
                # Can be selector or button text
                click_target = action["click"]
                context = action.get("context")
                if click_target.startswith((".", "#", "[", "/")):
                    # Looks like a selector
                    await test.click(click_target, description=action.get("description", ""))
                else:
                    # Button text
                    await test.click_button(click_target, context)
            
            elif "type" in action:
                type_data = action["type"]
                if isinstance(type_data, dict):
                    selector = type_data.get("selector", "")
                    text = type_data.get("text", "")
                    await test.type(selector, text, description=type_data.get("description", ""))
                else:
                    # Simple format not supported for type (needs selector)
                    raise ValueError("'type' action requires dict with 'selector' and 'text'")
            
            elif "wait" in action:
                seconds = action.get("wait", 1)
                if isinstance(seconds, (int, float)):
                    await test.wait(seconds)
                else:
                    await test.wait(1)
            
            elif "screenshot" in action:
                name = action.get("screenshot")
                description = action.get("description", name or "")
                await test.screenshot(name, description=description)
            
            else:
                # Unknown action
                print(f"  ⚠️  Unknown action: {list(action.keys())[0] if action else 'empty'}")
        
        return execute_action
    
    @classmethod
    def to_python_function(cls, yaml_data: Dict[str, Any]) -> Callable:
        """
        Convert YAML test definition to Python function with ForgeERP support.
        
        Supports user-friendly YAML format with inheritance, composition, setup/teardown:
        ```yaml
        extends: common_setup.yaml
        setup:
          - go_to_provision:
        steps:
          - fill_provision_form:
              client_name: "my-client"
              environment: "dev"
              database_type: "postgresql"
          - submit_form:
          - assert_no_errors:
        teardown:
          - go_to_home:
        save_session: true
        ```
        
        Args:
            yaml_data: YAML test data (already resolved for inheritance/includes)
            
        Returns:
            Python test function
        """
        # Import here to avoid circular dependency
        from .base import ForgeERPTestBase
        
        # Get setup, steps, and teardown
        setup_steps = yaml_data.get("setup", [])
        steps = yaml_data.get("steps", [])
        teardown_steps = yaml_data.get("teardown", [])
        config_data = yaml_data.get("config", {})
        save_session = yaml_data.get("save_session", False)
        load_session = yaml_data.get("load_session")
        
        async def test_function(page: Page, test: 'ForgeERPTestBase'):
            """Generated test function from user-friendly YAML."""
            # Apply configuration from YAML if provided
            if config_data:
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
            
            # Execute setup steps first
            if setup_steps:
                for step in setup_steps:
                    try:
                        action_func = cls.parse_forgeerp_action(step, test)
                        await action_func()
                    except Exception as e:
                        step_str = str(step)[:100]
                        raise RuntimeError(
                            f"Error executing setup: {step_str}\n"
                            f"Error: {str(e)}"
                        ) from e
            
            # Execute main steps
            try:
                for step in steps:
                    try:
                        action_func = cls.parse_forgeerp_action(step, test)
                        await action_func()
                    except Exception as e:
                        # Provide helpful error message
                        step_str = str(step)[:100]  # Limit length
                        raise RuntimeError(
                            f"Error executing step: {step_str}\n"
                            f"Error: {str(e)}"
                        ) from e
            finally:
                # Execute teardown steps (always, even on error)
                if teardown_steps:
                    for step in teardown_steps:
                        try:
                            action_func = cls.parse_forgeerp_action(step, test)
                            await action_func()
                        except Exception as e:
                            # Log but don't fail on teardown errors
                            print(f"  ⚠️  Teardown step failed: {e}")
        
        # Set function attributes for session management
        test_function.save_session = save_session if save_session else None
        test_function.load_session = load_session if load_session else None
        
        return test_function

    @staticmethod
    def parse_file(yaml_path: Path) -> Dict[str, Any]:
        """
        Parse YAML test file with support for inheritance and composition.
        
        This method uses the core YAMLResolver to parse files, replacing
        the old YAMLParser dependency.
        """
        return parse_yaml_file(yaml_path)

