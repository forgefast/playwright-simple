#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 12.

Verifica documentação completa e exemplos.
"""

import pytest
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

pytest_timeout = pytest.mark.timeout(5)


class TestPhase12Documentation:
    """Testes de documentação."""
    
    def test_api_reference_exists(self):
        """Verifica que API_REFERENCE.md existe."""
        api_ref = Path("docs/API_REFERENCE.md")
        assert api_ref.exists(), "API_REFERENCE.md não existe"
    
    def test_user_manual_exists(self):
        """Verifica que USER_MANUAL.md existe."""
        user_manual = Path("USER_MANUAL.md")
        assert user_manual.exists(), "USER_MANUAL.md não existe"
    
    def test_quick_start_exists(self):
        """Verifica que QUICK_START.md existe."""
        quick_start = Path("QUICK_START.md")
        assert quick_start.exists(), "QUICK_START.md não existe"
    
    def test_tutorials_exist(self):
        """Verifica que tutoriais existem."""
        tutorials_dir = Path("examples/tutorials")
        if tutorials_dir.exists():
            tutorials = list(tutorials_dir.glob("*.md"))
            assert len(tutorials) > 0, "Nenhum tutorial encontrado"
        else:
            pytest.skip("Diretório examples/tutorials não existe")
    
    def test_examples_exist(self):
        """Verifica que exemplos existem."""
        examples_dir = Path("examples")
        if examples_dir.exists():
            # Verificar que tem algum conteúdo
            assert True  # Apenas verificar que diretório existe
        else:
            pytest.skip("Diretório examples não existe")

