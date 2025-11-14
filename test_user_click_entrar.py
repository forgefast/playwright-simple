#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de captura de clique do usuário real em link "Entrar".

Este script abre o navegador e espera o usuário clicar em "Entrar"
para verificar se o evento é capturado corretamente pelo event_capture.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple.core.recorder import Recorder

async def main():
    """Test user click on 'Entrar' link."""
    print("=" * 60)
    print("🧪 TESTE: Captura de clique do usuário em link 'Entrar'")
    print("=" * 60)
    print()
    print("📋 Instruções:")
    print("   1. O navegador será aberto na página inicial do Odoo")
    print("   2. Clique no link 'Entrar' com o mouse")
    print("   3. Aguarde alguns segundos após o clique")
    print("   4. O script verificará se o clique foi capturado no YAML")
    print()
    
    output_file = Path("test_user_click_entrar.yaml")
    
    # Create recorder
    recorder = Recorder(
        output_path=output_file,
        initial_url="http://localhost:18069",
        headless=False,  # Mostrar navegador para usuário clicar
        debug=True,  # Modo debug para ver logs detalhados
        fast_mode=False
    )
    
    try:
        # Start recording
        print("🚀 Iniciando gravação...")
        await recorder.start()
        print("✅ Gravação iniciada!")
        print()
        print("👆 AGORA: Clique no link 'Entrar' na página do navegador")
        print("   (Aguarde alguns segundos após o clique para a navegação acontecer)")
        print()
        
        # Wait for user to click (give them time)
        print("⏳ Aguardando você clicar em 'Entrar'...")
        print("   (Pressione Enter quando terminar de clicar)")
        
        # Wait for Enter key or timeout
        import select
        import termios
        import tty
        
        # Set terminal to raw mode temporarily
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            # Wait up to 30 seconds for Enter key
            for _ in range(300):  # 30 seconds with 0.1s intervals
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    if key == '\n' or key == '\r':  # Enter key
                        break
                await asyncio.sleep(0.1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        print("\n✅ Continuando verificação...")
        
        # Check how many steps were captured
        steps_count = recorder.yaml_writer.get_steps_count()
        print()
        print(f"📊 Steps capturados até agora: {steps_count}")
        
        if steps_count > 1:  # More than just the go_to
            print("✅ Clique detectado! Verificando YAML...")
        else:
            print("⚠️  Apenas o go_to foi capturado. O clique pode não ter sido detectado.")
        
        # Stop recording
        print()
        print("🛑 Parando gravação...")
        await recorder.stop(save=True)
        print("✅ Gravação salva!")
        
        # Read and display YAML
        if output_file.exists():
            print()
            print(f"📄 Conteúdo do YAML gerado:")
            print("-" * 60)
            with open(output_file, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
                print(yaml_content)
            print("-" * 60)
            
            # Check if "Entrar" is in YAML
            if "Entrar" in yaml_content or "entrar" in yaml_content.lower():
                print()
                print("✅ SUCESSO: 'Entrar' encontrado no YAML!")
                print("   O clique do usuário foi capturado corretamente.")
            else:
                print()
                print("❌ PROBLEMA: 'Entrar' NÃO encontrado no YAML!")
                print("   O clique do usuário pode não ter sido capturado.")
                print("   Verifique os logs acima para mais detalhes.")
        else:
            print(f"❌ Arquivo YAML não foi criado: {output_file}")
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        await recorder.stop(save=True)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        await recorder.stop(save=False)
    finally:
        print()
        print("=" * 60)
        print("🏁 Teste finalizado")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

