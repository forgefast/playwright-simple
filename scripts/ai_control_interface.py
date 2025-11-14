#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Control Interface - Interface para a IA controlar o cursor e ações do Chromium diretamente.

Permite que a IA envie comandos explícitos como:
- mover_cursor: Mover cursor para um elemento
- click: Clicar em um elemento
- type: Digitar texto
- wait: Aguardar
- etc.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Adicionar projeto ao path
project_dir = Path(__file__).parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from playwright.async_api import async_playwright
from playwright_simple.odoo.base import OdooTestBase
from playwright_simple.core.config import TestConfig
from playwright_simple.core.logger import get_logger

logger = get_logger(__name__)

COMMAND_FILE = Path("/tmp/ai_commands.json")
RESPONSE_FILE = Path("/tmp/ai_response.json")


class AIControlInterface:
    """Interface para a IA controlar o navegador diretamente."""
    
    def __init__(self, page, test: OdooTestBase):
        self.page = page
        self.test = test
        self.command_file = COMMAND_FILE
        self.response_file = RESPONSE_FILE
        
    async def wait_for_command(self, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Aguarda comando da IA."""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.command_file.exists():
                try:
                    command_data = json.loads(self.command_file.read_text(encoding='utf-8'))
                    # Limpar arquivo após ler
                    self.command_file.unlink()
                    return command_data
                except Exception as e:
                    logger.debug(f"Erro ao ler comando: {e}")
            
            await asyncio.sleep(0.5)
        
        return None
    
    async def send_response(self, success: bool, message: str, data: Optional[Dict] = None):
        """Envia resposta para a IA."""
        response = {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.response_file.write_text(json.dumps(response, indent=2), encoding='utf-8')
    
    async def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Executa comando da IA."""
        cmd_type = command.get('command')
        
        try:
            if cmd_type == 'move_cursor':
                return await self._move_cursor(command)
            elif cmd_type == 'click':
                return await self._click(command)
            elif cmd_type == 'type':
                return await self._type(command)
            elif cmd_type == 'wait':
                return await self._wait(command)
            elif cmd_type == 'get_html':
                return await self._get_html(command)
            elif cmd_type == 'get_elements':
                return await self._get_elements(command)
            elif cmd_type == 'navigate':
                return await self._navigate(command)
            else:
                return {"success": False, "message": f"Comando desconhecido: {cmd_type}"}
        except Exception as e:
            logger.error(f"Erro ao executar comando {cmd_type}: {e}", exc_info=True)
            return {"success": False, "message": str(e), "error_type": type(e).__name__}
    
    async def _move_cursor(self, command: Dict) -> Dict[str, Any]:
        """Move cursor para um elemento."""
        selector = command.get('selector')
        text = command.get('text')
        
        if not selector and not text:
            return {"success": False, "message": "Seletor ou texto necessário"}
        
        try:
            if text:
                # Procurar por texto
                element = self.page.locator(f'text="{text}"').first
            else:
                element = self.page.locator(selector).first
            
            if await element.count() == 0:
                return {"success": False, "message": "Elemento não encontrado"}
            
            if not await element.is_visible():
                return {"success": False, "message": "Elemento não está visível"}
            
            box = await element.bounding_box()
            if not box:
                return {"success": False, "message": "Não foi possível obter posição do elemento"}
            
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            
            # Mover cursor
            await self.test.cursor_manager.move_to(x, y)
            await asyncio.sleep(0.3)
            
            return {
                "success": True,
                "message": f"Cursor movido para ({x:.0f}, {y:.0f})",
                "position": {"x": x, "y": y}
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _click(self, command: Dict) -> Dict[str, Any]:
        """Clica em um elemento."""
        selector = command.get('selector')
        text = command.get('text')
        
        if not selector and not text:
            return {"success": False, "message": "Seletor ou texto necessário"}
        
        try:
            if text:
                element = self.page.locator(f'text="{text}"').first
            else:
                element = self.page.locator(selector).first
            
            if await element.count() == 0:
                return {"success": False, "message": "Elemento não encontrado"}
            
            if not await element.is_visible():
                return {"success": False, "message": "Elemento não está visível"}
            
            box = await element.bounding_box()
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                
                # Mover cursor primeiro
                await self.test.cursor_manager.move_to(x, y)
                await asyncio.sleep(0.3)
                
                # Mostrar efeito de clique
                await self.test.cursor_manager.show_click_effect(x, y)
                await asyncio.sleep(0.1)
                
                # Clicar
                await self.page.mouse.click(x, y)
            else:
                await element.click()
            
            await asyncio.sleep(0.5)
            
            return {"success": True, "message": "Clique executado"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _type(self, command: Dict) -> Dict[str, Any]:
        """Digita texto em um elemento."""
        selector = command.get('selector')
        text = command.get('text')
        value = command.get('value')
        
        if not selector:
            return {"success": False, "message": "Seletor necessário"}
        
        if not text and not value:
            return {"success": False, "message": "Texto ou valor necessário"}
        
        try:
            element = self.page.locator(selector).first
            
            if await element.count() == 0:
                return {"success": False, "message": "Elemento não encontrado"}
            
            # Mover cursor para o elemento
            box = await element.bounding_box()
            if box:
                x = box['x'] + box['width'] / 2
                y = box['y'] + box['height'] / 2
                await self.test.cursor_manager.move_to(x, y)
                await asyncio.sleep(0.2)
            
            # Clicar no elemento primeiro
            await element.click()
            await asyncio.sleep(0.2)
            
            # Limpar e digitar
            await element.fill('')
            text_to_type = text or value
            await element.type(text_to_type, delay=50)  # Digitar com delay para visualizar
            
            return {"success": True, "message": f"Texto '{text_to_type}' digitado"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _wait(self, command: Dict) -> Dict[str, Any]:
        """Aguarda um tempo."""
        seconds = command.get('seconds', 1.0)
        await asyncio.sleep(seconds)
        return {"success": True, "message": f"Aguardou {seconds} segundos"}
    
    async def _get_html(self, command: Dict) -> Dict[str, Any]:
        """Obtém HTML da página."""
        try:
            html = await self.page.content()
            simplified = await self.page.evaluate("""
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
            
            # Salvar em arquivo também
            Path("/tmp/playwright_html.html").write_text(html, encoding='utf-8')
            Path("/tmp/playwright_html_simplified.json").write_text(
                json.dumps(simplified, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            return {
                "success": True,
                "message": "HTML obtido",
                "data": {
                    "url": simplified.get('url'),
                    "title": simplified.get('title'),
                    "buttons_count": len(simplified.get('buttons', [])),
                    "inputs_count": len(simplified.get('inputs', []))
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _get_elements(self, command: Dict) -> Dict[str, Any]:
        """Obtém lista de elementos."""
        try:
            elements = await self.page.evaluate("""
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
                        inputs: inputs
                    };
                }
            """)
            
            return {
                "success": True,
                "message": "Elementos obtidos",
                "data": elements
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _navigate(self, command: Dict) -> Dict[str, Any]:
        """Navega para uma URL."""
        url = command.get('url')
        if not url:
            return {"success": False, "message": "URL necessária"}
        
        try:
            await self.page.goto(url, wait_until='domcontentloaded')
            await asyncio.sleep(1)
            return {"success": True, "message": f"Navegou para {url}"}
        except Exception as e:
            return {"success": False, "message": str(e)}


async def main():
    """Executa loop de comandos da IA."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Control Interface - Controle do navegador pela IA')
    parser.add_argument('--base-url', type=str, help='URL base')
    parser.add_argument('--headless', action='store_true', default=False, help='Executar em modo headless')
    parser.add_argument('--no-headless', action='store_false', dest='headless', help='Executar com navegador visível')
    
    args = parser.parse_args()
    
    config = TestConfig(base_url=args.base_url)
    config.browser.headless = args.headless
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=args.headless, slow_mo=50)
        context = await browser.new_context()
        page = await context.new_page()
        
        if args.base_url:
            await page.goto(args.base_url, wait_until='domcontentloaded')
            await asyncio.sleep(1)
        
        test = OdooTestBase(page, config=config)
        await test._ensure_cursor()
        
        print("="*80)
        print("🤖 AI Control Interface - Pronto para receber comandos")
        print("="*80)
        print(f"📄 Arquivo de comandos: {COMMAND_FILE}")
        print(f"📄 Arquivo de resposta: {RESPONSE_FILE}")
        print(f"🌐 URL: {page.url}")
        print()
        print("💡 Envie comandos JSON para:", COMMAND_FILE)
        print("   Exemplo: {\"command\": \"get_elements\"}")
        print("="*80)
        print()
        
        interface = AIControlInterface(page, test)
        
        try:
            while True:
                command = await interface.wait_for_command(timeout=60.0)
                if command:
                    print(f"📥 Comando recebido: {command.get('command')}")
                    result = await interface.execute_command(command)
                    await interface.send_response(
                        result.get('success', False),
                        result.get('message', ''),
                        result.get('data')
                    )
                    print(f"📤 Resposta enviada: {result.get('message')}")
                else:
                    # Timeout - continuar aguardando
                    pass
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(main())

