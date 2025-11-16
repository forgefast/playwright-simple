#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de Validação do Login.

Testa o fluxo completo de login e valida:
- Não há cliques duplicados
- Cursor mantém posição após navegação
- Todos os steps são executados corretamente
"""

import pytest
import asyncio
import logging
from playwright.async_api import async_playwright, Page
from playwright_simple.core.playwright_commands.element_interactions import ElementInteractions
from playwright_simple.core.logging_config import FrameworkLogger

# Configurar logging para capturar eventos
FrameworkLogger.configure(level='DEBUG', debug=True)
logger = logging.getLogger(__name__)


@pytest.fixture
async def browser_page():
    """Create a browser page for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        yield page
        await browser.close()


class LogCapture:
    """Captura logs para análise."""
    
    def __init__(self):
        self.logs = []
        self.clicks = []
        self.cursor_movements = []
        self.navigations = []
        self.handler = None
    
    def setup(self):
        """Setup log capture."""
        import logging
        
        class LogHandler(logging.Handler):
            def __init__(self, capture_instance):
                super().__init__()
                self.capture = capture_instance
            
            def emit(self, record):
                msg = self.format(record)
                self.capture.logs.append({
                    'level': record.levelname,
                    'message': msg,
                    'module': record.module,
                    'funcName': record.funcName
                })
                
                # Capturar cliques
                if 'click' in msg.lower() and '🖱️' in msg:
                    self.capture.clicks.append({
                        'message': msg,
                        'timestamp': record.created
                    })
                
                # Capturar movimentos de cursor
                if 'cursor' in msg.lower() and ('move' in msg.lower() or 'position' in msg.lower()):
                    self.capture.cursor_movements.append({
                        'message': msg,
                        'timestamp': record.created
                    })
                
                # Capturar navegações
                if 'navigation' in msg.lower() or 'navigate' in msg.lower():
                    self.capture.navigations.append({
                        'message': msg,
                        'timestamp': record.created
                    })
        
        self.handler = LogHandler(self)
        self.handler.setLevel(logging.DEBUG)
        
        # Adicionar handler aos loggers relevantes
        logging.getLogger('playwright_simple.core.playwright_commands.element_interactions').addHandler(self.handler)
        logging.getLogger('playwright_simple.core.playwright_commands.visual_feedback').addHandler(self.handler)
        logging.getLogger('playwright_simple.core.cursor').addHandler(self.handler)
        logging.getLogger('playwright_simple.core.runner').addHandler(self.handler)
    
    def teardown(self):
        """Remove log capture."""
        if self.handler:
            logging.getLogger('playwright_simple.core.playwright_commands.element_interactions').removeHandler(self.handler)
            logging.getLogger('playwright_simple.core.playwright_commands.visual_feedback').removeHandler(self.handler)
            logging.getLogger('playwright_simple.core.cursor').removeHandler(self.handler)
            logging.getLogger('playwright_simple.core.runner').removeHandler(self.handler)


