"""
Testes para limpeza automática de sessões antigas.
"""
import pytest
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright_simple.core.recorder.command_server import cleanup_old_sessions, find_active_sessions


@pytest.mark.timeout(10)
def test_cleanup_function():
    """Testa a função de limpeza diretamente."""
    # Limpar tudo primeiro
    cleaned = cleanup_old_sessions(force=True, timeout=3.0)
    assert isinstance(cleaned, int), "Deve retornar um inteiro"
    assert cleaned >= 0, "Número de processos limpos deve ser >= 0"


@pytest.mark.timeout(10)
def test_cleanup_timeout():
    """Testa se a limpeza respeita o timeout."""
    # Deve completar rapidamente mesmo com muitos processos
    cleaned = cleanup_old_sessions(force=True, timeout=0.1)  # Timeout muito curto
    assert isinstance(cleaned, int), "Deve retornar um inteiro mesmo com timeout curto"
