#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se o EventCapture está capturando eventos no modo ULTRA_FAST.

Este script testa apenas a gravação (sem reprodução) para verificar se os eventos
estão sendo capturados corretamente.
"""

import asyncio
import sys
import yaml
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

YAML_PATH = project_root / "test_recording_ultra_fast_debug.yaml"

# Configuração: executar em modo headless
HEADLESS = True


async def test_recording_ultra_fast():
    """Testa a gravação no modo ULTRA_FAST com logs de debug."""
    print("=" * 80)
    print("TESTE DE GRAVAÇÃO ULTRA FAST - DEBUG")
    print("=" * 80)
    print()
    
    # Limpar YAML anterior
    if YAML_PATH.exists():
        print(f"🗑️  Removendo YAML anterior: {YAML_PATH}")
        YAML_PATH.unlink()
    
    try:
        from playwright_simple.core.recorder.recorder import Recorder
        from playwright_simple.core.recorder.config import RecorderConfig, SpeedLevel
        
        # Criar recorder com ULTRA_FAST e debug habilitado
        recorder_config = RecorderConfig.from_kwargs(
            output_path=YAML_PATH,
            initial_url='http://localhost:18069',
            headless=HEADLESS,
            debug=True,  # Habilitar debug para ver logs
            fast_mode=False,
            speed_level=SpeedLevel.ULTRA_FAST,
            mode='write',
            log_level='DEBUG'
        )
        recorder = Recorder(config=recorder_config)
        
        print(f"⚡ Modo: ULTRA_FAST")
        print(f"🔍 Debug: habilitado")
        print(f"📝 YAML: {YAML_PATH}")
        print()
        
        # Executar recorder em background
        async def run_recorder():
            await recorder.start()
        
        recorder_task = asyncio.create_task(run_recorder())
        
        # Aguardar recorder iniciar
        print("⏳ Aguardando recorder estar pronto...")
        page = None
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                if hasattr(recorder, 'page') and recorder.page:
                    page = recorder.page
                    try:
                        await asyncio.wait_for(
                            page.wait_for_load_state('domcontentloaded', timeout=2000),
                            timeout=2.5
                        )
                        if hasattr(recorder, 'is_recording') and recorder.is_recording:
                            print("✅ Recorder iniciado e pronto!")
                            break
                    except:
                        pass
            except:
                pass
            await asyncio.sleep(0.1)
        
        if not (page and hasattr(recorder, 'is_recording') and recorder.is_recording):
            print("⚠️  Recorder pode não estar totalmente pronto, continuando...")
            if page:
                try:
                    await asyncio.wait_for(
                        page.wait_for_load_state('domcontentloaded', timeout=2000),
                        timeout=2.5
                    )
                except:
                    pass
        
        # Verificar se EventCapture está ativo
        print()
        print("🔍 VERIFICANDO EventCapture...")
        if hasattr(recorder, 'event_capture') and recorder.event_capture:
            print(f"   ✅ EventCapture existe")
            print(f"   📊 is_capturing: {recorder.event_capture.is_capturing}")
            print(f"   🔍 debug: {recorder.event_capture.debug}")
        else:
            print(f"   ❌ EventCapture não encontrado!")
            return
        
        # Aguardar um pouco para garantir que o EventCapture está polling
        print()
        print("⏳ Aguardando 2s para EventCapture iniciar polling...")
        await asyncio.sleep(2.0)
        
        # Executar ações
        handlers = recorder.command_handlers
        
        async def run_with_timeout(coro, timeout_seconds, step_name):
            try:
                await asyncio.wait_for(coro, timeout=timeout_seconds)
                return True, None
            except asyncio.TimeoutError:
                return False, f"Timeout após {timeout_seconds}s"
            except Exception as e:
                return False, str(e)
        
        # 1. Clicar em "Entrar"
        print()
        print("1️⃣  Clicando em 'Entrar'...")
        print("   🔍 Verificando eventos antes do clique...")
        # Verificar eventos na fila antes
        if page:
            try:
                events_before = await page.evaluate("""
                    () => {
                        return {
                            count: (window.__playwright_recording_events || []).length,
                            initialized: !!(window.__playwright_recording_initialized && window.__playwright_recording_events)
                        };
                    }
                """)
                print(f"   📊 Eventos na fila antes: {events_before.get('count', 0)}")
                print(f"   📊 Script inicializado: {events_before.get('initialized', False)}")
            except Exception as e:
                print(f"   ⚠️  Erro ao verificar eventos: {e}")
        
        success, error = await run_with_timeout(
            handlers.handle_pw_click('Entrar'),
            timeout_seconds=5.0,
            step_name="click Entrar"
        )
        
        if not success:
            print(f"   ❌ Erro: {error}")
            return
        
        print("   ✅ Clique executado")
        
        # Aguardar um pouco para EventCapture capturar
        print("   ⏳ Aguardando 1s para EventCapture capturar evento...")
        await asyncio.sleep(1.0)
        
        # Verificar eventos após o clique
        if page:
            try:
                events_after = await page.evaluate("""
                    () => {
                        return {
                            count: (window.__playwright_recording_events || []).length,
                            initialized: !!(window.__playwright_recording_initialized && window.__playwright_recording_events)
                        };
                    }
                """)
                print(f"   📊 Eventos na fila depois: {events_after.get('count', 0)}")
            except Exception as e:
                print(f"   ⚠️  Erro ao verificar eventos: {e}")
        
        # Aguardar página de login
        if page:
            try:
                await asyncio.wait_for(
                    page.wait_for_selector('input[type="text"], input[type="email"], input[name*="login"], input[type="password"]', timeout=5000, state='visible'),
                    timeout=6.0
                )
            except:
                pass
        
        # 2. Digitar email
        print()
        print("2️⃣  Digitando email...")
        success, error = await run_with_timeout(
            handlers.handle_pw_type('admin into "E-mail"'),
            timeout_seconds=5.0,
            step_name="type email"
        )
        if not success:
            success, error = await run_with_timeout(
                handlers.handle_pw_type('admin into "login"'),
                timeout_seconds=5.0,
                step_name="type email (fallback)"
            )
        if not success:
            print(f"   ❌ Erro: {error}")
            return
        print("   ✅ Email digitado")
        
        # Aguardar para EventCapture capturar
        await asyncio.sleep(1.0)
        
        # 3. Digitar senha
        print()
        print("3️⃣  Digitando senha...")
        success, error = await run_with_timeout(
            handlers.handle_pw_type('admin into "Senha"'),
            timeout_seconds=5.0,
            step_name="type password"
        )
        if not success:
            success, error = await run_with_timeout(
                handlers.handle_pw_type('admin into "Password"'),
                timeout_seconds=5.0,
                step_name="type password (fallback)"
            )
        if not success:
            print(f"   ❌ Erro: {error}")
            return
        print("   ✅ Senha digitada")
        
        # Aguardar para EventCapture capturar
        await asyncio.sleep(1.0)
        
        # 4. Submeter formulário
        print()
        print("4️⃣  Submetendo formulário...")
        success, error = await run_with_timeout(
            handlers.handle_pw_submit('Entrar'),
            timeout_seconds=5.0,
            step_name="submit"
        )
        if not success:
            print(f"   ❌ Erro: {error}")
            return
        print("   ✅ Formulário submetido")
        
        # Aguardar para EventCapture capturar
        await asyncio.sleep(1.0)
        
        # 5. Salvar YAML
        print()
        print("5️⃣  Salvando YAML...")
        success, error = await run_with_timeout(
            handlers.handle_save(''),
            timeout_seconds=3.0,
            step_name="save"
        )
        if success:
            print("   ✅ YAML salvo")
        else:
            print(f"   ⚠️  Erro ao salvar: {error}")
        
        # Parar recorder
        recorder.is_recording = False
        try:
            await asyncio.wait_for(recorder.stop(save=False), timeout=2.0)
        except:
            pass
        recorder_task.cancel()
        try:
            await asyncio.wait_for(recorder_task, timeout=0.3)
        except:
            pass
        
        # Verificar YAML gerado
        print()
        print("=" * 80)
        print("RESULTADO")
        print("=" * 80)
        
        if YAML_PATH.exists():
            print(f"✅ YAML gerado: {YAML_PATH}")
            print(f"📊 Tamanho: {YAML_PATH.stat().st_size} bytes")
            
            # Ler e mostrar steps
            with open(YAML_PATH, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
            
            steps = yaml_content.get('steps', [])
            print(f"📝 Número de steps: {len(steps)}")
            print()
            print("Steps capturados:")
            for i, step in enumerate(steps, 1):
                action = step.get('action', step.get('caption', step.get('audio', 'unknown')))
                description = step.get('description', '')
                print(f"   {i}. {action}: {description}")
            
            if len(steps) < 4:
                print()
                print("⚠️  PROBLEMA: Menos steps do que esperado!")
                print(f"   Esperado: pelo menos 4 steps (go_to, click, type, type, submit)")
                print(f"   Encontrado: {len(steps)} steps")
                print()
                print("🔍 Possíveis causas:")
                print("   1. EventCapture não está capturando eventos a tempo")
                print("   2. Polling delay muito alto para ULTRA_FAST")
                print("   3. EventCapture não está ativo quando ações são executadas")
        else:
            print(f"❌ YAML não foi gerado!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_recording_ultra_fast())

