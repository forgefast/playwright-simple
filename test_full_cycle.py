#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste completo: Geração e Reprodução de YAML

Este script executa o ciclo completo:
1. Gera YAML através de interação automatizada
2. Reproduz o YAML gerado
3. Mostra resultados de ambos os processos
"""

import asyncio
import sys
import subprocess
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

YAML_PATH = project_root / "test_odoo_login_real.yaml"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step_num: int, description: str):
    """Print a formatted step."""
    print(f"\n{'─' * 80}")
    print(f"  PASSO {step_num}: {description}")
    print(f"{'─' * 80}\n")


async def run_generation():
    """Executa a geração do YAML."""
    print_step(1, "GERANDO YAML")
    
    # Limpar YAML anterior se existir
    if YAML_PATH.exists():
        print(f"🗑️  Removendo YAML anterior: {YAML_PATH}")
        YAML_PATH.unlink()
    
    # Executar script de geração
    print(f"▶️  Executando: python3 test_odoo_interactive.py")
    try:
        result = subprocess.run(
            ["python3", "test_odoo_interactive.py"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Mostrar saída
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Verificar se YAML foi gerado
        if YAML_PATH.exists():
            print(f"\n✅ YAML gerado com sucesso: {YAML_PATH}")
            print(f"📊 Tamanho: {YAML_PATH.stat().st_size} bytes")
            
            # Mostrar conteúdo do YAML
            print(f"\n📄 Conteúdo do YAML gerado:")
            print("─" * 80)
            with open(YAML_PATH, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:50], 1):  # Primeiras 50 linhas
                    print(f"  {i:3d}: {line.rstrip()}")
                if len(lines) > 50:
                    print(f"  ... ({len(lines) - 50} linhas restantes)")
            print("─" * 80)
            
            return True, result.returncode == 0
        else:
            print(f"\n❌ YAML não foi gerado!")
            return False, False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  Timeout ao gerar YAML (120s)")
        return False, False
    except Exception as e:
        print(f"\n❌ Erro ao gerar YAML: {e}")
        return False, False


async def run_reproduction():
    """Executa a reprodução do YAML."""
    print_step(2, "REPRODUZINDO YAML")
    
    if not YAML_PATH.exists():
        print(f"❌ YAML não encontrado: {YAML_PATH}")
        print("   Execute a geração primeiro!")
        return False, False
    
    # Executar script de reprodução
    print(f"▶️  Executando: python3 test_replay_yaml.py")
    try:
        result = subprocess.run(
            ["python3", "test_replay_yaml.py"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Mostrar saída
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Verificar resultado
        success = result.returncode == 0
        
        if success:
            print(f"\n✅ Reprodução concluída com sucesso!")
        else:
            print(f"\n❌ Reprodução falhou (código: {result.returncode})")
        
        return True, success
        
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  Timeout ao reproduzir YAML (120s)")
        return False, False
    except Exception as e:
        print(f"\n❌ Erro ao reproduzir YAML: {e}")
        return False, False


async def main():
    """Executa o ciclo completo."""
    print_section("CICLO COMPLETO: GERAÇÃO E REPRODUÇÃO DE YAML")
    
    # Passo 1: Gerar YAML
    yaml_exists, gen_success = await run_generation()
    
    if not yaml_exists:
        print("\n❌ Falha na geração. Abortando reprodução.")
        return 1
    
    if not gen_success:
        print("\n⚠️  Geração completou com avisos, mas YAML foi criado. Continuando...")
    
    # Passo 2: Reproduzir YAML
    repro_exists, repro_success = await run_reproduction()
    
    if not repro_exists:
        print("\n❌ Falha na reprodução.")
        return 1
    
    # Resumo final
    print_section("RESUMO DO CICLO COMPLETO")
    
    print(f"📝 Geração: {'✅ Sucesso' if gen_success else '⚠️  Completou com avisos'}")
    print(f"▶️  Reprodução: {'✅ Sucesso' if repro_success else '❌ Falhou'}")
    
    if gen_success and repro_success:
        print(f"\n🎉 CICLO COMPLETO EXECUTADO COM SUCESSO!")
        print(f"   YAML: {YAML_PATH}")
        return 0
    else:
        print(f"\n⚠️  CICLO COMPLETO COM PROBLEMAS")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

