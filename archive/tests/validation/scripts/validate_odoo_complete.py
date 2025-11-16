#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação completa para extensão Odoo.

Executa todas as validações e gera relatório consolidado.
"""

import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class OdooCompleteValidator:
    """Validador completo para extensão Odoo."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
        self.validation_results: Dict[str, bool] = {}
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validação Completa da Extensão Odoo")
        print("=" * 60)
        
        # Executar validações
        self._validate_auth()
        self._validate_navigation()
        self._validate_actions()
        self._validate_tests()
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        # Retornar sucesso/falha
        return len(self.errors) == 0
    
    def _validate_auth(self):
        """Valida autenticação."""
        print("\n🔐 Validando Autenticação...")
        script_path = Path(__file__).parent / "validate_odoo_auth.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("  ✅ Autenticação: PASSOU")
                self.validation_results['auth'] = True
            else:
                print(f"  ❌ Autenticação: FALHOU")
                print(f"     {result.stdout}")
                self.validation_results['auth'] = False
                self.errors.append("Autenticação falhou")
        except Exception as e:
            print(f"  ❌ Autenticação: ERRO - {e}")
            self.validation_results['auth'] = False
            self.errors.append(f"Erro ao validar autenticação: {e}")
    
    def _validate_navigation(self):
        """Valida navegação."""
        print("\n🧭 Validando Navegação...")
        script_path = Path(__file__).parent / "validate_odoo_navigation.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("  ✅ Navegação: PASSOU")
                self.validation_results['navigation'] = True
            else:
                print(f"  ❌ Navegação: FALHOU")
                print(f"     {result.stdout}")
                self.validation_results['navigation'] = False
                self.errors.append("Navegação falhou")
        except Exception as e:
            print(f"  ❌ Navegação: ERRO - {e}")
            self.validation_results['navigation'] = False
            self.errors.append(f"Erro ao validar navegação: {e}")
    
    def _validate_actions(self):
        """Valida ações."""
        print("\n⚡ Validando Ações...")
        script_path = Path(__file__).parent / "validate_odoo_actions.py"
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("  ✅ Ações: PASSOU")
                self.validation_results['actions'] = True
            else:
                print(f"  ❌ Ações: FALHOU")
                print(f"     {result.stdout}")
                self.validation_results['actions'] = False
                self.errors.append("Ações falharam")
        except Exception as e:
            print(f"  ❌ Ações: ERRO - {e}")
            self.validation_results['actions'] = False
            self.errors.append(f"Erro ao validar ações: {e}")
    
    def _validate_tests(self):
        """Valida testes unitários."""
        print("\n🧪 Validando Testes Unitários...")
        tests_dir = root_dir / "tests" / "odoo" / "validation"
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("  ✅ Testes Unitários: PASSOU")
                self.validation_results['tests'] = True
            else:
                print(f"  ❌ Testes Unitários: FALHOU")
                print(f"     {result.stdout[-500:]}")  # Last 500 chars
                self.validation_results['tests'] = False
                self.errors.append("Testes unitários falharam")
        except Exception as e:
            print(f"  ❌ Testes Unitários: ERRO - {e}")
            self.validation_results['tests'] = False
            self.errors.append(f"Erro ao executar testes: {e}")
    
    def _calculate_metrics(self):
        """Calcula métricas de validação."""
        elapsed = time.time() - self.start_time
        passed = sum(1 for v in self.validation_results.values() if v)
        total = len(self.validation_results)
        
        self.metrics = {
            'total_time': elapsed,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'validations_passed': passed,
            'validations_total': total,
            'success_rate': (passed / total * 100) if total > 0 else 0,
        }
    
    def _print_results(self):
        """Exibe resultados da validação."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação Completa")
        print("=" * 60)
        print(f"⏱️  Tempo total: {self.metrics['total_time']:.2f}s")
        print(f"✅ Validações passaram: {self.metrics['validations_passed']}/{self.metrics['validations_total']}")
        print(f"📈 Taxa de sucesso: {self.metrics['success_rate']:.1f}%")
        print(f"❌ Erros: {self.metrics['errors']}")
        print(f"⚠️  Avisos: {self.metrics['warnings']}")
        
        print("\n📋 Detalhes por Validação:")
        for name, passed in self.validation_results.items():
            status = "✅ PASSOU" if passed else "❌ FALHOU"
            print(f"  - {name}: {status}")
        
        if self.errors:
            print("\n❌ Erros encontrados:")
            for error in self.errors:
                print(f"  - {error}")
        
        if len(self.errors) == 0:
            print("\n✅ Validação Completa: PASSOU!")
        else:
            print("\n❌ Validação Completa: FALHOU!")


if __name__ == "__main__":
    validator = OdooCompleteValidator()
    success = validator.validate()
    sys.exit(0 if success else 1)

