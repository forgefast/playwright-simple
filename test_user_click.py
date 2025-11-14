#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste: abre navegador e aguarda clique do usuário em 'Entrar'."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple.core.recorder import Recorder

async def main():
    recorder = Recorder(
        output_path=Path("test_user_click.yaml"),
        initial_url="http://localhost:18069",
        headless=False,
        debug=True,
        fast_mode=False
    )
    
    print("🚀 Iniciando gravação...")
    await recorder.start()
    print("✅ Gravação iniciada!")
    print()
    print("👆 Clique no link 'Entrar' no navegador")
    print("💾 Quando terminar, use: playwright-simple save")
    print("🚪 Para sair: playwright-simple exit")
    print()
    
    # Aguardar indefinidamente (usuário vai salvar manualmente)
    try:
        while recorder.is_recording:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido")
        await recorder.stop(save=True)

if __name__ == "__main__":
    asyncio.run(main())

