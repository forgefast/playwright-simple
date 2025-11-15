#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste completo com gravação de vídeo: Geração e Reprodução de YAML

Este script executa o ciclo completo com gravação de vídeo:
1. Gera YAML através de interação automatizada
2. Reproduz o YAML gerado (com vídeo configurado via YAML)
3. Mostra resultados de ambos os processos
4. Valida que vídeo foi gerado
"""

import asyncio
import sys
import subprocess
import yaml
import re
from pathlib import Path
from typing import List, Dict, Any

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

YAML_PATH = project_root / "test_odoo_v18_with_video.yaml"
VIDEOS_DIR = project_root / "videos"

# Script para gerar YAML (similar ao test_odoo_interactive.py)
GENERATION_SCRIPT = project_root / "test_odoo_interactive.py"


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


def validate_yaml_for_video_config(yaml_path: Path) -> tuple[bool, List[str]]:
    """
    Valida YAML para verificar configuração de vídeo.
    
    Retorna: (is_valid, error_messages)
    """
    errors = []
    
    if not yaml_path.exists():
        return False, ["YAML não existe"]
    
    try:
        with open(yaml_path, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        if not yaml_content:
            return False, ["YAML inválido: arquivo vazio"]
        
        # Verificar se tem config.video
        if 'config' not in yaml_content:
            errors.append("YAML não tem seção 'config'")
        elif 'video' not in yaml_content['config']:
            errors.append("YAML não tem 'config.video'")
        else:
            video_config = yaml_content['config']['video']
            if not video_config.get('enabled', False):
                errors.append("Vídeo não está habilitado (config.video.enabled deve ser true)")
            
            # Verificar qualidade
            quality = video_config.get('quality', 'high')
            if quality not in ['low', 'medium', 'high']:
                errors.append(f"Qualidade de vídeo inválida: {quality}")
            
            # Verificar codec
            codec = video_config.get('codec', 'webm')
            if codec not in ['webm', 'mp4']:
                errors.append(f"Codec de vídeo inválido: {codec}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        return False, [f"Erro ao validar YAML: {e}"]


def validate_video_file(test_name: str) -> tuple[bool, Path]:
    """
    Valida que arquivo de vídeo foi gerado.
    
    Retorna: (video_exists, video_path)
    """
    # Procurar vídeo com nome do teste
    video_extensions = ['.webm', '.mp4']
    
    for ext in video_extensions:
        video_path = VIDEOS_DIR / f"{test_name}{ext}"
        if video_path.exists():
            return True, video_path
    
    # Se não encontrou com nome exato, procurar o mais recente
    if VIDEOS_DIR.exists():
        all_videos = []
        for ext in video_extensions:
            all_videos.extend(list(VIDEOS_DIR.glob(f"*{ext}")))
        
        if all_videos:
            # Pegar o mais recente
            latest_video = max(all_videos, key=lambda p: p.stat().st_mtime)
            return True, latest_video
    
    return False, None


async def run_generation():
    """Executa a geração do YAML via recorder e adiciona configuração básica de vídeo."""
    print_step(1, "GERANDO YAML VIA RECORDER")
    
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
        generated_yaml = project_root / "test_odoo_login_real.yaml"
        
        if generated_yaml.exists():
            print(f"\n✅ YAML gerado: {generated_yaml}")
            print(f"📊 Tamanho: {generated_yaml.stat().st_size} bytes")
            
            # Copiar para nosso YAML
            import shutil
            shutil.copy2(generated_yaml, YAML_PATH)
            print(f"📋 YAML copiado para: {YAML_PATH}")
            
            # Adicionar configuração básica de vídeo
            print(f"\n💡 Adicionando configuração básica de vídeo...")
            add_video_config_to_yaml(YAML_PATH)
            
            # Validar configuração de vídeo
            print(f"\n🔍 Validando configuração de vídeo no YAML...")
            yaml_valid, yaml_errors = validate_yaml_for_video_config(YAML_PATH)
            
            if not yaml_valid:
                print(f"\n⚠️  AVISOS NA CONFIGURAÇÃO DE VÍDEO:")
                for error in yaml_errors:
                    print(f"   {error}")
            else:
                print(f"✅ Configuração de vídeo válida")
            
            return True, yaml_valid
        else:
            print(f"\n❌ YAML não foi gerado!")
            return False, False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  Timeout ao gerar YAML (120s)")
        return False, False
    except Exception as e:
        print(f"\n❌ Erro ao gerar YAML: {e}")
        import traceback
        traceback.print_exc()
        return False, False


def add_video_config_to_yaml(yaml_path: Path):
    """Adiciona configuração básica de vídeo ao YAML se não existir."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
        
        if not yaml_content:
            yaml_content = {}
        
        if 'config' not in yaml_content:
            yaml_content['config'] = {}
        
        # Configuração básica de vídeo
        yaml_content['config']['video'] = {
            'enabled': True,
            'quality': 'high',
            'codec': 'webm',
            'dir': 'videos'
        }
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
        
        print(f"✅ Configuração básica de vídeo adicionada")
    except Exception as e:
        print(f"⚠️  Erro ao adicionar configuração de vídeo: {e}")


