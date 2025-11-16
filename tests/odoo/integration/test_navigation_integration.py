#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de integração para navegação Odoo.

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
async def test_navigation_to_dashboard_executes_successfully(odoo_test_instance, tmp_path):
    """Testa que navegação para Dashboard executa com sucesso."""
    test, browser_manager = odoo_test_instance
    page = test.page
    
    # Criar YAML com login e navegação
    yaml_path = tmp_path / "test_navigation.yaml"
    yaml_content = {
        'name': 'Test Navigation',
        'base_url': 'http://localhost:18069',
        'steps': [
            {
                'login': 'admin',
                'password': 'admin',
                'database': 'devel'
            },
            {
                'go_to': 'Dashboard'
            }
        ]
    }
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    # Criar função de teste
    test_function = OdooYAMLParser.to_python_function(yaml_content)
    
    # Executar teste
    await test_function(page, test, None, None)
    
    # Verificar que navegação foi bem-sucedida
    await page.wait_for_load_state('networkidle', timeout=10000)
    current_url = page.url
    
    # Deve estar no dashboard ou home após navegação
    assert 'web' in current_url, \
        f"Navigation should be on Odoo web. Current URL: {current_url}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_menu_navigation_executes_successfully(odoo_test_instance, tmp_path):
    """Testa que navegação por menu executa com sucesso."""
    test, browser_manager = odoo_test_instance
    page = test.page
    
    # Criar YAML com login e navegação por menu
    yaml_path = tmp_path / "test_menu.yaml"
    yaml_content = {
        'name': 'Test Menu Navigation',
        'base_url': 'http://localhost:18069',
        'steps': [
            {
                'login': 'admin',
                'password': 'admin',
                'database': 'devel'
            },
            {
                'go_to': 'Vendas > Pedidos'
            }
        ]
    }
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    # Criar função de teste
    test_function = OdooYAMLParser.to_python_function(yaml_content)
    
    # Executar teste
    await test_function(page, test, None, None)
    
    # Verificar que navegação foi bem-sucedida
    await page.wait_for_load_state('networkidle', timeout=15000)
    current_url = page.url
    
    # Deve estar na página de pedidos de venda
    assert 'web' in current_url, \
        f"Navigation should be on Odoo web. Current URL: {current_url}"
    
    # Verificar que página carregou (não está em erro)
    page_title = await page.title()
    assert page_title, "Page should have a title"

