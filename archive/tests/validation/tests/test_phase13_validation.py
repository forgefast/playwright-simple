#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de validação para FASE 13: Interface de Comandos CLI para Gravação Ativa.
"""

import pytest
from pathlib import Path
import subprocess
import sys


class TestPhase13Modules:
    """Testes de existência e importação de módulos."""
    
    def test_playwright_commands_exists(self):
        """Verifica que PlaywrightCommands existe."""
        from playwright_simple.core.playwright_commands import PlaywrightCommands
        assert PlaywrightCommands is not None
    
    def test_command_server_exists(self):
        """Verifica que CommandServer existe."""
        from playwright_simple.core.recorder.command_server import CommandServer
        assert CommandServer is not None
    
    def test_send_command_exists(self):
        """Verifica que send_command existe."""
        from playwright_simple.core.recorder.command_server import send_command
        assert send_command is not None
    
    def test_find_active_sessions_exists(self):
        """Verifica que find_active_sessions existe."""
        from playwright_simple.core.recorder.command_server import find_active_sessions
        assert find_active_sessions is not None


class TestPhase13PlaywrightCommands:
    """Testes da interface PlaywrightCommands."""
    
    def test_playwright_commands_has_methods(self):
        """Verifica que PlaywrightCommands tem todos os métodos necessários."""
        from playwright_simple.core.playwright_commands import PlaywrightCommands
        
        methods = [
            'find_element',
            'find_all_elements',
            'click',
            'type_text',
            'wait_for_element',
            'get_page_info',
            'get_html',
            'navigate',
            'take_screenshot'
        ]
        
        for method in methods:
            assert hasattr(PlaywrightCommands, method), f"Método {method} não encontrado"
    
    def test_playwright_commands_init(self):
        """Verifica que PlaywrightCommands pode ser inicializado."""
        from playwright_simple.core.playwright_commands import PlaywrightCommands
        from unittest.mock import MagicMock
        
        mock_page = MagicMock()
        commands = PlaywrightCommands(mock_page)
        assert commands.page == mock_page


class TestPhase13CommandServer:
    """Testes do CommandServer."""
    
    def test_command_server_init(self):
        """Verifica que CommandServer pode ser inicializado."""
        from playwright_simple.core.recorder.command_server import CommandServer
        from unittest.mock import MagicMock
        
        mock_recorder = MagicMock()
        server = CommandServer(mock_recorder, session_id='test_session')
        
        assert server.recorder == mock_recorder
        assert server.session_id == 'test_session'
        assert server.command_file is not None
        assert server.response_file is not None
        assert server.lock_file is not None
    
    def test_command_server_has_handlers(self):
        """Verifica que CommandServer tem handlers registrados."""
        from playwright_simple.core.recorder.command_server import CommandServer
        from unittest.mock import MagicMock
        
        mock_recorder = MagicMock()
        server = CommandServer(mock_recorder)
        
        # Verificar que handlers padrão estão registrados
        assert 'find' in server.command_handlers
        assert 'find-all' in server.command_handlers
        assert 'click' in server.command_handlers
        assert 'type' in server.command_handlers
        assert 'wait' in server.command_handlers
        assert 'info' in server.command_handlers
        assert 'navigate' in server.command_handlers


class TestPhase13CLI:
    """Testes dos comandos CLI."""
    
    def test_cli_find_command_exists(self):
        """Verifica que comando 'find' existe no CLI."""
        result = subprocess.run(
            [sys.executable, '-m', 'playwright_simple.cli', 'find', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Erro: {result.stderr}"
        assert 'find' in result.stdout.lower() or 'encontrar' in result.stdout.lower()
    
    def test_cli_click_command_exists(self):
        """Verifica que comando 'click' existe no CLI."""
        result = subprocess.run(
            [sys.executable, '-m', 'playwright_simple.cli', 'click', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Erro: {result.stderr}"
        assert 'click' in result.stdout.lower() or 'clicar' in result.stdout.lower()
    
    def test_cli_type_command_exists(self):
        """Verifica que comando 'type' existe no CLI."""
        result = subprocess.run(
            [sys.executable, '-m', 'playwright_simple.cli', 'type', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Erro: {result.stderr}"
        assert 'type' in result.stdout.lower() or 'digitar' in result.stdout.lower()
    
    def test_cli_wait_command_exists(self):
        """Verifica que comando 'wait' existe no CLI."""
        result = subprocess.run(
            [sys.executable, '-m', 'playwright_simple.cli', 'wait', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Erro: {result.stderr}"
        assert 'wait' in result.stdout.lower() or 'esperar' in result.stdout.lower()
    
    def test_cli_info_command_exists(self):
        """Verifica que comando 'info' existe no CLI."""
        result = subprocess.run(
            [sys.executable, '-m', 'playwright_simple.cli', 'info', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Erro: {result.stderr}"
        assert 'info' in result.stdout.lower() or 'informações' in result.stdout.lower()
    
    def test_cli_html_command_exists(self):
        """Verifica que comando 'html' existe no CLI."""
        result = subprocess.run(
            [sys.executable, '-m', 'playwright_simple.cli', 'html', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Erro: {result.stderr}"
        assert 'html' in result.stdout.lower()


class TestPhase13RecorderIntegration:
    """Testes de integração com Recorder."""
    
    def test_recorder_has_command_server(self):
        """Verifica que Recorder tem suporte a CommandServer."""
        from playwright_simple.core.recorder.recorder import Recorder
        from pathlib import Path
        
        recorder = Recorder(Path('test.yaml'))
        
        # Verificar que command_server existe (pode ser None inicialmente)
        assert hasattr(recorder, 'command_server')
    
    def test_recorder_imports_command_server(self):
        """Verifica que Recorder importa CommandServer."""
        from pathlib import Path
        recorder_file = Path("playwright_simple/core/recorder/recorder.py")
        
        if recorder_file.exists():
            content = recorder_file.read_text()
            assert "from .command_server import CommandServer" in content or "CommandServer" in content


class TestPhase13LinkCapture:
    """Testes de melhorias na captura de links."""
    
    def test_event_capture_captures_links(self):
        """Verifica que event_capture captura links sempre."""
        from pathlib import Path
        event_capture_file = Path("playwright_simple/core/recorder/event_capture.py")
        
        if event_capture_file.exists():
            content = event_capture_file.read_text()
            
            # Verificar que tem lógica especial para links
            has_link_capture = (
                "tag === 'A' && hasHref" in content or
                "tag === 'A'" in content and "hasHref" in content
            )
            assert has_link_capture, "EventCapture não tem lógica especial para capturar links"
    
    def test_link_capture_always_captures(self):
        """Verifica que links são sempre capturados, mesmo sem texto."""
        from pathlib import Path
        event_capture_file = Path("playwright_simple/core/recorder/event_capture.py")
        
        if event_capture_file.exists():
            content = event_capture_file.read_text()
            
            # Verificar que links são capturados antes da verificação de texto
            # (early return para links)
            has_early_return = (
                "return; // Early return for links" in content or
                "early return" in content.lower()
            )
            assert has_early_return, "Links não têm early return (podem ser ignorados)"


class TestPhase13Documentation:
    """Testes de documentação."""
    
    def test_cli_commands_docs_exist(self):
        """Verifica que documentação CLI_COMMANDS.md existe."""
        docs_file = Path("docs/CLI_COMMANDS.md")
        assert docs_file.exists(), "docs/CLI_COMMANDS.md não encontrado"
    
    def test_playwright_commands_docs_exist(self):
        """Verifica que documentação PLAYWRIGHT_COMMANDS.md existe."""
        docs_file = Path("docs/PLAYWRIGHT_COMMANDS.md")
        assert docs_file.exists(), "docs/PLAYWRIGHT_COMMANDS.md não encontrado"
    
    def test_docs_have_content(self):
        """Verifica que documentação tem conteúdo."""
        cli_docs = Path("docs/CLI_COMMANDS.md")
        pw_docs = Path("docs/PLAYWRIGHT_COMMANDS.md")
        
        if cli_docs.exists():
            content = cli_docs.read_text()
            assert len(content) > 500, "CLI_COMMANDS.md muito curto"
            assert 'find' in content.lower() or 'encontrar' in content.lower()
        
        if pw_docs.exists():
            content = pw_docs.read_text()
            assert len(content) > 500, "PLAYWRIGHT_COMMANDS.md muito curto"
            # Verificar que tem conteúdo sobre comandos ou interface
            has_content = (
                'playwright' in content.lower() or
                'comandos' in content.lower() or
                'interface' in content.lower() or
                'commands' in content.lower()
            )
            assert has_content, "PLAYWRIGHT_COMMANDS.md não tem conteúdo relevante"
    
    def test_cursor_visual_feedback_exists(self):
        """Verifica que teste de feedback visual do cursor existe."""
        test_file = Path("tests/test_cursor_visual_feedback.py")
        assert test_file.exists(), "test_cursor_visual_feedback.py não encontrado"
    
    def test_playwright_commands_click_has_cursor_controller(self):
        """Verifica que PlaywrightCommands.click() aceita cursor_controller."""
        from playwright_simple.core.playwright_commands import PlaywrightCommands
        import inspect
        
        sig = inspect.signature(PlaywrightCommands.click)
        assert 'cursor_controller' in sig.parameters, "click() não tem parâmetro cursor_controller"

