"""
Testes para limpeza automática de sessões antigas.
"""
import pytest
import asyncio
from pathlib import Path
from playwright_simple.core.recorder.recorder import Recorder
from playwright_simple.core.recorder.command_server import cleanup_old_sessions, find_active_sessions


@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_cleanup_before_start():
    """Testa se o recorder limpa sessões antigas antes de iniciar."""
    yaml_path = Path('test_cleanup_before_start.yaml')
    
    # Limpar qualquer sessão existente primeiro
    cleanup_old_sessions(force=True, timeout=3.0)
    
    # Iniciar primeiro recorder
    recorder1 = Recorder(yaml_path, initial_url='about:blank', headless=True)
    await recorder1.start()
    
    # Verificar que há uma sessão ativa
    sessions = find_active_sessions()
    assert len(sessions) >= 1, "Deve haver pelo menos uma sessão ativa"
    
    # Iniciar segundo recorder (deve limpar o primeiro)
    yaml_path2 = Path('test_cleanup_before_start2.yaml')
    recorder2 = Recorder(yaml_path2, initial_url='about:blank', headless=True)
    await recorder2.start()
    
    # Aguardar um pouco para garantir que a limpeza aconteceu
    await asyncio.sleep(0.5)
    
    # Verificar que agora há apenas uma sessão (a nova)
    sessions_after = find_active_sessions()
    assert len(sessions_after) == 1, f"Deve haver apenas uma sessão ativa, encontradas: {len(sessions_after)}"
    
    # Limpar
    await recorder2.stop(save=False)
    cleanup_old_sessions(force=True, timeout=3.0)


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
