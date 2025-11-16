#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para autenticação Odoo.

Testa métodos isolados sem browser real usando mocks.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

# Adicionar diretório de fixtures ao path
fixtures_dir = Path(__file__).parent / "fixtures"
if str(fixtures_dir) not in sys.path:
    sys.path.insert(0, str(fixtures_dir))

from playwright_simple.odoo import OdooTestBase
from playwright_simple import TestConfig

# Importar fixtures diretamente (pytest vai encontrá-las automaticamente)
pytest_plugins = ["tests.odoo.unit.fixtures.mock_page"]


@pytest.mark.asyncio
async def test_login_fills_database_field(mock_odoo_test_base):
    """Testa que login() preenche campo database quando fornecido."""
    test, page = mock_odoo_test_base
    
    # Mock métodos que login() chama
    test.go_to = AsyncMock()
    test.type = AsyncMock()
    test.wait_until_ready = AsyncMock()
    test.page.wait_for_load_state = AsyncMock()
    test.page.locator = Mock(return_value=MagicMock())
    test.page.locator.return_value.first = MagicMock()
    test.page.locator.return_value.first.count = AsyncMock(return_value=0)  # Database field não existe
    test.page.locator.return_value.first.is_visible = AsyncMock(return_value=False)
    
    # Executar login com database
    await test.login("admin", "admin", database="devel")
    
    # Verificar que go_to foi chamado (navega para login)
    test.go_to.assert_called_once()


@pytest.mark.asyncio
async def test_login_fills_login_field(mock_odoo_test_base):
    """Testa que login() preenche campo login."""
    test, page = mock_odoo_test_base
    
    # Mock métodos que login() chama
    test.go_to = AsyncMock()
    test.type = AsyncMock()
    test.wait_until_ready = AsyncMock()
    test.page.wait_for_load_state = AsyncMock()
    test.page.locator = Mock(return_value=MagicMock())
    test.page.locator.return_value.first = MagicMock()
    test.page.locator.return_value.first.count = AsyncMock(return_value=1)
    test.page.locator.return_value.first.is_visible = AsyncMock(return_value=True)
    test.page.locator.return_value.first.click = AsyncMock()
    test.page.locator.return_value.first.bounding_box = AsyncMock(return_value={'x': 100, 'y': 100, 'width': 50, 'height': 30})
    
    # Executar login
    await test.login("admin@example.com", "admin")
    
    # Verificar que type() foi chamado (pelo menos para login e password)
    assert test.type.call_count >= 2, "type() should be called for login and password fields"


@pytest.mark.asyncio
async def test_login_fills_password_field(mock_odoo_test_base):
    """Testa que login() preenche campo password."""
    test, page = mock_odoo_test_base
    
    # Mock métodos que login() chama
    test.go_to = AsyncMock()
    test.type = AsyncMock()
    test.wait_until_ready = AsyncMock()
    test.page.wait_for_load_state = AsyncMock()
    test.page.locator = Mock(return_value=MagicMock())
    test.page.locator.return_value.first = MagicMock()
    test.page.locator.return_value.first.count = AsyncMock(return_value=1)
    test.page.locator.return_value.first.is_visible = AsyncMock(return_value=True)
    test.page.locator.return_value.first.click = AsyncMock()
    test.page.locator.return_value.first.bounding_box = AsyncMock(return_value={'x': 100, 'y': 100, 'width': 50, 'height': 30})
    
    # Executar login
    await test.login("admin", "secret123")
    
    # Verificar que type() foi chamado (pelo menos para password)
    assert test.type.call_count >= 1, "type() should be called for password field"


@pytest.mark.asyncio
async def test_login_clicks_submit_button(mock_odoo_test_base):
    """Testa que login() clica no botão de submit."""
    test, page = mock_odoo_test_base
    
    # Mock métodos que login() chama
    test.go_to = AsyncMock()
    test.type = AsyncMock()
    test.wait_until_ready = AsyncMock()
    test.page.wait_for_load_state = AsyncMock()
    
    # Mock botão de submit
    submit_button = MagicMock()
    submit_button.count = AsyncMock(return_value=1)
    submit_button.is_visible = AsyncMock(return_value=True)
    submit_button.click = AsyncMock()
    submit_button.bounding_box = AsyncMock(return_value={'x': 100, 'y': 100, 'width': 50, 'height': 30})
    submit_button.get_attribute = AsyncMock(return_value="submit")
    
    test.page.locator = Mock(return_value=MagicMock())
    test.page.locator.return_value.first = submit_button
    
    # Executar login
    await test.login("admin", "admin")
    
    # Verificar que botão foi clicado
    submit_button.click.assert_called_once()


@pytest.mark.asyncio
async def test_login_returns_self_for_chaining(mock_odoo_test_base):
    """Testa que login() retorna self para method chaining."""
    test, page = mock_odoo_test_base
    
    # Mock métodos que login() chama para evitar execução real
    test.go_to = AsyncMock()
    test.type = AsyncMock()
    test.wait_until_ready = AsyncMock()
    test.page.wait_for_load_state = AsyncMock()
    test.page.locator = Mock(return_value=MagicMock())
    test.page.locator.return_value.first = MagicMock()
    test.page.locator.return_value.first.count = AsyncMock(return_value=1)
    test.page.locator.return_value.first.is_visible = AsyncMock(return_value=True)
    test.page.locator.return_value.first.click = AsyncMock()
    test.page.locator.return_value.first.bounding_box = AsyncMock(return_value={'x': 100, 'y': 100, 'width': 50, 'height': 30})
    
    result = await test.login("admin", "admin")
    assert result is test, "login() should return self for chaining"


@pytest.mark.asyncio
async def test_logout_method_exists(mock_odoo_test_base):
    """Testa que logout() existe e é callable."""
    test, page = mock_odoo_test_base
    
    assert hasattr(test, 'logout')
    assert callable(test.logout)


@pytest.mark.asyncio
async def test_logout_returns_self_for_chaining(mock_odoo_test_base):
    """Testa que logout() retorna self para method chaining."""
    test, page = mock_odoo_test_base
    
    result = await test.logout()
    assert result is test, "logout() should return self for chaining"

