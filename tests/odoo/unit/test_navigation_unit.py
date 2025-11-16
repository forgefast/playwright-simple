#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes unitários para navegação Odoo.

Testa métodos isolados sem browser real usando mocks.
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
async def test_go_to_accepts_menu_path(mock_odoo_test_base):
    """Testa que go_to() aceita menu path como string."""
    test, page = mock_odoo_test_base
    
    # Mock menu.go_to_menu para retornar True
    test.menu = MagicMock()
    test.menu.go_to_menu = AsyncMock(return_value=True)
    
    # Executar go_to com menu path
    result = await test.go_to("Vendas > Pedidos")
    
    # Verificar que retorna self
    assert result is test, "go_to() should return self for chaining"


@pytest.mark.asyncio
async def test_go_to_accepts_url(mock_odoo_test_base):
    """Testa que go_to() aceita URL."""
    test, page = mock_odoo_test_base
    
    # Mock go_to do SimpleTestBase (super().go_to)
    test._simple_go_to = AsyncMock()
    
    # Mock page.locator para não encontrar link
    page.locator = Mock(return_value=MagicMock())
    page.locator.return_value.first = MagicMock()
    page.locator.return_value.first.count = AsyncMock(return_value=0)
    
    # Mock super().go_to usando patch
    from unittest.mock import patch
    with patch('playwright_simple.odoo.base.SimpleTestBase.go_to', new_callable=AsyncMock) as mock_super_go_to:
        result = await test.go_to("http://localhost:18069/web")
        assert result is test, "go_to() should return self for chaining"


@pytest.mark.asyncio
async def test_go_to_menu_method_exists(mock_odoo_test_base):
    """Testa que go_to_menu() existe e é callable."""
    test, page = mock_odoo_test_base
    
    assert hasattr(test, 'go_to_menu')
    assert callable(test.go_to_menu)


@pytest.mark.asyncio
async def test_go_to_dashboard_method_exists(mock_odoo_test_base):
    """Testa que go_to_dashboard() existe e é callable."""
    test, page = mock_odoo_test_base
    
    assert hasattr(test, 'go_to_dashboard')
    assert callable(test.go_to_dashboard)


@pytest.mark.asyncio
async def test_go_to_returns_self_for_chaining(mock_odoo_test_base):
    """Testa que go_to() retorna self para method chaining."""
    test, page = mock_odoo_test_base
    
    # Mock menu para evitar erro
    test.menu = MagicMock()
    test.menu.go_to_dashboard = AsyncMock(return_value=True)
    
    result = await test.go_to("Dashboard")
    assert result is test, "go_to() should return self for chaining"

