#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 4.

Verifica comparação visual de screenshots.
"""

import pytest
import sys
from pathlib import Path
from PIL import Image
import tempfile
import shutil

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Timeout padrão
pytest_timeout = pytest.mark.timeout(5)


class TestPhase4VisualComparison:
    """Testes do VisualComparison."""
    
    def test_visual_comparison_exists(self):
        """Verifica que VisualComparison pode ser importado."""
        from playwright_simple.core.visual_comparison import VisualComparison
        assert VisualComparison is not None
    
    @pytest_timeout
    def test_visual_comparison_initialization(self):
        """Testa que VisualComparison pode ser inicializado."""
        from playwright_simple.core.visual_comparison import VisualComparison
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            comparison = VisualComparison(
                baseline_dir=Path(tmpdir) / "baseline",
                current_dir=Path(tmpdir) / "current",
                diff_dir=Path(tmpdir) / "diffs"
            )
            assert comparison is not None
    
    @pytest_timeout
    def test_compare_identical_screenshots(self):
        """Testa comparação de screenshots idênticos."""
        from playwright_simple.core.visual_comparison import VisualComparison
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_dir = Path(tmpdir) / "baseline"
            current_dir = Path(tmpdir) / "current"
            diff_dir = Path(tmpdir) / "diffs"
            
            baseline_dir.mkdir()
            current_dir.mkdir()
            diff_dir.mkdir()
            
            # Criar screenshots idênticos
            img = Image.new('RGB', (100, 100), color='red')
            baseline_path = baseline_dir / "test.png"
            current_path = current_dir / "test.png"
            
            img.save(baseline_path)
            img.save(current_path)
            
            comparison = VisualComparison(
                baseline_dir=baseline_dir,
                current_dir=current_dir,
                diff_dir=diff_dir
            )
            
            result = comparison.compare_screenshot("test.png", threshold=0.01)
            
            assert result is not None
            assert result.get('match') == True, "Screenshots idênticos devem ser detectados como match"
    
    @pytest_timeout
    def test_compare_different_screenshots(self):
        """Testa comparação de screenshots diferentes."""
        from playwright_simple.core.visual_comparison import VisualComparison
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_dir = Path(tmpdir) / "baseline"
            current_dir = Path(tmpdir) / "current"
            diff_dir = Path(tmpdir) / "diffs"
            
            baseline_dir.mkdir()
            current_dir.mkdir()
            diff_dir.mkdir()
            
            # Criar screenshots diferentes
            img1 = Image.new('RGB', (100, 100), color='red')
            img2 = Image.new('RGB', (100, 100), color='blue')
            
            baseline_path = baseline_dir / "test.png"
            current_path = current_dir / "test.png"
            
            img1.save(baseline_path)
            img2.save(current_path)
            
            comparison = VisualComparison(
                baseline_dir=baseline_dir,
                current_dir=current_dir,
                diff_dir=diff_dir
            )
            
            result = comparison.compare_screenshot("test.png", threshold=0.01)
            
            assert result is not None
            assert result.get('match') == False, "Screenshots diferentes devem ser detectados como não-match"
            assert 'difference' in result, "Resultado deve incluir diferença"
    
    @pytest_timeout
    def test_baseline_update(self):
        """Testa atualização de baseline."""
        from playwright_simple.core.visual_comparison import VisualComparison
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_dir = Path(tmpdir) / "baseline"
            current_dir = Path(tmpdir) / "current"
            diff_dir = Path(tmpdir) / "diffs"
            
            baseline_dir.mkdir()
            current_dir.mkdir()
            diff_dir.mkdir()
            
            # Criar screenshot atual
            img = Image.new('RGB', (100, 100), color='red')
            current_path = current_dir / "test.png"
            img.save(current_path)
            
            comparison = VisualComparison(
                baseline_dir=baseline_dir,
                current_dir=current_dir,
                diff_dir=diff_dir
            )
            
            # Atualizar baseline
            comparison.compare_screenshot("test.png", update_baseline=True)
            
            # Verificar que baseline foi criado
            baseline_path = baseline_dir / "test.png"
            assert baseline_path.exists(), "Baseline deve ser criado quando update_baseline=True"


class TestPhase4Metrics:
    """Testes de métricas da FASE 4."""
    
    def test_visual_comparison_file_exists(self):
        """Verifica que visual_comparison.py existe."""
        visual_comparison = Path("playwright_simple/core/visual_comparison.py")
        assert visual_comparison.exists(), "visual_comparison.py não existe"
    
    @pytest_timeout
    def test_compare_all_screenshots_exists(self):
        """Verifica que método compare_all_screenshots existe."""
        from playwright_simple.core.visual_comparison import VisualComparison
        
        comparison = VisualComparison(
            baseline_dir=Path("/tmp/baseline"),
            current_dir=Path("/tmp/current"),
            diff_dir=Path("/tmp/diffs")
        )
        
        assert hasattr(comparison, 'compare_all_screenshots')
        assert callable(comparison.compare_all_screenshots)