async def run_reproduction():
    """Executa a reprodução do YAML com gravação de vídeo."""
    print_step(2, "REPRODUZINDO YAML COM VÍDEO")
    
    if not YAML_PATH.exists():
        print(f"❌ YAML não encontrado: {YAML_PATH}")
        print("   Execute a geração primeiro!")
        return False, False
    
    # Ler nome do teste do YAML
    test_name = "test_odoo_v18_with_video"
    try:
        with open(YAML_PATH, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
            test_name = yaml_content.get('name', test_name)
            # Limpar nome para usar como nome de arquivo
            test_name = test_name.replace(' ', '_').replace('-', '_').lower()
    except Exception as e:
        print(f"⚠️  Erro ao ler nome do teste: {e}")
        pass
    
    # Limpar vídeos antigos do teste
    if VIDEOS_DIR.exists():
        for video_file in VIDEOS_DIR.glob(f"{test_name}.*"):
            try:
                video_file.unlink()
                print(f"🗑️  Removido vídeo anterior: {video_file.name}")
            except:
                pass
    
    # Executar script de reprodução
    print(f"▶️  Executando: python3 test_replay_yaml_with_video.py {YAML_PATH}")
    print(f"📹 Vídeo será gravado em: {VIDEOS_DIR}")
    try:
        result = subprocess.run(
            ["python3", "test_replay_yaml_with_video.py", str(YAML_PATH)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos para permitir gravação de vídeo
        )
        
        # Mostrar saída
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Verificar resultado
        success = result.returncode == 0
        
        # Verificar se vídeo foi gerado
        print(f"\n🔍 Verificando se vídeo foi gerado...")
        video_exists, video_path = validate_video_file(test_name)
        
        if video_exists:
            video_size = video_path.stat().st_size
            video_size_mb = video_size / (1024 * 1024)
            print(f"\n✅ Vídeo gerado com sucesso!")
            print(f"   Arquivo: {video_path}")
            print(f"   Tamanho: {video_size_mb:.2f} MB")
        else:
            print(f"\n⚠️  Vídeo não foi encontrado em: {VIDEOS_DIR}")
            print(f"   Verifique se a configuração de vídeo está correta no YAML")
        
        if success and video_exists:
            print(f"\n✅ Reprodução concluída com sucesso e vídeo gerado!")
            return True, True
        elif success:
            print(f"\n⚠️  Reprodução executou, mas vídeo não foi gerado")
            return True, False
        else:
            print(f"\n❌ Reprodução falhou (código: {result.returncode})")
            return False, False
        
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  Timeout ao reproduzir YAML (300s)")
        return False, False
    except Exception as e:
        print(f"\n❌ Erro ao reproduzir YAML: {e}")
        return False, False


async def main():
    """Executa o ciclo completo com gravação de vídeo."""
    print_section("CICLO COMPLETO COM GRAVAÇÃO DE VÍDEO: GERAÇÃO E REPRODUÇÃO DE YAML")
    
    # Criar diretório de vídeos se não existir
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Passo 1: Gerar YAML
    yaml_exists, gen_success = await run_generation()
    
    if not yaml_exists:
        print("\n❌ Falha na geração. Abortando reprodução.")
        return 1
    
    if not gen_success:
        print("\n⚠️  Geração completou com avisos, mas YAML foi criado. Continuando...")
    
    # Passo 2: Reproduzir YAML com vídeo
    repro_exists, repro_success = await run_reproduction()
    
    if not repro_exists:
        print("\n❌ Falha na reprodução.")
        return 1
    
    # Resumo final
    print_section("RESUMO DO CICLO COMPLETO COM VÍDEO")
    
    print(f"📝 Geração: {'✅ Sucesso' if gen_success else '⚠️  Completou com avisos'}")
    print(f"▶️  Reprodução: {'✅ Sucesso' if repro_success else '❌ Falhou'}")
    
    # Verificar vídeo final
    test_name = "test_odoo_v18_with_video"
    try:
        with open(YAML_PATH, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
            test_name = yaml_content.get('name', test_name)
            test_name = test_name.replace(' ', '_').replace('-', '_').lower()
    except:
        pass
    
    video_exists, video_path = validate_video_file(test_name)
    if video_exists:
        print(f"📹 Vídeo: ✅ Gerado em {video_path}")
    else:
        print(f"📹 Vídeo: ❌ Não foi gerado")
    
    if gen_success and repro_success and video_exists:
        print(f"\n🎉 CICLO COMPLETO COM VÍDEO EXECUTADO COM SUCESSO!")
        print(f"   YAML: {YAML_PATH}")
        print(f"   Vídeo: {video_path}")
        return 0
    else:
        print(f"\n⚠️  CICLO COMPLETO COM PROBLEMAS")
        if not video_exists:
            print(f"   ⚠️  Vídeo não foi gerado - verifique configuração")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

