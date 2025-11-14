#!/usr/bin/env python3
"""
Script simples para testar captura do clique em "Entrar".
Foca apenas no primeiro clique para debugar o problema.
"""
import asyncio
import sys
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, str(Path(__file__).parent))

from playwright_simple.core.recorder.recorder import Recorder

async def test_entrar_click():
    """Testa apenas o clique em 'Entrar'."""
    yaml_path = Path('test_entrar_click.yaml')
    
    print("🚀 Iniciando recorder...")
    recorder = Recorder(yaml_path, initial_url='http://localhost:18069', headless=False, fast_mode=True, debug=True)
    
    # Iniciar recorder
    async def run_recorder():
        await recorder.start()
    
    recorder_task = asyncio.create_task(run_recorder())
    
    # Aguardar recorder estar pronto
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
        await asyncio.sleep(0.2)
    
    if not page or not hasattr(recorder, 'is_recording') or not recorder.is_recording:
        print("⚠️  Recorder pode não estar totalmente pronto, continuando...")
        if page:
            try:
                await asyncio.wait_for(
                    page.wait_for_load_state('networkidle', timeout=5000),
                    timeout=6.0
                )
            except:
                pass
    
    print("\n📝 Testando apenas o clique em 'Entrar'...\n")
    
    # Usar command_handlers diretamente
    handlers = recorder.command_handlers
    
    # 1. Encontrar botão "Entrar"
    print("1️⃣  Procurando 'Entrar'...")
    try:
        await asyncio.wait_for(
            handlers.handle_find('Entrar'),
            timeout=10.0
        )
        print("   ✅ Elemento encontrado")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        await recorder.stop(save=False)
        return
    
    # Verificar eventos antes do clique
    print("\n🔍 Verificando eventos ANTES do clique...")
    events_before = await page.evaluate("""
        () => {
            return {
                events: window.__playwright_recording_events || [],
                count: (window.__playwright_recording_events || []).length
            };
        }
    """)
    print(f"   Eventos antes: {events_before['count']}")
    
    # 2. Clicar em "Entrar"
    print("\n2️⃣  Clicando em 'Entrar'...")
    try:
        await asyncio.wait_for(
            handlers.handle_pw_click('Entrar'),
            timeout=10.0
        )
        print("   ✅ Clique executado")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        await recorder.stop(save=False)
        return
    
    # Verificar eventos imediatamente após o clique (antes da navegação)
    print("\n🔍 Verificando eventos IMEDIATAMENTE após o clique...")
    try:
        events_after = await page.evaluate("""
            () => {
                return {
                    events: window.__playwright_recording_events || [],
                    count: (window.__playwright_recording_events || []).length,
                    initialized: !!(window.__playwright_recording_initialized)
                };
            }
        """)
        print(f"   Eventos após: {events_after['count']}")
        print(f"   Script inicializado: {events_after['initialized']}")
        if events_after['events']:
            for i, event in enumerate(events_after['events']):
                print(f"   Evento {i+1}: {event.get('type')} - {event.get('element', {}).get('tagName')} - {event.get('element', {}).get('text', '')[:50]}")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar eventos: {e}")
    
    # Aguardar um pouco para garantir que o evento seja processado
    print("\n⏳ Aguardando processamento de eventos...")
    await asyncio.sleep(2.0)
    
    # Verificar eventos após aguardar
    print("\n🔍 Verificando eventos APÓS aguardar...")
    try:
        events_final = await page.evaluate("""
            () => {
                return {
                    events: window.__playwright_recording_events || [],
                    count: (window.__playwright_recording_events || []).length
                };
            }
        """)
        print(f"   Eventos finais: {events_final['count']}")
        if events_final['events']:
            for i, event in enumerate(events_final['events']):
                print(f"   Evento {i+1}: {event.get('type')} - {event.get('element', {}).get('tagName')} - {event.get('element', {}).get('text', '')[:50]}")
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar eventos finais: {e}")
    
    # Verificar quantos steps foram capturados
    steps_count = recorder.yaml_writer.get_steps_count()
    print(f"\n📊 Steps capturados até agora: {steps_count}")
    
    # Listar os steps
    if steps_count > 0:
        print("\n📋 Steps no YAML:")
        for i, step in enumerate(recorder.yaml_writer.steps, 1):
            action = step.get('action', 'unknown')
            description = step.get('description', '')
            text = step.get('text', '')
            selector = step.get('selector', '')
            print(f"   {i}. {action}: {description}")
            if text:
                print(f"      text: {text}")
            if selector:
                print(f"      selector: {selector}")
    
    # 3. Parar e salvar
    print("\n3️⃣  Parando recorder e salvando...")
    try:
        await asyncio.wait_for(recorder.stop(save=True), timeout=5.0)
        print("   ✅ Recorder parado")
        recorder_task.cancel()
        try:
            await asyncio.wait_for(recorder_task, timeout=1.0)
        except:
            pass
    except Exception as e:
        print(f"   ⚠️  Erro ao parar: {e}")
    
    # Verificar YAML gerado
    if yaml_path.exists():
        print(f"\n✅ YAML salvo em: {yaml_path.absolute()}")
        print(f"\n📄 Conteúdo completo do YAML:")
        with open(yaml_path, 'r') as f:
            print(f.read())
        
        # Verificar se o clique em "Entrar" está no YAML
        with open(yaml_path, 'r') as f:
            content = f.read()
            if 'Entrar' in content:
                print("\n✅ 'Entrar' encontrado no YAML!")
            else:
                print("\n❌ 'Entrar' NÃO encontrado no YAML!")
    else:
        print(f"\n❌ YAML não foi salvo!")

if __name__ == '__main__':
    asyncio.run(test_entrar_click())

