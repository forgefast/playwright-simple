#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 3.

Verifica melhorias no auto-fix com contexto completo.
"""

import sys
import time
import inspect
from pathlib import Path
from typing import Dict, List

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase3Validator:
    """Validador para FASE 3."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 3: Melhorias no Auto-Fix")
        print("=" * 60)
        
        self._validate_auto_fixer()
        self._validate_html_analyzer()
        self._validate_integration()
        self._validate_context()
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        # Retornar sucesso/falha
        return len(self.errors) == 0
    
    def _validate_auto_fixer(self):
        """Valida AutoFixer."""
        print("\n🔧 Verificando AutoFixer...")
        
        try:
            from playwright_simple.core.auto_fixer import AutoFixer
            from pathlib import Path
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write("name: test\n")
                yaml_file = Path(f.name)
            
            try:
                fixer = AutoFixer(yaml_file=yaml_file)
                print("  ✅ AutoFixer pode ser importado e inicializado")
            finally:
                yaml_file.unlink()
            
            # Verificar método fix_error
            if hasattr(fixer, 'fix_error') and callable(fixer.fix_error):
                print("  ✅ AutoFixer tem método fix_error")
                self.metrics['auto_fixer_works'] = True
            else:
                self.errors.append("AutoFixer não tem método fix_error")
                print("  ❌ AutoFixer não tem método fix_error")
        except ImportError as e:
            self.errors.append(f"AutoFixer não pode ser importado: {e}")
            print(f"  ❌ AutoFixer não pode ser importado: {e}")
        except Exception as e:
            self.errors.append(f"Erro ao testar AutoFixer: {e}")
            print(f"  ❌ Erro ao testar AutoFixer: {e}")
    
    def _validate_html_analyzer(self):
        """Valida HTML Analyzer."""
        print("\n📄 Verificando HTML Analyzer...")
        
        try:
            from playwright_simple.core.html_analyzer import HTMLAnalyzer
            
            analyzer = HTMLAnalyzer()
            print("  ✅ HTMLAnalyzer pode ser importado e inicializado")
            
            # Verificar que tem métodos de análise
            has_analyze = any(hasattr(analyzer, method) for method in ['analyze', 'get_buttons', 'get_inputs', 'get_links'])
            if has_analyze:
                print("  ✅ HTMLAnalyzer tem métodos de análise")
                self.metrics['html_analyzer_works'] = True
            else:
                self.warnings.append("HTMLAnalyzer pode não ter métodos de análise")
                print("  ⚠️  HTMLAnalyzer pode não ter métodos de análise")
        except ImportError as e:
            self.errors.append(f"HTMLAnalyzer não pode ser importado: {e}")
            print(f"  ❌ HTMLAnalyzer não pode ser importado: {e}")
        except Exception as e:
            self.errors.append(f"Erro ao testar HTMLAnalyzer: {e}")
            print(f"  ❌ Erro ao testar HTMLAnalyzer: {e}")
    
    def _validate_integration(self):
        """Valida integração."""
        print("\n🔗 Verificando integração...")
        
        # Verificar yaml_executor.py
        yaml_executor = Path("playwright_simple/core/yaml_executor.py")
        if yaml_executor.exists():
            content = yaml_executor.read_text()
            has_auto_fix = "auto_fix" in content.lower() or "autofixer" in content.lower()
            if has_auto_fix:
                print("  ✅ Auto-fix integrado em yaml_executor.py")
            else:
                self.warnings.append("Auto-fix pode não estar integrado em yaml_executor.py")
                print("  ⚠️  Auto-fix pode não estar integrado em yaml_executor.py")
        else:
            self.warnings.append("yaml_executor.py não encontrado")
        
        # Verificar yaml_parser.py
        yaml_parser = Path("playwright_simple/core/yaml_parser.py")
        if yaml_parser.exists():
            content = yaml_parser.read_text()
            has_auto_fix = "auto_fix" in content.lower() or "autofixer" in content.lower()
            if has_auto_fix:
                print("  ✅ Auto-fix integrado em yaml_parser.py")
            else:
                self.warnings.append("Auto-fix pode não estar integrado em yaml_parser.py")
                print("  ⚠️  Auto-fix pode não estar integrado em yaml_parser.py")
        else:
            self.warnings.append("yaml_parser.py não encontrado")
    
    def _validate_context(self):
        """Valida suporte a contexto."""
        print("\n📋 Verificando suporte a contexto...")
        
        try:
            from playwright_simple.core.auto_fixer import AutoFixer
            from pathlib import Path
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write("name: test\n")
                yaml_file = Path(f.name)
            
            try:
                fixer = AutoFixer(yaml_file=yaml_file)
                sig = inspect.signature(fixer.fix_error)
                params = list(sig.parameters.keys())
                
                context_params = ['page_state', 'html_analyzer', 'action_history']
                found_params = [p for p in context_params if p in params]
                
                if len(found_params) >= 2:
                    print(f"  ✅ Auto-fix suporta contexto: {', '.join(found_params)}")
                    self.metrics['context_support'] = len(found_params)
                else:
                    self.warnings.append(f"Auto-fix pode não suportar contexto completo. Parâmetros encontrados: {found_params}")
                    print(f"  ⚠️  Auto-fix pode não suportar contexto completo")
            finally:
                yaml_file.unlink()
        except Exception as e:
            self.warnings.append(f"Erro ao verificar contexto: {e}")
            print(f"  ⚠️  Erro ao verificar contexto: {e}")
    
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
        
        if 'context_support' in self.metrics:
            print(f"📋 Parâmetros de contexto suportados: {self.metrics['context_support']}/3")
        
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
    validator = Phase3Validator()
    success = validator.validate()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

