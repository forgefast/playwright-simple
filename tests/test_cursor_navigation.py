#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes TDD para comportamento do cursor após navegação.

Estes testes definem o comportamento ESPERADO do cursor:
- Cursor deve manter posição após clicar em link que causa navegação
- Cursor NÃO deve ser criado no centro após navegação
- Posição do cursor deve ser salva ANTES do clique causar navegação
"""

import pytest
import asyncio
import logging
from playwright.async_api import async_playwright, Page
from playwright_simple.core import CursorManager, TestConfig
from playwright_simple.core.playwright_commands.element_interactions import ElementInteractions

logger = logging.getLogger(__name__)


@pytest.fixture
async def browser_page():
    """Create a browser page for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        yield page
        await browser.close()


@pytest.mark.asyncio
async def test_cursor_position_saved_before_link_click(browser_page: Page):
    """
    TDD: Cursor deve salvar posição ANTES de clicar em link que causa navegação.
    
    Comportamento esperado:
    - Quando o cursor está em uma posição (x, y)
    - E clica em um link que causa navegação
    - A posição (x, y) deve ser salva ANTES da navegação acontecer
    - Após navegação, o cursor deve ser restaurado na mesma posição (x, y)
    """
    config = TestConfig(base_url="http://localhost")
    cursor_manager = CursorManager(browser_page, config.cursor)
    
    # Setup: página com link
    await browser_page.set_content("""
        <html>
            <body>
                <a href="#page2" id="link">Go to Page 2</a>
                <div id="page2" style="display:none;">Page 2 Content</div>
            </body>
        </html>
    """)
    
    # Injetar cursor
    await cursor_manager.inject(force=True)
    
    # Mover cursor para posição específica (não centro)
    target_x, target_y = 500, 300
    await cursor_manager.move_to(target_x, target_y)
    await asyncio.sleep(0.2)
    
    # Verificar posição antes do clique
    pos_before = await browser_page.evaluate("""
        () => {
            const cursor = document.getElementById('playwright-cursor');
            if (!cursor) return null;
            return {
                x: parseFloat(cursor.style.left) || 0,
                y: parseFloat(cursor.style.top) || 0
            };
        }
    """)
    
    assert pos_before is not None, "Cursor deve existir antes do clique"
    assert abs(pos_before['x'] - target_x) < 5, f"Cursor deve estar em {target_x} antes do clique"
    assert abs(pos_before['y'] - target_y) < 5, f"Cursor deve estar em {target_y} antes do clique"
    
    # Verificar se posição foi salva no storage
    saved_pos = await browser_page.evaluate("""
        () => {
            try {
                const stored = sessionStorage.getItem('__playwright_cursor_last_position');
                if (stored) {
                    return JSON.parse(stored);
                }
            } catch (e) {}
            return window.__playwright_cursor_last_position || null;
        }
    """)
    
    assert saved_pos is not None, "Posição do cursor deve estar salva no storage"
    assert abs(saved_pos['x'] - target_x) < 5, f"Posição salva X deve ser {target_x}"
    assert abs(saved_pos['y'] - target_y) < 5, f"Posição salva Y deve ser {target_y}"
    
    # Simular clique em link (que causa navegação)
    # Em um teste real, isso seria feito via ElementInteractions, mas aqui simulamos
    await browser_page.evaluate("""
        () => {
            const link = document.getElementById('link');
            if (link) {
                // Simular clique que causa navegação
                link.click();
            }
        }
    """)
    
    # Simular navegação (carregar nova página)
    await browser_page.set_content("""
        <html>
            <body>
                <h1>Nova Página Após Navegação</h1>
            </body>
        </html>
    """)
    
    # Aguardar cursor ser restaurado
    await asyncio.sleep(0.3)
    await cursor_manager.inject(force=True)
    await asyncio.sleep(0.3)
    
    # Verificar posição após navegação
    pos_after = await browser_page.evaluate("""
        () => {
            const cursor = document.getElementById('playwright-cursor');
            if (!cursor) return null;
            return {
                x: parseFloat(cursor.style.left) || 0,
                y: parseFloat(cursor.style.top) || 0
            };
        }
    """)
    
    assert pos_after is not None, "Cursor deve existir após navegação"
    
    # CRITICAL: Cursor deve estar na mesma posição (não no centro)
    x_diff = abs(pos_after['x'] - target_x)
    y_diff = abs(pos_after['y'] - target_y)
    
    assert x_diff < 20, \
        f"Cursor X deve manter posição após navegação. Esperado: {target_x}, Atual: {pos_after['x']}, Diferença: {x_diff}"
    assert y_diff < 20, \
        f"Cursor Y deve manter posição após navegação. Esperado: {target_y}, Atual: {pos_after['y']}, Diferença: {y_diff}"


