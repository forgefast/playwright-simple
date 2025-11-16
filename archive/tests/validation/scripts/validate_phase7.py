#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 7.

Verifica extensão Odoo - CRUD completo.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase7Validator:
    """Validador para FASE 7."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 7: Extensão Odoo - CRUD Completo")
        print("=" * 60)
        
        self._validate_crud_methods()
        self._validate_crud_file()
        
        self.metrics['validation_time'] = time.time() - self.start_time
        self.metrics['errors_count'] = len(self.errors)
        self.metrics['success'] = len(self.errors) == 0
        
        self._print_results()
        return len(self.errors) == 0
    
    def _validate_crud_methods(self):
        """Valida métodos CRUD."""
        print("\n🔧 Verificando métodos CRUD...")
        
        try:
            from playwright_simple.odoo import OdooTestBase
            
            required_methods = ['create_record', 'search_and_open', 'open_record', 'assert_record_exists']
            found = []
            missing = []
            
            for method in required_methods:
                if hasattr(OdooTestBase, method):
                    found.append(method)
                    print(f"  ✅ {method} existe")
                else:
                    missing.append(method)
                    print(f"  ❌ {method} não existe")
            
            self.metrics['methods_found'] = len(found)
            self.metrics['methods_required'] = len(required_methods)
            
            if missing:
                self.errors.append(f"Métodos faltando: {', '.join(missing)}")
        except ImportError as e:
            self.errors.append(f"OdooTestBase não pode ser importado: {e}")
    
    def _validate_crud_file(self):
        """Valida arquivo crud.py."""
        print("\n📄 Verificando arquivo crud.py...")
        
        crud_file = Path("playwright_simple/odoo/crud.py")
        if crud_file.exists():
            print("  ✅ crud.py existe")
            self.metrics['crud_file_exists'] = True
        else:
            self.errors.append("crud.py não existe")
            print("  ❌ crud.py não existe")
    
    def _print_results(self):
        """Exibe resultados."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        print(f"\n⏱️  Tempo: {self.metrics.get('validation_time', 0):.2f}s")
        if 'methods_found' in self.metrics:
            print(f"🔧 Métodos: {self.metrics['methods_found']}/{self.metrics.get('methods_required', 0)}")
        
        if self.errors:
            print(f"\n❌ Erros: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
            print("\n❌ VALIDAÇÃO FALHOU")
        else:
            print("\n✅ VALIDAÇÃO PASSOU")
        
        print("=" * 60)


def main():
    validator = Phase7Validator()
    sys.exit(0 if validator.validate() else 1)


if __name__ == "__main__":
    main()

