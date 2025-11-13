#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo selectors by version.

Maps CSS/XPath selectors for different Odoo versions (14-18)
and editions (Community/Enterprise).
"""

from typing import Dict, List, Optional


# Base selectors that work across versions
BASE_SELECTORS = {
    "login": {
        "db_input": 'input[name="db"]',
        "login_input": 'input[name="login"]',
        "password_input": 'input[name="password"]',
        "submit_button": 'button[type="submit"], button:has-text("Entrar"), button:has-text("Log in")',
    },
    "many2one": {
        "input": '.o_field_many2one input',
        "dropdown": '.ui-autocomplete li, .o_m2o_dropdown_option',
        "first_option": '.ui-autocomplete li:first-child, .o_m2o_dropdown_option:first-child',
    },
    "buttons": {
        "create": 'button:has-text("Criar"), button[title*="Criar"], .o_list_button_add, button.o_form_button_create',
        "save": 'button:has-text("Salvar"), button[title*="Salvar"], button.o_form_button_save',
        "edit": 'button:has-text("Editar"), button[title*="Editar"], button.o_form_button_edit',
        "delete": 'button:has-text("Excluir"), button[title*="Excluir"], button.o_form_button_delete',
        "confirm": 'button:has-text("Confirmar"), button[title*="Confirmar"]',
        "cancel": 'button:has-text("Cancelar"), button[title*="Cancelar"], button.o_form_button_cancel',
        "discard": 'button:has-text("Descartar"), button[title*="Descartar"]',
    },
    "views": {
        "list": '.o_list_view, .o_list_table',
        "kanban": '.o_kanban_view',
        "form": '.o_form_view',
        "graph": '.o_graph_view',
        "pivot": '.o_pivot_view',
        "calendar": '.o_calendar_view',
    },
    "search": {
        "input": 'input[placeholder*="Buscar"], .o_searchview_input',
        "clear": 'button[title*="Limpar"], .o_searchview_clear',
    },
}


# Version-specific selectors
VERSION_SELECTORS: Dict[str, Dict[str, Dict[str, str]]] = {
    "14.0": {
        "menu": {
            "apps_toggle": 'button.o_menu_toggle',
            "apps_menu": '.o_apps_menu',
            "menu_item": '.o_app[data-menu-xmlid], .o_menu_item',
        },
        "fields": {
            "many2one_input": '.o_field_many2one input',
            "many2many_tags": '.o_field_many2many_tags',
            "one2many_list": '.o_field_one2many_list',
        },
    },
    "15.0": {
        "menu": {
            "apps_toggle": 'button.o_menu_toggle',
            "apps_menu": '.o_apps_menu',
            "menu_item": '.o_app[data-menu-xmlid], .o_menu_item',
        },
        "fields": {
            "many2one_input": '.o_field_many2one input',
            "many2many_tags": '.o_field_many2many_tags',
            "one2many_list": '.o_field_one2many_list',
        },
    },
    "16.0": {
        "menu": {
            "apps_toggle": 'button.o_menu_toggle, button[aria-label*="Menu"]',
            "apps_menu": '.o_apps_menu, .o_main_navbar',
            "menu_item": '.o_app[data-menu-xmlid], .o_menu_item, .o_apps_menu_item',
        },
        "fields": {
            "many2one_input": '.o_field_many2one input',
            "many2many_tags": '.o_field_many2many_tags',
            "one2many_list": '.o_field_one2many_list',
        },
    },
    "17.0": {
        "menu": {
            "apps_toggle": 'button.o_menu_toggle, button[aria-label*="Menu"], button[title*="Apps"]',
            "apps_menu": '.o_apps_menu, .o_main_navbar',
            "menu_item": '.o_app[data-menu-xmlid], .o_menu_item, .o_apps_menu_item',
        },
        "fields": {
            "many2one_input": '.o_field_many2one input',
            "many2many_tags": '.o_field_many2many_tags',
            "one2many_list": '.o_field_one2many_list',
        },
    },
    "18.0": {
        "menu": {
            "apps_toggle": 'button.o_menu_toggle, button[aria-label*="Menu"], button[title*="Apps"]',
            "apps_menu": '.o_apps_menu, .o_main_navbar',
            "menu_item": '.o_app[data-menu-xmlid], .o_menu_item, .o_apps_menu_item',
        },
        "fields": {
            "many2one_input": '.o_field_many2one input',
            "many2many_tags": '.o_field_many2many_tags',
            "one2many_list": '.o_field_one2many_list',
        },
    },
}


def get_selectors(version: Optional[str] = None, category: str = "all") -> Dict[str, any]:
    """
    Get selectors for a specific version and category.
    
    Args:
        version: Odoo version (e.g., "14.0", "15.0"). If None, returns base selectors.
        category: Selector category ("menu", "fields", "buttons", "views", "search", "all")
        
    Returns:
        Dictionary of selectors
    """
    result = {}
    
    # Start with base selectors
    if category == "all" or category in BASE_SELECTORS:
        if category == "all":
            result.update(BASE_SELECTORS)
        else:
            result[category] = BASE_SELECTORS[category]
    
    # Add version-specific selectors
    if version and version in VERSION_SELECTORS:
        version_sel = VERSION_SELECTORS[version]
        if category == "all":
            result.update(version_sel)
        elif category in version_sel:
            if category not in result:
                result[category] = {}
            result[category].update(version_sel[category])
    
    return result


def get_selector(version: Optional[str], category: str, key: str, fallback: Optional[str] = None) -> str:
    """
    Get a specific selector with fallback.
    
    Args:
        version: Odoo version
        category: Selector category
        key: Selector key
        fallback: Fallback selector if not found
        
    Returns:
        Selector string
    """
    selectors = get_selectors(version, category)
    
    if category in selectors and key in selectors[category]:
        return selectors[category][key]
    
    # Try base selectors
    if category in BASE_SELECTORS and key in BASE_SELECTORS[category]:
        return BASE_SELECTORS[category][key]
    
    return fallback or f".{key}"


def get_menu_selectors(version: Optional[str] = None) -> Dict[str, str]:
    """Get menu-related selectors."""
    return get_selectors(version, "menu").get("menu", {})


def get_field_selectors(version: Optional[str] = None) -> Dict[str, str]:
    """Get field-related selectors."""
    return get_selectors(version, "fields").get("fields", {})


def get_button_selectors(version: Optional[str] = None) -> Dict[str, str]:
    """Get button-related selectors."""
    return get_selectors(version, "buttons").get("buttons", {})


def get_view_selectors(version: Optional[str] = None) -> Dict[str, str]:
    """Get view-related selectors."""
    return get_selectors(version, "views").get("views", {})


def get_search_selectors(version: Optional[str] = None) -> Dict[str, str]:
    """Get search-related selectors."""
    return get_selectors(version, "search").get("search", {})


def get_selector_list(version: Optional[str], category: str, key: str) -> List[str]:
    """
    Get a list of selectors to try (for fallback strategy).
    
    Args:
        version: Odoo version
        category: Selector category
        key: Selector key
        
    Returns:
        List of selectors to try in order
    """
    selectors = []
    
    # Version-specific first
    if version and version in VERSION_SELECTORS:
        if category in VERSION_SELECTORS[version] and key in VERSION_SELECTORS[version][category]:
            selectors.append(VERSION_SELECTORS[version][category][key])
    
    # Base selectors
    if category in BASE_SELECTORS and key in BASE_SELECTORS[category]:
        base_sel = BASE_SELECTORS[category][key]
        if base_sel not in selectors:
            selectors.append(base_sel)
    
    return selectors if selectors else [f".{key}"]

