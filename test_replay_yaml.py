#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar/reproduzir um teste YAML gerado.
"""

import asyncio
from pathlib import Path
from playwright_simple.core.yaml_parser import YAMLParser
from playwright_simple.core.runner.test_runner import TestRunner
from playwright_simple.core.config import TestConfig

async def replay_yaml(yaml_path: Path):
    """Reproduzir um teste YAML."""
    print(f"📄 Carregando YAML: {yaml_path}")
    
    # Carregar teste do YAML
    test_name, test_func = YAMLParser.load_test(yaml_path)
    print(f"✅ Teste carregado: {test_name}")
    
    # Criar configuração
    config = TestConfig(
        base_url="http://localhost:18069",
        headless=False,
        step_fast_mode=True  # Usar fast mode na reprodução também
    )
    
    # Criar runner
    runner = TestRunner(config=config)
    
    # Executar teste
    print(f"▶️  Executando teste...")
    result = await runner.run_test(test_name, test_func)
    
    print(f"✅ Teste concluído!")
    return result

if __name__ == '__main__':
    yaml_path = Path('test_odoo_login_real.yaml')
    if not yaml_path.exists():
        print(f"❌ YAML não encontrado: {yaml_path}")
        exit(1)
    
    asyncio.run(replay_yaml(yaml_path))

