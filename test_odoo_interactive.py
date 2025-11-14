#!/usr/bin/env python3
"""
Script para testar o login do Odoo de forma interativa via CLI.
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple.core.recorder.recorder import Recorder

async def test_odoo_login():
    """Testa o login do Odoo passo a passo."""
    yaml_path = Path('test_odoo_login_real.yaml')
    
    print("🚀 Iniciando recorder...")
    # Enable fast mode to accelerate steps (delays can be adjusted in video post-processing)
    recorder = Recorder(yaml_path, initial_url='http://localhost:18069', headless=False, fast_mode=True)
    
    # Iniciar recorder (vai esperar pelo console, então executamos em background)
    async def run_recorder():
        await recorder.start()
    
    # Executar recorder em background
    recorder_task = asyncio.create_task(run_recorder())
    
    # Aguardar recorder iniciar (com timeout dinâmico)
    try:
        # Wait for recorder to be ready using dynamic wait
        page = None
        for attempt in range(20):  # Try up to 20 times (4s total)
            try:
                if hasattr(recorder, 'page') and recorder.page:
                    page = recorder.page
                    # Check if page is ready
                    try:
                        await asyncio.wait_for(
                            page.wait_for_load_state('domcontentloaded', timeout=1000),
                            timeout=1.5
                        )
                        # Page is ready
                        break
                    except:
                        # Page exists but not ready yet, continue waiting
                        pass
            except:
                pass
            await asyncio.sleep(0.2)  # Small delay between attempts
        
        if page:
            print("✅ Recorder iniciado!")
            # Wait a bit more for page to be fully interactive
            if not recorder.fast_mode:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(0.2)
        else:
            print("⚠️  Recorder iniciado (página ainda carregando)")
            # Wait a bit anyway
            await asyncio.sleep(1 if not recorder.fast_mode else 0.3)
    except Exception as e:
        print(f"⚠️  Erro ao iniciar recorder: {e}")
        await asyncio.sleep(1 if not recorder.fast_mode else 0.3)
    
    print("📝 Testando comandos diretamente...\n")
    
    # Usar command_handlers diretamente
    handlers = recorder.command_handlers
    
    # Helper para executar com timeout
    async def run_with_timeout(coro, timeout_seconds, step_name):
        """Executa uma corrotina com timeout."""
        try:
            await asyncio.wait_for(coro, timeout=timeout_seconds)
            return True, None
        except asyncio.TimeoutError:
            return False, f"Timeout após {timeout_seconds}s"
        except Exception as e:
            return False, str(e)
    
    # 1. Encontrar botão "Entrar"
    print("1️⃣  Procurando botão 'Entrar'...")
    success, error = await run_with_timeout(
        handlers.handle_find('Entrar'),
        timeout_seconds=10.0,
        step_name="find Entrar"
    )
    if not success:
        print(f"   ❌ Erro: {error}")
        await recorder.stop(save=False)
        return
    print("   ✅ Elemento encontrado")
    if not recorder.fast_mode:
        await asyncio.sleep(1)
    
    # 2. Clicar em "Entrar"
    print("\n2️⃣  Clicando em 'Entrar'...")
    success, error = await run_with_timeout(
        handlers.handle_pw_click('Entrar'),
        timeout_seconds=10.0,
        step_name="click Entrar"
    )
    if not success:
        print(f"   ❌ Erro: {error}")
        await recorder.stop(save=False)
        return
    print("   ✅ Clique executado")
    
    # Aguardar página de login carregar completamente
    print("   ⏳ Aguardando página de login carregar...")
    try:
        page = recorder.page
        if page:
            # Aguardar inputs aparecerem na página
            await asyncio.wait_for(
                page.wait_for_selector('input[type="text"], input[type="email"], input[name*="login"], input[id*="login"]', timeout=10000),
                timeout=12.0
            )
            print("   ✅ Campos de login detectados")
    except Exception as e:
            print(f"   ⚠️  Timeout aguardando campos: {e}")
    if not recorder.fast_mode:
        await asyncio.sleep(1)
    
    # 3. Encontrar campo Email
    print("\n3️⃣  Procurando campo 'Email'...")
    success, error = await run_with_timeout(
        handlers.handle_find('Email'),
        timeout_seconds=10.0,
        step_name="find Email"
    )
    if not success:
        print(f"   ❌ Erro: {error}")
        await recorder.stop(save=False)
        return
    print("   ✅ Campo encontrado")
    if not recorder.fast_mode:
        await asyncio.sleep(1)
    
    # 4. Digitar email
    print("\n4️⃣  Digitando email...")
    success, error = await run_with_timeout(
        handlers.handle_pw_type('admin@example.com into "Email"'),
        timeout_seconds=10.0,
        step_name="type email"
    )
    if not success:
        print(f"   ❌ Erro: {error}")
        await recorder.stop(save=False)
        return
    print("   ✅ Email digitado")
    if not recorder.fast_mode:
        await asyncio.sleep(1)
    
    # 5. Encontrar campo Password
    print("\n5️⃣  Procurando campo 'Password'...")
    success, error = await run_with_timeout(
        handlers.handle_find('Password'),
        timeout_seconds=10.0,
        step_name="find Password"
    )
    if not success:
        print(f"   ❌ Erro: {error}")
        await recorder.stop(save=False)
        return
    print("   ✅ Campo encontrado")
    if not recorder.fast_mode:
        await asyncio.sleep(1)
    
    # 6. Digitar senha
    print("\n6️⃣  Digitando senha...")
    success, error = await run_with_timeout(
        handlers.handle_pw_type('admin into "Password"'),
        timeout_seconds=10.0,
        step_name="type password"
    )
    if not success:
        print(f"   ❌ Erro: {error}")
        await recorder.stop(save=False)
        return
    print("   ✅ Senha digitada")
    if not recorder.fast_mode:
        await asyncio.sleep(1)
    
    # 7. Submeter formulário
    print("\n7️⃣  Submetendo formulário...")
    success, error = await run_with_timeout(
        handlers.handle_pw_submit('Entrar'),
        timeout_seconds=10.0,
        step_name="submit"
    )
    if not success:
        print(f"   ❌ Erro: {error}")
        await recorder.stop(save=False)
        return
    print("   ✅ Formulário submetido")
    if not recorder.fast_mode:
        await asyncio.sleep(3)
    else:
        await asyncio.sleep(0.5)  # Reduced delay in fast mode
    
    # 8. Verificar info
    print("\n8️⃣  Verificando estado da página...")
    success, error = await run_with_timeout(
        handlers.handle_pw_info(''),
        timeout_seconds=10.0,
        step_name="info"
    )
    if success:
        print("   ✅ Info obtida")
    else:
        print(f"   ⚠️  Erro ao obter info: {error}")
    
    # 9. Salvar
    print("\n9️⃣  Salvando YAML...")
    success, error = await run_with_timeout(
        handlers.handle_save(''),
        timeout_seconds=5.0,
        step_name="save"
    )
    if success:
        print("   ✅ YAML salvo")
    else:
        print(f"   ⚠️  Erro ao salvar: {error}")
    
    # 10. Parar
    print("\n🔟 Parando recorder...")
    try:
        # Cancelar task do recorder
        recorder_task.cancel()
        try:
            await recorder_task
        except asyncio.CancelledError:
            pass
        
        # Parar recorder
        await asyncio.wait_for(recorder.stop(save=True), timeout=10.0)
        print("   ✅ Recorder parado")
    except asyncio.TimeoutError:
        print("   ⚠️  Timeout ao parar recorder")
    except Exception as e:
        print(f"   ⚠️  Erro ao parar recorder: {e}")
    
    # Verificar YAML gerado
    if yaml_path.exists():
        print(f"\n✅ YAML salvo em: {yaml_path.absolute()}")
        print(f"📊 Conteúdo (primeiras 30 linhas):")
        with open(yaml_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:30], 1):
                print(f"   {i:2d}: {line.rstrip()}")
    else:
        print(f"\n❌ YAML não foi salvo!")

if __name__ == '__main__':
    asyncio.run(test_odoo_login())

