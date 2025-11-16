#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 6.

Verifica extensão Odoo - ações básicas.
"""

import sys
import time
import inspect
from pathlib import Path
from typing import Dict, List

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase6Validator:
    """Validador para FASE 6."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 6: Extensão Odoo - Ações Básicas")
        print("=" * 60)
        
        self._validate_module_exists()
        self._validate_odoo_test_base()
        self._validate_methods()
        self._validate_integration()
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        # Retornar sucesso/falha
        return len(self.errors) == 0
    
    def _validate_module_exists(self):
        """Valida que módulo Odoo existe."""
        print("\n📦 Verificando módulo Odoo...")
        
        odoo_dir = Path("playwright_simple/odoo")
        if odoo_dir.exists():
            print("  ✅ Diretório odoo existe")
            self.metrics['module_exists'] = True
            
            # Verificar __init__.py
            init_file = odoo_dir / "__init__.py"
            if init_file.exists():
                print("  ✅ __init__.py existe")
            else:
                self.warnings.append("__init__.py não encontrado no módulo odoo")
                print("  ⚠️  __init__.py não encontrado")
        else:
            self.errors.append("Diretório odoo não existe")
            print("  ❌ Diretório odoo não existe")
    
    def _validate_odoo_test_base(self):
        """Valida classe OdooTestBase."""
        print("\n🏗️  Verificando OdooTestBase...")
        
        try:
            from playwright_simple.odoo import OdooTestBase
            print("  ✅ OdooTestBase pode ser importado")
            self.metrics['class_exists'] = True
        except ImportError as e:
            self.errors.append(f"OdooTestBase não pode ser importado: {e}")
            print(f"  ❌ OdooTestBase não pode ser importado: {e}")
            return
        
        # Verificar herança
        try:
            from playwright_simple import SimpleTestBase
            if issubclass(OdooTestBase, SimpleTestBase):
                print("  ✅ OdooTestBase herda de SimpleTestBase")
                self.metrics['inheritance_correct'] = True
            else:
                self.errors.append("OdooTestBase não herda de SimpleTestBase")
                print("  ❌ OdooTestBase não herda de SimpleTestBase")
        except ImportError:
            self.warnings.append("SimpleTestBase não pode ser importado")
            print("  ⚠️  SimpleTestBase não pode ser importado")
    
    def _validate_methods(self):
        """Valida métodos principais."""
        print("\n🔧 Verificando métodos...")
        
        try:
            from playwright_simple.odoo import OdooTestBase
            
            required_methods = ['login', 'go_to', 'fill', 'click']
            found_methods = []
            missing_methods = []
            
            for method in required_methods:
                if hasattr(OdooTestBase, method):
                    found_methods.append(method)
                    print(f"  ✅ Método {method} existe")
                else:
                    missing_methods.append(method)
                    print(f"  ❌ Método {method} não existe")
            
            self.metrics['methods_found'] = len(found_methods)
            self.metrics['methods_required'] = len(required_methods)
            
            if missing_methods:
                self.errors.append(f"Métodos faltando: {', '.join(missing_methods)}")
        except ImportError:
            self.errors.append("OdooTestBase não pode ser importado para verificar métodos")
    
    def _validate_integration(self):
        """Valida integração com core."""
        print("\n🔗 Verificando integração com core...")
        
        try:
            from playwright_simple.odoo import OdooTestBase
            from playwright_simple import SimpleTestBase
            
            # Verificar que não duplica métodos do core
            core_methods = set(dir(SimpleTestBase))
            odoo_methods = set(dir(OdooTestBase))
            
            # Métodos específicos do Odoo
            odoo_specific = odoo_methods - core_methods
            
            if len(odoo_specific) > 0:
                print(f"  ✅ OdooTestBase tem {len(odoo_specific)} método(s) específico(s)")
                self.metrics['odoo_specific_methods'] = len(odoo_specific)
            else:
                self.warnings.append("OdooTestBase não tem métodos específicos")
                print("  ⚠️  OdooTestBase não tem métodos específicos")
        except ImportError as e:
            self.warnings.append(f"Erro ao verificar integração: {e}")
            print(f"  ⚠️  Erro ao verificar integração: {e}")
    
    def _calculate_metrics(self):
        """Calcula métricas finais."""
        self.metrics['validation_time'] = time.time() - self.start_time
        self.metrics['errors_count'] = len(self.errors)
        self.metrics['warnings_count'] = len(self.warnings)
        self.metrics['success'] = len(self.errors) == 0
    
    def _print_results(self):
        """Exibe resultados da validação."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        print(f"\n⏱️  Tempo de validação: {self.metrics.get('validation_time', 0):.2f}s")
        
        if 'methods_found' in self.metrics:
            print(f"🔧 Métodos encontrados: {self.metrics['methods_found']}/{self.metrics.get('methods_required', 0)}")
        
        if 'odoo_specific_methods' in self.metrics:
            print(f"🎯 Métodos específicos Odoo: {self.metrics['odoo_specific_methods']}")
        
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
    """Função principal."""
    validator = Phase6Validator()
    success = validator.validate()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