@pytest.mark.asyncio
async def test_login_no_duplicate_clicks(browser_page: Page):
    """
    TDD: Testa que não há cliques duplicados durante o login.
    
    FALHA se:
    - Houver cliques duplicados no mesmo elemento
    - Clique em label causar clique duplicado no input associado
    """
    capture = LogCapture()
    capture.setup()
    
    try:
        await browser_page.set_content("""
            <html>
                <body>
                    <form id="login-form">
                        <label for="email">Email</label>
                        <input id="email" type="email" name="email" />
                        
                        <label for="password">Password</label>
                        <input id="password" type="password" name="password" />
                        
                        <button type="submit">Login</button>
                    </form>
                </body>
            </html>
        """)
        
        interactions = ElementInteractions(browser_page, fast_mode=True)
        
        # Executar fluxo de login
        await interactions.type_text(text="test@example.com", into="Email")
        
        # CRITICAL: Type password - clicar no label "Password" pode causar clique duplicado
        clicks_before_password = len(capture.clicks)
        await interactions.type_text(text="password123", into="Password")
        clicks_after_password = len(capture.clicks)
        
        await interactions.submit_form(button_text="Login")
        
        # Aguardar um pouco para capturar todos os logs
        await asyncio.sleep(0.5)
        
        # Analisar cliques capturados
        click_messages = capture.clicks
        
        # Verificar se há cliques duplicados no mesmo elemento
        # Cliques duplicados seriam cliques no mesmo elemento em menos de 200ms
        duplicate_clicks = []
        for i, click1 in enumerate(click_messages):
            for click2 in click_messages[i+1:]:
                time_diff = abs(click2['timestamp'] - click1['timestamp'])
                if time_diff < 0.2:  # 200ms
                    # Verificar se é o mesmo elemento (mesma mensagem ou muito similar)
                    msg1 = click1['message'].lower()
                    msg2 = click2['message'].lower()
                    # Se as mensagens são muito similares, pode ser duplicado
                    if msg1 == msg2 or (len(msg1) > 20 and msg1[:20] == msg2[:20]):
                        duplicate_clicks.append((click1, click2, time_diff))
        
        # Verificar especificamente cliques no password
        password_clicks = [c for c in click_messages if 'password' in c['message'].lower() or 'senha' in c['message'].lower()]
        password_duplicates = []
        for i, click1 in enumerate(password_clicks):
            for click2 in password_clicks[i+1:]:
                time_diff = abs(click2['timestamp'] - click1['timestamp'])
                if time_diff < 300:  # 300ms - janela para label->input
                    password_duplicates.append((click1, click2, time_diff))
        
        # Log detalhado para debug
        logger.info(f"Total de cliques capturados: {len(click_messages)}")
        logger.info(f"Cliques no password: {len(password_clicks)}")
        logger.info(f"Cliques duplicados encontrados: {len(duplicate_clicks)}")
        logger.info(f"Cliques duplicados no password: {len(password_duplicates)}")
        
        for click in click_messages:
            logger.debug(f"Click: {click['message']}")
        
        if duplicate_clicks:
            for dup1, dup2, time_diff in duplicate_clicks:
                logger.error(f"Clique duplicado detectado: {time_diff*1000:.0f}ms entre cliques")
                logger.error(f"  Click 1: {dup1['message']}")
                logger.error(f"  Click 2: {dup2['message']}")
        
        # CRITICAL ASSERT: não deve haver cliques duplicados no password
        assert len(password_duplicates) == 0, \
            f"❌ PROBLEMA DETECTADO: Cliques duplicados no password! " \
            f"Encontrados {len(password_duplicates)} pares de cliques duplicados. " \
            f"Total de cliques no password: {len(password_clicks)}. " \
            f"Detalhes: {password_duplicates}"
        
        # Assert: não deve haver cliques duplicados em geral
        assert len(duplicate_clicks) == 0, \
            f"❌ PROBLEMA DETECTADO: Encontrados {len(duplicate_clicks)} cliques duplicados durante o login"
        
    finally:
        capture.teardown()


