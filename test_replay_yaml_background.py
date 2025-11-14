#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar/reproduzir um teste YAML gerado em background.
Permite interação via CLI durante a execução.
"""
import asyncio
import logging
from pathlib import Path
from playwright_simple.core.yaml_parser import YAMLParser
from playwright_simple.core.runner.test_runner import TestRunner
from playwright_simple.core.config import TestConfig

# Configurar logging em modo DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

# Habilitar logs debug para módulos específicos
logging.getLogger('playwright_simple.core.yaml_executor').setLevel(logging.DEBUG)
logging.getLogger('playwright_simple.core.yaml_actions').setLevel(logging.DEBUG)
logging.getLogger('playwright_simple.core.runner').setLevel(logging.DEBUG)
logging.getLogger('playwright_simple.core.base').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

async def replay_yaml_background(yaml_path: Path):
    """Reproduzir um teste YAML em background, mantendo o processo rodando."""
    logger.debug(f"Iniciando replay do YAML: {yaml_path}")
    print(f"📄 Carregando YAML: {yaml_path}")
    
    # Carregar teste do YAML
    logger.debug("Carregando teste do YAML...")
    test_name, test_func = YAMLParser.load_test(yaml_path)
    logger.debug(f"Teste carregado: {test_name}, função: {test_func}")
    print(f"✅ Teste carregado: {test_name}")
    
    # Criar configuração
    logger.debug("Criando configuração...")
    config = TestConfig(
        base_url="http://localhost:18069"
    )
    # Configurar opções
    config.browser.headless = False
    config.step.fast_mode = True  # Usar fast mode na reprodução também
    logger.debug(f"Config criada: headless={config.browser.headless}, fast_mode={config.step.fast_mode}")
    
    # Criar runner
    logger.debug("Criando TestRunner...")
    runner = TestRunner(config=config, headless=False)
    logger.debug("TestRunner criado")
    
    # Executar teste (browser será criado automaticamente se não fornecido)
    print(f"▶️  Executando teste em background...")
    print(f"💡 Deixe este processo rodando e use comandos CLI em outro terminal")
    print(f"   Exemplo: playwright-simple find \"Entrar\"")
    logger.debug("Iniciando execução do teste...")
    
    try:
        # Executar teste em background
        result = await runner.run_test(test_name, test_func)
        logger.debug(f"Teste executado com sucesso. Resultado: {result}")
        print(f"✅ Teste concluído!")
        
        # Manter processo rodando para permitir interação
        print(f"💡 Processo mantido rodando. Use Ctrl+C para parar.")
        try:
            await asyncio.sleep(3600)  # 1 hora
        except KeyboardInterrupt:
            print("\n🛑 Parando...")
        
        return result
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
                logger.debug(f"Cleaned up {cleaned} orphan browser process(es) after test")
                print(f"🧹 Limpeza: {cleaned} processo(s) órfão(s) removido(s)")
        except Exception as e:
            logger.debug(f"Error cleaning up orphan processes: {e}")

if __name__ == '__main__':
    yaml_path = Path('test_odoo_login_real.yaml')
    if not yaml_path.exists():
        print(f"❌ YAML não encontrado: {yaml_path}")
        exit(1)
    
    # Limpar processos órfãos antes de iniciar
    try:
        from playwright_simple.core.recorder.command_server import cleanup_old_sessions
        cleaned = cleanup_old_sessions(force=True, timeout=5.0)
        if cleaned > 0:
            print(f"🧹 Limpeza inicial: {cleaned} processo(s) órfão(s) removido(s)")
    except Exception as e:
        logger.debug(f"Error cleaning up orphan processes before test: {e}")
    
    # Executar sem timeout (permite interação manual)
    try:
        asyncio.run(replay_yaml_background(yaml_path))
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        # Limpar processos órfãos mesmo em caso de interrupção
        try:
            from playwright_simple.core.recorder.command_server import cleanup_old_sessions
            cleanup_old_sessions(force=True, timeout=5.0)
        except:
            pass
        exit(1)

