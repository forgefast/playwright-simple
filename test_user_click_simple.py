#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples: verifica se o clique do usuário foi capturado.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple.core.recorder import Recorder

async def main():
    output_file = Path("test_user_click_entrar.yaml")
    
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
        print("⏳ Aguardando 10 segundos...")
        await asyncio.sleep(10)
        
        steps_count = recorder.yaml_writer.get_steps_count()
        print(f"\n📊 Steps capturados: {steps_count}")
        
        print("\n🛑 Parando gravação...")
        await recorder.stop(save=True)
        
        if output_file.exists():
            print(f"\n📄 YAML gerado:")
            print("-" * 60)
            with open(output_file, 'r', encoding='utf-8') as f:
                print(f.read())
            print("-" * 60)
            
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
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
        await recorder.stop(save=True)

if __name__ == "__main__":
    asyncio.run(main())

