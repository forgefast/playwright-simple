#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 5.

Verifica documentação do fluxo híbrido.
"""

import pytest
import sys
from pathlib import Path
import re

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Timeout padrão
pytest_timeout = pytest.mark.timeout(5)


class TestPhase5Documentation:
    """Testes da documentação."""
    
    def test_hybrid_workflow_exists(self):
        """Verifica que HYBRID_WORKFLOW.md existe."""
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        assert workflow_file.exists(), "HYBRID_WORKFLOW.md não existe"
        assert workflow_file.is_file(), "HYBRID_WORKFLOW.md não é um arquivo"
    
    @pytest_timeout
    def test_hybrid_workflow_content(self):
        """Verifica que documentação tem conteúdo adequado."""
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if not workflow_file.exists():
            pytest.skip("HYBRID_WORKFLOW.md não existe")
        
        content = workflow_file.read_text()
        
        # Verificar tamanho
        word_count = len(content.split())
        assert word_count >= 500, f"Documentação muito curta: {word_count} palavras (esperado >= 500)"
    
    @pytest_timeout
    def test_hybrid_workflow_keywords(self):
        """Verifica que documentação menciona palavras-chave importantes."""
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if not workflow_file.exists():
            pytest.skip("HYBRID_WORKFLOW.md não existe")
        
        content = workflow_file.read_text().lower()
        
        # Verificar palavras-chave
        keywords = ["gravar", "editar", "executar", "record", "run", "yaml"]
        found_keywords = [kw for kw in keywords if kw in content]
        
        assert len(found_keywords) >= 3, f"Documentação não cobre fluxo completo. Palavras encontradas: {found_keywords}"
    
    @pytest_timeout
    def test_hybrid_workflow_examples(self):
        """Verifica que documentação tem exemplos."""
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if not workflow_file.exists():
            pytest.skip("HYBRID_WORKFLOW.md não existe")
        
        content = workflow_file.read_text()
        
        # Contar exemplos (código blocks)
        code_blocks = content.count("```")
        examples = code_blocks // 2  # Cada exemplo tem 2 ```
        
        assert examples >= 3, f"Documentação tem apenas {examples} exemplos (esperado >= 3)"
    
    @pytest_timeout
    def test_hybrid_workflow_structure(self):
        """Verifica que documentação tem estrutura adequada."""
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if not workflow_file.exists():
            pytest.skip("HYBRID_WORKFLOW.md não existe")
        
        content = workflow_file.read_text()
        
        # Verificar que tem seções (títulos com #)
        headings = re.findall(r'^#+\s+.+', content, re.MULTILINE)
        assert len(headings) >= 3, f"Documentação tem apenas {len(headings)} seções (esperado >= 3)"


class TestPhase5Metrics:
    """Testes de métricas da FASE 5."""
    
    def test_documentation_file_size(self):
        """Verifica tamanho do arquivo de documentação."""
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if not workflow_file.exists():
            pytest.skip("HYBRID_WORKFLOW.md não existe")
        
        size = workflow_file.stat().st_size
        assert size > 0, "Arquivo de documentação está vazio"
        assert size >= 5000, f"Arquivo muito pequeno: {size} bytes (esperado >= 5000)"

