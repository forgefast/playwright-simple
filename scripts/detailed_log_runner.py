#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed Log Runner - Executa teste com logging completo de todos os eventos.

Registra TUDO que acontece para facilitar correção manual:
- Cada passo executado
- Cada elemento encontrado/não encontrado
- Cada erro com detalhes completos
- HTML da página em cada passo
- Estado do cursor
- Timestamps de tudo
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

LOG_DIR = Path("/tmp/playwright_detailed_logs")
LOG_DIR.mkdir(exist_ok=True)


class DetailedLogger:
    """Logger detalhado de todos os eventos."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.log_file = LOG_DIR / f"{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.events = []
        
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Registra um evento."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            **data
        }
        self.events.append(event)
        
        # Escrever em JSONL (uma linha por evento)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        # Também printar no console
        print(f"[{event['timestamp']}] {event_type}: {data.get('message', '')}")
    
    async def log_page_state(self, page, step_number: Optional[int] = None):
        """Registra estado completo da página."""
        try:
            html = await page.content()
            simplified = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button, a[role="button"], input[type="submit"], input[type="button"]'))
                        .map(btn => ({
                            text: btn.textContent?.trim() || btn.value || btn.getAttribute('aria-label') || '',
                            tag: btn.tagName.toLowerCase(),
                            id: btn.id || '',
                            class: btn.className || '',
                            visible: btn.offsetParent !== null,
                            selector: btn.id ? `#${btn.id}` : btn.className ? `.${btn.className.split(' ')[0]}` : btn.tagName.toLowerCase()
                        }))
                        .filter(btn => btn.visible);
                    
                    const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea'))
                        .map(inp => ({
                            type: inp.type,
                            placeholder: inp.placeholder || '',
                            name: inp.name || '',
                            id: inp.id || '',
                            label: inp.labels?.[0]?.textContent?.trim() || '',
                            visible: inp.offsetParent !== null
                        }))
                        .filter(inp => inp.visible);
                    
                    return {
                        buttons: buttons,
                        inputs: inputs,
                        url: window.location.href,
                        title: document.title
                    };
                }
            """)
            
            # Salvar HTML completo
            html_file = LOG_DIR / f"step_{step_number or 'unknown'}_html.html"
            html_file.write_text(html, encoding='utf-8')
            
            # Salvar simplificado
            simplified_file = LOG_DIR / f"step_{step_number or 'unknown'}_elements.json"
            simplified_file.write_text(json.dumps(simplified, indent=2, ensure_ascii=False), encoding='utf-8')
            
            self.log_event("page_state", {
                "step_number": step_number,
                "url": simplified.get('url'),
                "title": simplified.get('title'),
                "buttons_count": len(simplified.get('buttons', [])),
                "inputs_count": len(simplified.get('inputs', [])),
                "html_file": str(html_file),
                "elements_file": str(simplified_file),
                "buttons": simplified.get('buttons', [])[:10],  # Primeiros 10
                "inputs": simplified.get('inputs', [])[:10]
            })
            
        except Exception as e:
            self.log_event("page_state_error", {
                "step_number": step_number,
                "error": str(e)
            })


