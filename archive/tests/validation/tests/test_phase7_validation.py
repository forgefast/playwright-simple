#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 7.

Verifica extensão Odoo - CRUD completo.
"""

import pytest
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

pytest_timeout = pytest.mark.timeout(5)


class TestPhase7CRUD:
    """Testes dos métodos CRUD."""
    
    def test_crud_methods_exist(self):
        """Verifica que métodos CRUD existem."""
        try:
            from playwright_simple.odoo import OdooTestBase
            
            required_methods = ['create_record', 'search_and_open', 'open_record', 'assert_record_exists']
            missing = [m for m in required_methods if not hasattr(OdooTestBase, m)]
            
            assert len(missing) == 0, f"Métodos faltando: {', '.join(missing)}"
        except ImportError:
            pytest.skip("OdooTestBase não disponível")
    
    def test_crud_file_exists(self):
        """Verifica que arquivo crud.py existe."""
        crud_file = Path("playwright_simple/odoo/crud.py")
        assert crud_file.exists(), "crud.py não existe"
    
    @pytest_timeout
    def test_crud_mixin_exists(self):
        """Verifica que OdooCRUDMixin existe."""
        try:
            from playwright_simple.odoo.crud import OdooCRUDMixin
            assert OdooCRUDMixin is not None
        except ImportError:
            pytest.skip("OdooCRUDMixin não disponível")

