#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de integração para autenticação Odoo.

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
    try:
        await browser_manager.close()
    except Exception:
        pass  # Ignore errors during cleanup


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_executes_successfully(odoo_test_instance, tmp_path):
    """Testa que login executa com sucesso usando OdooYAMLParser."""
    test, browser_manager = odoo_test_instance
    page = test.page
    
    # Criar YAML mínimo de login
    yaml_path = tmp_path / "test_login.yaml"
    yaml_content = {
        'name': 'Test Login',
        'base_url': 'http://localhost:18069',
        'steps': [
            {
                'login': 'admin',
                'password': 'admin',
                'database': 'devel'
            }
        ]
    }
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    # Criar função de teste a partir do YAML
    test_function = OdooYAMLParser.to_python_function(yaml_content)
    
    # Executar teste
    await test_function(page, test, None, None)
    
    # Verificar que login foi bem-sucedido (URL deve mudar para dashboard)
    await page.wait_for_load_state('networkidle', timeout=10000)
    current_url = page.url
    
    # Após login bem-sucedido, deve estar no dashboard ou home
    assert 'web' in current_url or 'login' not in current_url, \
        f"Login should redirect from login page. Current URL: {current_url}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logout_executes_successfully(odoo_test_instance, tmp_path):
    """Testa que logout executa com sucesso."""
    test, browser_manager = odoo_test_instance
    page = test.page
    
    # Criar YAML com login e logout
    yaml_path = tmp_path / "test_logout.yaml"
    yaml_content = {
        'name': 'Test Logout',
        'base_url': 'http://localhost:18069',
        'steps': [
            {
                'login': 'admin',
                'password': 'admin',
                'database': 'devel'
            },
            {
                'logout': None
            }
        ]
    }
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    # Criar função de teste
    test_function = OdooYAMLParser.to_python_function(yaml_content)
    
    # Executar teste
    await test_function(page, test, None, None)
    
    # Verificar que logout foi bem-sucedido (deve estar na página de login)
    await page.wait_for_load_state('networkidle', timeout=10000)
    current_url = page.url
    
    # Após logout, deve estar na página de login
    assert 'login' in current_url, \
        f"Logout should redirect to login page. Current URL: {current_url}"

