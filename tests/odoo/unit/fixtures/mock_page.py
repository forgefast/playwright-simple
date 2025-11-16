#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixtures reutilizáveis para testes unitários Odoo.

Fornece mocks de Page e elementos Odoo para testes rápidos.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from playwright.async_api import Page
from playwright_simple.odoo import OdooTestBase
from playwright_simple import TestConfig


@pytest.fixture
def mock_page():
    """Cria um mock de Page com estrutura Odoo básica."""
    page = MagicMock(spec=Page)
    
    # Configurar locator básico
    locator_mock = MagicMock()
    locator_mock.count = AsyncMock(return_value=1)
    locator_mock.is_visible = AsyncMock(return_value=True)
    locator_mock.first = locator_mock
    locator_mock.nth = Mock(return_value=locator_mock)
    locator_mock.input_value = AsyncMock(return_value="")
    locator_mock.click = AsyncMock()
    locator_mock.fill = AsyncMock()
    locator_mock.type = AsyncMock()
    locator_mock.press = AsyncMock()
    locator_mock.bounding_box = AsyncMock(return_value={'x': 100, 'y': 100, 'width': 50, 'height': 30})
    locator_mock.get_attribute = AsyncMock(return_value=None)
    locator_mock.text_content = AsyncMock(return_value="")
    locator_mock.evaluate = AsyncMock(return_value="")
    locator_mock.wait_for = AsyncMock()
    
    page.locator = Mock(return_value=locator_mock)
    page.url = "http://localhost:18069/web/login"
    page.title = AsyncMock(return_value="Login - Odoo")
    page.wait_for_load_state = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.wait_for_function = AsyncMock()
    
    return page


@pytest.fixture
def mock_odoo_login_page(mock_page):
    """Cria mock de página de login Odoo."""
    # Configurar elementos de login
    login_input = MagicMock()
    login_input.count = AsyncMock(return_value=1)
    login_input.is_visible = AsyncMock(return_value=True)
    login_input.input_value = AsyncMock(return_value="")
    login_input.fill = AsyncMock()
    
    password_input = MagicMock()
    password_input.count = AsyncMock(return_value=1)
    password_input.is_visible = AsyncMock(return_value=True)
    password_input.input_value = AsyncMock(return_value="")
    password_input.fill = AsyncMock()
    
    submit_button = MagicMock()
    submit_button.count = AsyncMock(return_value=1)
    submit_button.is_visible = AsyncMock(return_value=True)
    submit_button.click = AsyncMock()
    submit_button.bounding_box = AsyncMock(return_value={'x': 200, 'y': 200, 'width': 100, 'height': 40})
    submit_button.get_attribute = AsyncMock(return_value="submit")
    submit_button.text_content = AsyncMock(return_value="Entrar")
    
    def locator_side_effect(selector):
        loc = MagicMock()
        loc.count = AsyncMock(return_value=1)
        loc.is_visible = AsyncMock(return_value=True)
        loc.first = loc
        loc.input_value = AsyncMock(return_value="")
        loc.fill = AsyncMock()
        loc.click = AsyncMock()
        loc.bounding_box = AsyncMock(return_value={'x': 100, 'y': 100, 'width': 50, 'height': 30})
        loc.get_attribute = AsyncMock(return_value=None)
        loc.text_content = AsyncMock(return_value="")
        
        if 'name="login"' in selector or 'login' in selector.lower():
            loc.input_value = AsyncMock(return_value="admin")
            return loc
        elif 'name="password"' in selector or 'password' in selector.lower():
            loc.input_value = AsyncMock(return_value="")
            return loc
        elif 'name="db"' in selector or 'db' in selector.lower():
            loc.count = AsyncMock(return_value=0)  # Database field may not exist
            return loc
        elif 'submit' in selector.lower() or 'button[type="submit"]' in selector:
            return submit_button
        return loc
    
    mock_page.locator = Mock(side_effect=locator_side_effect)
    mock_page.url = "http://localhost:18069/web/login"
    
    return mock_page


@pytest.fixture
def mock_odoo_test_base(mock_page):
    """Cria instância de OdooTestBase com page mockada."""
    config = TestConfig(base_url="http://localhost:18069")
    
    # Mock cursor_manager (será injetado após inicialização)
    cursor_manager = MagicMock()
    cursor_manager.move_to = AsyncMock()
    cursor_manager.show_click_effect = AsyncMock()
    cursor_manager._ensure_cursor_exists = AsyncMock()
    
    # Criar OdooTestBase (OdooTestBase aceita cursor_manager, mas SimpleTestBase não)
    # Então não passamos cursor_manager no __init__, injetamos depois
    test = OdooTestBase(
        mock_page,
        config,
        cursor_manager=cursor_manager  # OdooTestBase aceita e gerencia internamente
    )
    
    return test, mock_page


@pytest.fixture
def mock_odoo_form_page(mock_page):
    """Cria mock de página de formulário Odoo."""
    # Configurar elementos de formulário
    field_input = MagicMock()
    field_input.count = AsyncMock(return_value=1)
    field_input.is_visible = AsyncMock(return_value=True)
    field_input.input_value = AsyncMock(return_value="")
    field_input.fill = AsyncMock()
    
    button = MagicMock()
    button.count = AsyncMock(return_value=1)
    button.is_visible = AsyncMock(return_value=True)
    button.click = AsyncMock()
    button.text_content = AsyncMock(return_value="Salvar")
    button.bounding_box = AsyncMock(return_value={'x': 300, 'y': 300, 'width': 80, 'height': 35})
    
    def locator_side_effect(selector):
        loc = MagicMock()
        loc.count = AsyncMock(return_value=1)
        loc.is_visible = AsyncMock(return_value=True)
        loc.first = loc
        loc.input_value = AsyncMock(return_value="")
        loc.fill = AsyncMock()
        loc.click = AsyncMock()
        loc.bounding_box = AsyncMock(return_value={'x': 100, 'y': 100, 'width': 200, 'height': 30})
        loc.text_content = AsyncMock(return_value="")
        
        if 'button' in selector.lower():
            return button
        return field_input
    
    mock_page.locator = Mock(side_effect=locator_side_effect)
    mock_page.url = "http://localhost:18069/web#id=1&model=sale.order&view_type=form"
    
    return mock_page

