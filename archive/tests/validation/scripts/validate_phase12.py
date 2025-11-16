#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 12.

Verifica documentação completa e exemplos.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase12Validator:
    """Validador para FASE 12."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 12: Documentação Completa e Exemplos")
        print("=" * 60)
        
        self._validate_documentation()
        self._validate_tutorials()
        self._validate_examples()
        
        self.metrics['validation_time'] = time.time() - self.start_time
        self.metrics['errors_count'] = len(self.errors)
        self.metrics['success'] = len(self.errors) == 0
        
        self._print_results()
        return len(self.errors) == 0
    
    def _validate_documentation(self):
        """Valida documentação principal."""
        print("\n📚 Verificando documentação...")
        
        docs = {
            "API_REFERENCE.md": Path("docs/API_REFERENCE.md"),
            "USER_MANUAL.md": Path("USER_MANUAL.md"),
            "QUICK_START.md": Path("QUICK_START.md")
        }
        
        docs_found = 0
        for name, path in docs.items():
            if path.exists():
                print(f"  ✅ {name} existe")
                docs_found += 1
            else:
                self.errors.append(f"{name} não existe")
                print(f"  ❌ {name} não existe")
        
        self.metrics['docs_found'] = docs_found
        self.metrics['docs_required'] = len(docs)
    
    def _validate_tutorials(self):
        """Valida tutoriais."""
        print("\n📖 Verificando tutoriais...")
        
        tutorials_dir = Path("examples/tutorials")
        if tutorials_dir.exists():
            tutorials = list(tutorials_dir.glob("*.md"))
            self.metrics['tutorials_count'] = len(tutorials)
            
            if len(tutorials) > 0:
                print(f"  ✅ {len(tutorials)} tutorial(is) encontrado(s)")
                for tutorial in tutorials:
                    print(f"    - {tutorial.name}")
            else:
                self.warnings.append("Nenhum tutorial encontrado")
                print("  ⚠️  Nenhum tutorial encontrado")
        else:
            self.warnings.append("Diretório examples/tutorials não existe")
            print("  ⚠️  Diretório examples/tutorials não existe")
    
    def _validate_examples(self):
        """Valida exemplos."""
        print("\n💡 Verificando exemplos...")
        
        examples_dir = Path("examples")
        if examples_dir.exists():
            print("  ✅ Diretório examples existe")
            self.metrics['examples_dir_exists'] = True
        else:
            self.warnings.append("Diretório examples não existe")
            print("  ⚠️  Diretório examples não existe")
    
    def _print_results(self):
        """Exibe resultados."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        print(f"\n⏱️  Tempo: {self.metrics.get('validation_time', 0):.2f}s")
        if 'docs_found' in self.metrics:
            print(f"📚 Documentos: {self.metrics['docs_found']}/{self.metrics.get('docs_required', 0)}")
        if 'tutorials_count' in self.metrics:
            print(f"📖 Tutoriais: {self.metrics['tutorials_count']}")
        
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
    validator = Phase12Validator()
    sys.exit(0 if validator.validate() else 1)


if __name__ == "__main__":
    main()

