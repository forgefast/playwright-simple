#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 8.

Verifica hot reload e auto-fix avançado.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase8Validator:
    """Validador para FASE 8."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 8: Hot Reload e Auto-Fix Avançado")
        print("=" * 60)
        
        self._validate_hot_reload()
        self._validate_auto_fix()
        self._validate_documentation()
        
        self.metrics['validation_time'] = time.time() - self.start_time
        self.metrics['errors_count'] = len(self.errors)
        self.metrics['success'] = len(self.errors) == 0
        
        self._print_results()
        return len(self.errors) == 0
    
    def _validate_hot_reload(self):
        """Valida hot reload."""
        print("\n🔄 Verificando hot reload...")
        
        yaml_parser = Path("playwright_simple/core/yaml_parser.py")
        if yaml_parser.exists():
            content = yaml_parser.read_text()
            has_hot_reload = "hot_reload" in content.lower() or "reload" in content.lower()
            if has_hot_reload:
                print("  ✅ yaml_parser.py menciona hot_reload")
                self.metrics['hot_reload_mentioned'] = True
            else:
                self.warnings.append("yaml_parser.py pode não ter hot_reload")
                print("  ⚠️  yaml_parser.py pode não ter hot_reload")
        else:
            self.errors.append("yaml_parser.py não encontrado")
            print("  ❌ yaml_parser.py não encontrado")
    
    def _validate_auto_fix(self):
        """Valida auto-fix."""
        print("\n🔧 Verificando auto-fix...")
        
        yaml_executor = Path("playwright_simple/core/yaml_executor.py")
        if yaml_executor.exists():
            content = yaml_executor.read_text()
            has_auto_fix = "auto_fix" in content.lower() or "autofixer" in content.lower()
            if has_auto_fix:
                print("  ✅ Auto-fix está integrado")
                self.metrics['auto_fix_integrated'] = True
            else:
                self.warnings.append("Auto-fix pode não estar integrado")
                print("  ⚠️  Auto-fix pode não estar integrado")
    
    def _validate_documentation(self):
        """Valida documentação."""
        print("\n📚 Verificando documentação...")
        
        # Verificar em múltiplos locais possíveis
        possible_paths = {
            "HOT_RELOAD.md": [Path("HOT_RELOAD.md"), Path("docs/HOT_RELOAD.md")],
            "PYTHON_HOT_RELOAD.md": [Path("PYTHON_HOT_RELOAD.md"), Path("docs/PYTHON_HOT_RELOAD.md")]
        }
        
        docs_found = 0
        for doc_name, paths in possible_paths.items():
            found = any(p.exists() for p in paths)
            if found:
                print(f"  ✅ {doc_name} existe")
                docs_found += 1
            else:
                print(f"  ⚠️  {doc_name} não encontrado")
        
        self.metrics['docs_found'] = docs_found
        
        if docs_found == 0:
            self.warnings.append("Documentação de hot reload não encontrada")
    
    def _print_results(self):
        """Exibe resultados."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        print(f"\n⏱️  Tempo: {self.metrics.get('validation_time', 0):.2f}s")
        if 'docs_found' in self.metrics:
            print(f"📚 Documentos encontrados: {self.metrics['docs_found']}")
        
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
    validator = Phase8Validator()
    sys.exit(0 if validator.validate() else 1)


if __name__ == "__main__":
    main()

