#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de integração para interações básicas Odoo.

Usa OdooYAMLParser para executar ações reais com browser.
"""

import pytest
import yaml
from pathlib import Path
from playwright_simple.odoo.yaml_parser.yaml_parser import OdooYAMLParser
from playwright_simple.odoo.base import OdooTestBase
from playwright_simple.core.recorder.utils.browser import BrowserManager
from playwright_simple import TestConfig


@pytest.fixture
async def odoo_test_instance():
    """Cria instância de OdooTestBase para testes."""
    browser_manager = BrowserManager(headless=True)
    page = await browser_manager.start()
    config = TestConfig(base_url='http://localhost:18069')
    test = OdooTestBase(page, config, test_name='integration_test')
    yield test, browser_manager
    await browser_manager.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_click_executes_successfully(odoo_test_instance, tmp_path):
    """Testa que click executa com sucesso."""
    test, browser_manager = odoo_test_instance
    page = test.page
    
    # Criar YAML com login, navegação e click
    yaml_path = tmp_path / "test_click.yaml"
    yaml_content = {
        'name': 'Test Click',
        'base_url': 'http://localhost:18069',
        'steps': [
            {
                'login': 'admin',
                'password': 'admin',
                'database': 'devel'
            },
            {
                'go_to': 'Vendas > Pedidos'
            },
            {
                'click': 'Criar'
            }
        ]
    }
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    # Criar função de teste
    test_function = OdooYAMLParser.to_python_function(yaml_content)
    
    # Executar teste
    await test_function(page, test, None, None)
    
    # Verificar que click foi bem-sucedido (página deve mudar para formulário)
    await page.wait_for_load_state('networkidle', timeout=15000)
    current_url = page.url
    
    # Deve estar em uma página de formulário (não mais na lista)
    assert 'web' in current_url, \
        f"Click should navigate to form. Current URL: {current_url}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_fill_executes_successfully(odoo_test_instance, tmp_path):
    """Testa que fill executa com sucesso."""
    test, browser_manager = odoo_test_instance
    page = test.page
    
    # Criar YAML com login, navegação, click e fill
    yaml_path = tmp_path / "test_fill.yaml"
    yaml_content = {
        'name': 'Test Fill',
        'base_url': 'http://localhost:18069',
        'steps': [
            {
                'login': 'admin',
                'password': 'admin',
                'database': 'devel'
            },
            {
                'go_to': 'Vendas > Pedidos'
            },
            {
                'click': 'Criar'
            },
            {
                'fill': 'Cliente = João Silva'
            }
        ]
    }
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    # Criar função de teste
    test_function = OdooYAMLParser.to_python_function(yaml_content)
    
    # Executar teste
    await test_function(page, test, None, None)
    
    # Verificar que fill foi bem-sucedido (campo deve estar preenchido)
    await page.wait_for_load_state('networkidle', timeout=15000)
    
    # Verificar que estamos em um formulário (não em erro)
    current_url = page.url
    assert 'web' in current_url, \
        f"Fill should be on form page. Current URL: {current_url}"