@pytest.mark.asyncio
async def test_cursor_position_after_navigation(browser_page: Page):
    """
    TDD: Testa que o cursor mantém a posição após navegação.
    
    FALHA se:
    - Cursor for criado no centro após navegação
    - Cursor não manter posição original
    """
    from playwright_simple.core.cursor import CursorManager
    from playwright_simple.core.config import TestConfig
    
    config = TestConfig(base_url="http://localhost")
    cursor_manager = CursorManager(browser_page, config.cursor)
    
    # Iniciar cursor
    await cursor_manager.inject(force=True)
    
    # Mover cursor para posição específica (não centro)
    initial_x, initial_y = 500, 300
    await cursor_manager.move_to(initial_x, initial_y)
    await asyncio.sleep(0.2)  # Aguardar animação
    
    # Verificar posição inicial
    initial_pos = await browser_page.evaluate("""
        () => {
            const cursor = document.getElementById('playwright-cursor');
            if (!cursor) return null;
            return {
                x: parseFloat(cursor.style.left) || 0,
                y: parseFloat(cursor.style.top) || 0
            };
        }
    """)
    
    assert initial_pos is not None, "Cursor deve existir"
    assert abs(initial_pos['x'] - initial_x) < 5, f"Cursor X deve estar em {initial_x}, está em {initial_pos['x']}"
    assert abs(initial_pos['y'] - initial_y) < 5, f"Cursor Y deve estar em {initial_y}, está em {initial_pos['y']}"
    
    # Simular navegação (carregar nova página)
    await browser_page.set_content("""
        <html>
            <body>
                <h1>Nova Página</h1>
            </body>
        </html>
    """)
    
    # Aguardar cursor ser restaurado
    await asyncio.sleep(0.5)
    
    # Verificar se cursor foi restaurado na mesma posição
    # O cursor deve ser reinjetado após navegação
    await cursor_manager.inject(force=True)
    await asyncio.sleep(0.3)
    
    final_pos = await browser_page.evaluate("""
        () => {
            const cursor = document.getElementById('playwright-cursor');
            if (!cursor) return null;
            return {
                x: parseFloat(cursor.style.left) || 0,
                y: parseFloat(cursor.style.top) || 0
            };
        }
    """)
    
    assert final_pos is not None, "Cursor deve existir após navegação"
    
    # CRITICAL: Verificar que NÃO está no centro
    viewport = browser_page.viewport_size
    center_x = viewport['width'] / 2
    center_y = viewport['height'] / 2
    
    x_diff_from_center = abs(final_pos['x'] - center_x)
    y_diff_from_center = abs(final_pos['y'] - center_y)
    is_at_center = x_diff_from_center < 30 and y_diff_from_center < 30
    
    assert not is_at_center, \
        f"❌ PROBLEMA DETECTADO: Cursor está no centro após navegação! " \
        f"Posição: ({final_pos['x']}, {final_pos['y']}), " \
        f"Centro: ({center_x}, {center_y}), " \
        f"Esperado próximo de: ({initial_x}, {initial_y})"
    
    # Verificar se a posição foi mantida (com tolerância de 10px)
    x_diff = abs(final_pos['x'] - initial_x)
    y_diff = abs(final_pos['y'] - initial_y)
    
    assert x_diff < 10, \
        f"❌ PROBLEMA DETECTADO: Cursor X não manteve posição após navegação. " \
        f"Esperado: {initial_x}, Atual: {final_pos['x']}, Diferença: {x_diff}"
    assert y_diff < 10, \
        f"❌ PROBLEMA DETECTADO: Cursor Y não manteve posição após navegação. " \
        f"Esperado: {initial_y}, Atual: {final_pos['y']}, Diferença: {y_diff}"


