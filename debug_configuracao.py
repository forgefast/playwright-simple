#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug para investigar o que aparece após clicar em "Configuração".
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
from playwright_simple.core.recorder.utils.browser import BrowserManager
from playwright_simple.core.recorder.command_handlers.handlers import CommandHandlers
from playwright_simple.core.recorder.yaml_writer import YAMLWriter
from playwright_simple.core.recorder.action_converter import ActionConverter
from playwright_simple.core.recorder.event_handlers import EventHandlers
from playwright_simple.core.recorder.cursor_controller.controller import CursorController
from playwright_simple.core.recorder.config import SpeedLevel

BASE_URL = "http://localhost:18069"
HEADLESS = False

async def main():
    browser_manager = BrowserManager(headless=HEADLESS)
    page = await browser_manager.start()
    await page.goto(BASE_URL)
    
    yaml_writer = YAMLWriter(output_path=project_root / "temp_test.yaml")
    action_converter = ActionConverter()
    event_handlers = EventHandlers(yaml_writer, action_converter)
    
    cursor_controller = CursorController(page, speed_level=SpeedLevel.ULTRA_FAST)
    await cursor_controller.start()
    
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
    
    # Login
    print("1. Login...")
    await handlers.handle_pw_click("Entrar")
    await handlers.handle_pw_type("admin", "E-mail")
    await handlers.handle_pw_type("admin", "Senha")
    await handlers.handle_pw_submit("Entrar")
    await asyncio.sleep(1)
    
    # Abrir menu Apps
    print("2. Abrindo menu Apps...")
    await handlers.handle_pw_click("selector button.o_grid_apps_menu__button")
    await asyncio.sleep(1)
    
    # Clicar em Contatos
    print("3. Clicando em Contatos...")
    await handlers.handle_pw_click("Contatos")
    await asyncio.sleep(2)
    
    # Clicar em Configuração
    print("4. Clicando em Configuração...")
    result = await handlers.handle_pw_click("Configuração")
    print(f"   Resultado: {result}")
    await asyncio.sleep(2)
    
    # Capturar elementos visíveis
    print("5. Capturando elementos visíveis...")
    elements = await page.evaluate("""
        () => {
            const all = Array.from(document.querySelectorAll('button, a, [role="button"], [role="menuitem"]'));
            const visible = all.filter(el => {
                return el.offsetParent !== null && 
                       el.style.display !== 'none' && 
                       el.style.visibility !== 'hidden';
            });
            
            return visible.map(el => {
                const text = (el.textContent || el.value || el.getAttribute('aria-label') || '').trim();
                return {
                    text: text,
                    tag: el.tagName,
                    role: el.getAttribute('role') || '',
                    href: el.href || '',
                    className: el.className || '',
                    id: el.id || ''
                };
            }).filter(item => item.text.length > 0);
        }
    """)
    
    print(f"\n📋 {len(elements)} elementos visíveis encontrados:")
    for el in elements[:50]:  # Mostrar primeiros 50
        if 'tag' in el.get('text', '').lower() or 'categoria' in el.get('text', '').lower() or 'contact' in el.get('text', '').lower():
            print(f"   ⭐ '{el['text']}' ({el['tag']}, role={el['role']}, class={el['className'][:50]})")
        else:
            print(f"   - '{el['text']}' ({el['tag']}, role={el['role']})")
    
    # Buscar especificamente por variações de "Contact Tags"
    print("\n🔍 Buscando variações de 'Contact Tags'...")
    variations = ['contact tags', 'contacttags', 'tags', 'categorias', 'categoria']
    for variation in variations:
        matching = [el for el in elements if variation in el['text'].lower()]
        if matching:
            print(f"   ✅ Encontrado '{variation}':")
            for match in matching:
                print(f"      - '{match['text']}'")
    
    await asyncio.sleep(5)
    await browser_manager.stop()

if __name__ == '__main__':
    asyncio.run(main())

