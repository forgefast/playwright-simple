#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar se a refatoração não quebrou nada.
Executa um teste simples e gera vídeo.
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple import TestRunner, TestConfig
from playwright_simple.odoo import OdooTestBase, OdooYAMLParser


async def test_simple_navigation(page, test: OdooTestBase):
    """Teste simples de navegação."""
    print("  🧪 Executando teste de navegação...")
    
    # Login simples
    await test.login("admin", "admin")
    await test.wait(1)
    
    # Navegar para dashboard
    await test.go_to_dashboard()
    await test.wait(2)
    
    print("  ✅ Teste concluído!")


async def main():
    """Executa o teste e gera vídeo."""
    print("🚀 Iniciando teste após refatoração...")
    
    config = TestConfig.load(
        base_url="http://localhost:8069",
        cursor_style="arrow",
        cursor_color="#007bff",
        video_enabled=True,
        video_quality="high",
        video_subtitles=True,
        browser_headless=True,
        browser_slow_mo=100,
    )
    
    runner = TestRunner(config=config)
    
    try:
        # Executar teste
        await runner.run_all([
            ("test_refactoring", test_simple_navigation)
        ])
        
        # Imprimir resumo
        runner._print_summary()
        
        # Encontrar e abrir vídeo
        video_dir = Path("videos")
        if video_dir.exists():
            videos = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.webm"))
            if videos:
                latest_video = max(videos, key=lambda p: p.stat().st_mtime)
                print(f"\n  🎬 Vídeo gerado: {latest_video}")
                
                # Abrir no VLC
                import subprocess
                try:
                    subprocess.Popen(["vlc", str(latest_video)], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                    print("  ✅ Vídeo aberto no VLC")
                except FileNotFoundError:
                    print("  ⚠️  VLC não encontrado. Abra manualmente:", latest_video)
        
    except Exception as e:
        print(f"  ❌ Erro ao executar teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