@pytest.mark.asyncio
async def test_login_complete_flow_with_validation(browser_page: Page):
    """
    TDD: Testa o fluxo completo de login e FALHA se houver problemas.
    
    Problemas que devem ser detectados:
    - Cliques duplicados no password após clicar no label
    - Cursor sendo criado no centro após navegação (se houver)
    """
    from playwright_simple.core import CursorManager, TestConfig
    
    capture = LogCapture()
    capture.setup()
    
    try:
        config = TestConfig(base_url="http://localhost")
        cursor_manager = CursorManager(browser_page, config.cursor)
        
        # Setup: página inicial com link de login (simula navegação real)
        await browser_page.set_content("""
            <html>
                <body>
                    <a href="#login" id="login-link">Entrar</a>
                    <div id="login" style="display:none;">
                        <form id="login-form">
                            <label for="email">Email</label>
                            <input id="email" type="email" name="email" />
                            
                            <label for="password">Password</label>
                            <input id="password" type="password" name="password" />
                            
                            <button type="submit">Login</button>
                        </form>
                    </div>
                </body>
            </html>
        """)
        
        # Injetar cursor
        await cursor_manager.inject(force=True)
        
        # Mover cursor para posição inicial (não centro)
        initial_x, initial_y = 500, 300
        await cursor_manager.move_to(initial_x, initial_y)
        await asyncio.sleep(0.2)
        
        # Verificar posição inicial
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
        
        assert pos_before is not None, "Cursor deve existir"
        assert abs(pos_before['x'] - initial_x) < 5, f"Cursor deve estar em {initial_x} antes do login"
        
        interactions = ElementInteractions(browser_page, fast_mode=True)
        
        # Step 1: Clicar em link "Entrar" (causa navegação)
        result = await interactions.click(text="Entrar")
        assert result is True, "Click em 'Entrar' deve funcionar"
        
        # Simular navegação (carregar página de login)
        await browser_page.set_content("""
            <html>
                <body>
                    <form id="login-form">
                        <label for="email">Email</label>
                        <input id="email" type="email" name="email" />
                        
                        <label for="password">Password</label>
                        <input id="password" type="password" name="password" />
                        
                        <button type="submit">Login</button>
                    </form>
                </body>
            </html>
        """)
        
        # Aguardar cursor ser restaurado após navegação
        await asyncio.sleep(0.3)
        await cursor_manager.inject(force=True)
        await asyncio.sleep(0.3)
        
        # CRITICAL TEST 1: Cursor NÃO deve estar no centro após navegação
        viewport = browser_page.viewport_size
        center_x = viewport['width'] / 2
        center_y = viewport['height'] / 2
        
        pos_after_nav = await browser_page.evaluate("""
            () => {
                const cursor = document.getElementById('playwright-cursor');
                if (!cursor) return null;
                return {
                    x: parseFloat(cursor.style.left) || 0,
                    y: parseFloat(cursor.style.top) || 0
                };
            }
        """)
        
        assert pos_after_nav is not None, "Cursor deve existir após navegação"
        
        x_diff_from_center = abs(pos_after_nav['x'] - center_x)
        y_diff_from_center = abs(pos_after_nav['y'] - center_y)
        is_at_center = x_diff_from_center < 30 and y_diff_from_center < 30
        
        assert not is_at_center, \
            f"❌ PROBLEMA DETECTADO: Cursor está no centro após navegação! " \
            f"Posição: ({pos_after_nav['x']}, {pos_after_nav['y']}), " \
            f"Centro: ({center_x}, {center_y}), " \
            f"Esperado próximo de: ({initial_x}, {initial_y})"
        
        # Verificar que está próximo da posição original
        x_diff_from_initial = abs(pos_after_nav['x'] - initial_x)
        y_diff_from_initial = abs(pos_after_nav['y'] - initial_y)
        
        assert x_diff_from_initial < 50, \
            f"❌ PROBLEMA DETECTADO: Cursor não manteve posição após navegação. " \
            f"Esperado X: {initial_x}, Atual: {pos_after_nav['x']}, Diferença: {x_diff_from_initial}"
        
        # Step 2: Type email
        result = await interactions.type_text(text="test@example.com", into="Email")
        assert result is True, "Type email deve funcionar"
        
        email_value = await browser_page.evaluate("document.getElementById('email').value")
        assert email_value == "test@example.com", f"Email deve ser 'test@example.com', got '{email_value}'"
        
        # Step 3: Type password (clicar no label "Password" pode causar clique duplicado)
        # CRITICAL TEST 2: Não deve haver clique duplicado no password
        clicks_before_password = len(capture.clicks)
        
        result = await interactions.type_text(text="password123", into="Password")
        assert result is True, "Type password deve funcionar"
        
        password_value = await browser_page.evaluate("document.getElementById('password').value")
        assert password_value == "password123", f"Password deve ser 'password123', got '{password_value}'"
        
        # Aguardar logs
        await asyncio.sleep(0.5)
        
        # Verificar cliques capturados
        clicks_after_password = len(capture.clicks)
        password_clicks = [c for c in capture.clicks if 'password' in c['message'].lower() or 'senha' in c['message'].lower()]
        
        # CRITICAL: Não deve haver múltiplos cliques no password
        # Um clique no label "Password" pode causar um clique automático no input
        # Mas o sistema deve filtrar o clique duplicado
        duplicate_password_clicks = []
        for i, click1 in enumerate(password_clicks):
            for click2 in password_clicks[i+1:]:
                time_diff = abs(click2['timestamp'] - click1['timestamp'])
                if time_diff < 300:  # 300ms - janela para label->input
                    duplicate_password_clicks.append((click1, click2, time_diff))
        
        assert len(duplicate_password_clicks) == 0, \
            f"❌ PROBLEMA DETECTADO: Cliques duplicados no password! " \
            f"Encontrados {len(duplicate_password_clicks)} pares de cliques duplicados. " \
            f"Total de cliques no password: {len(password_clicks)}. " \
            f"Detalhes: {duplicate_password_clicks}"
        
        # Validar que não há cliques duplicados em geral
        all_duplicate_clicks = []
        for i, click1 in enumerate(capture.clicks):
            for click2 in capture.clicks[i+1:]:
                time_diff = abs(click2['timestamp'] - click1['timestamp'])
                if time_diff < 0.2:  # 200ms
                    msg1 = click1['message'].lower()
                    msg2 = click2['message'].lower()
                    if msg1 == msg2 or (len(msg1) > 20 and msg1[:20] == msg2[:20]):
                        all_duplicate_clicks.append((click1, click2, time_diff))
        
        assert len(all_duplicate_clicks) == 0, \
            f"❌ PROBLEMA DETECTADO: Encontrados {len(all_duplicate_clicks)} cliques duplicados no fluxo completo"
        
        # Step 4: Submit
        result = await interactions.submit_form(button_text="Login")
        assert result is True, "Submit deve funcionar"
        
        # Validar que todos os steps foram executados
        assert email_value == "test@example.com", "Email deve estar preenchido"
        assert password_value == "password123", "Password deve estar preenchido"
        
    finally:
        capture.teardown()


