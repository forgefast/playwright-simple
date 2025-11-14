#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python Module Hot Reload - Recarrega módulos Python automaticamente.

Monitora mudanças em arquivos .py e recarrega módulos usando importlib.reload().
"""

import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Set
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

logger = logging.getLogger(__name__)


class PythonModuleReloader:
    """Recarrega módulos Python quando arquivos são modificados."""
    
    def __init__(self, watch_dirs: list[Path], auto_reload: bool = True):
        """
        Inicializa reloader de módulos Python.
        
        Args:
            watch_dirs: Diretórios para monitorar (ex: [Path('playwright_simple')])
            auto_reload: Se True, recarrega automaticamente quando detecta mudanças
        """
        self.watch_dirs = [Path(d) for d in watch_dirs]
        self.auto_reload = auto_reload
        self.module_mtimes: Dict[str, float] = {}
        self.loaded_modules: Set[str] = set()
        self.observer: Optional[Observer] = None
        
        # Mapear arquivos .py para nomes de módulos
        self._file_to_module: Dict[Path, str] = {}
        self._build_file_module_map()
        
        if WATCHDOG_AVAILABLE and auto_reload:
            self._setup_watchdog()
    
    def _build_file_module_map(self):
        """Constrói mapeamento de arquivos .py para nomes de módulos."""
        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue
            
            # Encontrar diretório raiz do projeto
            # Se watch_dir já é playwright_simple, usar o pai
            # Se não, procurar onde está playwright_simple
            if watch_dir.name == "playwright_simple":
                project_root = watch_dir.parent
            else:
                project_root = watch_dir
                while project_root.parent != project_root:
                    if (project_root / "playwright_simple").exists():
                        project_root = project_root
                        break
                    project_root = project_root.parent
            
            # Encontrar todos os arquivos .py
            for py_file in watch_dir.rglob("*.py"):
                if py_file.is_file():
                    # Calcular nome do módulo
                    try:
                        # Se watch_dir é playwright_simple, usar relativo a ele
                        if watch_dir.name == "playwright_simple":
                            relative_path = py_file.relative_to(watch_dir)
                        else:
                            # Tentar relativo ao project_root
                            try:
                                relative_path = py_file.relative_to(project_root)
                            except ValueError:
                                # Se falhar, tentar relativo ao watch_dir
                                relative_path = py_file.relative_to(watch_dir)
                        
                        module_name = str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')
                        # Garantir que começa com playwright_simple
                        if not module_name.startswith('playwright_simple'):
                            if watch_dir.name == "playwright_simple":
                                module_name = f"playwright_simple.{module_name}"
                            else:
                                module_name = f"playwright_simple.{relative_path.with_suffix('')}".replace('/', '.').replace('\\', '.')
                        
                        self._file_to_module[py_file] = module_name
                    except Exception as e:
                        logger.debug(f"Erro ao mapear {py_file}: {e}")
                        pass
    
    def _setup_watchdog(self):
        """Configura watchdog para monitorar mudanças."""
        if not WATCHDOG_AVAILABLE:
            return
        
        class PythonFileHandler(FileSystemEventHandler):
            def __init__(self, reloader):
                self.reloader = reloader
            
            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith('.py'):
                    path = Path(event.src_path)
                    if path in self.reloader._file_to_module:
                        logger.info(f"🔄 Arquivo Python modificado: {path}")
                        self.reloader.reload_module(path)
        
        self.observer = Observer()
        handler = PythonFileHandler(self)
        
        for watch_dir in self.watch_dirs:
            if watch_dir.exists():
                self.observer.schedule(handler, str(watch_dir), recursive=True)
        
        self.observer.start()
        logger.info(f"✅ Python hot reload ativado para: {[str(d) for d in self.watch_dirs]}")
    
    def reload_module(self, file_path: Optional[Path] = None, module_name: Optional[str] = None) -> bool:
        """
        Recarrega um módulo Python.
        
        Args:
            file_path: Caminho do arquivo .py
            module_name: Nome do módulo (alternativa a file_path)
            
        Returns:
            True se recarregou com sucesso
        """
        # Determinar nome do módulo
        if file_path:
            module_name = self._file_to_module.get(file_path)
            if not module_name:
                logger.warning(f"⚠️  Módulo não encontrado para arquivo: {file_path}")
                return False
        
        if not module_name:
            logger.warning("⚠️  Nome do módulo não fornecido")
            return False
        
        # Verificar se módulo está carregado
        if module_name not in sys.modules:
            logger.debug(f"📦 Módulo não está carregado: {module_name}")
            return False
        
        try:
            # Recarregar módulo
            module = sys.modules[module_name]
            importlib.reload(module)
            
            # Recarregar também submódulos relacionados
            related_modules = [
                name for name in sys.modules.keys()
                if name.startswith(module_name + '.')
            ]
            for related_name in related_modules:
                try:
                    importlib.reload(sys.modules[related_name])
                except Exception as e:
                    logger.debug(f"⚠️  Não foi possível recarregar submódulo {related_name}: {e}")
            
            logger.info(f"✅ Módulo recarregado: {module_name}")
            print(f"  🔄 Python hot reload: {module_name} recarregado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao recarregar módulo {module_name}: {e}")
            print(f"  ⚠️  Erro ao recarregar {module_name}: {e}")
            return False
    
    def check_and_reload_all(self) -> int:
        """
        Verifica todos os módulos monitorados e recarrega se necessário.
        
        Returns:
            Número de módulos recarregados
        """
        reloaded_count = 0
        
        for file_path, module_name in self._file_to_module.items():
            if not file_path.exists():
                continue
            
            # Verificar mtime
            current_mtime = file_path.stat().st_mtime
            last_mtime = self.module_mtimes.get(str(file_path), 0)
            
            if current_mtime > last_mtime:
                # Arquivo foi modificado
                if self.reload_module(file_path):
                    reloaded_count += 1
                    self.module_mtimes[str(file_path)] = current_mtime
        
        return reloaded_count
    
    def stop(self):
        """Para monitoramento."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None


# Instância global
_global_reloader: Optional[PythonModuleReloader] = None


def get_reloader(watch_dirs: Optional[list[Path]] = None, auto_reload: bool = True) -> PythonModuleReloader:
    """
    Obtém ou cria instância global do reloader.
    
    Args:
        watch_dirs: Diretórios para monitorar (default: playwright_simple)
        auto_reload: Se True, recarrega automaticamente
        
    Returns:
        PythonModuleReloader instance
    """
    global _global_reloader
    
    if _global_reloader is None:
        if watch_dirs is None:
            # Padrão: monitorar playwright_simple
            project_root = Path(__file__).parent.parent.parent
            watch_dirs = [project_root / "playwright_simple"]
        
        _global_reloader = PythonModuleReloader(watch_dirs, auto_reload)
    
    return _global_reloader


def reload_module(module_name: str) -> bool:
    """
    Recarrega um módulo específico.
    
    Args:
        module_name: Nome do módulo (ex: 'playwright_simple.core.interactions.click_interactions')
        
    Returns:
        True se recarregou com sucesso
    """
    reloader = get_reloader()
    return reloader.reload_module(module_name=module_name)

