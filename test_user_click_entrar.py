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
    print("   3. Aguarde a navegação acontecer (você verá a tela de login)")
    print("   4. O script verificará automaticamente se o clique foi capturado")
    print()
    
    output_file = Path("test_user_click_entrar.yaml")
    
    # Remove YAML anterior se existir
    if output_file.exists():
        output_file.unlink()
        print(f"🗑️  Removido YAML anterior: {output_file}")
        print()
    
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
        print("   (Aguarde a navegação acontecer - você verá a tela de login)")
        print()
        
        # Wait for navigation to happen (user clicks "Entrar")
        print("⏳ Aguardando você clicar em 'Entrar' e a navegação acontecer...")
        print("   (Aguardando até 30 segundos)")
        
        # Wait for URL to change (navigation happened)
        initial_url = recorder.page.url
        max_wait = 30  # seconds
        waited = 0
        navigation_detected = False
        
        while waited < max_wait:
            try:
                current_url = recorder.page.url
                if current_url != initial_url:
                    print(f"\n✅ Navegação detectada! URL mudou de '{initial_url}' para '{current_url}'")
                    navigation_detected = True
                    break
            except Exception:
                # Page might be navigating, continue waiting
                pass
            
            await asyncio.sleep(0.5)
            waited += 0.5
            if waited % 5 == 0:
                print(f"   ... ainda aguardando ({int(waited)}s)")
        else:
            if not navigation_detected:
                print("\n⚠️  Timeout: Navegação não detectada após 30 segundos")
                print("   Mas vamos verificar se o clique foi capturado mesmo assim...")
        
        # Give a bit more time for event processing
        print("\n⏳ Aguardando processamento de eventos...")
        await asyncio.sleep(2)
        
        # Check how many steps were captured
        steps_count = recorder.yaml_writer.get_steps_count()
        print()
        print(f"📊 Steps capturados: {steps_count}")
        
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
                return True
            else:
                print()
                print("❌ PROBLEMA: 'Entrar' NÃO encontrado no YAML!")
                print("   O clique do usuário pode não ter sido capturado.")
                print("   Verifique os logs acima para mais detalhes.")
                return False
        else:
            print(f"❌ Arquivo YAML não foi criado: {output_file}")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        await recorder.stop(save=True)
        return False
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        await recorder.stop(save=False)
        return False
    finally:
        print()
        print("=" * 60)
        print("🏁 Teste finalizado")
        print("=" * 60)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

