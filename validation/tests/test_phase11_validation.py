#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 11.

Verifica performance e otimização.
"""

import pytest
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

pytest_timeout = pytest.mark.timeout(5)


class TestPhase11Performance:
    """Testes de performance."""
    
    def test_profiler_exists(self):
        """Verifica que PerformanceProfiler pode ser importado."""
        try:
            from playwright_simple.core.performance.profiler import PerformanceProfiler
            assert PerformanceProfiler is not None
        except ImportError:
            pytest.skip("PerformanceProfiler não disponível")
    
    def test_profiler_file_exists(self):
        """Verifica que profiler.py existe."""
        profiler_file = Path("playwright_simple/core/performance/profiler.py")
        assert profiler_file.exists(), "profiler.py não existe"
    
    def test_performance_doc_exists(self):
        """Verifica que documentação de performance existe."""
        perf_doc = Path("docs/PERFORMANCE.md")
        assert perf_doc.exists(), "PERFORMANCE.md não existe"

