#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar/reproduzir um teste YAML gerado com gravação de vídeo.
"""

import asyncio
import logging
import sys
from pathlib import Path
from playwright_simple.core.recorder.recorder import Recorder

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


async def replay_yaml(yaml_path: Path):
    """Reproduzir um teste YAML usando Recorder diretamente com vídeo."""
    logger.info(f"Iniciando replay do YAML: {yaml_path}")
    print(f"📄 Carregando YAML: {yaml_path}")
    
    # Criar Recorder em modo read (vai ler configuração de vídeo do YAML)
    logger.info("Criando Recorder em modo read...")
    recorder = Recorder(
        output_path=yaml_path,  # Input YAML file
        initial_url=None,  # Will be read from YAML
        headless=False,
        debug=False,
        fast_mode=True,  # Usar fast mode na reprodução
        mode='read'  # Read mode: import YAML instead of export
    )
    logger.info("Recorder criado")
    
    # Executar teste (Recorder vai ler YAML, configurar vídeo e executar steps)
    print(f"▶️  Executando teste com gravação de vídeo...")
    logger.info("Iniciando execução do teste...")
    try:
        await recorder.start()
        logger.info("Teste executado com sucesso")
        print(f"✅ Teste concluído!")
        return {'success': True}
    except Exception as e:
        logger.error(f"Erro ao executar teste: {e}", exc_info=True)
        print(f"❌ Erro ao executar teste: {e}")
        raise
    finally:
        # Sempre limpar processos órfãos, mesmo em caso de erro
        try:
            from playwright_simple.core.recorder.command_server import cleanup_old_sessions
            cleaned = cleanup_old_sessions(force=True, timeout=5.0)
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} orphan browser process(es) after test")
                print(f"🧹 Limpeza: {cleaned} processo(s) órfão(s) removido(s)")
        except Exception as e:
            logger.debug(f"Error cleaning up orphan processes: {e}")


if __name__ == '__main__':
    # Aceitar YAML como argumento ou usar padrão
    if len(sys.argv) > 1:
        yaml_path = Path(sys.argv[1])
    else:
        yaml_path = Path('test_odoo_v18_with_video.yaml')
    
    if not yaml_path.exists():
        print(f"❌ YAML não encontrado: {yaml_path}")
        print(f"   Uso: python3 {sys.argv[0]} [caminho_do_yaml]")
        exit(1)
    
    # Limpar processos órfãos antes de iniciar
    try:
        from playwright_simple.core.recorder.command_server import cleanup_old_sessions
        cleaned = cleanup_old_sessions(force=True, timeout=5.0)
        if cleaned > 0:
            print(f"🧹 Limpeza inicial: {cleaned} processo(s) órfão(s) removido(s)")
    except Exception as e:
        logger.debug(f"Error cleaning up orphan processes before test: {e}")
    
    # Timeout aumentado para permitir gravação de vídeo (5 minutos)
    try:
        asyncio.run(asyncio.wait_for(replay_yaml(yaml_path), timeout=300.0))
    except asyncio.TimeoutError:
        print("❌ Timeout: O teste demorou mais de 5 minutos")
        # Limpar processos órfãos mesmo em caso de timeout
        try:
            from playwright_simple.core.recorder.command_server import cleanup_old_sessions
            cleanup_old_sessions(force=True, timeout=5.0)
        except:
            pass
        exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        # Limpar processos órfãos mesmo em caso de interrupção
        try:
            from playwright_simple.core.recorder.command_server import cleanup_old_sessions
            cleanup_old_sessions(force=True, timeout=5.0)
        except:
            pass
        exit(1)

