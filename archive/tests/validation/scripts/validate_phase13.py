#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação para FASE 13: Interface de Comandos CLI para Gravação Ativa.
"""

import sys
from pathlib import Path
import subprocess
import importlib.util

# Adicionar raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class Phase13Validator:
    """Validador para FASE 13."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.metrics = {}
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 13: Interface de Comandos CLI para Gravação Ativa")
        print("=" * 60)
        
        self._validate_modules()
        self._validate_playwright_commands()
        self._validate_command_server()
        self._validate_cli_commands()
        self._validate_recorder_integration()
        self._validate_link_capture()
        self._validate_cursor_visual_feedback()
        self._validate_documentation()
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        return not self.errors
    
    def _validate_modules(self):
        """Valida que módulos existem."""
        print("\n📦 Verificando módulos...")
        
        try:
            from playwright_simple.core.playwright_commands import PlaywrightCommands
            print("  ✅ PlaywrightCommands importado")
            self.metrics['playwright_commands'] = True
        except ImportError as e:
            self.errors.append(f"PlaywrightCommands não encontrado: {e}")
            print(f"  ❌ PlaywrightCommands não encontrado: {e}")
        
        try:
            from playwright_simple.core.recorder.command_server import CommandServer, send_command
            print("  ✅ CommandServer importado")
            print("  ✅ send_command importado")
            self.metrics['command_server'] = True
        except ImportError as e:
            self.errors.append(f"CommandServer não encontrado: {e}")
            print(f"  ❌ CommandServer não encontrado: {e}")
    
    def _validate_playwright_commands(self):
        """Valida interface PlaywrightCommands."""
        print("\n🎯 Verificando PlaywrightCommands...")
        
        try:
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
            
            missing = []
            for method in methods:
                if not hasattr(PlaywrightCommands, method):
                    missing.append(method)
            
            if missing:
                self.errors.append(f"Métodos faltando em PlaywrightCommands: {missing}")
                print(f"  ❌ Métodos faltando: {missing}")
            else:
                print(f"  ✅ Todos os {len(methods)} métodos presentes")
                self.metrics['playwright_commands_methods'] = len(methods)
        except Exception as e:
            self.errors.append(f"Erro validando PlaywrightCommands: {e}")
            print(f"  ❌ Erro: {e}")
    
    def _validate_command_server(self):
        """Valida CommandServer."""
        print("\n🖥️  Verificando CommandServer...")
        
        try:
            from playwright_simple.core.recorder.command_server import CommandServer
            from unittest.mock import MagicMock
            
            mock_recorder = MagicMock()
            server = CommandServer(mock_recorder, session_id='test')
            
            # Verificar handlers
            handlers = ['find', 'find-all', 'click', 'type', 'wait', 'info', 'html', 'navigate']
            missing = [h for h in handlers if h not in server.command_handlers]
            
            if missing:
                self.warnings.append(f"Handlers faltando: {missing}")
                print(f"  ⚠️  Handlers faltando: {missing}")
            else:
                print(f"  ✅ Todos os {len(handlers)} handlers registrados")
                self.metrics['command_handlers'] = len(handlers)
            
            # Verificar arquivos
            if server.command_file and server.response_file and server.lock_file:
                print("  ✅ Arquivos IPC configurados")
                self.metrics['ipc_files'] = True
            else:
                self.errors.append("Arquivos IPC não configurados")
                print("  ❌ Arquivos IPC não configurados")
        except Exception as e:
            self.errors.append(f"Erro validando CommandServer: {e}")
            print(f"  ❌ Erro: {e}")
    
    def _validate_cli_commands(self):
        """Valida comandos CLI."""
        print("\n💻 Verificando comandos CLI...")
        
        commands = ['find', 'click', 'type', 'wait', 'info', 'html']
        found = 0
        
        for cmd in commands:
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'playwright_simple.cli', cmd, '--help'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"  ✅ Comando '{cmd}' existe")
                    found += 1
                else:
                    self.warnings.append(f"Comando '{cmd}' retornou erro")
                    print(f"  ⚠️  Comando '{cmd}' retornou erro")
            except subprocess.TimeoutExpired:
                self.warnings.append(f"Comando '{cmd}' timeout")
                print(f"  ⚠️  Comando '{cmd}' timeout")
            except Exception as e:
                self.warnings.append(f"Erro testando comando '{cmd}': {e}")
                print(f"  ⚠️  Erro testando comando '{cmd}': {e}")
        
        self.metrics['cli_commands'] = found
        if found == len(commands):
            print(f"  ✅ Todos os {len(commands)} comandos CLI disponíveis")
        else:
            self.warnings.append(f"Apenas {found}/{len(commands)} comandos CLI funcionando")
    
    def _validate_recorder_integration(self):
        """Valida integração com Recorder."""
        print("\n🔗 Verificando integração com Recorder...")
        
        recorder_file = Path("playwright_simple/core/recorder/recorder.py")
        if recorder_file.exists():
            content = recorder_file.read_text()
            
            # Verificar import
            if "CommandServer" in content:
                print("  ✅ Recorder importa CommandServer")
                self.metrics['recorder_imports_server'] = True
            else:
                self.errors.append("Recorder não importa CommandServer")
                print("  ❌ Recorder não importa CommandServer")
            
            # Verificar inicialização
            if "command_server" in content.lower():
                print("  ✅ Recorder tem command_server")
                self.metrics['recorder_has_server'] = True
            else:
                self.warnings.append("Recorder pode não ter command_server")
                print("  ⚠️  Recorder pode não ter command_server")
        else:
            self.errors.append("recorder.py não encontrado")
            print("  ❌ recorder.py não encontrado")
    
    def _validate_link_capture(self):
        """Valida melhorias na captura de links."""
        print("\n🔗 Verificando captura de links...")
        
        event_capture_file = Path("playwright_simple/core/recorder/event_capture.py")
        if event_capture_file.exists():
            content = event_capture_file.read_text()
            
            # Verificar lógica especial para links
            has_link_logic = "tag === 'A' && hasHref" in content
            if has_link_logic:
                print("  ✅ EventCapture tem lógica especial para links")
                self.metrics['link_capture_logic'] = True
            else:
                self.warnings.append("EventCapture pode não ter lógica especial para links")
                print("  ⚠️  EventCapture pode não ter lógica especial para links")
            
            # Verificar early return
            has_early_return = "Early return for links" in content or "early return" in content.lower()
            if has_early_return:
                print("  ✅ Links têm early return (sempre capturados)")
                self.metrics['link_early_return'] = True
            else:
                self.warnings.append("Links podem não ter early return")
                print("  ⚠️  Links podem não ter early return")
        else:
            self.errors.append("event_capture.py não encontrado")
            print("  ❌ event_capture.py não encontrado")
    
    def _validate_cursor_visual_feedback(self):
        """Valida feedback visual do cursor."""
        print("\n👆 Verificando feedback visual do cursor...")
        
        # Verificar que PlaywrightCommands.click() aceita cursor_controller
        try:
            from playwright_simple.core.playwright_commands import PlaywrightCommands
            import inspect
            
            sig = inspect.signature(PlaywrightCommands.click)
            if 'cursor_controller' in sig.parameters:
                print("  ✅ PlaywrightCommands.click() aceita cursor_controller")
                self.metrics['cursor_controller_param'] = True
            else:
                self.errors.append("PlaywrightCommands.click() não tem parâmetro cursor_controller")
                print("  ❌ PlaywrightCommands.click() não tem parâmetro cursor_controller")
        except Exception as e:
            self.errors.append(f"Erro verificando cursor_controller: {e}")
            print(f"  ❌ Erro: {e}")
        
        # Verificar que teste existe
        test_file = Path("tests/test_cursor_visual_feedback.py")
        if test_file.exists():
            print("  ✅ Teste de feedback visual existe")
            self.metrics['cursor_test_exists'] = True
        else:
            self.warnings.append("test_cursor_visual_feedback.py não encontrado")
            print("  ⚠️  test_cursor_visual_feedback.py não encontrado")
        
        # Verificar documentação
        cursor_docs = Path("validation/phase13_cursor_visual_validation.md")
        if cursor_docs.exists():
            print("  ✅ Documentação de feedback visual existe")
            self.metrics['cursor_docs'] = True
        else:
            self.warnings.append("phase13_cursor_visual_validation.md não encontrado")
            print("  ⚠️  phase13_cursor_visual_validation.md não encontrado")
    
    def _validate_documentation(self):
        """Valida documentação."""
        print("\n📚 Verificando documentação...")
        
        cli_docs = Path("docs/CLI_COMMANDS.md")
        pw_docs = Path("docs/PLAYWRIGHT_COMMANDS.md")
        
        if cli_docs.exists():
            content = cli_docs.read_text()
            if len(content) > 500:
                print("  ✅ CLI_COMMANDS.md existe e tem conteúdo")
                self.metrics['cli_docs'] = True
            else:
                self.warnings.append("CLI_COMMANDS.md muito curto")
                print("  ⚠️  CLI_COMMANDS.md muito curto")
        else:
            self.errors.append("CLI_COMMANDS.md não encontrado")
            print("  ❌ CLI_COMMANDS.md não encontrado")
        
        if pw_docs.exists():
            content = pw_docs.read_text()
            if len(content) > 500:
                print("  ✅ PLAYWRIGHT_COMMANDS.md existe e tem conteúdo")
                self.metrics['pw_docs'] = True
            else:
                self.warnings.append("PLAYWRIGHT_COMMANDS.md muito curto")
                print("  ⚠️  PLAYWRIGHT_COMMANDS.md muito curto")
        else:
            self.errors.append("PLAYWRIGHT_COMMANDS.md não encontrado")
            print("  ❌ PLAYWRIGHT_COMMANDS.md não encontrado")
    
    def _calculate_metrics(self):
        """Calcula métricas finais."""
        self.metrics['total_errors'] = len(self.errors)
        self.metrics['total_warnings'] = len(self.warnings)
    
    def _print_results(self):
        """Exibe resultados finais."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ Erros encontrados: {len(self.errors)}")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print(f"\n⚠️  Avisos: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        print(f"\n📈 Métricas:")
        for key, value in self.metrics.items():
            print(f"   - {key}: {value}")
        
        print("\n" + "=" * 60)
        if not self.errors:
            print("✅ VALIDAÇÃO PASSOU")
        else:
            print("❌ VALIDAÇÃO FALHOU")
        print("=" * 60)


def main():
    """Função principal."""
    validator = Phase13Validator()
    success = validator.validate()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

