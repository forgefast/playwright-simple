#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 2.

Verifica integração do recorder, ElementIdentifier e modularização.
"""

import pytest
import subprocess
import sys
import importlib
from pathlib import Path
import time


class TestPhase2CLI:
    """Testes do comando CLI."""
    
    def test_cli_command_exists(self):
        """Verifica que comando record existe."""
        result = subprocess.run(
            [sys.executable, "-m", "playwright_simple.cli", "record", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Comando record não existe ou não funciona: {result.stderr}"
        assert "record" in result.stdout.lower() or "gravar" in result.stdout.lower()
    
    def test_cli_command_options(self):
        """Verifica que comando record tem opções esperadas."""
        result = subprocess.run(
            [sys.executable, "-m", "playwright_simple.cli", "record", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout.lower()
        # Verificar opções comuns
        has_url = "--url" in output or "url" in output
        has_headless = "--headless" in output or "headless" in output
        
        assert has_url or has_headless, "Comando record não tem opções esperadas"


class TestPhase2ElementIdentifier:
    """Testes do ElementIdentifier."""
    
    def test_element_identifier_exists(self):
        """Verifica que ElementIdentifier pode ser importado."""
        from playwright_simple.core.recorder.element_identifier import ElementIdentifier
        assert ElementIdentifier is not None
    
    def test_element_identifier_identify(self):
        """Testa que identify() funciona."""
        from playwright_simple.core.recorder.element_identifier import ElementIdentifier
        
        element_info = {
            "tagName": "BUTTON",
            "textContent": "Click Me",
            "id": "btn"
        }
        
        result = ElementIdentifier.identify(element_info)
        assert result is not None, "identify() retornou None"
        assert isinstance(result, dict), "identify() não retornou dict"
        # Verificar que tem alguma estratégia de identificação
        assert len(result) > 0, "identify() retornou dict vazio"
    
    def test_element_identifier_identify_for_input(self):
        """Testa que identify_for_input() funciona."""
        from playwright_simple.core.recorder.element_identifier import ElementIdentifier
        
        element_info = {
            "tagName": "INPUT",
            "type": "text",
            "name": "email",
            "placeholder": "Enter email"
        }
        
        result = ElementIdentifier.identify_for_input(element_info)
        assert result is not None, "identify_for_input() retornou None"
        assert isinstance(result, dict), "identify_for_input() não retornou dict"


class TestPhase2RecorderModules:
    """Testes dos módulos do recorder."""
    
    def test_recorder_modules_exist(self):
        """Verifica que módulos do recorder existem e podem ser importados."""
        required_modules = [
            "playwright_simple.core.recorder.recorder",
            "playwright_simple.core.recorder.event_handlers",
            "playwright_simple.core.recorder.command_handlers",
            "playwright_simple.core.recorder.event_capture",
            "playwright_simple.core.recorder.action_converter",
            "playwright_simple.core.recorder.yaml_writer",
            "playwright_simple.core.recorder.element_identifier",
            "playwright_simple.core.recorder.console_interface"
        ]
        
        failed_imports = []
        for module_name in required_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                failed_imports.append(f"{module_name}: {e}")
        
        assert len(failed_imports) == 0, f"Módulos não podem ser importados: {', '.join(failed_imports)}"
    
    def test_file_sizes(self):
        """Verifica que arquivos não são muito grandes."""
        recorder_dir = Path("playwright_simple/core/recorder")
        if not recorder_dir.exists():
            pytest.skip("Diretório recorder não existe")
        
        max_lines = 1000
        large_files = []
        
        for py_file in recorder_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                lines = len(py_file.read_text().splitlines())
                if lines >= max_lines:
                    large_files.append(f"{py_file.name}: {lines} linhas")
            except Exception as e:
                # Ignorar erros de leitura
                pass
        
        assert len(large_files) == 0, f"Arquivos muito grandes: {', '.join(large_files)}"
    
    def test_event_handlers_exists(self):
        """Verifica que event_handlers.py existe."""
        event_handlers = Path("playwright_simple/core/recorder/event_handlers.py")
        assert event_handlers.exists(), "event_handlers.py não existe"
        assert event_handlers.is_file(), "event_handlers.py não é um arquivo"
    
    def test_command_handlers_exists(self):
        """Verifica que command_handlers.py existe."""
        command_handlers = Path("playwright_simple/core/recorder/command_handlers.py")
        assert command_handlers.exists(), "command_handlers.py não existe"
        assert command_handlers.is_file(), "command_handlers.py não é um arquivo"


class TestPhase2RecorderStructure:
    """Testes da estrutura do recorder."""
    
    def test_recorder_class_exists(self):
        """Verifica que classe Recorder existe."""
        from playwright_simple.core.recorder.recorder import Recorder
        assert Recorder is not None
        assert hasattr(Recorder, 'start')
        assert hasattr(Recorder, 'stop')
    
    def test_recorder_initialization(self):
        """Verifica que Recorder pode ser inicializado."""
        from playwright_simple.core.recorder.recorder import Recorder
        from pathlib import Path
        
        output_path = Path("/tmp/test_recorder.yaml")
        recorder = Recorder(output_path=output_path, initial_url="about:blank", headless=True)
        
        assert recorder is not None
        assert recorder.output_path == output_path


class TestPhase2InitialClickCapture:
    """Testes de captura de clique inicial."""
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_recorder_waits_for_page_load(self):
        """Verifica que recorder espera página carregar antes de iniciar captura."""
        from playwright_simple.core.recorder.recorder import Recorder
        from pathlib import Path
        
        # Verificar que recorder.py tem wait_for_load_state
        recorder_file = Path("playwright_simple/core/recorder/recorder.py")
        if recorder_file.exists():
            content = recorder_file.read_text()
            # Verificar que tem espera por networkidle ou load
            has_wait = "wait_for_load_state" in content or "networkidle" in content or "wait_until" in content
            assert has_wait, "Recorder não espera página carregar antes de iniciar captura"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_event_capture_verifies_script_ready(self):
        """Verifica que event_capture verifica se script está pronto."""
        event_capture_file = Path("playwright_simple/core/recorder/event_capture.py")
        if event_capture_file.exists():
            content = event_capture_file.read_text()
            # Verificar que tem verificação de script inicializado
            has_verification = "initialized" in content.lower() and "eventsArrayReady" in content
            assert has_verification, "EventCapture não verifica se script está pronto"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_event_capture_early_injection(self):
        """Verifica que event_capture injeta script cedo (domcontentloaded)."""
        event_capture_file = Path("playwright_simple/core/recorder/event_capture.py")
        if event_capture_file.exists():
            content = event_capture_file.read_text()
            # Verificar que injeta no domcontentloaded
            has_early_injection = "domcontentloaded" in content.lower() or "dom_content_loaded" in content.lower()
            assert has_early_injection, "EventCapture não injeta script no domcontentloaded"
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_event_capture_multiple_polls(self):
        """Verifica que event_capture faz múltiplos polls imediatos."""
        event_capture_file = Path("playwright_simple/core/recorder/event_capture.py")
        if event_capture_file.exists():
            content = event_capture_file.read_text()
            # Verificar que faz múltiplos polls
            has_multiple_polls = "poll_attempt" in content or "range(3)" in content or "immediate poll" in content.lower()
            assert has_multiple_polls, "EventCapture não faz múltiplos polls imediatos"


class TestPhase2Metrics:
    """Testes de métricas da FASE 2."""
    
    def test_count_recorder_files(self):
        """Verifica número mínimo de arquivos do recorder."""
        recorder_dir = Path("playwright_simple/core/recorder")
        if not recorder_dir.exists():
            pytest.skip("Diretório recorder não existe")
        
        py_files = [f for f in recorder_dir.glob("*.py") if f.name != "__init__.py"]
        assert len(py_files) >= 8, f"Apenas {len(py_files)} arquivos encontrados (esperado >= 8)"
    
    def test_average_file_size(self):
        """Verifica tamanho médio dos arquivos."""
        recorder_dir = Path("playwright_simple/core/recorder")
        if not recorder_dir.exists():
            pytest.skip("Diretório recorder não existe")
        
        sizes = []
        for py_file in recorder_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                lines = len(py_file.read_text().splitlines())
                sizes.append(lines)
            except:
                pass
        
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            assert avg_size < 500, f"Tamanho médio muito grande: {avg_size:.0f} linhas (esperado < 500)"

