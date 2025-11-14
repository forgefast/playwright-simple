#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 5.

Verifica documentação do fluxo híbrido.
"""

import sys
import time
import re
from pathlib import Path
from typing import Dict, List

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase5Validator:
    """Validador para FASE 5."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 5: Documentação do Fluxo Híbrido")
        print("=" * 60)
        
        self._validate_file_exists()
        self._validate_content()
        self._validate_examples()
        self._validate_structure()
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        # Retornar sucesso/falha
        return len(self.errors) == 0
    
    def _validate_file_exists(self):
        """Valida que arquivo existe."""
        print("\n📄 Verificando arquivo...")
        
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if workflow_file.exists():
            print("  ✅ HYBRID_WORKFLOW.md existe")
            self.metrics['file_exists'] = True
        else:
            self.errors.append("HYBRID_WORKFLOW.md não existe")
            print("  ❌ HYBRID_WORKFLOW.md não existe")
    
    def _validate_content(self):
        """Valida conteúdo da documentação."""
        print("\n📝 Verificando conteúdo...")
        
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if not workflow_file.exists():
            return
        
        try:
            content = workflow_file.read_text()
            
            # Verificar tamanho
            word_count = len(content.split())
            self.metrics['word_count'] = word_count
            
            if word_count >= 500:
                print(f"  ✅ Documentação tem {word_count} palavras")
            else:
                self.warnings.append(f"Documentação muito curta: {word_count} palavras (esperado >= 500)")
                print(f"  ⚠️  Documentação muito curta: {word_count} palavras")
            
            # Verificar palavras-chave
            content_lower = content.lower()
            keywords = ["gravar", "editar", "executar", "record", "run", "yaml"]
            found_keywords = [kw for kw in keywords if kw in content_lower]
            
            if len(found_keywords) >= 3:
                print(f"  ✅ Documentação cobre fluxo completo ({len(found_keywords)} palavras-chave encontradas)")
            else:
                self.warnings.append(f"Documentação pode não cobrir fluxo completo. Palavras encontradas: {found_keywords}")
                print(f"  ⚠️  Documentação pode não cobrir fluxo completo")
            
        except Exception as e:
            self.errors.append(f"Erro ao ler documentação: {e}")
            print(f"  ❌ Erro ao ler documentação: {e}")
    
    def _validate_examples(self):
        """Valida exemplos na documentação."""
        print("\n💡 Verificando exemplos...")
        
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if not workflow_file.exists():
            return
        
        try:
            content = workflow_file.read_text()
            
            # Contar exemplos (código blocks)
            code_blocks = content.count("```")
            examples = code_blocks // 2  # Cada exemplo tem 2 ```
            
            self.metrics['examples_count'] = examples
            
            if examples >= 3:
                print(f"  ✅ Documentação tem {examples} exemplos")
            else:
                self.warnings.append(f"Documentação tem apenas {examples} exemplos (esperado >= 3)")
                print(f"  ⚠️  Documentação tem apenas {examples} exemplos")
        except Exception as e:
            self.warnings.append(f"Erro ao contar exemplos: {e}")
            print(f"  ⚠️  Erro ao contar exemplos: {e}")
    
    def _validate_structure(self):
        """Valida estrutura da documentação."""
        print("\n📑 Verificando estrutura...")
        
        workflow_file = Path("docs/HYBRID_WORKFLOW.md")
        if not workflow_file.exists():
            return
        
        try:
            content = workflow_file.read_text()
            
            # Verificar seções (títulos com #)
            headings = re.findall(r'^#+\s+.+', content, re.MULTILINE)
            self.metrics['headings_count'] = len(headings)
            
            if len(headings) >= 3:
                print(f"  ✅ Documentação tem {len(headings)} seções")
            else:
                self.warnings.append(f"Documentação tem apenas {len(headings)} seções (esperado >= 3)")
                print(f"  ⚠️  Documentação tem apenas {len(headings)} seções")
        except Exception as e:
            self.warnings.append(f"Erro ao verificar estrutura: {e}")
            print(f"  ⚠️  Erro ao verificar estrutura: {e}")
    
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
        
        if 'word_count' in self.metrics:
            print(f"📝 Palavras: {self.metrics['word_count']}")
        if 'examples_count' in self.metrics:
            print(f"💡 Exemplos: {self.metrics['examples_count']}")
        if 'headings_count' in self.metrics:
            print(f"📑 Seções: {self.metrics['headings_count']}")
        
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
    validator = Phase5Validator()
    success = validator.validate()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

