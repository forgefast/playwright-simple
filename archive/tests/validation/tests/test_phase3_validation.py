#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 3.

Verifica melhorias no auto-fix com contexto completo.
"""

import pytest
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Timeout padrão
pytest_timeout = pytest.mark.timeout(10)


class TestPhase3AutoFix:
    """Testes do auto-fix."""
    
    def test_auto_fix_exists(self):
        """Verifica que AutoFixer pode ser importado."""
        from playwright_simple.core.auto_fixer import AutoFixer
        assert AutoFixer is not None
    
    @pytest_timeout
    def test_auto_fix_initialization(self):
        """Testa que AutoFixer pode ser inicializado."""
        from playwright_simple.core.auto_fixer import AutoFixer
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("name: test\n")
            yaml_file = Path(f.name)
        
        try:
            fixer = AutoFixer(yaml_file=yaml_file)
            assert fixer is not None
        finally:
            yaml_file.unlink()
    
    @pytest_timeout
    def test_auto_fix_has_fix_error_method(self):
        """Verifica que AutoFixer tem método fix_error."""
        from playwright_simple.core.auto_fixer import AutoFixer
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("name: test\n")
            yaml_file = Path(f.name)
        
        try:
            fixer = AutoFixer(yaml_file=yaml_file)
            assert hasattr(fixer, 'fix_error')
            assert callable(fixer.fix_error)
        finally:
            yaml_file.unlink()


class TestPhase3HTMLAnalyzer:
    """Testes do HTML Analyzer."""
    
    def test_html_analyzer_exists(self):
        """Verifica que HTMLAnalyzer pode ser importado."""
        from playwright_simple.core.html_analyzer import HTMLAnalyzer
        assert HTMLAnalyzer is not None
    
    @pytest_timeout
    def test_html_analyzer_initialization(self):
        """Testa que HTMLAnalyzer pode ser inicializado."""
        from playwright_simple.core.html_analyzer import HTMLAnalyzer
        
        analyzer = HTMLAnalyzer()
        assert analyzer is not None
    
    @pytest_timeout
    def test_html_analyzer_has_analyze_method(self):
        """Verifica que HTMLAnalyzer tem método analyze."""
        from playwright_simple.core.html_analyzer import HTMLAnalyzer
        
        analyzer = HTMLAnalyzer()
        # Verificar que tem método de análise
        assert hasattr(analyzer, 'analyze') or hasattr(analyzer, 'get_buttons') or hasattr(analyzer, 'get_inputs')


class TestPhase3Integration:
    """Testes de integração."""
    
    def test_auto_fix_integrated_yaml_executor(self):
        """Verifica que auto-fix está integrado em yaml_executor."""
        yaml_executor = Path("playwright_simple/core/yaml_executor.py")
        if yaml_executor.exists():
            content = yaml_executor.read_text()
            # Verificar que menciona auto_fix ou AutoFixer
            has_auto_fix = "auto_fix" in content.lower() or "autofixer" in content.lower()
            assert has_auto_fix, "Auto-fix não está integrado em yaml_executor.py"
    
    def test_auto_fix_integrated_yaml_parser(self):
        """Verifica que auto-fix está integrado em yaml_parser."""
        yaml_parser = Path("playwright_simple/core/yaml_parser.py")
        if yaml_parser.exists():
            content = yaml_parser.read_text()
            # Verificar que menciona auto_fix ou AutoFixer
            has_auto_fix = "auto_fix" in content.lower() or "autofixer" in content.lower()
            assert has_auto_fix, "Auto-fix não está integrado em yaml_parser.py"


class TestPhase3Context:
    """Testes de contexto."""
    
    @pytest_timeout
    def test_auto_fix_supports_page_state(self):
        """Verifica que auto-fix suporta page_state."""
        from playwright_simple.core.auto_fixer import AutoFixer
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("name: test\n")
            yaml_file = Path(f.name)
        
        try:
            fixer = AutoFixer(yaml_file=yaml_file)
            
            # Verificar que fix_error aceita page_state
            import inspect
            sig = inspect.signature(fixer.fix_error)
            params = list(sig.parameters.keys())
            
            assert 'page_state' in params, "fix_error não aceita page_state"
        finally:
            yaml_file.unlink()
    
    @pytest_timeout
    def test_auto_fix_supports_html_analyzer(self):
        """Verifica que auto-fix suporta html_analyzer."""
        from playwright_simple.core.auto_fixer import AutoFixer
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("name: test\n")
            yaml_file = Path(f.name)
        
        try:
            fixer = AutoFixer(yaml_file=yaml_file)
            
            # Verificar que fix_error aceita html_analyzer
            import inspect
            sig = inspect.signature(fixer.fix_error)
            params = list(sig.parameters.keys())
            
            assert 'html_analyzer' in params, "fix_error não aceita html_analyzer"
        finally:
            yaml_file.unlink()
    
    @pytest_timeout
    def test_auto_fix_supports_action_history(self):
        """Verifica que auto-fix suporta action_history."""
        from playwright_simple.core.auto_fixer import AutoFixer
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("name: test\n")
            yaml_file = Path(f.name)
        
        try:
            fixer = AutoFixer(yaml_file=yaml_file)
            
            # Verificar que fix_error aceita action_history
            import inspect
            sig = inspect.signature(fixer.fix_error)
            params = list(sig.parameters.keys())
            
            assert 'action_history' in params, "fix_error não aceita action_history"
        finally:
            yaml_file.unlink()


class TestPhase3Metrics:
    """Testes de métricas da FASE 3."""
    
    def test_auto_fixer_file_exists(self):
        """Verifica que auto_fixer.py existe."""
        auto_fixer = Path("playwright_simple/core/auto_fixer.py")
        assert auto_fixer.exists(), "auto_fixer.py não existe"
    
    def test_html_analyzer_file_exists(self):
        """Verifica que html_analyzer.py existe."""
        html_analyzer = Path("playwright_simple/core/html_analyzer.py")
        assert html_analyzer.exists(), "html_analyzer.py não existe"

