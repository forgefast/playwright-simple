#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control Interface - Comunicação entre processos para auto-fix.

Usa watchdog para monitorar mudanças em arquivos de controle.
Mais eficiente que polling manual.
"""

import json
import os
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


class ControlFileHandler(FileSystemEventHandler):
    """Handler para mudanças em arquivos de controle usando watchdog."""
    
    def __init__(self, callback: Callable[[Path], None]):
        """
        Inicializa handler.
        
        Args:
            callback: Função chamada quando arquivo muda (recebe Path)
        """
        self.callback = callback
        self.last_modified = {}
    
    def on_modified(self, event):
        """Chamado quando arquivo é modificado."""
        if not event.is_directory:
            path = Path(event.src_path)
            current_mtime = path.stat().st_mtime
            if path not in self.last_modified or current_mtime > self.last_modified[path]:
                self.last_modified[path] = current_mtime
                if self.callback:
                    self.callback(path)


class ControlInterface:
    """Interface de controle para comunicação entre processos."""
    
    def __init__(self, test_name: str, control_dir: Optional[Path] = None, use_watchdog: bool = True):
        """
        Inicializa interface de controle.
        
        Args:
            test_name: Nome do teste
            control_dir: Diretório para arquivos de controle (default: /tmp/playwright_control)
            use_watchdog: Usar watchdog para monitoramento eficiente (default: True)
        """
        self.test_name = test_name
        self.control_dir = Path(control_dir) if control_dir else Path("/tmp/playwright_control")
        self.control_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivos de controle
        self.state_file = self.control_dir / f"{test_name}_state.json"
        self.command_file = self.control_dir / f"{test_name}_command.json"
        self.error_file = self.control_dir / f"{test_name}_error.json"
        
        # Watchdog para monitoramento eficiente
        self.use_watchdog = use_watchdog and WATCHDOG_AVAILABLE
        self.observer: Optional[Observer] = None
        self.file_callbacks: Dict[Path, Callable] = {}
    
    def save_step_state(
        self,
        step_number: int,
        action: str,
        step_data: Dict[str, Any],
        url: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        Salva estado do passo atual.
        
        Args:
            step_number: Número do passo
            action: Ação sendo executada
            step_data: Dados do passo
            url: URL atual da página
            error: Erro ocorrido (se houver)
        """
        state = {
            "test_name": self.test_name,
            "step_number": step_number,
            "action": action,
            "step_data": step_data,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "error": None
        }
        
        if error:
            state["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": None  # Não salvar traceback completo para evitar arquivos grandes
            }
        
        self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
        
        # Também escrever em stdout como JSON line para comunicação direta
        try:
            import sys
            event = {
                "type": "state",
                **state
            }
            print(json.dumps(event), file=sys.stdout, flush=True)
        except:
            pass  # Não falhar se stdout não estiver disponível
    
    def get_step_state(self) -> Optional[Dict[str, Any]]:
        """Obtém estado do passo atual."""
        if not self.state_file.exists():
            return None
        
        try:
            return json.loads(self.state_file.read_text(encoding='utf-8'))
        except:
            return None
    
    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Envia comando para o processo.
        
        Args:
            command: Comando (reload, continue, pause, etc.)
            params: Parâmetros adicionais
        """
        cmd_data = {
            "command": command,
            "params": params or {},
            "timestamp": datetime.now().isoformat()
        }
        self.command_file.write_text(json.dumps(cmd_data, indent=2), encoding='utf-8')
    
    def get_command(self) -> Optional[Dict[str, Any]]:
        """Obtém comando pendente e remove arquivo."""
        if not self.command_file.exists():
            return None
        
        try:
            cmd_data = json.loads(self.command_file.read_text(encoding='utf-8'))
            # Remover arquivo após ler
            self.command_file.unlink()
            return cmd_data
        except:
            return None
    
    def save_error(self, error: Exception, step_number: Optional[int] = None) -> None:
        """
        Salva erro para processo externo.
        
        Args:
            error: Exceção ocorrida
            step_number: Número do passo onde ocorreu
        """
        error_data = {
            "test_name": self.test_name,
            "step_number": step_number,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        self.error_file.write_text(json.dumps(error_data, indent=2), encoding='utf-8')
        
        # Também escrever em stdout como JSON line para comunicação direta
        try:
            import sys
            event = {
                "type": "error",
                **error_data
            }
            print(json.dumps(event), file=sys.stdout, flush=True)
        except:
            pass  # Não falhar se stdout não estiver disponível
    
    def get_error(self) -> Optional[Dict[str, Any]]:
        """Obtém último erro e remove arquivo."""
        if not self.error_file.exists():
            return None
        
        try:
            error_data = json.loads(self.error_file.read_text(encoding='utf-8'))
            # Não remover arquivo - pode ser lido múltiplas vezes
            return error_data
        except:
            return None
    
    def clear_error(self) -> None:
        """Limpa arquivo de erro."""
        if self.error_file.exists():
            self.error_file.unlink()
    
    def wait_for_command(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Aguarda comando com timeout.
        
        Args:
            timeout: Timeout em segundos
            
        Returns:
            Comando recebido ou None
        """
        start = time.time()
        while time.time() - start < timeout:
            cmd = self.get_command()
            if cmd:
                return cmd
            time.sleep(0.1)
        return None
    
    def watch_file(self, file_path: Path, callback: Callable[[Path], None]) -> None:
        """
        Monitora arquivo usando watchdog (mais eficiente que polling).
        
        Args:
            file_path: Arquivo para monitorar
            callback: Função chamada quando arquivo muda
        """
        if not self.use_watchdog:
            return
        
        if self.observer is None:
            self.observer = Observer()
            handler = ControlFileHandler(self._on_file_changed)
            self.observer.schedule(handler, str(self.control_dir), recursive=False)
            self.observer.start()
        
        self.file_callbacks[file_path] = callback
    
    def _on_file_changed(self, path: Path):
        """Callback interno quando arquivo muda."""
        if path in self.file_callbacks:
            self.file_callbacks[path](path)
    
    def stop_watching(self):
        """Para monitoramento."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.file_callbacks.clear()

