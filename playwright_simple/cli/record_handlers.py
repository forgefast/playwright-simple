#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Record Command Handlers.

Handles execution of 'record' command.
"""

import asyncio
from pathlib import Path
from typing import Optional

from playwright_simple.core.recorder.recorder import Recorder


async def record_interactions(
    output_path: str,
    initial_url: Optional[str] = None,
    headless: bool = False,
    debug: bool = False
) -> None:
    """Record user interactions and generate YAML."""
    output = Path(output_path).resolve()
    
    print(f"🎬 Iniciando gravação...")
    print(f"   Arquivo de saída: {output}")
    if initial_url:
        print(f"   Iniciando em: {initial_url}")
    else:
        print(f"   Iniciando em: about:blank (use --url para iniciar em um site específico)")
    print(f"\n📝 Comandos do console:")
    print(f"   start - Iniciar gravação")
    print(f"   save - Salvar YAML sem parar (continua gravando)")
    print(f"   exit - Sair sem salvar")
    print(f"   pause - Pausar gravação")
    print(f"   resume - Retomar gravação")
    print(f'   caption "texto" - Adicionar legenda (cria step separado)')
    print(f'   subtitle "texto" - Adicionar legenda ao último step (para vídeo)')
    print(f'   audio "texto" - Adicionar narração')
    print(f"   screenshot - Tirar screenshot")
    print(f"\n📹 Comandos de configuração de vídeo (via CLI em outro terminal):")
    print(f"   playwright-simple video-enable - Habilitar vídeo no YAML")
    print(f"   playwright-simple video-disable - Desabilitar vídeo no YAML")
    print(f"   playwright-simple video-quality [low|medium|high] - Qualidade")
    print(f"   playwright-simple video-codec [webm|mp4] - Codec")
    print(f"   playwright-simple video-dir <diretório> - Diretório de vídeos")
    print(f"   playwright-simple video-speed <número> - Velocidade (1.0 = normal)")
    print(f"   playwright-simple video-subtitles [true|false] - Legendas")
    print(f"   playwright-simple video-audio [true|false] - Áudio")
    print(f"   help - Mostrar ajuda")
    print(f"\n💡 Dica: Digite 'exit' no console quando terminar\n")
    
    recorder = Recorder(output_path=output, initial_url=initial_url, headless=headless, debug=debug)
    await recorder.start()

