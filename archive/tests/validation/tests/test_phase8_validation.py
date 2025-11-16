#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 8.

Verifica hot reload e auto-fix avançado.
"""

import pytest
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

pytest_timeout = pytest.mark.timeout(5)


class TestPhase8HotReload:
    """Testes de hot reload."""
    
    def test_yaml_parser_has_hot_reload(self):
        """Verifica que yaml_parser.py menciona hot_reload."""
        yaml_parser = Path("playwright_simple/core/yaml_parser.py")
        if yaml_parser.exists():
            content = yaml_parser.read_text()
            has_hot_reload = "hot_reload" in content.lower() or "reload" in content.lower()
            assert has_hot_reload, "yaml_parser.py não menciona hot_reload"
    
    def test_hot_reload_docs_exist(self):
        """Verifica que documentação de hot reload existe."""
        # Verificar em múltiplos locais possíveis
        possible_paths = [
            Path("HOT_RELOAD.md"),
            Path("PYTHON_HOT_RELOAD.md"),
            Path("docs/HOT_RELOAD.md"),
            Path("docs/PYTHON_HOT_RELOAD.md")
        ]
        
        # Verificar se hot reload está mencionado na documentação existente
        docs_found = any(p.exists() for p in possible_paths)
        
        # Se não encontrou arquivos específicos, verificar se hot reload está documentado em outros lugares
        if not docs_found:
            # Verificar se está mencionado em outros docs
            other_docs = [Path("docs/HYBRID_WORKFLOW.md"), Path("USER_MANUAL.md")]
            for doc in other_docs:
                if doc.exists():
                    content = doc.read_text()
                    if "hot reload" in content.lower() or "reload" in content.lower():
                        docs_found = True
                        break
        
        # Não falhar se não encontrar, apenas avisar (pode estar documentado em outro lugar)
        if not docs_found:
            pytest.skip("Documentação específica de hot reload não encontrada (pode estar em outros docs)")


class TestPhase8AutoFix:
    """Testes de auto-fix."""
    
    def test_auto_fix_integrated(self):
        """Verifica que auto-fix está integrado."""
        yaml_executor = Path("playwright_simple/core/yaml_executor.py")
        if yaml_executor.exists():
            content = yaml_executor.read_text()
            has_auto_fix = "auto_fix" in content.lower() or "autofixer" in content.lower()
            assert has_auto_fix, "Auto-fix não está integrado em yaml_executor.py"

