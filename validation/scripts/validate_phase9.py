#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação automatizada para FASE 9.

Verifica vídeo, áudio e legendas avançados.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List

root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class Phase9Validator:
    """Validador para FASE 9."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metrics: Dict[str, any] = {}
        self.start_time = time.time()
    
    def validate(self) -> bool:
        """Executa todas as validações."""
        print("🔍 Validando FASE 9: Vídeo, Áudio e Legendas Avançados")
        print("=" * 60)
        
        self._validate_video_processor()
        self._validate_features()
        
        self.metrics['validation_time'] = time.time() - self.start_time
        self.metrics['errors_count'] = len(self.errors)
        self.metrics['success'] = len(self.errors) == 0
        
        self._print_results()
        return len(self.errors) == 0
    
    def _validate_video_processor(self):
        """Valida VideoProcessor."""
        print("\n🎬 Verificando VideoProcessor...")
        
        video_file = Path("playwright_simple/core/runner/video_processor.py")
        if video_file.exists():
            print("  ✅ video_processor.py existe")
            self.metrics['video_processor_exists'] = True
            
            try:
                from playwright_simple.core.runner.video_processor import VideoProcessor
                print("  ✅ VideoProcessor pode ser importado")
                self.metrics['video_processor_importable'] = True
            except ImportError as e:
                self.errors.append(f"VideoProcessor não pode ser importado: {e}")
                print(f"  ❌ VideoProcessor não pode ser importado: {e}")
        else:
            self.errors.append("video_processor.py não existe")
            print("  ❌ video_processor.py não existe")
    
    def _validate_features(self):
        """Valida funcionalidades."""
        print("\n🎯 Verificando funcionalidades...")
        
        video_file = Path("playwright_simple/core/runner/video_processor.py")
        if video_file.exists():
            content = video_file.read_text()
            
            has_subtitles = "subtitle" in content.lower() or "caption" in content.lower()
            has_audio = "audio" in content.lower()
            
            if has_subtitles:
                print("  ✅ Suporte a legendas")
                self.metrics['supports_subtitles'] = True
            else:
                self.warnings.append("Suporte a legendas pode não estar implementado")
                print("  ⚠️  Suporte a legendas pode não estar implementado")
            
            if has_audio:
                print("  ✅ Suporte a áudio")
                self.metrics['supports_audio'] = True
            else:
                self.warnings.append("Suporte a áudio pode não estar implementado")
                print("  ⚠️  Suporte a áudio pode não estar implementado")
    
    def _print_results(self):
        """Exibe resultados."""
        print("\n" + "=" * 60)
        print("📊 Resultados da Validação")
        print("=" * 60)
        
        print(f"\n⏱️  Tempo: {self.metrics.get('validation_time', 0):.2f}s")
        
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
    validator = Phase9Validator()
    sys.exit(0 if validator.validate() else 1)


if __name__ == "__main__":
    main()

