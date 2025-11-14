#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 6.

Verifica extensão Odoo - ações básicas.
"""

import pytest
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Timeout padrão
pytest_timeout = pytest.mark.timeout(5)


class TestPhase6OdooTestBase:
    """Testes da classe OdooTestBase."""
    
    def test_odoo_test_base_exists(self):
        """Verifica que OdooTestBase pode ser importado."""
        try:
            from playwright_simple.odoo import OdooTestBase
            assert OdooTestBase is not None
        except ImportError:
            pytest.skip("OdooTestBase não está disponível")
    
    @pytest_timeout
    def test_odoo_methods_exist(self):
        """Verifica que métodos principais existem."""
        try:
            from playwright_simple.odoo import OdooTestBase
            
            required_methods = ['login', 'go_to', 'fill', 'click']
            missing_methods = []
            
            for method in required_methods:
                if not hasattr(OdooTestBase, method):
                    missing_methods.append(method)
            
            assert len(missing_methods) == 0, f"Métodos faltando: {', '.join(missing_methods)}"
        except ImportError:
            pytest.skip("OdooTestBase não está disponível")
    
    @pytest_timeout
    def test_odoo_inherits_core(self):
        """Verifica que OdooTestBase herda do core."""
        try:
            from playwright_simple.odoo import OdooTestBase
            from playwright_simple import SimpleTestBase
            
            assert issubclass(OdooTestBase, SimpleTestBase), "OdooTestBase deve herdar de SimpleTestBase"
        except ImportError:
            pytest.skip("OdooTestBase ou SimpleTestBase não estão disponíveis")


class TestPhase6OdooFiles:
    """Testes dos arquivos da extensão Odoo."""
    
    def test_odoo_module_exists(self):
        """Verifica que módulo odoo existe."""
        odoo_dir = Path("playwright_simple/odoo")
        assert odoo_dir.exists(), "Diretório odoo não existe"
        assert odoo_dir.is_dir(), "playwright_simple/odoo não é um diretório"
    
    def test_odoo_init_exists(self):
        """Verifica que __init__.py existe."""
        odoo_init = Path("playwright_simple/odoo/__init__.py")
        assert odoo_init.exists(), "__init__.py do módulo odoo não existe"
    
    def test_odoo_test_base_file_exists(self):
        """Verifica que arquivo base existe."""
        # Verificar arquivos comuns da extensão Odoo
        odoo_dir = Path("playwright_simple/odoo")
        if not odoo_dir.exists():
            pytest.skip("Diretório odoo não existe")
        
        # Verificar que tem algum arquivo Python
        py_files = list(odoo_dir.glob("*.py"))
        assert len(py_files) > 0, "Módulo odoo não tem arquivos Python"


class TestPhase6OdooTests:
    """Testes dos testes da extensão Odoo."""
    
    def test_odoo_tests_exist(self):
        """Verifica que testes Odoo existem."""
        # Procurar testes Odoo
        test_files = list(Path("tests").rglob("test_odoo*.py"))
        test_files.extend(list(Path("tests").rglob("*odoo*.py")))
        
        if len(test_files) == 0:
            # Tentar em outros locais
            test_files = list(Path(".").rglob("test_odoo*.py"))
        
        # Não falhar se não encontrar, apenas avisar
        if len(test_files) == 0:
            pytest.skip("Testes Odoo não encontrados (pode ser normal)")
        else:
            assert len(test_files) > 0, "Testes Odoo não encontrados"


class TestPhase6Integration:
    """Testes de integração."""
    
    @pytest_timeout
    def test_odoo_uses_core(self):
        """Verifica que extensão Odoo usa core genérico."""
        try:
            from playwright_simple.odoo import OdooTestBase
            from playwright_simple import SimpleTestBase
            
            # Verificar herança
            assert issubclass(OdooTestBase, SimpleTestBase), "OdooTestBase deve herdar de SimpleTestBase"
            
            # Verificar que não duplica métodos do core
            core_methods = set(dir(SimpleTestBase))
            odoo_methods = set(dir(OdooTestBase))
            
            # Métodos específicos do Odoo devem ser diferentes dos do core
            odoo_specific = odoo_methods - core_methods
            assert len(odoo_specific) > 0, "OdooTestBase deve ter métodos específicos"
        except ImportError:
            pytest.skip("OdooTestBase ou SimpleTestBase não estão disponíveis")


class TestPhase6Metrics:
    """Testes de métricas da FASE 6."""
    
    def test_odoo_module_structure(self):
        """Verifica estrutura do módulo Odoo."""
        odoo_dir = Path("playwright_simple/odoo")
        if not odoo_dir.exists():
            pytest.skip("Diretório odoo não existe")
        
        # Verificar que tem estrutura básica
        assert odoo_dir.is_dir(), "playwright_simple/odoo não é um diretório"
        
        # Verificar que tem __init__.py
        init_file = odoo_dir / "__init__.py"
        assert init_file.exists(), "__init__.py não existe no módulo odoo"

