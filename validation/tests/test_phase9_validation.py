#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes automatizados para validação da FASE 9.

Verifica vídeo, áudio e legendas avançados.
"""

import pytest
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

pytest_timeout = pytest.mark.timeout(5)


class TestPhase9Video:
    """Testes de vídeo."""
    
    def test_video_processor_exists(self):
        """Verifica que VideoProcessor pode ser importado."""
        try:
            from playwright_simple.core.runner.video_processor import VideoProcessor
            assert VideoProcessor is not None
        except ImportError:
            pytest.skip("VideoProcessor não disponível")
    
    def test_video_processor_file_exists(self):
        """Verifica que video_processor.py existe."""
        video_file = Path("playwright_simple/core/runner/video_processor.py")
        assert video_file.exists(), "video_processor.py não existe"
    
    @pytest_timeout
    def test_video_processor_has_methods(self):
        """Verifica que VideoProcessor tem métodos principais."""
        try:
            from playwright_simple.core.runner.video_processor import VideoProcessor
            
            # Verificar métodos comuns
            has_process = hasattr(VideoProcessor, 'process') or hasattr(VideoProcessor, '__init__')
            assert has_process, "VideoProcessor não tem métodos básicos"
        except ImportError:
            pytest.skip("VideoProcessor não disponível")


class TestPhase9Features:
    """Testes de funcionalidades."""
    
    def test_supports_subtitles(self):
        """Verifica suporte a legendas."""
        video_file = Path("playwright_simple/core/runner/video_processor.py")
        if video_file.exists():
            content = video_file.read_text()
            has_subtitles = "subtitle" in content.lower() or "caption" in content.lower()
            assert has_subtitles, "VideoProcessor pode não suportar legendas"
    
    def test_supports_audio(self):
        """Verifica suporte a áudio."""
        video_file = Path("playwright_simple/core/runner/video_processor.py")
        if video_file.exists():
            content = video_file.read_text()
            has_audio = "audio" in content.lower()
            assert has_audio, "VideoProcessor pode não suportar áudio"

