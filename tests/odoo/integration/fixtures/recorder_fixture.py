#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixtures para testes de integração com Recorder.

Reaproveita estrutura de test_full_cycle_with_video.py.
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from playwright_simple.core.recorder.recorder import Recorder


@pytest.fixture
def tmp_yaml_path(tmp_path):
    """Cria caminho temporário para YAML."""
    return tmp_path / "test.yaml"


@pytest.fixture
async def recorder_with_login_yaml(tmp_yaml_path):
    """Cria Recorder com YAML mínimo de login."""
    yaml_content = {
        'name': 'Test Login',
        'base_url': 'http://localhost:18069',
        'steps': [
            {
                'action': 'go_to',
                'url': 'http://localhost:18069/web/login'
            },
            {
                'login': 'admin',
                'password': 'admin',
                'database': 'devel'
            }
        ]
    }
    
    with open(tmp_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    recorder = Recorder(
        output_path=tmp_yaml_path,
        initial_url=None,
        headless=True,
        fast_mode=True,
        mode='read'
    )
    
    return recorder, tmp_yaml_path


@pytest.fixture
async def recorder_with_navigation_yaml(tmp_yaml_path):
    """Cria Recorder com YAML de navegação."""
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
    
    with open(tmp_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    recorder = Recorder(
        output_path=tmp_yaml_path,
        initial_url=None,
        headless=True,
        fast_mode=True,
        mode='read'
    )
    
    return recorder, tmp_yaml_path


@pytest.fixture
async def recorder_with_fill_yaml(tmp_yaml_path):
    """Cria Recorder com YAML de preenchimento."""
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
    
    with open(tmp_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    recorder = Recorder(
        output_path=tmp_yaml_path,
        initial_url=None,
        headless=True,
        fast_mode=True,
        mode='read'
    )
    
    return recorder, tmp_yaml_path

