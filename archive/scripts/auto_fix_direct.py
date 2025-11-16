#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Fix Direct - Executa teste diretamente e corrige automaticamente.

Esta é a abordagem mais eficiente:
- Executa teste no contexto Python direto
- Captura exceções imediatamente
- Corrige código/YAML automaticamente
- Usa hot reload para aplicar correções
- Continua até o teste passar completamente
- Zero overhead de comunicação
"""

import asyncio
import sys
import os
import signal
from pathlib import Path
from typing import Optional, Dict, Any
import json
import traceback

# Tentar importar psutil, senão usar pkill
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    import subprocess

# Adicionar projeto ao path
project_dir = Path(__file__).parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from playwright.async_api import async_playwright
from playwright_simple import TestRunner
from playwright_simple.core.yaml_parser import YAMLParser
from playwright_simple.core.python_reloader import get_reloader
# AutoFixer e HTMLAnalyzer removidos - a IA corrige diretamente
from playwright_simple.core.yaml_executor import StepExecutor
from playwright_simple.core.state import WebState
from playwright_simple.core.logger import get_logger

logger = get_logger(__name__)


class AutoFixDirect:
    """Executa teste com auto-correção integrada."""
    
    def __init__(self, yaml_file: Path, base_url: str = None, headless: bool = True):
        self.yaml_file = Path(yaml_file).absolute()
        self.base_url = base_url
        self.headless = headless
        self.fix_count = 0
        self.max_fixes = 50  # Limite de segurança
        # Não fazer hot reload inicial - apenas durante execução
        self.python_reloader = get_reloader(auto_reload=False)
        
        # Matar processos antigos
        self._kill_existing_processes()
    
    def _kill_existing_processes(self):
        """Encerra processos existentes de playwright antes de iniciar novo."""
        try:
            killed = []
            current_pid = os.getpid()
            
            if PSUTIL_AVAILABLE:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info.get('cmdline', [])
                        if not cmdline:
                            continue
                        cmdline_str = ' '.join(cmdline)
                        # Verificar se é processo do playwright-simple ou auto_fix
                        if ('playwright_simple.cli' in cmdline_str or 
                            'auto_fix' in cmdline_str or
                            'chromium' in cmdline_str.lower() and 'playwright' in cmdline_str.lower()):
                            # Não matar o próprio processo
                            if proc.pid != current_pid:
                                proc.terminate()
                                try:
                                    proc.wait(timeout=3)
                                except psutil.TimeoutExpired:
                                    proc.kill()
                                killed.append(proc.pid)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                # Usar pkill como fallback
                try:
                    subprocess.run(['pkill', '-f', 'playwright_simple.cli'], 
                                 capture_output=True, timeout=5)
                    subprocess.run(['pkill', '-f', 'auto_fix'], 
                                 capture_output=True, timeout=5)
                except:
                    pass
            
            if killed:
                print(f"⚠️  Encerrados {len(killed)} processo(s) antigo(s): {killed}")
                import time
                time.sleep(1)  # Aguardar processos encerrarem
        except Exception as e:
            logger.debug(f"Erro ao encerrar processos: {e}")
        
    async def run(self) -> int:
        """Executa teste com auto-correção."""
        print("="*80)
        print("🚀 Auto-Fix Direct - Execução com Correção Automática")
        print("="*80)
        print(f"📄 YAML: {self.yaml_file}")
        print(f"🌐 Base URL: {self.base_url or 'N/A'}")
        print(f"👁️  Headless: {self.headless}")
        print(f"📹 Vídeo: Será salvo em videos/")
        print()
        
        # Configurar hot reload
        print("✅ Python hot reload ativado")
        print("✅ YAML hot reload ativado")
        print()
        
        # Criar config (será usado depois)
        from playwright_simple.core.config import TestConfig
        test_config = TestConfig(base_url=self.base_url)
        test_config.browser.headless = self.headless
        
        # Executar teste
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                slow_mo=50  # Um pouco mais lento para visualizar
            )
            
            try:
                # Habilitar vídeo
                video_dir = project_dir / "videos"
                video_dir.mkdir(exist_ok=True)
                
                context = await browser.new_context(
                    record_video_dir=str(video_dir),
                    record_video_size={"width": 1280, "height": 720}
                )
                page = await context.new_page()
                
                # Navegar para base_url primeiro
                if self.base_url:
                    print(f"🌐 Navegando para: {self.base_url}")
                    await page.goto(self.base_url, wait_until='domcontentloaded')
                    await asyncio.sleep(1)  # Aguardar página carregar
                    print(f"✅ Página carregada: {page.url}\n")
                
                # Carregar teste
                test_name, test_func = YAMLParser.load_test(self.yaml_file)
                print(f"📋 Teste: {test_name}")
                print()
                
                # Criar instância do teste (usar OdooTestBase para ter cursor visual)
                from playwright_simple.odoo.base import OdooTestBase
                test = OdooTestBase(page, config=test_config)
                
                # Garantir que cursor está visível
                await test._ensure_cursor()
                print("✅ Cursor visual ativado")
                
                # Executar com auto-correção
                result = await self._run_with_auto_fix(test, test_func, page, test_name)
                
                if result['status'] == 'passed':
                    print()
                    print("="*80)
                    print(f"✅ TESTE PASSOU COMPLETAMENTE!")
                    print(f"   Correções aplicadas: {self.fix_count}")
                    print("="*80)
                    return 0
                else:
                    print()
                    print("="*80)
                    print(f"❌ TESTE FALHOU APÓS {self.fix_count} CORREÇÕES")
                    print(f"   Erro: {result.get('error', 'Unknown')}")
                    print("="*80)
                    return 1
                    
            finally:
                await browser.close()
    
    async def _run_with_auto_fix(
        self,
        test: 'SimpleTestBase',
        test_func,
        page,
        test_name: str
    ) -> Dict[str, Any]:
        """Executa teste com loop de auto-correção."""
        
        # Obter steps do YAML
        yaml_data = YAMLParser.parse_file(self.yaml_file)
        steps = yaml_data.get('steps', [])
        base_dir = self.yaml_file.parent
        
        # Estado inicial
        current_state = WebState()
        context = {
            'test': test,
            'page': page,
            'base_url': self.base_url,
            'base_dir': base_dir,
            'vars': {},  # Variáveis do teste
            'params': {}  # Parâmetros de ações compostas
        }
        
        last_yaml_mtime = self.yaml_file.stat().st_mtime
        current_step_index = 0
        max_retries_per_step = 5
        
        while current_step_index < len(steps):
            # Hot reload Python antes de cada passo
            reloaded_count = self.python_reloader.check_and_reload_all()
            if reloaded_count > 0:
                print(f"  🔄 Python hot reload: {reloaded_count} módulo(s) recarregado(s)")
            
            # Hot reload YAML se modificado
            current_yaml_mtime = self.yaml_file.stat().st_mtime
            if current_yaml_mtime > last_yaml_mtime:
                print(f"  🔄 YAML hot reload: arquivo modificado")
                yaml_data = YAMLParser.parse_file(self.yaml_file)
                steps = yaml_data.get('steps', [])
                last_yaml_mtime = current_yaml_mtime
                # Ajustar índice se necessário
                if current_step_index >= len(steps):
                    break
            
            step = steps[current_step_index]
            action = step.get('action')
            
            if not action and 'compose' not in step and 'for' not in step and 'if' not in step and 'set' not in step and 'try' not in step:
                current_step_index += 1
                continue
            
            # Capturar estado antes do passo
            state_before = await self._capture_state(page)
            
            # Tentar executar passo com retry e auto-fix
            retry_count = 0
            step_success = False
            
            print(f"\n📍 Passo {current_step_index + 1}/{len(steps)}: {action}")
            
            while retry_count < max_retries_per_step and not step_success:
                try:
                    # Executar passo
                    current_state = await StepExecutor.execute_step(
                        step, test, base_dir, context, current_state
                    )
                    step_success = True
                    print(f"  ✅ Passo {current_step_index + 1} executado com sucesso")
                    current_step_index += 1
                    
                except Exception as e:
                    retry_count += 1
                    error_type = type(e).__name__
                    error_message = str(e)
                    
                    print(f"  ⚠️  Erro no passo {current_step_index + 1} (tentativa {retry_count}/{max_retries_per_step})")
                    print(f"     Tipo: {error_type}")
                    print(f"     Mensagem: {error_message[:100]}")
                    
                    # Verificar limite de correções
                    if self.fix_count >= self.max_fixes:
                        print(f"  ❌ Limite de correções ({self.max_fixes}) atingido")
                        return {
                            'status': 'failed',
                            'error': f'Limite de correções atingido após {self.fix_count} tentativas'
                        }
                    
                    # Capturar informações para análise
                    error_info = await self._capture_error_info(
                        e, page, step, current_step_index + 1
                    )
                    
                    # Mostrar informações do erro para correção manual pela IA
                    print(f"\n{'='*80}")
                    print(f"🔍 ERRO DETECTADO - Aguardando correção pela IA")
                    print(f"{'='*80}")
                    print(f"Passo: {current_step_index + 1}/{len(steps)}")
                    print(f"Ação: {action}")
                    print(f"Tipo: {error_type}")
                    print(f"Mensagem: {error_message}")
                    print(f"URL: {page.url}")
                    
                    # Capturar HTML se disponível
                    html_simplified = error_info.get('html_simplified')
                    if html_simplified:
                        print(f"\n📄 Elementos disponíveis na página:")
                        buttons = html_simplified.get('buttons', [])
                        if buttons:
                            print(f"  Botões ({len(buttons)}):")
                            for btn in buttons[:5]:
                                print(f"    - '{btn.get('text', '')}' (tag: {btn.get('tag')}, id: {btn.get('id')})")
                        inputs = html_simplified.get('inputs', [])
                        if inputs:
                            print(f"  Inputs ({len(inputs)}):")
                            for inp in inputs[:5]:
                                print(f"    - {inp.get('type')} (name: {inp.get('name')}, placeholder: {inp.get('placeholder')})")
                    
                    print(f"\n💡 A IA deve corrigir o erro agora...")
                    print(f"{'='*80}\n")
                    
                    # Aguardar correção (a IA vai corrigir usando suas ferramentas)
                    # Por enquanto, apenas aguardar um pouco para dar tempo da IA corrigir
                    await asyncio.sleep(2)
                    
                    # Verificar se YAML foi modificado (IA pode ter corrigido)
                    current_yaml_mtime = self.yaml_file.stat().st_mtime
                    if current_yaml_mtime > last_yaml_mtime:
                        print(f"  ✅ YAML modificado - recarregando...")
                        yaml_data = YAMLParser.parse_file(self.yaml_file)
                        steps = yaml_data.get('steps', [])
                        last_yaml_mtime = current_yaml_mtime
                        # Atualizar step atual
                        if current_step_index < len(steps):
                            step = steps[current_step_index]
                        self.fix_count += 1
                        
                        # Aguardar hot reload processar
                        await asyncio.sleep(0.5)
                        
                        # Rollback: restaurar estado antes do passo
                        await self._restore_state(page, state_before)
                        
                        # Tentar novamente
                        continue
                    else:
                        print(f"  ⚠️  YAML não foi modificado ainda...")
                        if retry_count >= max_retries_per_step:
                            print(f"  ❌ Máximo de tentativas atingido - aguardando correção manual")
                            return {
                                'status': 'failed',
                                'error': f'{error_type}: {error_message}',
                                'step': current_step_index + 1,
                                'needs_manual_fix': True
                            }
                    
                    # Aguardar antes de tentar novamente
                    await asyncio.sleep(1)
            
            if not step_success:
                return {
                    'status': 'failed',
                    'error': 'Passo falhou após todas tentativas',
                    'step': current_step_index + 1
                }
        
        # Todos os passos executados com sucesso
        return {'status': 'passed'}
    
    async def _capture_state(self, page) -> Dict[str, Any]:
        """Captura estado atual da página."""
        return {
            'url': page.url,
            'title': await page.title()
        }
    
    async def _restore_state(self, page, state: Dict[str, Any]):
        """Restaura estado da página."""
        try:
            if state.get('url') and page.url != state['url']:
                await page.goto(state['url'], wait_until='domcontentloaded')
        except:
            pass  # Ignorar erros de navegação
    
    async def _capture_error_info(
        self,
        error: Exception,
        page,
        step: Dict,
        step_number: int
    ) -> Dict[str, Any]:
        """Captura informações completas do erro para análise."""
        try:
            html = await page.content()
            html_simplified = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button, a[role="button"], input[type="submit"], input[type="button"]'))
                        .map(btn => ({
                            text: btn.textContent?.trim() || btn.value || btn.getAttribute('aria-label') || '',
                            tag: btn.tagName.toLowerCase(),
                            id: btn.id || '',
                            class: btn.className || '',
                            visible: btn.offsetParent !== null
                        }))
                        .filter(btn => btn.visible && btn.text);
                    
                    const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea'))
                        .map(inp => ({
                            type: inp.type,
                            placeholder: inp.placeholder || '',
                            name: inp.name || '',
                            id: inp.id || '',
                            label: inp.labels?.[0]?.textContent?.trim() || ''
                        }));
                    
                    return {
                        buttons: buttons,
                        inputs: inputs,
                        url: window.location.href,
                        title: document.title
                    };
                }
            """)
        except:
            html = None
            html_simplified = None
        
        return {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'step': step,
            'step_number': step_number,
            'html': html,
            'html_simplified': html_simplified,
            'url': page.url
        }
    
    # Removido _auto_fix - a IA corrige diretamente usando suas ferramentas


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-Fix Direct - Execução com correção automática')
    parser.add_argument('yaml_file', type=str, help='Arquivo YAML do teste')
    parser.add_argument('--base-url', type=str, help='URL base')
    parser.add_argument('--headless', action='store_true', default=True, help='Executar em modo headless')
    parser.add_argument('--no-headless', action='store_false', dest='headless', help='Executar com navegador visível')
    
    args = parser.parse_args()
    
    runner = AutoFixDirect(
        yaml_file=args.yaml_file,
        base_url=args.base_url,
        headless=args.headless
    )
    
    exit_code = await runner.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())

