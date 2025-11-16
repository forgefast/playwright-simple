#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step-by-Step Fix - Executa passo a passo com timeout e foco em corrigir cursor.

- Timeout de 20s por passo
- Limpa vídeos antes de cada execução
- Para em cada erro para análise
- Foca em corrigir movimento do cursor
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Adicionar projeto ao path
project_dir = Path(__file__).parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from playwright.async_api import async_playwright
from playwright_simple.odoo.base import OdooTestBase
from playwright_simple.core.config import TestConfig
from playwright_simple.core.yaml_parser import YAMLParser
from playwright_simple.core.yaml_executor import StepExecutor
from playwright_simple.core.state import WebState
from playwright_simple.core.logger import get_logger

logger = get_logger(__name__)

STEP_TIMEOUT = 20.0  # 20 segundos por passo


class StepByStepFix:
    """Executa teste passo a passo com timeout e logging."""
    
    def __init__(self, yaml_file: Path, base_url: str = None, headless: bool = True):
        self.yaml_file = Path(yaml_file).absolute()
        self.base_url = base_url
        self.headless = headless
        self.video_dir = project_dir / "videos"
        
    def _clean_videos(self):
        """Limpa vídeos antigos."""
        if self.video_dir.exists():
            for video_file in self.video_dir.glob("*.webm"):
                try:
                    video_file.unlink()
                    print(f"  🗑️  Removido: {video_file.name}")
                except:
                    pass
            print(f"  ✅ Vídeos limpos")
        else:
            self.video_dir.mkdir(exist_ok=True)
    
    async def run(self) -> int:
        """Executa teste passo a passo."""
        print("="*80)
        print("🔧 Step-by-Step Fix - Execução com Timeout")
        print("="*80)
        print(f"📄 YAML: {self.yaml_file}")
        print(f"🌐 Base URL: {self.base_url or 'N/A'}")
        print(f"👁️  Headless: {self.headless}")
        print(f"⏱️  Timeout por passo: {STEP_TIMEOUT}s")
        print()
        
        # Limpar vídeos
        self._clean_videos()
        
        # Carregar teste
        test_name, test_func = YAMLParser.load_test(self.yaml_file)
        print(f"📋 Teste: {test_name}")
        print()
        
        # Criar config
        config = TestConfig(base_url=self.base_url)
        config.browser.headless = self.headless
        
        # Executar teste
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                slow_mo=100
            )
            
            try:
                # Habilitar vídeo
                context = await browser.new_context(
                    record_video_dir=str(self.video_dir),
                    record_video_size={"width": 1280, "height": 720}
                )
                page = await context.new_page()
                
                # Navegar para base_url
                if self.base_url:
                    print(f"🌐 Navegando para: {self.base_url}")
                    await page.goto(self.base_url, wait_until='domcontentloaded', timeout=10000)
                    await asyncio.sleep(1)
                    print(f"✅ Página carregada: {page.url}\n")
                
                # Criar instância do teste
                test = OdooTestBase(page, config=config)
                await test._ensure_cursor()
                print("✅ Cursor visual ativado\n")
                
                # Obter steps
                yaml_data = YAMLParser.parse_file(self.yaml_file)
                steps = yaml_data.get('steps', [])
                base_dir = self.yaml_file.parent
                
                print(f"📋 Total de passos: {len(steps)}\n")
                
                # Estado inicial
                current_state = WebState()
                context = {
                    'test': test,
                    'page': page,
                    'base_url': self.base_url,
                    'base_dir': base_dir,
                    'vars': {},
                    'params': {}
                }
                
                # Executar cada passo com timeout
                for step_index, step in enumerate(steps, 1):
                    action = step.get('action')
                    
                    if not action and 'compose' not in step and 'for' not in step and 'if' not in step and 'set' not in step and 'try' not in step:
                        continue
                    
                    print("="*80)
                    print(f"📍 PASSO {step_index}/{len(steps)}: {action}")
                    print("="*80)
                    print(f"Descrição: {step.get('description', 'N/A')}")
                    print(f"Timeout: {STEP_TIMEOUT}s")
                    print()
                    
                    # Capturar estado antes
                    url_before = page.url
                    print(f"🌐 URL antes: {url_before}")
                    
                    try:
                        # Executar passo com timeout
                        print(f"▶️  Executando passo...")
                        
                        result = await asyncio.wait_for(
                            StepExecutor.execute_step(step, test, base_dir, context, current_state),
                            timeout=STEP_TIMEOUT
                        )
                        
                        current_state = result
                        
                        # Verificar se houve mudança
                        url_after = page.url
                        if url_after != url_before:
                            print(f"🌐 URL depois: {url_after}")
                        
                        print(f"✅ Passo {step_index} executado com sucesso!")
                        print()
                        
                        # Aguardar um pouco para visualizar
                        await asyncio.sleep(1)
                        
                    except asyncio.TimeoutError:
                        print()
                        print("="*80)
                        print(f"⏱️  TIMEOUT no passo {step_index}!")
                        print("="*80)
                        print(f"O passo não completou em {STEP_TIMEOUT}s")
                        print(f"Ação: {action}")
                        print(f"URL atual: {page.url}")
                        print()
                        print("💡 Verifique:")
                        print("   - Se o cursor está se movendo")
                        print("   - Se o elemento existe na página")
                        print("   - Se há algum erro no console")
                        print()
                        print("📹 Vídeo salvo em:", self.video_dir)
                        print("="*80)
                        return 1
                        
                    except Exception as e:
                        error_type = type(e).__name__
                        error_message = str(e)
                        
                        print()
                        print("="*80)
                        print(f"❌ ERRO no passo {step_index}")
                        print("="*80)
                        print(f"Tipo: {error_type}")
                        print(f"Mensagem: {error_message}")
                        print(f"Ação: {action}")
                        print(f"URL: {page.url}")
                        print()
                        
                        # Capturar HTML para análise
                        try:
                            html = await page.content()
                            html_file = Path(f"/tmp/step_{step_index}_error.html")
                            html_file.write_text(html, encoding='utf-8')
                            print(f"📄 HTML salvo em: {html_file}")
                            
                            # Elementos disponíveis
                            elements = await page.evaluate("""
                                () => {
                                    const buttons = Array.from(document.querySelectorAll('button, a[role="button"], input[type="submit"]'))
                                        .map(btn => ({
                                            text: btn.textContent?.trim() || btn.value || '',
                                            tag: btn.tagName.toLowerCase(),
                                            id: btn.id || '',
                                            class: btn.className || '',
                                            visible: btn.offsetParent !== null
                                        }))
                                        .filter(btn => btn.visible);
                                    
                                    return { buttons: buttons };
                                }
                            """)
                            
                            elements_file = Path(f"/tmp/step_{step_index}_elements.json")
                            elements_file.write_text(json.dumps(elements, indent=2, ensure_ascii=False), encoding='utf-8')
                            print(f"📋 Elementos salvos em: {elements_file}")
                            
                            if elements.get('buttons'):
                                print(f"\n🔘 Botões disponíveis na página:")
                                for btn in elements['buttons'][:10]:
                                    print(f"   - '{btn.get('text')}' (tag: {btn.get('tag')}, id: {btn.get('id')}, class: {btn.get('class')[:50]})")
                            
                        except Exception as html_error:
                            print(f"⚠️  Erro ao capturar HTML: {html_error}")
                        
                        print()
                        print("📹 Vídeo salvo em:", self.video_dir)
                        print("="*80)
                        print()
                        print("💡 CORRIJA O ERRO E EXECUTE NOVAMENTE")
                        print("="*80)
                        return 1
                
                print()
                print("="*80)
                print("✅ TODOS OS PASSOS EXECUTADOS COM SUCESSO!")
                print("="*80)
                print(f"📹 Vídeo final salvo em: {self.video_dir}")
                return 0
                
            finally:
                await browser.close()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Step-by-Step Fix - Execução passo a passo com timeout')
    parser.add_argument('yaml_file', type=str, help='Arquivo YAML do teste')
    parser.add_argument('--base-url', type=str, help='URL base')
    parser.add_argument('--headless', action='store_true', default=True, help='Executar em modo headless')
    parser.add_argument('--no-headless', action='store_false', dest='headless', help='Executar com navegador visível')
    
    args = parser.parse_args()
    
    runner = StepByStepFix(
        yaml_file=args.yaml_file,
        base_url=args.base_url,
        headless=args.headless
    )
    
    exit_code = await runner.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())