class DetailedLogRunner:
    """Runner com logging detalhado."""
    
    def __init__(self, yaml_file: Path, base_url: str = None, headless: bool = True):
        self.yaml_file = Path(yaml_file).absolute()
        self.base_url = base_url
        self.headless = headless
        
    async def run(self) -> int:
        """Executa teste com logging detalhado."""
        print("="*80)
        print("📋 Detailed Log Runner - Logging Completo de Eventos")
        print("="*80)
        print(f"📄 YAML: {self.yaml_file}")
        print(f"🌐 Base URL: {self.base_url or 'N/A'}")
        print(f"👁️  Headless: {self.headless}")
        print(f"📁 Logs: {LOG_DIR}")
        print()
        
        # Carregar teste
        test_name, test_func = YAMLParser.load_test(self.yaml_file)
        detailed_logger = DetailedLogger(test_name)
        
        detailed_logger.log_event("test_started", {
            "test_name": test_name,
            "yaml_file": str(self.yaml_file),
            "base_url": self.base_url
        })
        
        # Criar config
        config = TestConfig(base_url=self.base_url)
        config.browser.headless = self.headless
        
        # Executar teste
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                slow_mo=100  # Mais lento para visualizar
            )
            
            try:
                context = await browser.new_context()
                page = await context.new_page()
                
                # Navegar para base_url
                if self.base_url:
                    detailed_logger.log_event("navigation", {
                        "url": self.base_url,
                        "action": "goto"
                    })
                    await page.goto(self.base_url, wait_until='domcontentloaded')
                    await asyncio.sleep(1)
                    detailed_logger.log_event("navigation_complete", {
                        "url": page.url,
                        "title": await page.title()
                    })
                    await detailed_logger.log_page_state(page, step_number=0)
                
                # Criar instância do teste
                test = OdooTestBase(page, config=config)
                await test._ensure_cursor()
                detailed_logger.log_event("test_instance_created", {
                    "cursor_enabled": True
                })
                
                # Obter steps
                yaml_data = YAMLParser.parse_file(self.yaml_file)
                steps = yaml_data.get('steps', [])
                base_dir = self.yaml_file.parent
                
                detailed_logger.log_event("steps_loaded", {
                    "steps_count": len(steps),
                    "steps": [{"action": s.get('action'), "description": s.get('description')} for s in steps]
                })
                
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
                
                # Executar cada passo
                for step_index, step in enumerate(steps, 1):
                    action = step.get('action')
                    
                    detailed_logger.log_event("step_started", {
                        "step_number": step_index,
                        "step_total": len(steps),
                        "action": action,
                        "step_data": step
                    })
                    
                    # Log estado antes do passo
                    await detailed_logger.log_page_state(page, step_number=step_index)
                    
                    try:
                        # Executar passo
                        detailed_logger.log_event("step_executing", {
                            "step_number": step_index,
                            "action": action
                        })
                        
                        current_state = await StepExecutor.execute_step(
                            step, test, base_dir, context, current_state
                        )
                        
                        detailed_logger.log_event("step_completed", {
                            "step_number": step_index,
                            "action": action,
                            "success": True
                        })
                        
                        # Log estado após o passo
                        await asyncio.sleep(0.5)
                        await detailed_logger.log_page_state(page, step_number=step_index)
                        
                    except Exception as e:
                        error_type = type(e).__name__
                        error_message = str(e)
                        
                        detailed_logger.log_event("step_error", {
                            "step_number": step_index,
                            "action": action,
                            "error_type": error_type,
                            "error_message": error_message,
                            "error_traceback": str(e.__traceback__) if hasattr(e, '__traceback__') else None
                        })
                        
                        # Log estado no erro
                        await detailed_logger.log_page_state(page, step_number=step_index)
                        
                        print()
                        print("="*80)
                        print(f"❌ ERRO NO PASSO {step_index}")
                        print("="*80)
                        print(f"Tipo: {error_type}")
                        print(f"Mensagem: {error_message}")
                        print(f"Ação: {action}")
                        print(f"Log completo: {detailed_logger.log_file}")
                        print(f"HTML: {LOG_DIR / f'step_{step_index}_html.html'}")
                        print(f"Elementos: {LOG_DIR / f'step_{step_index}_elements.json'}")
                        print("="*80)
                        print()
                        
                        # Continuar ou parar?
                        raise
                
                detailed_logger.log_event("test_completed", {
                    "success": True,
                    "steps_executed": len(steps)
                })
                
                print()
                print("="*80)
                print("✅ TESTE COMPLETO!")
                print(f"📁 Log completo: {detailed_logger.log_file}")
                print("="*80)
                
                return 0
                
            finally:
                await browser.close()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Detailed Log Runner - Logging completo de eventos')
    parser.add_argument('yaml_file', type=str, help='Arquivo YAML do teste')
    parser.add_argument('--base-url', type=str, help='URL base')
    parser.add_argument('--headless', action='store_true', default=True, help='Executar em modo headless')
    parser.add_argument('--no-headless', action='store_false', dest='headless', help='Executar com navegador visível')
    
    args = parser.parse_args()
    
    runner = DetailedLogRunner(
        yaml_file=args.yaml_file,
        base_url=args.base_url,
        headless=args.headless
    )
    
    exit_code = await runner.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())

