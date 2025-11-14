#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 0.

Verifica estrutura, configuração e imports básicos.
"""

import sys
import subprocess
from pathlib import Path
import yaml
import time
from typing import Dict, List, Tuple


class Phase0Validator:
    """Validador para FASE 0."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 0: Preparação e Infraestrutura Base")
        print("=" * 60)
        
        # Executar validações
        self._validate_structure()
        self._validate_pytest_config()
        self._validate_ci_workflow()
        self._validate_imports()
        self._validate_pytest_collection()
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        # Retornar sucesso/falha
        return len(self.errors) == 0
    
    def _validate_structure(self):
        """Valida estrutura de diretórios."""
        print("\n📁 Verificando estrutura de diretórios...")
        
        required_dirs = [
            "tests/unit/core",
            "tests/integration/core_yaml",
            "tests/e2e/generic",
            "playwright_simple/core/recorder"
        ]
        
        found_dirs = []
        for dir_path in required_dirs:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                found_dirs.append(dir_path)
                print(f"  ✅ {dir_path}")
            else:
                self.errors.append(f"Diretório não encontrado: {dir_path}")
                print(f"  ❌ {dir_path} - NÃO ENCONTRADO")
        
        self.metrics['directories_found'] = len(found_dirs)
        self.metrics['directories_required'] = len(required_dirs)
    
    def _validate_pytest_config(self):
        """Valida configuração do pytest."""
        print("\n⚙️  Verificando pytest.ini...")
        
        pytest_ini = Path("pytest.ini")
        if not pytest_ini.exists():
            self.errors.append("pytest.ini não existe")
            print("  ❌ pytest.ini não existe")
            return
        
        if not pytest_ini.is_file():
            self.errors.append("pytest.ini não é um arquivo")
            print("  ❌ pytest.ini não é um arquivo")
            return
        
        print("  ✅ pytest.ini existe")
        
        # Verificar conteúdo básico
        try:
            content = pytest_ini.read_text()
            if len(content.strip()) == 0:
                self.warnings.append("pytest.ini está vazio")
                print("  ⚠️  pytest.ini está vazio")
            else:
                print("  ✅ pytest.ini tem conteúdo")
        except Exception as e:
            self.errors.append(f"Erro ao ler pytest.ini: {e}")
            print(f"  ❌ Erro ao ler pytest.ini: {e}")
    
    def _validate_ci_workflow(self):
        """Valida CI/CD workflow."""
        print("\n🔄 Verificando CI/CD workflow...")
        
        ci_file = Path(".github/workflows/ci.yml")
        if not ci_file.exists():
            self.errors.append("CI/CD workflow não existe")
            print("  ❌ .github/workflows/ci.yml não existe")
            return
        
        print("  ✅ CI/CD workflow existe")
        
        # Verificar sintaxe YAML
        try:
            with open(ci_file) as f:
                data = yaml.safe_load(f)
                if data is None:
                    self.errors.append("CI/CD workflow YAML inválido (None)")
                    print("  ❌ CI/CD workflow YAML inválido")
                elif not isinstance(data, dict):
                    self.errors.append("CI/CD workflow não é um dicionário YAML")
                    print("  ❌ CI/CD workflow não é um dicionário YAML")
                else:
                    print("  ✅ CI/CD workflow YAML válido")
                    
                    # Verificar estrutura básica
                    if "jobs" in data or "on" in data:
                        print("  ✅ CI/CD workflow tem estrutura válida")
                    else:
                        self.warnings.append("CI/CD workflow pode estar incompleto")
                        print("  ⚠️  CI/CD workflow pode estar incompleto")
        except yaml.YAMLError as e:
            self.errors.append(f"CI/CD workflow YAML inválido: {e}")
            print(f"  ❌ Erro ao parsear YAML: {e}")
        except Exception as e:
            self.errors.append(f"Erro ao ler CI/CD workflow: {e}")
            print(f"  ❌ Erro ao ler CI/CD workflow: {e}")
    
    def _validate_imports(self):
        """Valida imports básicos."""
        print("\n📦 Verificando imports básicos...")
        
        imports_to_test = [
            ("SimpleTestBase", "from playwright_simple import SimpleTestBase"),
            ("YAMLParser", "from playwright_simple.core.yaml_parser import YAMLParser"),
            ("TestConfig", "from playwright_simple import TestConfig")
        ]
        
        successful_imports = 0
        for name, import_stmt in imports_to_test:
            try:
                # Adicionar diretório raiz ao path se necessário
                import sys
                root_dir = Path(__file__).parent.parent.parent
                if str(root_dir) not in sys.path:
                    sys.path.insert(0, str(root_dir))
                
                exec(import_stmt)
                print(f"  ✅ {name} importado com sucesso")
                successful_imports += 1
            except ImportError as e:
                # Tentar verificar se módulo existe pelo menos
                module_name = import_stmt.split()[-1].split('.')[0]
                module_path = Path(f"playwright_simple/{module_name}.py")
                if module_path.exists() or Path(f"playwright_simple/{module_name}").exists():
                    self.warnings.append(f"Import {name} falhou mas módulo existe (pode ser problema de instalação): {e}")
                    print(f"  ⚠️  {name} - módulo existe mas import falhou (instalar com: pip install -e .)")
                else:
                    self.errors.append(f"Falha ao importar {name}: {e}")
                    print(f"  ❌ Falha ao importar {name}: {e}")
            except Exception as e:
                self.errors.append(f"Erro ao importar {name}: {e}")
                print(f"  ❌ Erro ao importar {name}: {e}")
        
        self.metrics['imports_successful'] = successful_imports
        self.metrics['imports_required'] = len(imports_to_test)
    
    def _validate_pytest_collection(self):
        """Valida coleta de testes pelo pytest."""
        print("\n🧪 Verificando coleta de testes...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Código 0 = sucesso, código 5 = nenhum teste encontrado (OK)
            if result.returncode in [0, 5]:
                print("  ✅ pytest consegue coletar testes")
                
                # Contar testes coletados
                if result.returncode == 0:
                    test_count = result.stdout.count("test_")
                    self.metrics['tests_collected'] = test_count
                    print(f"  ✅ {test_count} testes coletados")
                else:
                    self.warnings.append("Nenhum teste encontrado (pode ser normal)")
                    print("  ⚠️  Nenhum teste encontrado")
            else:
                self.errors.append(f"pytest --collect-only falhou com código {result.returncode}")
                print(f"  ❌ pytest falhou: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            self.errors.append("pytest --collect-only timeout")
            print("  ❌ pytest timeout")
        except Exception as e:
            self.errors.append(f"Erro ao executar pytest: {e}")
            print(f"  ❌ Erro ao executar pytest: {e}")
    
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
        
        print(f"\n✅ Diretórios encontrados: {self.metrics.get('directories_found', 0)}/{self.metrics.get('directories_required', 0)}")
        print(f"✅ Imports bem-sucedidos: {self.metrics.get('imports_successful', 0)}/{self.metrics.get('imports_required', 0)}")
        print(f"⏱️  Tempo de validação: {self.metrics.get('validation_time', 0):.2f}s")
        
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
    validator = Phase0Validator()
    success = validator.validate()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