@pytest.mark.asyncio
async def test_cursor_not_created_at_center_after_navigation(browser_page: Page):
    """
    TDD: Testa que o cursor não é criado no centro da tela após navegação.
    
    FALHA se:
    - Cursor for criado no centro após navegação
    - Cursor não manter posição original
    """
    from playwright_simple.core import CursorManager, TestConfig
    
    config = TestConfig(base_url="http://localhost")
    cursor_manager = CursorManager(browser_page, config.cursor)
    
    # Iniciar cursor
    await cursor_manager.inject(force=True)
    
    # Mover cursor para posição específica (não centro)
    target_x, target_y = 600, 400
    await cursor_manager.move_to(target_x, target_y)
    await asyncio.sleep(0.3)
    
    # Obter dimensões da viewport
    viewport = browser_page.viewport_size
    center_x = viewport['width'] / 2
    center_y = viewport['height'] / 2
    
    # Simular navegação
    await browser_page.set_content("""
        <html>
            <body>
                <h1>Nova Página Após Navegação</h1>
            </body>
        </html>
    """)
    
    # Aguardar e reinjetar cursor
    await asyncio.sleep(0.5)
    await cursor_manager.inject(force=True)
    await asyncio.sleep(0.3)
    
    # Verificar posição do cursor
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
    
    # CRITICAL: Verificar que NÃO está no centro
    x_diff_from_center = abs(cursor_pos['x'] - center_x)
    y_diff_from_center = abs(cursor_pos['y'] - center_y)
    is_too_close_to_center = x_diff_from_center < 30 and y_diff_from_center < 30
    
    assert not is_too_close_to_center, \
        f"❌ PROBLEMA DETECTADO: Cursor está no centro após navegação! " \
        f"Posição: ({cursor_pos['x']}, {cursor_pos['y']}), " \
        f"Centro: ({center_x}, {center_y}), " \
        f"Diferença: ({x_diff_from_center}, {y_diff_from_center}), " \
        f"Esperado próximo de: ({target_x}, {target_y})"
    
    # Verificar que está próximo da posição original (tolerância de 50px para permitir pequenas variações)
    x_diff_from_target = abs(cursor_pos['x'] - target_x)
    y_diff_from_target = abs(cursor_pos['y'] - target_y)
    
    assert x_diff_from_target < 50, \
        f"❌ PROBLEMA DETECTADO: Cursor não manteve posição após navegação. " \
        f"Esperado X: {target_x}, Atual: {cursor_pos['x']}, Diferença: {x_diff_from_target}"
    assert y_diff_from_target < 50, \
        f"❌ PROBLEMA DETECTADO: Cursor não manteve posição após navegação. " \
        f"Esperado Y: {target_y}, Atual: {cursor_pos['y']}, Diferença: {y_diff_from_target}"

