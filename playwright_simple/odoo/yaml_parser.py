#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAML parser for Odoo tests - User-friendly version.

Supports simple, intuitive YAML syntax for QAs without programming experience.
"""

from typing import Dict, Any, Callable, TYPE_CHECKING, Optional
from playwright.async_api import Page

from ..core.yaml_parser import YAMLParser

if TYPE_CHECKING:
    from .base import OdooTestBase


class OdooYAMLParser(YAMLParser):
    """YAML parser with Odoo-specific actions - User-friendly syntax."""
    
    @staticmethod
    def parse_odoo_action(action: Dict[str, Any], test: 'OdooTestBase') -> Callable:
        """
        Parse an Odoo-specific action from YAML (user-friendly syntax).
        
        Supports actions like:
        - login: admin
        - go_to: "Vendas > Pedidos"
        - click: "Criar"
        - fill: "Cliente = João Silva"
        - add_line: "Adicionar linha"
        - open_record: "João Silva"
        
        Args:
            action: Action dictionary from YAML
            test: OdooTestBase instance
            
        Returns:
            Async function to execute the action
        """
        async def execute_action():
            # Login action
            if "login" in action:
                username = action["login"]
                password = action.get("password", "")
                database = action.get("database")
                print(f"🔐 DEBUG YAML: Executing login action for '{username}'")
                await test.login(username, password, database)
                print(f"🔐 DEBUG YAML: Login action completed")
            
            # Logout action
            elif "logout" in action:
                await test.logout()
            
            # Go to menu (user-friendly format)
            elif "go_to" in action:
                menu_path = action["go_to"]
                await test.go_to(menu_path)
            
            # Click button (user-friendly - just text)
            elif "click" in action:
                button_text = action["click"]
                context = action.get("context")  # "wizard" or "form"
                await test.click_button(button_text, context)
                
                # Check if wizard section follows
                if "wizard" in action:
                    wizard_steps = action["wizard"]
                    for wizard_step in wizard_steps:
                        wizard_action_func = OdooYAMLParser.parse_odoo_action(wizard_step, test)
                        await wizard_action_func()
            
            # Fill field (user-friendly format)
            elif "fill" in action:
                fill_value = action["fill"]
                context = action.get("context")
                
                # Support both formats: "Cliente = João" or separate label/value
                if isinstance(fill_value, str) and '=' in fill_value:
                    await test.fill(fill_value, context=context)
                else:
                    # Assume it's a dict with label and value
                    label = fill_value if isinstance(fill_value, str) else action.get("label", "")
                    value = action.get("value", "")
                    await test.fill(label, value, context)
            
            # Add line to One2many table
            elif "add_line" in action:
                button_text = action.get("add_line")
                await test.add_line(button_text)
            
            # Open record by search
            elif "open_record" in action:
                search_text = action["open_record"]
                position = action.get("position")  # "primeiro", "segundo", "último"
                await test.open_record(search_text, position)
            
            # Search records
            elif "search" in action:
                search_text = action["search"]
                await test.view.search_records(search_text)
            
            # Screenshot
            elif "screenshot" in action:
                name = action["screenshot"]
                description = action.get("description", name)
                await test.screenshot(name, description=description)
            
            # Wait
            elif "wait" in action:
                seconds = action.get("wait", 1)
                if isinstance(seconds, (int, float)):
                    await test.wait(seconds)
                else:
                    await test.wait(1)
            
            # Scroll
            elif "scroll" in action:
                scroll_value = action["scroll"]
                if isinstance(scroll_value, str):
                    if scroll_value.lower() in ["down", "baixo"]:
                        await test.scroll_down()
                    elif scroll_value.lower() in ["up", "cima"]:
                        await test.scroll_up()
                else:
                    # Assume it's a dict with direction and amount
                    direction = action.get("direction", "down")
                    amount = action.get("amount", 500)
                    if direction.lower() in ["down", "baixo"]:
                        await test.scroll_down(amount)
                    elif direction.lower() in ["up", "cima"]:
                        await test.scroll_up(amount)
            
            # Hover
            elif "hover" in action:
                text = action["hover"]
                context = action.get("context")
                await test.hover(text, context)
            
            # Double click
            elif "double_click" in action:
                text = action["double_click"]
                context = action.get("context")
                await test.double_click(text, context)
            
            # Right click
            elif "right_click" in action:
                text = action["right_click"]
                context = action.get("context")
                await test.right_click(text, context)
            
            # Drag and drop
            elif "drag" in action:
                drag_data = action["drag"]
                if isinstance(drag_data, dict):
                    from_text = drag_data.get("from")
                    to_text = drag_data.get("to")
                    if from_text and to_text:
                        await test.drag_and_drop(from_text, to_text)
                else:
                    # Assume it's a string with "from > to" format
                    if ">" in str(drag_data):
                        parts = str(drag_data).split(">")
                        from_text = parts[0].strip()
                        to_text = parts[1].strip() if len(parts) > 1 else ""
                        if from_text and to_text:
                            await test.drag_and_drop(from_text, to_text)
            
            # Legacy actions (for backward compatibility)
            elif "action" in action:
                action_type = action["action"]
                
                if action_type == "login":
                    await test.login(
                        action["username"],
                        action["password"],
                        action.get("database")
                    )
                elif action_type == "go_to_menu":
                    await test.go_to_menu(
                        action["menu"],
                        action.get("submenu")
                    )
                elif action_type == "fill_field":
                    field_type = action.get("type", "char")
                    field_name = action["field"]
                    value = action["value"]
                    
                    if field_type == "many2one":
                        await test.field.fill_many2one(field_name, value)
                    elif field_type == "char":
                        await test.field.fill_char(field_name, value)
                    elif field_type == "integer":
                        await test.field.fill_integer(field_name, value)
                    elif field_type == "float":
                        await test.field.fill_float(field_name, value)
                    elif field_type == "boolean":
                        await test.field.toggle_boolean(field_name)
                    elif field_type == "date":
                        await test.field.fill_date(field_name, value)
                    elif field_type == "datetime":
                        await test.field.fill_datetime(field_name, value)
        
        return execute_action
    
    @classmethod
    def to_python_function(cls, yaml_data: Dict[str, Any]) -> Callable:
        """
        Convert YAML test definition to Python function with Odoo support.
        
        Supports user-friendly YAML format with inheritance, composition, setup/teardown:
        ```yaml
        extends: common_login.yaml
        setup:
          - login: admin
            password: admin
        steps:
          - go_to: "Vendas > Pedidos"
          - click: "Criar"
          - fill: "Cliente = João Silva"
        teardown:
          - logout:
        save_session: true
        ```
        
        Args:
            yaml_data: YAML test data (already resolved for inheritance/includes)
            
        Returns:
            Python test function
        """
        # Import here to avoid circular dependency
        from .base import OdooTestBase
        
        # Get setup, steps, and teardown
        setup_steps = yaml_data.get("setup", [])
        steps = yaml_data.get("steps", [])
        teardown_steps = yaml_data.get("teardown", [])
        config_data = yaml_data.get("config", {})
        save_session = yaml_data.get("save_session", False)
        load_session = yaml_data.get("load_session")
        
        async def test_function(page: Page, test: 'OdooTestBase'):
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
                print(f"  🔧 Executando {len(setup_steps)} passo(s) de setup...")
                for i, step in enumerate(setup_steps, 1):
                    try:
                        print(f"    [{i}/{len(setup_steps)}] Setup: {str(step)[:80]}")
                        action_func = cls.parse_odoo_action(step, test)
                        await action_func()
                        print(f"    ✅ Setup passo {i} concluído")
                    except Exception as e:
                        step_str = str(step)[:100]
                        print(f"    ❌ Erro no setup passo {i}: {e}")
                        raise RuntimeError(
                            f"Erro ao executar setup passo {i}: {step_str}\n"
                            f"Erro: {str(e)}"
                        ) from e
            
            # Execute main steps
            try:
                print(f"  ▶️  Executando {len(steps)} passo(s) principal(is)...")
                for i, step in enumerate(steps, 1):
                    try:
                        print(f"    [{i}/{len(steps)}] Passo: {str(step)[:80]}")
                        action_func = cls.parse_odoo_action(step, test)
                        await action_func()
                        print(f"    ✅ Passo {i} concluído")
                    except Exception as e:
                        # Provide helpful error message
                        step_str = str(step)[:100]  # Limit length
                        print(f"    ❌ Erro no passo {i}: {e}")
                        # Take debug screenshot
                        try:
                            debug_screenshot = test.screenshot_manager.test_dir / f"debug_error_step_{i}.png"
                            await test.page.screenshot(path=str(debug_screenshot), full_page=True)
                            print(f"    📸 Screenshot de debug salvo: {debug_screenshot}")
                        except Exception:
                            pass
                        raise RuntimeError(
                            f"Erro ao executar passo {i}: {step_str}\n"
                            f"Erro: {str(e)}"
                        ) from e
            finally:
                # Execute teardown steps (always, even on error)
                if teardown_steps:
                    for step in teardown_steps:
                        try:
                            action_func = cls.parse_odoo_action(step, test)
                            await action_func()
                        except Exception as e:
                            # Log but don't fail on teardown errors
                            print(f"  ⚠️  Teardown step failed: {e}")
        
        # Set function attributes for session management
        test_function.save_session = save_session if save_session else None
        test_function.load_session = load_session if load_session else None
        
        return test_function

# Inherit parse_file to get inheritance/composition support
OdooYAMLParser.parse_file = staticmethod(YAMLParser.parse_file)