@pytest.mark.asyncio
async def test_cursor_not_created_at_center_after_link_navigation(browser_page: Page):
    """
    TDD: Cursor NÃO deve ser criado no centro após navegação causada por clique em link.
    
    Comportamento esperado:
    - Cursor em posição (x, y) antes de clicar em link
    - Após navegação, cursor deve ser restaurado em (x, y), NÃO no centro
    """
    config = TestConfig(base_url="http://localhost")
    cursor_manager = CursorManager(browser_page, config.cursor)
    
    await browser_page.set_content("""
        <html>
            <body>
                <a href="#page2" id="link">Go to Page 2</a>
            </body>
        </html>
    """)
    
    await cursor_manager.inject(force=True)
    
    # Mover para posição específica (longe do centro)
    target_x, target_y = 600, 400
    await cursor_manager.move_to(target_x, target_y)
    await asyncio.sleep(0.2)
    
    # Obter dimensões da viewport
    viewport = browser_page.viewport_size
    center_x = viewport['width'] / 2
    center_y = viewport['height'] / 2
    
    # Simular navegação
    await browser_page.set_content("""
        <html>
            <body>
                <h1>Nova Página</h1>
            </body>
        </html>
    """)
    
    await asyncio.sleep(0.3)
    await cursor_manager.inject(force=True)
    await asyncio.sleep(0.3)
    
    # Verificar posição
    cursor_pos = await browser_page.evaluate("""
        () => {
            const cursor = document.getElementById('playwright-cursor');
            if (!cursor) return null;
            return {
                x: parseFloat(cursor.style.left) || 0,
                y: parseFloat(cursor.style.top) || 0
            };
        }
    """)
    
    assert cursor_pos is not None, "Cursor deve existir após navegação"
    
    # Verificar que NÃO está no centro
    x_diff_from_center = abs(cursor_pos['x'] - center_x)
    y_diff_from_center = abs(cursor_pos['y'] - center_y)
    
    is_too_close_to_center = x_diff_from_center < 30 and y_diff_from_center < 30
    
    assert not is_too_close_to_center, \
        f"Cursor NÃO deve estar no centro após navegação. Posição: ({cursor_pos['x']}, {cursor_pos['y']}), Centro: ({center_x}, {center_y})"
    
    # Verificar que está próximo da posição original
    x_diff_from_target = abs(cursor_pos['x'] - target_x)
    y_diff_from_target = abs(cursor_pos['y'] - target_y)
    
    assert x_diff_from_target < 50, \
        f"Cursor deve estar próximo da posição original. Esperado X: {target_x}, Atual: {cursor_pos['x']}"
    assert y_diff_from_target < 50, \
        f"Cursor deve estar próximo da posição original. Esperado Y: {target_y}, Atual: {cursor_pos['y']}"


@pytest.mark.asyncio
async def test_no_duplicate_click_after_label_click(browser_page: Page):
    """
    TDD: Clique em label NÃO deve gerar clique duplicado no input associado.
    
    Comportamento esperado:
    - Quando clica em um label (ex: "Senha")
    - O label automaticamente foca/clica no input associado
    - O sistema deve capturar APENAS o clique no label
    - NÃO deve capturar o clique automático no input
    """
    from playwright_simple.core.recorder.action_converter import ActionConverter
    
    converter = ActionConverter()
    
    # Simular clique em label
    label_click_event = {
        'type': 'click',
        'timestamp': 1000,
        'element': {
            'tagName': 'LABEL',
            'text': 'Senha',
            'id': '',
            'name': '',
            'label': ''
        }
    }
    
    # Converter clique no label
    label_action = converter.convert_click(label_click_event)
    assert label_action is not None, "Clique no label deve ser capturado"
    assert label_action['action'] == 'click', "Clique no label deve ser ação 'click'"
    
    # Simular clique automático no input (causado pelo label) - deve ser FILTRADO
    input_click_event = {
        'type': 'click',
        'timestamp': 1100,  # 100ms depois (dentro da janela de 300ms)
        'element': {
            'tagName': 'INPUT',
            'text': '',
            'id': 'password',
            'name': 'password',
            'type': 'password',
            'placeholder': '',
            'label': 'Senha'  # Mesmo label
        }
    }
    
    # Converter clique no input - deve ser FILTRADO
    input_action = converter.convert_click(input_click_event)
    assert input_action is None, \
        "Clique no input após clique no label deve ser FILTRADO (não deve gerar ação duplicada)"
    
    # Verificar que apenas o clique no label foi capturado
    assert converter._last_click['tag'] == 'LABEL', "Último clique registrado deve ser no label"
    assert converter._last_click['text'].lower() == 'senha', "Último clique deve ter texto 'Senha'"


