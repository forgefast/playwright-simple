#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 2.

Verifica integração do recorder, ElementIdentifier e modularização.
"""

import sys
import subprocess
import time
import importlib
from pathlib import Path
from typing import Dict, List

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase2Validator:
    """Validador para FASE 2."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 2: Integração do Recorder (v2 → v1)")
        print("=" * 60)
        
        self._validate_cli()
        self._validate_element_identifier()
        self._validate_recorder_modules()
        self._validate_initial_click_capture()
        self._validate_modularization()
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        # Retornar sucesso/falha
        return len(self.errors) == 0
    
    def _validate_cli(self):
        """Valida comando CLI."""
        print("\n💻 Verificando comando CLI...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "playwright_simple.cli", "record", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("  ✅ Comando record existe e funciona")
                self.metrics['cli_command_exists'] = True
            else:
                self.errors.append("Comando record não funciona")
                print(f"  ❌ Comando record não funciona: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.errors.append("Comando record timeout")
            print("  ❌ Comando record timeout")
        except FileNotFoundError:
            self.errors.append("playwright-simple não encontrado")
            print("  ❌ playwright-simple não encontrado (instalar com: pip install -e .)")
        except Exception as e:
            self.errors.append(f"Erro ao verificar CLI: {e}")
            print(f"  ❌ Erro ao verificar CLI: {e}")
    
    def _validate_element_identifier(self):
        """Valida ElementIdentifier."""
        print("\n🎯 Verificando ElementIdentifier...")
        
        try:
            from playwright_simple.core.recorder.element_identifier import ElementIdentifier
            
            # Testar identify()
            element_info = {
                "tagName": "BUTTON",
                "textContent": "Click Me",
                "id": "btn"
            }
            
            result = ElementIdentifier.identify(element_info)
            if result and isinstance(result, dict) and len(result) > 0:
                print("  ✅ ElementIdentifier.identify() funciona")
            else:
                self.errors.append("ElementIdentifier.identify() não funciona corretamente")
                print("  ❌ ElementIdentifier.identify() não funciona corretamente")
            
            # Testar identify_for_input()
            input_info = {
                "tagName": "INPUT",
                "type": "text",
                "name": "email"
            }
            
            result = ElementIdentifier.identify_for_input(input_info)
            if result and isinstance(result, dict):
                print("  ✅ ElementIdentifier.identify_for_input() funciona")
            else:
                self.warnings.append("ElementIdentifier.identify_for_input() pode não estar funcionando")
                print("  ⚠️  ElementIdentifier.identify_for_input() pode não estar funcionando")
            
            self.metrics['element_identifier_works'] = True
        except ImportError as e:
            self.errors.append(f"ElementIdentifier não pode ser importado: {e}")
            print(f"  ❌ ElementIdentifier não pode ser importado: {e}")
        except Exception as e:
            self.errors.append(f"Erro ao testar ElementIdentifier: {e}")
            print(f"  ❌ Erro ao testar ElementIdentifier: {e}")
    
    def _validate_recorder_modules(self):
        """Valida módulos do recorder."""
        print("\n📦 Verificando módulos do recorder...")
        
        required_modules = [
            ("recorder", "playwright_simple.core.recorder.recorder"),
            ("event_handlers", "playwright_simple.core.recorder.event_handlers"),
            ("command_handlers", "playwright_simple.core.recorder.command_handlers"),
            ("event_capture", "playwright_simple.core.recorder.event_capture"),
            ("action_converter", "playwright_simple.core.recorder.action_converter"),
            ("yaml_writer", "playwright_simple.core.recorder.yaml_writer"),
            ("element_identifier", "playwright_simple.core.recorder.element_identifier"),
            ("console_interface", "playwright_simple.core.recorder.console_interface")
        ]
        
        successful_imports = 0
        for name, module_name in required_modules:
            try:
                importlib.import_module(module_name)
                print(f"  ✅ {name} importado com sucesso")
                successful_imports += 1
            except ImportError as e:
                self.errors.append(f"Falha ao importar {name}: {e}")
                print(f"  ❌ Falha ao importar {name}: {e}")
            except Exception as e:
                self.errors.append(f"Erro ao importar {name}: {e}")
                print(f"  ❌ Erro ao importar {name}: {e}")
        
        self.metrics['modules_found'] = successful_imports
        self.metrics['modules_required'] = len(required_modules)
    
    def _validate_initial_click_capture(self):
        """Valida captura de clique inicial."""
        print("\n🖱️  Verificando captura de clique inicial...")
        
        recorder_file = Path("playwright_simple/core/recorder/recorder.py")
        if recorder_file.exists():
            content = recorder_file.read_text()
            
            # Verificar que espera página carregar
            has_wait = "wait_for_load_state" in content or "networkidle" in content
            if has_wait:
                print("  ✅ Recorder espera página carregar antes de iniciar")
                self.metrics['waits_for_page_load'] = True
            else:
                self.warnings.append("Recorder pode não esperar página carregar")
                print("  ⚠️  Recorder pode não esperar página carregar")
            
            # Verificar que verifica script pronto
            has_verification = "script_ready" in content or "eventsArrayReady" in content
            if has_verification:
                print("  ✅ Recorder verifica se script está pronto")
                self.metrics['verifies_script_ready'] = True
            else:
                self.warnings.append("Recorder pode não verificar se script está pronto")
                print("  ⚠️  Recorder pode não verificar se script está pronto")
            
            # Verificar injeção antecipada
            has_early_injection = "domcontentloaded" in content.lower() or "before navigation" in content.lower()
            if has_early_injection:
                print("  ✅ Recorder injeta script cedo (domcontentloaded)")
                self.metrics['early_injection'] = True
            else:
                self.warnings.append("Recorder pode não injetar script cedo o suficiente")
                print("  ⚠️  Recorder pode não injetar script cedo o suficiente")
        
        # Verificar event_capture.py também
        event_capture_file = Path("playwright_simple/core/recorder/event_capture.py")
        if event_capture_file.exists():
            content = event_capture_file.read_text()
            
            # Verificar múltiplos polls
            has_multiple_polls = "poll_attempt" in content or "range(3)" in content or "immediate poll" in content.lower()
            if has_multiple_polls:
                print("  ✅ EventCapture faz múltiplos polls imediatos")
                self.metrics['multiple_immediate_polls'] = True
            else:
                self.warnings.append("EventCapture pode não fazer múltiplos polls imediatos")
                print("  ⚠️  EventCapture pode não fazer múltiplos polls imediatos")
            
            # Verificar polling frequente inicial
            has_fast_initial_polling = "0.05" in content and "poll_count <= 10" in content
            if has_fast_initial_polling:
                print("  ✅ EventCapture usa polling mais frequente inicialmente")
                self.metrics['fast_initial_polling'] = True
            else:
                self.warnings.append("EventCapture pode não usar polling frequente inicialmente")
                print("  ⚠️  EventCapture pode não usar polling frequente inicialmente")
        else:
            self.errors.append("recorder.py não encontrado")
            print("  ❌ recorder.py não encontrado")
    
    def _validate_modularization(self):
        """Valida modularização."""
        print("\n📏 Verificando modularização...")
        
        recorder_dir = Path("playwright_simple/core/recorder")
        if not recorder_dir.exists():
            self.errors.append("Diretório recorder não existe")
            print("  ❌ Diretório recorder não existe")
            return
        
        max_lines = 1000
        file_sizes = []
        large_files = []
        
        for py_file in recorder_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                lines = len(py_file.read_text().splitlines())
                file_sizes.append(lines)
                
                if lines >= max_lines:
                    large_files.append(f"{py_file.name}: {lines} linhas")
                    print(f"  ⚠️  {py_file.name}: {lines} linhas (muito grande)")
                else:
                    print(f"  ✅ {py_file.name}: {lines} linhas")
            except Exception as e:
                self.warnings.append(f"Erro ao ler {py_file.name}: {e}")
        
        if large_files:
            self.errors.append(f"Arquivos muito grandes: {', '.join(large_files)}")
        
        if file_sizes:
            avg_size = sum(file_sizes) / len(file_sizes)
            self.metrics['average_file_size'] = avg_size
            self.metrics['max_file_size'] = max(file_sizes)
            
            if avg_size > 500:
                self.warnings.append(f"Tamanho médio muito grande: {avg_size:.0f} linhas")
        
        # Verificar arquivos específicos
        event_handlers = recorder_dir / "event_handlers.py"
        command_handlers = recorder_dir / "command_handlers.py"
        
        if event_handlers.exists():
            print("  ✅ event_handlers.py existe")
        else:
            self.errors.append("event_handlers.py não existe")
            print("  ❌ event_handlers.py não existe")
        
        if command_handlers.exists():
            print("  ✅ command_handlers.py existe")
        else:
            self.errors.append("command_handlers.py não existe")
            print("  ❌ command_handlers.py não existe")
    
    def _calculate_metrics(self):
        """Calcula métricas finais."""
        self.metrics['validation_time'] = time.time() - self.start_time
        self.metrics['errors_count'] = len(self.errors)
        self.metrics['warnings_count'] = len(self.warnings)
        self.metrics['success'] = len(self.errors) == 0
    
    def _print_results(self):
        """Exibe resultados da validação."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        print(f"\n⏱️  Tempo de validação: {self.metrics.get('validation_time', 0):.2f}s")
        print(f"✅ Módulos encontrados: {self.metrics.get('modules_found', 0)}/{self.metrics.get('modules_required', 0)}")
        
        if 'average_file_size' in self.metrics:
            print(f"📏 Tamanho médio de arquivo: {self.metrics['average_file_size']:.0f} linhas")
        if 'max_file_size' in self.metrics:
            print(f"📏 Arquivo maior: {self.metrics['max_file_size']} linhas")
        
        if self.warnings:
            print(f"\n⚠️  Avisos: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.errors:
            print(f"\n❌ Erros: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
            print("\n❌ VALIDAÇÃO FALHOU")
        else:
            print("\n✅ VALIDAÇÃO PASSOU")
        
        print("=" * 60)


def main():
    """Função principal."""
    validator = Phase2Validator()
    success = validator.validate()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

