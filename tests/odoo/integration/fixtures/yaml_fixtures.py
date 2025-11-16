#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAMLs mínimos reutilizáveis para testes de integração.

Fornece YAMLs prontos para diferentes cenários de teste.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def create_login_yaml(output_path: Path) -> Dict[str, Any]:
    """Cria YAML mínimo para teste de login."""
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
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    return yaml_content


def create_navigation_yaml(output_path: Path) -> Dict[str, Any]:
    """Cria YAML mínimo para teste de navegação."""
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
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    return yaml_content


def create_fill_yaml(output_path: Path) -> Dict[str, Any]:
    """Cria YAML mínimo para teste de preenchimento."""
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
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    return yaml_content


def create_click_yaml(output_path: Path) -> Dict[str, Any]:
    """Cria YAML mínimo para teste de clique."""
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
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
    
    return yaml_content

