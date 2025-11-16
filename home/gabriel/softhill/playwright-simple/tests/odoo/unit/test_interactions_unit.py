#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para interações básicas Odoo.

Testa click, fill, type isoladamente usando mocks.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Adicionar diretório de fixtures ao path
fixtures_dir = Path(__file__).parent / "fixtures"
if str(fixtures_dir) not in sys.path:
    sys.path.insert(0, str(fixtures_dir))

from playwright_simple.odoo import OdooTestBase
from playwright_simple import TestConfig

# Importar fixtures diretamente (pytest vai encontrá-las automaticamente)
pytest_plugins = ["tests.odoo.unit.fixtures.mock_page"]


@pytest.mark.asyncio
async def test_click_method_exists(mock_odoo_test_base):
    """Testa que click() existe e é callable."""
    test, page = mock_odoo_test_base
    
    assert hasattr(test, 'click')
    assert callable(test.click)


@pytest.mark.asyncio
async def test_click_returns_self_for_chaining(mock_odoo_test_base):
    """Testa que click() retorna self para method chaining."""
    test, page = mock_odoo_test_base
    
    # Mock click_button (que será chamado quando não for CSS selector)
    test.click_button = AsyncMock(return_value=test)
    
    # "Criar" não é CSS selector, então chama click_button
    result = await test.click("Criar")
    assert result is test, "click() should return self for chaining"
    test.click_button.assert_called_once_with("Criar", None)


@pytest.mark.asyncio
async def test_fill_method_exists(mock_odoo_test_base):
    """Testa que fill() existe e é callable."""
    test, page = mock_odoo_test_base
    
    assert hasattr(test, 'fill')
    assert callable(test.fill)


@pytest.mark.asyncio
async def test_fill_with_separate_args(mock_odoo_test_base):
    """Testa que fill() funciona com argumentos separados."""
    test, page = mock_odoo_test_base
    
    # Mock field helper
    mock_field = MagicMock()
    mock_field.fill_field = AsyncMock()
    
    # Mock property field para retornar mock_field
    type(test).field = property(lambda self: mock_field)
    
    result = await test.fill("Cliente", "João Silva")
    assert result is test, "fill() should return self for chaining"
    
    # Verificar que field.fill_field foi chamado
    mock_field.fill_field.assert_called_once_with("Cliente", "João Silva", None)


@pytest.mark.asyncio
async def test_fill_with_assignment_syntax(mock_odoo_test_base):
    """Testa que fill() funciona com sintaxe de atribuição."""
    test, page = mock_odoo_test_base
    
    # Mock field helper
    mock_field = MagicMock()
    mock_field.fill_field = AsyncMock()
    
    # Mock property field para retornar mock_field
    type(test).field = property(lambda self: mock_field)
    
    result = await test.fill("Cliente = João Silva")
    assert result is test, "fill() should return self for chaining"
    
    # Verificar que field.fill_field foi chamado com valores parseados
    mock_field.fill_field.assert_called_once()
    # Verificar que foi chamado com "Cliente" e "João Silva"
    call_args = mock_field.fill_field.call_args[0]
    assert call_args[0] == "Cliente"
    assert call_args[1] == "João Silva"


@pytest.mark.asyncio
async def test_click_button_method_exists(mock_odoo_test_base):
    """Testa que click_button() existe e é callable."""
    test, page = mock_odoo_test_base
    
    assert hasattr(test, 'click_button')
    assert callable(test.click_button)


@pytest.mark.asyncio
async def test_click_button_returns_self_for_chaining(mock_odoo_test_base):
    """Testa que click_button() retorna self para method chaining."""
    test, page = mock_odoo_test_base
    
    # Mock wizard e page.locator para click_button funcionar
    test.wizard = MagicMock()
    test.wizard.is_visible = AsyncMock(return_value=False)
    
    # Mock page.locator para encontrar botão
    button_locator = MagicMock()
    button_locator.count = AsyncMock(return_value=1)
    button_locator.is_visible = AsyncMock(return_value=True)
    button_locator.bounding_box = AsyncMock(return_value={'x': 100, 'y': 100, 'width': 50, 'height': 30})
    button_locator.click = AsyncMock()
    
    page.locator = Mock(return_value=button_locator)
    
    # Mock cursor_manager
    test.cursor_manager = MagicMock()
    test.cursor_manager.move_to = AsyncMock()
    test.cursor_manager.show_click_effect = AsyncMock()
    
    result = await test.click_button("Salvar")
    assert result is test, "click_button() should return self for chaining"

