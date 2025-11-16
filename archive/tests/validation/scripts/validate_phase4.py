#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 4.

Verifica comparação visual de screenshots.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List
from PIL import Image
import tempfile

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase4Validator:
    """Validador para FASE 4."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 4: Comparação Visual de Screenshots")
        print("=" * 60)
        
        self._validate_visual_comparison()
        self._validate_comparison_functionality()
        
        # Calcular métricas
        self._calculate_metrics()
        
        # Exibir resultados
        self._print_results()
        
        # Retornar sucesso/falha
        return len(self.errors) == 0
    
    def _validate_visual_comparison(self):
        """Valida VisualComparison."""
        print("\n🖼️  Verificando VisualComparison...")
        
        try:
            from playwright_simple.core.visual_comparison import VisualComparison
            
            # Testar inicialização
            with tempfile.TemporaryDirectory() as tmpdir:
                comparison = VisualComparison(
                    baseline_dir=Path(tmpdir) / "baseline",
                    current_dir=Path(tmpdir) / "current",
                    diff_dir=Path(tmpdir) / "diffs"
                )
                print("  ✅ VisualComparison pode ser importado e inicializado")
                self.metrics['visual_comparison_works'] = True
        except ImportError as e:
            self.errors.append(f"VisualComparison não pode ser importado: {e}")
            print(f"  ❌ VisualComparison não pode ser importado: {e}")
        except Exception as e:
            self.errors.append(f"Erro ao testar VisualComparison: {e}")
            print(f"  ❌ Erro ao testar VisualComparison: {e}")
    
    def _validate_comparison_functionality(self):
        """Valida funcionalidade de comparação."""
        print("\n🔍 Verificando funcionalidade de comparação...")
        
        try:
            from playwright_simple.core.visual_comparison import VisualComparison
            
            with tempfile.TemporaryDirectory() as tmpdir:
                baseline_dir = Path(tmpdir) / "baseline"
                current_dir = Path(tmpdir) / "current"
                diff_dir = Path(tmpdir) / "diffs"
                
                baseline_dir.mkdir()
                current_dir.mkdir()
                diff_dir.mkdir()
                
                comparison = VisualComparison(
                    baseline_dir=baseline_dir,
                    current_dir=current_dir,
                    diff_dir=diff_dir
                )
                
                # Testar comparação de screenshots idênticos
                img = Image.new('RGB', (100, 100), color='red')
                baseline_path = baseline_dir / "test.png"
                current_path = current_dir / "test.png"
                
                img.save(baseline_path)
                img.save(current_path)
                
                start_time = time.time()
                result = comparison.compare_screenshot("test.png", threshold=0.01)
                elapsed = time.time() - start_time
                
                if result and result.get('match') == True:
                    print(f"  ✅ Comparação de screenshots idênticos funciona ({elapsed:.2f}s)")
                    if elapsed < 2.0:
                        print(f"  ✅ Tempo de comparação OK: {elapsed:.2f}s")
                    else:
                        self.warnings.append(f"Comparação lenta: {elapsed:.2f}s")
                else:
                    self.errors.append("Comparação de screenshots idênticos não funciona")
                    print("  ❌ Comparação de screenshots idênticos não funciona")
                
                # Testar comparação de screenshots diferentes
                img2 = Image.new('RGB', (100, 100), color='blue')
                current_path = current_dir / "test2.png"
                img2.save(current_path)
                baseline_path = baseline_dir / "test2.png"
                img.save(baseline_path)
                
                result = comparison.compare_screenshot("test2.png", threshold=0.01)
                
                if result and result.get('match') == False:
                    print("  ✅ Comparação de screenshots diferentes funciona")
                    if 'difference' in result:
                        print(f"  ✅ Diferença detectada: {result.get('difference', 0)*100:.2f}%")
                else:
                    self.errors.append("Comparação de screenshots diferentes não funciona")
                    print("  ❌ Comparação de screenshots diferentes não funciona")
                
                # Verificar método compare_all_screenshots
                if hasattr(comparison, 'compare_all_screenshots'):
                    print("  ✅ Método compare_all_screenshots existe")
                else:
                    self.warnings.append("Método compare_all_screenshots não existe")
                    print("  ⚠️  Método compare_all_screenshots não existe")
                
        except ImportError:
            self.errors.append("PIL/Pillow não está instalado (necessário para comparação)")
            print("  ❌ PIL/Pillow não está instalado")
        except Exception as e:
            self.errors.append(f"Erro ao testar comparação: {e}")
            print(f"  ❌ Erro ao testar comparação: {e}")
    
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
    validator = Phase4Validator()
    success = validator.validate()
    
    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

