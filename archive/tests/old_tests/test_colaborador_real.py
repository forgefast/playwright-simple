#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar o teste real de colaborador_portal.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar paths
sys.path.insert(0, str(Path(__file__).parent))
presentation_path = Path("/home/gabriel/softhill/presentation/playwright")
if presentation_path.exists():
    sys.path.insert(0, str(presentation_path))

from playwright_simple import TestRunner
from playwright_simple.odoo import OdooYAMLParser

# Tentar importar racco_config, se não existir usar config padrão
try:
    from racco_config import get_racco_config
    USE_RACCO_CONFIG = True
except ImportError:
    USE_RACCO_CONFIG = False
    from playwright_simple import TestConfig


async def main():
    """Executa o teste real de colaborador_portal."""
    print("🚀 Executando teste real: Colaborador Portal")
    print()
    
    # Carregar configuração
    if USE_RACCO_CONFIG:
        config = get_racco_config()
        print("✅ Configuração Racco carregada")
    else:
        config = TestConfig.load(
            base_url="http://localhost:8069",
            video_enabled=True,
            video_quality="high",
            video_subtitles=True,
            browser_headless=True,
            browser_slow_mo=100,
        )
        print("⚠️  Usando configuração padrão (racco_config não encontrado)")
    
    # Carregar teste YAML
    yaml_path = presentation_path / "tests/yaml/test_colaborador_portal.yaml"
    
    if not yaml_path.exists():
        print(f"❌ Arquivo não encontrado: {yaml_path}")
        return
    
    print(f"📄 Carregando: {yaml_path}")
    
    try:
        # Parse YAML
        yaml_data = OdooYAMLParser.parse_file(yaml_path)
        print(f"   ✅ YAML parseado: {yaml_data.get('name', 'N/A')}")
        
        # Converter para função Python
        test_function = OdooYAMLParser.to_python_function(yaml_data)
        print(f"   ✅ Função Python criada")
        
        # Criar runner
        runner = TestRunner(config=config)
        
        # Executar teste
        test_name = "Colaborador Portal"
        print(f"\n🎬 Executando teste: {test_name}")
        print()
        
        result = await runner.run_test(test_name, test_function)
        
        # Verificar resultado
        if result.get("status") == "passed":
            print(f"\n✅ Teste passou!")
        else:
            print(f"\n❌ Teste falhou: {result.get('error', 'Erro desconhecido')}")
        
        # Verificar vídeo
        video_path = result.get("video_path")
        if video_path:
            video_path = Path(video_path)
            if video_path.exists():
                import subprocess
                # Verificar duração
                dur_result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if dur_result.returncode == 0:
                    duration = float(dur_result.stdout.strip())
                    print(f"\n📹 Vídeo gerado: {video_path.name}")
                    print(f"   ⏱️  Duração: {duration:.2f} segundos")
                    print(f"   📁 Caminho: {video_path}")
                    
                    # Abrir no VLC
                    try:
                        subprocess.Popen(
                            ["vlc", str(video_path)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        print(f"   ✅ Vídeo aberto no VLC")
                    except FileNotFoundError:
                        print(f"   ⚠️  VLC não encontrado. Abra manualmente: {video_path}")
                else:
                    print(f"   ⚠️  Não foi possível verificar duração")
            else:
                print(f"   ⚠️  Vídeo não encontrado: {video_path}")
        else:
            print(f"   ⚠️  Nenhum vídeo gerado")
        
    except Exception as e:
        print(f"❌ Erro ao executar teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

