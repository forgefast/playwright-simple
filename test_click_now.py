#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste rápido: abre navegador, aguarda clique, verifica e salva."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple.core.recorder import Recorder

async def main():
    output_file = Path("test_click_result.yaml")
    
    recorder = Recorder(
        output_path=output_file,
        initial_url="http://localhost:18069",
        headless=False,
        debug=False,
        fast_mode=False
    )
    
    try:
        print("🚀 Iniciando...")
        await recorder.start()
        print("✅ Pronto! Clique em 'Entrar' no navegador.")
        print("⏳ Aguardando 8 segundos...")
        await asyncio.sleep(8)
        
        steps = recorder.yaml_writer.get_steps_count()
        print(f"\n📊 Steps: {steps}")
        
        await recorder.stop(save=True)
        
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n📄 YAML:")
                print(content)
                print()
                if "Entrar" in content or "entrar" in content.lower():
                    print("✅ 'Entrar' encontrado!")
                else:
                    print("❌ 'Entrar' NÃO encontrado")
        else:
            print("❌ YAML não criado")
    except Exception as e:
        print(f"❌ Erro: {e}")
        await recorder.stop(save=True)

if __name__ == "__main__":
    asyncio.run(main())

