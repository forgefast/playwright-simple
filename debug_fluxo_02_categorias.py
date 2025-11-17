#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug para investigar problema "Categorias" não encontrado no fluxo_02.
Captura HTML, URL, elementos visíveis e screenshot quando erro ocorre.
"""

import asyncio
import sys
import re
from pathlib import Path
from datetime import datetime

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from playwright.async_api import async_playwright
from playwright_simple.core.recorder.utils.browser import BrowserManager
from playwright_simple.core.recorder.command_handlers.handlers import CommandHandlers
from playwright_simple.core.recorder.yaml_writer import YAMLWriter
from playwright_simple.core.recorder.action_converter import ActionConverter
from playwright_simple.core.recorder.event_handlers import EventHandlers
from playwright_simple.core.recorder.cursor_controller.controller import CursorController
from playwright_simple.core.recorder.config import SpeedLevel

# Configuração
BASE_URL = "http://localhost:18069"
HEADLESS = False
MD_FILE = project_root / "test_complete_racco_flows.md"
DEBUG_OUTPUT_DIR = project_root / "debug_fluxo_02"
DEBUG_OUTPUT_DIR.mkdir(exist_ok=True)


def parse_commands_from_md_until_categorias(md_file: Path) -> list[str]:
    """Lê comandos do arquivo MD até chegar no comando 'Categorias'"""
    if not md_file.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {md_file}")
    
    commands = []
    in_bash_block = False
    in_fluxo_02 = False
    found_categorias = False
    
    with open(md_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Detectar início do bloco bash
            if line == '```bash':
                in_bash_block = True
                continue
            
            # Detectar fim do bloco bash
            if line == '```' and in_bash_block:
                in_bash_block = False
                continue
            
            if in_bash_block:
                # Verificar se é fluxo_02
                if '# FLUXO 02:' in line or '# FLUXO 02' in line:
                    in_fluxo_02 = True
                    continue
                
                # Verificar se é outro fluxo (parar)
                if in_fluxo_02 and line.startswith('# FLUXO'):
                    break
                
                # Se estamos no fluxo_02, pegar comandos
                if in_fluxo_02:
                    if line.startswith('pw-'):
                        # Parar quando encontrar o comando que tenta clicar em "Categorias"
                        if 'pw-click "Categorias"' in line:
                            found_categorias = True
                            # Não adicionar este comando, vamos investigar antes
                            break
                        commands.append(line)
    
    return commands


async def capture_page_state(page, output_file: Path):
    """Captura estado completo da página"""
    print(f"\n📸 Capturando estado da página em {output_file}...")
    
    # Capturar informações
    url = page.url
    title = await page.title()
    html = await page.content()
    
    # Capturar elementos visíveis relacionados a "Contatos" e "Categorias"
    elements_info = await page.evaluate("""
        () => {
            const info = {
                url: window.location.href,
                title: document.title,
                all_clickable_texts: [],
                menu_items: [],
                links_with_categorias: [],
                buttons_with_categorias: []
            };
            
            // Todos os textos clicáveis
            const clickable = document.querySelectorAll('button, a, [role="button"], [role="menuitem"], [onclick]');
            clickable.forEach(el => {
                const text = (el.textContent || '').trim();
                if (text) {
                    info.all_clickable_texts.push({
                        text: text,
                        tag: el.tagName,
                        role: el.getAttribute('role') || '',
                        href: el.href || '',
                        visible: el.offsetParent !== null
                    });
                }
            });
            
            // Buscar por "Categorias" ou variações
            const categorias_variations = ['categorias', 'categoria', 'tags', 'contact tags', 'contacttags'];
            clickable.forEach(el => {
                const text = (el.textContent || '').trim().toLowerCase();
                categorias_variations.forEach(variation => {
                    if (text.includes(variation)) {
                        info.links_with_categorias.push({
                            text: el.textContent.trim(),
                            tag: el.tagName,
                            role: el.getAttribute('role') || '',
                            href: el.href || '',
                            visible: el.offsetParent !== null,
                            boundingRect: el.getBoundingClientRect()
                        });
                    }
                });
            });
            
            // Buscar por "Contatos"
            clickable.forEach(el => {
                const text = (el.textContent || '').trim().toLowerCase();
                if (text.includes('contatos') || text.includes('contato')) {
                    info.menu_items.push({
                        text: el.textContent.trim(),
                        tag: el.tagName,
                        role: el.getAttribute('role') || '',
                        href: el.href || '',
                        visible: el.offsetParent !== null,
                        hasChildren: el.querySelector('ul, [role="menu"]') !== null
                    });
                }
            });
            
            return info;
        }
    """)
    
    # Capturar screenshot
    screenshot_path = output_file.with_suffix('.png')
    await page.screenshot(path=str(screenshot_path), full_page=True)
    
    # Salvar informações em arquivo
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'url': url,
        'title': title,
        'elements_info': elements_info,
        'html_length': len(html)
    }
    
    import json
    with open(output_file.with_suffix('.json'), 'w', encoding='utf-8') as f:
        json.dump(debug_info, f, indent=2, ensure_ascii=False)
    
    # Salvar HTML (primeiros 50000 caracteres)
    html_preview = html[:50000]
    with open(output_file.with_suffix('.html'), 'w', encoding='utf-8') as f:
        f.write(html_preview)
    
    print(f"✅ Estado capturado:")
    print(f"   - URL: {url}")
    print(f"   - Título: {title}")
    print(f"   - Screenshot: {screenshot_path}")
    print(f"   - JSON: {output_file.with_suffix('.json')}")
    print(f"   - HTML: {output_file.with_suffix('.html')}")
    print(f"\n📋 Elementos encontrados:")
    print(f"   - Total de elementos clicáveis: {len(elements_info.get('all_clickable_texts', []))}")
    print(f"   - Itens de menu 'Contatos': {len(elements_info.get('menu_items', []))}")
    print(f"   - Elementos com 'Categorias': {len(elements_info.get('links_with_categorias', []))}")
    
    if elements_info.get('links_with_categorias'):
        print(f"\n🔍 Elementos relacionados a 'Categorias':")
        for item in elements_info['links_with_categorias']:
            print(f"   - '{item['text']}' ({item['tag']}, role={item['role']}, visible={item['visible']})")
    
    if elements_info.get('menu_items'):
        print(f"\n📂 Itens de menu 'Contatos':")
        for item in elements_info['menu_items']:
            print(f"   - '{item['text']}' ({item['tag']}, hasChildren={item['hasChildren']}, visible={item['visible']})")


async def main():
    """Função principal - executa até ponto de falha e captura estado"""
    
    print("🔍 Debug: Investigando problema 'Categorias' no fluxo_02\n")
    
    # Ler comandos até "Categorias"
    print(f"📖 Lendo comandos de {MD_FILE} até 'Categorias'...")
    commands = parse_commands_from_md_until_categorias(MD_FILE)
    print(f"✅ {len(commands)} comandos encontrados (até antes de 'Categorias')\n")
    
    if not commands:
        print("❌ Nenhum comando encontrado")
        return 1
    
    # Inicializar browser
    browser_manager = BrowserManager(headless=HEADLESS)
    page = await browser_manager.start()
    await page.goto(BASE_URL)
    
    # Inicializar componentes necessários para handlers
    yaml_writer = YAMLWriter(output_path=project_root / "temp_test.yaml")
    action_converter = ActionConverter()
    event_handlers = EventHandlers(yaml_writer, action_converter)
    
    # Inicializar cursor controller
    cursor_controller = CursorController(page, speed_level=SpeedLevel.ULTRA_FAST)
    await cursor_controller.start()
    
    # Criar handlers
    def get_page():
        return page
    
    def get_cursor_controller():
        return cursor_controller
    
    handlers = CommandHandlers(
        yaml_writer=yaml_writer,
        page_getter=get_page,
        cursor_controller_getter=get_cursor_controller,
        recorder=None,
        recorder_logger=None
    )
    
    # Executar comandos
    print("▶️  Executando comandos até antes de 'Categorias'...\n")
    for i, command in enumerate(commands, 1):
        print(f"[{i}/{len(commands)}] {command}")
        
        # Parsear comando
        parts = command.split(None, 1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        
        # Parsear args
        if args.startswith('selector '):
            selector_part = args[9:].strip().strip('"\'')
            args = f"selector {selector_part}"
        else:
            args = args.strip('"\'')
        
        # Executar comando
        try:
            if cmd == "pw-click":
                result = await handlers.handle_pw_click(args)
            elif cmd == "pw-type":
                result = await handlers.handle_pw_type(args)
            elif cmd == "pw-submit":
                result = await handlers.handle_pw_submit(args)
            elif cmd == "pw-press":
                result = await handlers.handle_pw_press(args)
            else:
                print(f"  ⚠️  Comando desconhecido: {cmd}")
                continue
            
            if not result.get('success', False):
                error = result.get('error', 'Erro desconhecido')
                print(f"  ❌ Erro: {error}")
                # Capturar estado mesmo com erro
                await capture_page_state(page, DEBUG_OUTPUT_DIR / "error_state")
                return 1
            
            print(f"  ✅ Sucesso")
        except Exception as e:
            print(f"  ❌ Exceção: {e}")
            # Capturar estado mesmo com exceção
            await capture_page_state(page, DEBUG_OUTPUT_DIR / "error_state")
            return 1
    
    # Aguardar um pouco para página estabilizar
    print("\n⏳ Aguardando página estabilizar...")
    await asyncio.sleep(2)
    
    # Capturar estado da página ANTES de tentar clicar em "Categorias"
    print("\n" + "="*60)
    print("📸 CAPTURANDO ESTADO DA PÁGINA ANTES DE CLICAR EM 'CATEGORIAS'")
    print("="*60)
    await capture_page_state(page, DEBUG_OUTPUT_DIR / "before_categorias")
    
    # Tentar clicar em "Categorias" e capturar estado se falhar
    print("\n" + "="*60)
    print("🖱️  TENTANDO CLICAR EM 'CATEGORIAS'")
    print("="*60)
    try:
        result = await handlers.handle_pw_click("Categorias")
        if result.get('success', False):
            print("✅ Sucesso ao clicar em 'Categorias'!")
            await asyncio.sleep(1)
            await capture_page_state(page, DEBUG_OUTPUT_DIR / "after_categorias_success")
        else:
            print("❌ Falha ao clicar em 'Categorias'")
            await capture_page_state(page, DEBUG_OUTPUT_DIR / "after_categorias_failure")
    except Exception as e:
        print(f"❌ Exceção ao clicar em 'Categorias': {e}")
        await capture_page_state(page, DEBUG_OUTPUT_DIR / "after_categorias_exception")
    
    print(f"\n✅ Debug completo! Arquivos salvos em: {DEBUG_OUTPUT_DIR}")
    
    # Manter browser aberto por alguns segundos para inspeção manual
    print("\n⏳ Mantendo browser aberto por 10 segundos para inspeção...")
    await asyncio.sleep(10)
    
    # Fechar browser
    await browser_manager.stop()
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

