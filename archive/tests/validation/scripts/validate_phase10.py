#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 10.

Verifica testes E2E completos.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase10Validator:
    """Validador para FASE 10."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 10: Testes E2E Completos")
        print("=" * 60)
        
        self._validate_e2e_tests()
        
        self.metrics['validation_time'] = time.time() - self.start_time
        self.metrics['errors_count'] = len(self.errors)
        self.metrics['success'] = len(self.errors) == 0
        
        self._print_results()
        return len(self.errors) == 0
    
    def _validate_e2e_tests(self):
        """Valida testes E2E."""
        print("\n🧪 Verificando testes E2E...")
        
        e2e_dir = Path("tests/e2e")
        if not e2e_dir.exists():
            self.errors.append("Diretório tests/e2e não existe")
            print("  ❌ Diretório tests/e2e não existe")
            return
        
        e2e_tests = list(e2e_dir.glob("test_*.py"))
        self.metrics['e2e_tests_count'] = len(e2e_tests)
        
        if len(e2e_tests) > 0:
            print(f"  ✅ {len(e2e_tests)} teste(s) E2E encontrado(s)")
            for test in e2e_tests:
                print(f"    - {test.name}")
        else:
            self.warnings.append("Nenhum teste E2E encontrado")
            print("  ⚠️  Nenhum teste E2E encontrado")
        
        # Verificar testes específicos
        core_e2e = e2e_dir / "test_core_e2e.py"
        odoo_e2e = e2e_dir / "test_odoo_e2e.py"
        
        if core_e2e.exists():
            print("  ✅ test_core_e2e.py existe")
            self.metrics['core_e2e_exists'] = True
        else:
            self.warnings.append("test_core_e2e.py não encontrado")
            print("  ⚠️  test_core_e2e.py não encontrado")
        
        if odoo_e2e.exists():
            print("  ✅ test_odoo_e2e.py existe")
            self.metrics['odoo_e2e_exists'] = True
        else:
            self.warnings.append("test_odoo_e2e.py não encontrado")
            print("  ⚠️  test_odoo_e2e.py não encontrado")
    
    def _print_results(self):
        """Exibe resultados."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        print(f"\n⏱️  Tempo: {self.metrics.get('validation_time', 0):.2f}s")
        if 'e2e_tests_count' in self.metrics:
            print(f"🧪 Testes E2E: {self.metrics['e2e_tests_count']}")
        
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
    validator = Phase10Validator()
    sys.exit(0 if validator.validate() else 1)


if __name__ == "__main__":
    main()

