#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 11.

Verifica performance e otimização.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase11Validator:
    """Validador para FASE 11."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 11: Performance e Otimização")
        print("=" * 60)
        
        self._validate_profiler()
        self._validate_documentation()
        
        self.metrics['validation_time'] = time.time() - self.start_time
        self.metrics['errors_count'] = len(self.errors)
        self.metrics['success'] = len(self.errors) == 0
        
        self._print_results()
        return len(self.errors) == 0
    
    def _validate_profiler(self):
        """Valida PerformanceProfiler."""
        print("\n⚡ Verificando PerformanceProfiler...")
        
        profiler_file = Path("playwright_simple/core/performance/profiler.py")
        if profiler_file.exists():
            print("  ✅ profiler.py existe")
            self.metrics['profiler_exists'] = True
            
            try:
                from playwright_simple.core.performance.profiler import PerformanceProfiler
                print("  ✅ PerformanceProfiler pode ser importado")
                self.metrics['profiler_importable'] = True
            except ImportError as e:
                self.errors.append(f"PerformanceProfiler não pode ser importado: {e}")
                print(f"  ❌ PerformanceProfiler não pode ser importado: {e}")
        else:
            self.errors.append("profiler.py não existe")
            print("  ❌ profiler.py não existe")
    
    def _validate_documentation(self):
        """Valida documentação."""
        print("\n📚 Verificando documentação...")
        
        perf_doc = Path("docs/PERFORMANCE.md")
        if perf_doc.exists():
            print("  ✅ PERFORMANCE.md existe")
            self.metrics['perf_doc_exists'] = True
        else:
            self.warnings.append("PERFORMANCE.md não encontrado")
            print("  ⚠️  PERFORMANCE.md não encontrado")
    
    def _print_results(self):
        """Exibe resultados."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        print(f"\n⏱️  Tempo: {self.metrics.get('validation_time', 0):.2f}s")
        
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
    validator = Phase11Validator()
    sys.exit(0 if validator.validate() else 1)


if __name__ == "__main__":
    main()