@pytest.mark.asyncio
async def test_label_click_filters_associated_input_click(browser_page: Page):
    """
    TDD: Sistema deve detectar e filtrar cliques em input causados por clique em label.
    
    Comportamento esperado:
    - Clique em label "Senha" com for="password"
    - Clique automático em input#password (causado pelo label)
    - Apenas o clique no label deve ser capturado
    """
    from playwright_simple.core.recorder.action_converter import ActionConverter
    
    converter = ActionConverter()
    
    # Clique no label
    label_event = {
        'type': 'click',
        'timestamp': 1000,
        'element': {
            'tagName': 'LABEL',
            'text': 'Senha',
            'id': 'label-password',
            'name': '',
            'label': ''
        }
    }
    
    label_action = converter.convert_click(label_event)
    assert label_action is not None, "Clique no label deve ser capturado"
    
    # Clique automático no input associado (via for="password")
    input_event = {
        'type': 'click',
        'timestamp': 1050,  # 50ms depois
        'element': {
            'tagName': 'INPUT',
            'text': '',
            'id': 'password',
            'name': 'password',
            'type': 'password',
            'placeholder': '',
            'label': 'Senha'  # Label associado
        }
    }
    
    # Deve ser filtrado
    input_action = converter.convert_click(input_event)
    assert input_action is None, \
        "Clique no input após clique no label associado deve ser FILTRADO"


@pytest.mark.asyncio
async def test_cursor_position_persisted_across_multiple_navigations(browser_page: Page):
    """
    TDD: Cursor deve manter posição através de múltiplas navegações.
    
    Comportamento esperado:
    - Cursor em posição (x, y)
    - Navegação 1: cursor mantém (x, y)
    - Navegação 2: cursor ainda mantém (x, y)
    - Posição deve persistir em sessionStorage
    """
    config = TestConfig(base_url="http://localhost")
    cursor_manager = CursorManager(browser_page, config.cursor)
    
    await browser_page.set_content("<html><body><h1>Page 1</h1></body></html>")
    await cursor_manager.inject(force=True)
    
    target_x, target_y = 700, 500
    await cursor_manager.move_to(target_x, target_y)
    await asyncio.sleep(0.2)
    
    # Primeira navegação
    await browser_page.set_content("<html><body><h1>Page 2</h1></body></html>")
    await asyncio.sleep(0.3)
    await cursor_manager.inject(force=True)
    await asyncio.sleep(0.2)
    
    pos1 = await browser_page.evaluate("""
        () => {
            const cursor = document.getElementById('playwright-cursor');
            if (!cursor) return null;
            return {
                x: parseFloat(cursor.style.left) || 0,
                y: parseFloat(cursor.style.top) || 0
            };
        }
    """)
    
    assert pos1 is not None, "Cursor deve existir após primeira navegação"
    assert abs(pos1['x'] - target_x) < 20, f"Posição X deve ser mantida após primeira navegação"
    assert abs(pos1['y'] - target_y) < 20, f"Posição Y deve ser mantida após primeira navegação"
    
    # Segunda navegação
    await browser_page.set_content("<html><body><h1>Page 3</h1></body></html>")
    await asyncio.sleep(0.3)
    await cursor_manager.inject(force=True)
    await asyncio.sleep(0.2)
    
    pos2 = await browser_page.evaluate("""
        () => {
            const cursor = document.getElementById('playwright-cursor');
            if (!cursor) return null;
            return {
                x: parseFloat(cursor.style.left) || 0,
                y: parseFloat(cursor.style.top) || 0
            };
        }
    """)
    
    assert pos2 is not None, "Cursor deve existir após segunda navegação"
    assert abs(pos2['x'] - target_x) < 20, f"Posição X deve ser mantida após segunda navegação"
    assert abs(pos2['y'] - target_y) < 20, f"Posição Y deve ser mantida após segunda navegação"

