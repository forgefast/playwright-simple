#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste final: aguarda clique e salva automaticamente."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple.core.recorder import Recorder

async def main():
    output_file = Path("test_click_final.yaml")
    
    recorder = Recorder(
        output_path=output_file,
        initial_url="http://localhost:18069",
        headless=False,
        debug=True,
        fast_mode=False
    )
    
    try:
        print("🚀 Iniciando gravação...")
        await recorder.start()
        print("✅ Gravação iniciada!")
        print()
        print("👆 Clique no link 'Entrar' no navegador")
        print("⏳ Aguardando 10 segundos para você clicar...")
        await asyncio.sleep(10)
        
        steps = recorder.yaml_writer.get_steps_count()
        print(f"\n📊 Steps capturados: {steps}")
        
        # Force stop: set is_recording to False to exit _wait_for_exit loop
        print("\n🛑 Parando gravação...")
        recorder.is_recording = False
        
        # Give a moment for _wait_for_exit to exit
        await asyncio.sleep(0.5)
        
        # Now stop and save
        await recorder.stop(save=True)
        print("✅ Salvo!")
        
        if output_file.exists():
            print(f"\n📄 YAML gerado:")
            print("=" * 60)
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
            print("=" * 60)
            
            if "Entrar" in content or "entrar" in content.lower():
                print("\n✅ SUCESSO: 'Entrar' encontrado no YAML!")
            else:
                print("\n❌ 'Entrar' NÃO encontrado no YAML!")
        else:
            print("❌ YAML não foi criado")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        try:
            recorder.is_recording = False
            await recorder.stop(save=True)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())

