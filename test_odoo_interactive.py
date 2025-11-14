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
    
    # Aguardar recorder iniciar (com espera dinâmica baseada em condições reais)
    print("⏳ Aguardando recorder estar pronto...")
    try:
        # Wait for recorder to be ready using dynamic conditions
        page = None
        max_attempts = 30  # Up to 6 seconds total
        for attempt in range(max_attempts):
            try:
                # Check if recorder has page attribute and it's set
                if hasattr(recorder, 'page') and recorder.page:
                    page = recorder.page
                    # Check if page is ready using dynamic wait
                    try:
                        # Wait for page to be in a ready state
                        await asyncio.wait_for(
                            page.wait_for_load_state('domcontentloaded', timeout=2000),
                            timeout=2.5
                        )
                        # Check if recording has actually started
                        if hasattr(recorder, 'is_recording') and recorder.is_recording:
                            # Recorder is ready!
                            print("✅ Recorder iniciado e pronto!")
                            break
                    except asyncio.TimeoutError:
                        # Page not ready yet, continue waiting
                        pass
                    except Exception as e:
                        # Other error, might be navigation, continue waiting
                        pass
            except Exception as e:
                # Recorder not ready yet, continue waiting
                pass
            
            # Small delay between attempts (dynamic, not static)
            await asyncio.sleep(0.2)
        
        if page and hasattr(recorder, 'is_recording') and recorder.is_recording:
            print("✅ Recorder pronto para interações!")
        else:
            print("⚠️  Recorder pode não estar totalmente pronto, continuando...")
            # Wait a bit more using dynamic wait
            if page:
                try:
                    await asyncio.wait_for(
                        page.wait_for_load_state('networkidle', timeout=5000),
                        timeout=6.0
                    )
                except:
                    pass  # Continue anyway
    except Exception as e:
        print(f"⚠️  Erro ao aguardar recorder: {e}")
    
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
    
    # Aguardar página de login carregar completamente (espera dinâmica)
    print("   ⏳ Aguardando página de login carregar...")
    try:
        page = recorder.page
        if page:
            # Wait for page to be ready (dynamic wait)
            try:
                await asyncio.wait_for(
                    page.wait_for_load_state('networkidle', timeout=10000),
                    timeout=12.0
                )
            except:
                # Fallback: wait for domcontentloaded
                try:
                    await asyncio.wait_for(
                        page.wait_for_load_state('domcontentloaded', timeout=5000),
                        timeout=6.0
                    )
                except:
                    pass
            
            # Aguardar inputs aparecerem na página (dynamic wait)
            try:
                await asyncio.wait_for(
                    page.wait_for_selector('input[type="text"], input[type="email"], input[name*="login"], input[id*="login"], input[type="password"]', timeout=10000, state='visible'),
                    timeout=12.0
                )
                print("   ✅ Campos de login detectados")
            except Exception as e:
                print(f"   ⚠️  Campos não detectados ainda: {e}")
                # Try alternative selectors
                try:
                    await asyncio.wait_for(
                        page.wait_for_selector('input', timeout=5000, state='visible'),
                        timeout=6.0
                    )
                    print("   ✅ Inputs detectados (seletores alternativos)")
                except:
                    print("   ⚠️  Continuando mesmo sem detectar campos explicitamente")
    except Exception as e:
        print(f"   ⚠️  Erro aguardando página: {e}")
    
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
    # Removed static sleep - fast mode should be instant
    
    # 4. Digitar login (admin)
    print("\n4️⃣  Digitando login...")
    # Try multiple variations to find email/login field
    success, error = await run_with_timeout(
        handlers.handle_pw_type('admin into "E-mail"'),
        timeout_seconds=10.0,
        step_name="type login"
    )
    if not success:
        # Fallback: try with "login" or just "email"
        print("   ⚠️  Tentando variações...")
        success, error = await run_with_timeout(
            handlers.handle_pw_type('admin into "login"'),
            timeout_seconds=10.0,
            step_name="type login (fallback)"
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
    # Removed static sleep - fast mode should be instant
    
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
    
    # Aguardar navegação após login (espera dinâmica)
    print("   ⏳ Aguardando próxima tela após login...")
    try:
        page = recorder.page
        if page:
            # Wait for navigation to complete (dynamic wait)
            try:
                # Wait for URL to change (indicating navigation started)
                initial_url = page.url
                await asyncio.wait_for(
                    page.wait_for_function(
                        f"window.location.href !== '{initial_url}'",
                        timeout=10000
                    ),
                    timeout=12.0
                )
                print("   ✅ Navegação detectada")
            except:
                # Fallback: wait for load state
                pass
            
            # Wait for new page to be fully loaded (dynamic wait)
            try:
                await asyncio.wait_for(
                    page.wait_for_load_state('networkidle', timeout=15000),
                    timeout=18.0
                )
                print("   ✅ Página carregada completamente")
            except:
                # Fallback: wait for domcontentloaded
                try:
                    await asyncio.wait_for(
                        page.wait_for_load_state('domcontentloaded', timeout=10000),
                        timeout=12.0
                    )
                    print("   ✅ DOM carregado")
                except:
                    print("   ⚠️  Continuando mesmo sem aguardar completamente")
            
            # Adicionar passo estático ao YAML (modelagem, não execução)
            # O delay será aplicado durante a reprodução, não durante a gravação
            print("   ⏸️  Adicionando passo estático ao YAML...")
            static_step = {
                'action': 'wait',
                'description': 'Passo estático (feedback visual)',
                'static': True
                # Não especificar 'seconds' - será determinado durante a reprodução
            }
            recorder.yaml_writer.add_step(static_step)
            print("   ✅ Passo estático adicionado (delay será aplicado na reprodução)")
    except Exception as e:
        print(f"   ⚠️  Erro aguardando próxima tela: {e}")
        # Wait a bit anyway
        await asyncio.sleep(1 if not recorder.fast_mode else 0.3)
    
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
        # Parar recorder diretamente (já salvamos antes)
        # Não esperar pelo recorder_task para evitar delays
        await asyncio.wait_for(recorder.stop(save=True), timeout=5.0)
        print("   ✅ Recorder parado")
        
        # Cancelar task do recorder depois (não bloqueia)
        recorder_task.cancel()
        try:
            await asyncio.wait_for(recorder_task, timeout=1.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass  # Ignore - já paramos o recorder
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

