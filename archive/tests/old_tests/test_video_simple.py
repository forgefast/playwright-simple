#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar gravação de vídeo sem depender de servidor.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple import TestRunner, TestConfig
from playwright_simple.core import SimpleTestBase


async def test_simple_video(page, test: SimpleTestBase):
    """Teste simples que apenas navega e espera."""
    print("  🧪 Executando teste de vídeo...")
    
    # Navegar para uma página simples (about:blank)
    await page.goto("about:blank")
    await test.wait(2)  # Esperar 2 segundos
    
    # Adicionar algum conteúdo na página para ter algo para gravar
    await page.set_content("""
        <!DOCTYPE html>
        <html>
        <head><title>Test Video</title></head>
        <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
            <div style="text-align: center;">
                <h1 style="font-size: 48px; margin: 0;">🎬 Teste de Vídeo</h1>
                <p style="font-size: 24px; margin-top: 20px;">Gravando vídeo de teste...</p>
            </div>
        </body>
        </html>
    """)
    await test.wait(3)  # Esperar 3 segundos
    
    # Fazer alguns movimentos de cursor
    await test.click("h1", "Título")
    await test.wait(1)
    
    print("  ✅ Teste concluído!")


async def main():
    """Executa o teste e gera vídeo."""
    print("🚀 Teste de gravação de vídeo (sem servidor)...")
    
    config = TestConfig.load(
        base_url="about:blank",
        cursor_style="arrow",
        cursor_color="#007bff",
        video_enabled=True,
        video_quality="high",
        video_subtitles=False,  # Desabilitar legendas para teste mais rápido
        browser_headless=True,
        browser_slow_mo=100,
    )
    
    runner = TestRunner(config=config)
    
    try:
        # Executar teste
        await runner.run_all([
            ("test_video_simple", test_simple_video)
        ])
        
        # Encontrar e verificar vídeo
        video_dir = Path("videos")
        if video_dir.exists():
            videos = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.webm"))
            if videos:
                latest_video = max(videos, key=lambda p: p.stat().st_mtime)
                print(f"\n  🎬 Vídeo gerado: {latest_video}")
                
                # Verificar duração
                import subprocess
                try:
                    result = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                         "-of", "default=noprint_wrappers=1:nokey=1", str(latest_video)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        duration = float(result.stdout.strip())
                        print(f"  ⏱️  Duração do vídeo: {duration:.2f} segundos")
                        if duration < 1.0:
                            print("  ⚠️  PROBLEMA: Vídeo muito curto!")
                        else:
                            print("  ✅ Vídeo tem duração adequada")
                except Exception as e:
                    print(f"  ⚠️  Não foi possível verificar duração: {e}")
                
                # Abrir no VLC
                try:
                    subprocess.Popen(["vlc", str(latest_video)], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                    print("  ✅ Vídeo aberto no VLC")
                except FileNotFoundError:
                    print("  ⚠️  VLC não encontrado. Abra manualmente:", latest_video)
            else:
                print("  ❌ Nenhum vídeo encontrado!")
        else:
            print("  ❌ Diretório de vídeos não existe!")
        
    except Exception as e:
        print(f"  ❌ Erro ao executar teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

