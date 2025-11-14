#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 0.

Verifica estrutura de diretórios, configuração e imports básicos.
"""

import pytest
import yaml
from pathlib import Path
import sys
import importlib


class TestPhase0Structure:
    """Testes de estrutura de diretórios."""
    
    def test_structure_exists(self):
        """Verifica que estrutura de diretórios existe."""
        required_dirs = [
            "tests/unit/core",
            "tests/integration/core_yaml",
            "tests/e2e/generic",
            "playwright_simple/core/recorder"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)
        
        assert len(missing_dirs) == 0, f"Diretórios faltando: {', '.join(missing_dirs)}"
    
    def test_structure_is_directory(self):
        """Verifica que caminhos são diretórios, não arquivos."""
        required_dirs = [
            "tests/unit/core",
            "tests/integration/core_yaml",
            "tests/e2e/generic",
            "playwright_simple/core/recorder"
        ]
        
        for dir_path in required_dirs:
            path = Path(dir_path)
            assert path.exists(), f"Diretório {dir_path} não existe"
            assert path.is_dir(), f"{dir_path} não é um diretório"


class TestPhase0Config:
    """Testes de configuração."""
    
    def test_pytest_config_exists(self):
        """Verifica que pytest.ini existe."""
        pytest_ini = Path("pytest.ini")
        assert pytest_ini.exists(), "pytest.ini não existe"
        assert pytest_ini.is_file(), "pytest.ini não é um arquivo"
    
    def test_pytest_config_content(self):
        """Verifica que pytest.ini tem configuração básica."""
        pytest_ini = Path("pytest.ini")
        if not pytest_ini.exists():
            pytest.skip("pytest.ini não existe")
        
        content = pytest_ini.read_text()
        # Verificar que tem alguma configuração
        assert len(content.strip()) > 0, "pytest.ini está vazio"
        
        # Verificar configurações comuns
        has_config = any(keyword in content.lower() for keyword in [
            "testpaths", "python_files", "python_classes", "python_functions"
        ])
        assert has_config, "pytest.ini sem configuração básica detectada"
    
    def test_ci_workflow_exists(self):
        """Verifica que CI/CD workflow existe."""
        ci_file = Path(".github/workflows/ci.yml")
        assert ci_file.exists(), "CI/CD workflow não existe"
        assert ci_file.is_file(), "CI/CD workflow não é um arquivo"
    
    def test_ci_workflow_valid_yaml(self):
        """Verifica que CI/CD workflow é YAML válido."""
        ci_file = Path(".github/workflows/ci.yml")
        if not ci_file.exists():
            pytest.skip("CI/CD workflow não existe")
        
        try:
            with open(ci_file) as f:
                data = yaml.safe_load(f)
                assert data is not None, "CI/CD workflow YAML inválido (None)"
                assert isinstance(data, dict), "CI/CD workflow não é um dicionário YAML"
        except yaml.YAMLError as e:
            pytest.fail(f"CI/CD workflow YAML inválido: {e}")
    
    def test_ci_workflow_has_jobs(self):
        """Verifica que CI/CD workflow tem jobs configurados."""
        ci_file = Path(".github/workflows/ci.yml")
        if not ci_file.exists():
            pytest.skip("CI/CD workflow não existe")
        
        try:
            with open(ci_file) as f:
                data = yaml.safe_load(f)
                # Verificar que tem jobs ou steps
                has_structure = "jobs" in data or "on" in data
                assert has_structure, "CI/CD workflow sem estrutura válida"
        except Exception as e:
            pytest.fail(f"Erro ao ler CI/CD workflow: {e}")


class TestPhase0Imports:
    """Testes de imports básicos."""
    
    def test_import_simple_test_base(self):
        """Verifica que SimpleTestBase pode ser importado."""
        try:
            from playwright_simple import SimpleTestBase
            assert SimpleTestBase is not None
        except ImportError as e:
            pytest.fail(f"Falha ao importar SimpleTestBase: {e}")
    
    def test_import_yaml_parser(self):
        """Verifica que YAMLParser pode ser importado."""
        try:
            from playwright_simple.core.yaml_parser import YAMLParser
            assert YAMLParser is not None
        except ImportError as e:
            pytest.fail(f"Falha ao importar YAMLParser: {e}")
    
    def test_import_test_config(self):
        """Verifica que TestConfig pode ser importado."""
        try:
            from playwright_simple import TestConfig
            assert TestConfig is not None
        except ImportError as e:
            pytest.fail(f"Falha ao importar TestConfig: {e}")
    
    def test_imports_are_callable(self):
        """Verifica que imports são classes/funções utilizáveis."""
        from playwright_simple import SimpleTestBase, TestConfig
        from playwright_simple.core.yaml_parser import YAMLParser
        
        # Verificar que são classes
        assert isinstance(SimpleTestBase, type) or callable(SimpleTestBase), "SimpleTestBase não é uma classe"
        assert isinstance(TestConfig, type) or callable(TestConfig), "TestConfig não é uma classe"
        assert isinstance(YAMLParser, type) or callable(YAMLParser), "YAMLParser não é uma classe"


class TestPhase0PytestCollection:
    """Testes de coleta de testes pelo pytest."""
    
    def test_pytest_can_collect_tests(self):
        """Verifica que pytest consegue coletar testes."""
        import subprocess
        import sys
        
        # Executar pytest --collect-only
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Verificar que não houve erro crítico
        # Pytest pode retornar código 5 (nenhum teste encontrado) que é OK
        assert result.returncode in [0, 5], f"pytest --collect-only falhou com código {result.returncode}: {result.stderr}"
        
        # Verificar que stdout não contém erros críticos
        critical_errors = ["error", "failed", "traceback"]
        stderr_lower = result.stderr.lower()
        has_critical_error = any(error in stderr_lower for error in critical_errors if "no tests" not in stderr_lower)
        
        if has_critical_error and result.returncode != 5:
            pytest.fail(f"pytest encontrou erros críticos: {result.stderr}")


class TestPhase0Metrics:
    """Testes de métricas da FASE 0."""
    
    def test_count_directories(self):
        """Verifica número mínimo de diretórios."""
        required_dirs = [
            "tests/unit/core",
            "tests/integration/core_yaml",
            "tests/e2e/generic",
            "playwright_simple/core/recorder"
        ]
        
        existing_dirs = [d for d in required_dirs if Path(d).exists()]
        assert len(existing_dirs) >= 4, f"Apenas {len(existing_dirs)} de {len(required_dirs)} diretórios existem"
    
    def test_count_config_files(self):
        """Verifica número mínimo de arquivos de configuração."""
        config_files = [
            "pytest.ini",
            ".github/workflows/ci.yml"
        ]
        
        existing_files = [f for f in config_files if Path(f).exists()]
        assert len(existing_files) >= 2, f"Apenas {len(existing_files)} de {len(config_files)} arquivos de configuração existem"

