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
            
            # Open filters menu (Odoo-specific action)
            elif "open_filters" in action:
                from ..specific.filters import FilterHelper
                # Store test instance and cursor_manager in page for FilterHelper to use
                test.page._test_instance = test
                if hasattr(test, 'cursor_manager'):
                    test.page._cursor_manager = test.cursor_manager
                filter_helper = FilterHelper(test.page)
                success = await filter_helper.open_filter_menu()
                if not success:
                    raise RuntimeError("Não foi possível abrir o menu de filtros - botão não encontrado")
            
            # Click button or element (supports both text and CSS selectors, or dict with description)
            elif "click" in action:
                click_data = action["click"]
                context = action.get("context")  # "wizard" or "form"
                
                # Support both formats:
                # 1. click: "texto ou seletor" (string)
                # 2. click: { description: "descrição do elemento" } (dict)
                if isinstance(click_data, dict):
                    click_target = click_data.get("description", "")
                    description = click_target
                else:
                    click_target = click_data
                    description = action.get("description", click_target)
                
                # Map common descriptions to CSS selectors
                description_to_selector = {
                    "botão do menu de apps no canto superior esquerdo": "button.o_grid_apps_menu__button",
                    "botão do menu de apps": "button.o_grid_apps_menu__button",
                    "menu de apps": "button.o_grid_apps_menu__button",
                    "app contatos no menu de apps": 'a:has-text("Contatos"), a[data-menu-xmlid*="contacts"]',
                    "app vendas no menu de apps": 'a:has-text("Vendas"), a[data-menu-xmlid*="sale"]',
                    "menu pedidos no submenu de vendas": 'a:has-text("Pedidos"), a[data-menu-xmlid*="sale.order"]',
                    "menu produtos no submenu de vendas": 'a:has-text("Produtos"), a[data-menu-xmlid*="product"]',
                    "setinha para baixo do searchbar": ".o_filters_menu .dropdown-toggle, .o_filters_menu button.dropdown-toggle, button.o_filters_menu_button.dropdown-toggle, .o_control_panel .o_filters_menu button",
                    "setinha do searchbar": ".o_filters_menu .dropdown-toggle, .o_filters_menu button.dropdown-toggle, button.o_filters_menu_button.dropdown-toggle, .o_control_panel .o_filters_menu button",
                    "botão de filtros": ".o_filters_menu .dropdown-toggle, .o_filters_menu button.dropdown-toggle, button.o_filters_menu_button.dropdown-toggle, .o_control_panel .o_filters_menu button",
                }
                
                # Check if description maps to a known selector or special action
                click_target_lower = click_target.lower().strip()
                
                # Note: "Filtros" should use open_filters action instead of click
                # This is kept for backward compatibility but open_filters is preferred
                if click_target_lower in ["filtros", "filters", "menu de filtros"]:
                    logger.warning("Using 'click: Filtros' is deprecated. Use 'open_filters: true' instead.")
                    from ...odoo.specific.filters import FilterHelper
                    filter_helper = FilterHelper(test.page)
                    success = await filter_helper.open_filter_menu()
                    if not success:
                        raise RuntimeError("Não foi possível abrir o menu de filtros - botão não encontrado")
                elif click_target_lower in description_to_selector:
                    click_target = description_to_selector[click_target_lower]
                    is_css_selector = True
                    # Use direct CSS selector click
                    await test.click(click_target, description)
                else:
                    # Check if it's a CSS selector (starts with common CSS selector patterns)
                    is_css_selector = (
                        click_target.startswith(".") or  # .class
                        click_target.startswith("#") or  # #id
                        click_target.startswith("[") or  # [attribute]
                        click_target.startswith("button.") or  # button.class
                        click_target.startswith("a.") or  # a.class
                        " > " in click_target or  # child selector
                        " " in click_target and ("." in click_target or "#" in click_target)  # descendant with class/id
                    )
                    
                    if is_css_selector:
                        # Use direct CSS selector click
                        await test.click(click_target, description)
                    elif click_target.lower() in ["apps", "aplicativos", "aplicações"]:
                        # Special handling for "Apps" button - use menu navigator
                        await test.menu.open_apps_menu()
                    else:
                        # Text-based click (user-friendly) - use description to find element
                        await test.click_button(click_target or description, context)
                
                # Check if wizard section follows
                if "wizard" in action:
                    wizard_steps = action["wizard"]
                    for wizard_step in wizard_steps:
                        wizard_action_func = ActionParser.parse_odoo_action(wizard_step, test, None)
                        await wizard_action_func()
            
            # Press key (e.g., "Escape", "Enter", "Tab")
            elif "press" in action:
                key = action["press"]
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"DEPRECATED: page.keyboard.press('{key}') usado sem cursor. "
                    "Esta ação será removida em versão futura. "
                    "Use métodos que utilizam cursor_manager para melhor visualização."
                )
                await test.page.keyboard.press(key)
            
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
            
            # Create record (CRUD)
            elif "create" in action:
                model_name = action.get("model")
                fields = action.get("fields", {})
                await test.create_record(model_name, fields)
            
            # Update record (CRUD) - update current record
            elif "update" in action:
                fields = action.get("fields", {})
                # Update fields in current record
                for field_name, value in fields.items():
                    await test.fill(f"{field_name} = {value}")
            
            # Delete record (CRUD) - delete current record
            elif "delete" in action:
                # Click delete button (usually "Excluir" or "Delete")
                await test.click_button("Excluir", context="form")
                # Confirm deletion if confirmation dialog appears
                try:
                    await test.click_button("Confirmar", context="wizard")
                except:
                    pass  # No confirmation needed
            
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
            
            # Hover (supports both string and dict with description)
            elif "hover" in action:
                hover_data = action["hover"]
                context = action.get("context")
                
                # Support both formats:
                # 1. hover: "texto" (string)
                # 2. hover: { description: "descrição do elemento" } (dict)
                if isinstance(hover_data, dict):
                    hover_target = hover_data.get("description", "")
                else:
                    hover_target = hover_data
                
                # Map common descriptions to CSS selectors
                description_to_selector = {
                    "botão do menu de apps no canto superior esquerdo": "button.o_grid_apps_menu__button",
                    "botão do menu de apps": "button.o_grid_apps_menu__button",
                    "menu de apps": "button.o_grid_apps_menu__button",
                    "app contatos no menu de apps": 'a:has-text("Contatos"), a[data-menu-xmlid*="contacts"]',
                    "app vendas no menu de apps": 'a:has-text("Vendas"), a[data-menu-xmlid*="sale"]',
                    "menu pedidos no submenu de vendas": 'a:has-text("Pedidos"), a[data-menu-xmlid*="sale.order"]',
                    "menu produtos no submenu de vendas": 'a:has-text("Produtos"), a[data-menu-xmlid*="product"]',
                }
                
                # Check if description maps to a known selector
                hover_target_lower = hover_target.lower().strip()
                if hover_target_lower in description_to_selector:
                    # Use selector directly
                    await test.click(description_to_selector[hover_target_lower], hover_target)
                    # Hover is just moving cursor, so we'll use click which includes hover
                    # Actually, we need to use hover method, not click
                    # Let's use the selector with hover
                    selector = description_to_selector[hover_target_lower]
                    element = test.page.locator(selector).first
                    if await element.count() > 0:
                        box = await element.bounding_box()
                        if box and test.cursor_manager:
                            x = box['x'] + box['width'] / 2
                            y = box['y'] + box['height'] / 2
                            await test.cursor_manager.move_to(x, y)
                            await asyncio.sleep(0.3)  # Pause on hover
                else:
                    # Use text-based hover
                    await test.hover(hover_target, context)
            
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

