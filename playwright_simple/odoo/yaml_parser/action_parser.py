#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Action parser for Odoo YAML tests.

Converts YAML action dictionaries into executable Python functions.
"""

import asyncio
from typing import Dict, Any, Callable, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..base import OdooTestBase


class ActionParser:
    """Parser for Odoo-specific actions from YAML."""
    
    @staticmethod
    def parse_odoo_action(action: Dict[str, Any], test: 'OdooTestBase', step: Optional[Any] = None) -> Callable:
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
            step: Optional TestStep instance (for future use)
            
        Returns:
            Async function to execute the action
        """
        async def execute_action():
            # Login action
            if "login" in action:
                username = action["login"]
                password = action.get("password", "")
                database = action.get("database")
                await test.login(username, password, database)
            
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
                
                # Special handling for "Apps" button - use menu navigator
                if button_text.lower() in ["apps", "aplicativos", "aplicações"]:
                    await test.menu.open_apps_menu()
                else:
                    await test.click_button(button_text, context)
                
                # Check if wizard section follows
                if "wizard" in action:
                    wizard_steps = action["wizard"]
                    for wizard_step in wizard_steps:
                        wizard_action_func = ActionParser.parse_odoo_action(wizard_step, test, None)
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
                records = await test.view.search_records(search_text)
                # Search is complete, wait_until_ready will be called automatically
            
            # Filter records (using Odoo filters menu)
            elif "filter_by" in action:
                filter_name = action["filter_by"]
                await test.view.filter_records(filter_name)
            
            # Screenshot
            elif "screenshot" in action:
                name = action["screenshot"]
                description = action.get("description", name)
                await test.screenshot(name, description=description)
            
            # Wait - Converted to minimal visual delay only
            # Waits are now automatic based on page readiness
            # This is kept only for minimal visual pauses (e.g., 0.1s max)
            elif "wait" in action:
                seconds = action.get("wait", 0.1)
                if isinstance(seconds, (int, float)):
                    # Cap wait at 0.2s - anything longer is unnecessary
                    # The automatic wait_until_ready handles actual readiness
                    max_wait = min(float(seconds), 0.2)
                    await asyncio.sleep(max_wait)
                else:
                    await asyncio.sleep(0.1)  # Minimal default
            
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

