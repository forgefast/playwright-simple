#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gravar YAML a partir de um MD (sem headless, apenas gravação).

Uso:
    python3 record_yaml_from_md.py fluxo_01_consumidor
"""

import asyncio
import sys
import yaml
from pathlib import Path
from typing import List

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Diretórios
FLUXOS_DIR = Path(__file__).parent
YAMLS_DIR = project_root / "yaml_fluxos_racco"
ODOO_URL = "http://localhost:18069"

# Criar diretório
YAMLS_DIR.mkdir(exist_ok=True)

# Mapeamento de nomes de fluxo para arquivos MD
FLOW_MAP = {
    "fluxo_01_consumidor": ("fluxo_01_criterios_ingresso_consumidor.md", "Fluxo 01 - Consumidor"),
    "fluxo_02_revendedor": ("fluxo_02_criterios_ingresso_revendedor.md", "Fluxo 02 - Revendedor"),
    "fluxo_03_escalonamento": ("fluxo_03_escalonamento_niveis.md", "Fluxo 03 - Escalonamento"),
    "fluxo_04_treinamento": ("fluxo_04_jornada_treinamento.md", "Fluxo 04 - Treinamento"),
    "fluxo_05_gamificacao": ("fluxo_05_gamificacao.md", "Fluxo 05 - Gamificacao"),
    "fluxo_06_venda": ("fluxo_06_venda_revendedor.md", "Fluxo 06 - Venda"),
    "fluxo_07_comissoes": ("fluxo_07_sistema_comissoes.md", "Fluxo 07 - Comissoes"),
    "fluxo_08_portal_consumidor": ("fluxo_08_portal_consumidor.md", "Fluxo 08 - Portal Consumidor"),
    "fluxo_09_portal_revendedor": ("fluxo_09_portal_revendedor.md", "Fluxo 09 - Portal Revendedor"),
    "fluxo_10_gestao_parceiros": ("fluxo_10_gestao_parceiros.md", "Fluxo 10 - Gestao Parceiros"),
}


def parse_commands_from_md(md_file: Path) -> List[str]:
    """Extrai comandos da seção 'Comandos de Terminal Completos' do MD."""
    commands = []
    in_commands_section = False
    in_code_block = False
    
    with open(md_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '## Comandos de Terminal Completos' in line:
                in_commands_section = True
                continue
            
            if in_commands_section:
                # Detectar início/fim de bloco de código
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                
                # Ignorar linhas fora do bloco de código
                if not in_code_block:
                    if line.startswith('##'):
                        break
                    continue
                
                # Ignorar comentários e linhas vazias
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Adicionar comando
                commands.append(stripped)
    
    return commands


def add_video_config_to_yaml(yaml_path: Path, flow_name: str, display_name: str):
    """Adiciona configuração de vídeo ao YAML e atualiza nome do teste."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
        
        # Atualizar nome do teste (usado como nome do vídeo)
        yaml_content['name'] = display_name
        if 'description' not in yaml_content or 'Gravação Automática' in yaml_content.get('description', ''):
            yaml_content['description'] = f'Vídeo demonstrativo: {display_name}'
        
        if 'config' not in yaml_content:
            yaml_content['config'] = {}
        
        if 'video' not in yaml_content['config']:
            yaml_content['config']['video'] = {
                'enabled': True,
                'quality': 'high',
                'codec': 'mp4',
                'dir': str(project_root / "videos_fluxos_racco"),
                'subtitles': True,
                'hard_subtitles': True,
                'audio': True,
                'audio_engine': 'edge-tts',
                'audio_lang': 'pt-BR',
                'audio_voice': 'pt-BR-MacerioMultilingualNeural'
            }
        else:
            video_config = yaml_content['config']['video']
            video_config['codec'] = 'mp4'
            video_config['dir'] = str(project_root / "videos_fluxos_racco")
            if 'subtitles' not in video_config:
                video_config['subtitles'] = True
            if 'hard_subtitles' not in video_config:
                video_config['hard_subtitles'] = True
            if 'audio' not in video_config:
                video_config['audio'] = True
            if 'audio_engine' not in video_config:
                video_config['audio_engine'] = 'edge-tts'
            if 'audio_lang' not in video_config:
                video_config['audio_lang'] = 'pt-BR'
            if 'audio_voice' not in video_config:
                video_config['audio_voice'] = 'pt-BR-MacerioMultilingualNeural'
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)
        
        print(f"✅ Configuração de vídeo adicionada (nome: {display_name})")
    except Exception as e:
        print(f"⚠️  Erro ao adicionar configuração de vídeo: {e}")


async def record_yaml_from_md(flow_name: str, flow_commands: List[str], display_name: str) -> bool:
    """Grava YAML a partir dos comandos do MD."""
    yaml_path = YAMLS_DIR / f"{flow_name}.yaml"
    
    print(f"📝 Gravando YAML: {yaml_path.name}")
    print(f"   Modo: VISÍVEL (não headless)")
    print(f"   Fast mode: True (apenas para gravação)")
    print(f"   Comandos: {len(flow_commands)}")
    
    # Limpar YAML anterior
    if yaml_path.exists():
        yaml_path.unlink()
        print(f"🗑️  YAML anterior removido")
    
    try:
        from playwright_simple.core.recorder.recorder import Recorder
        
        # Criar recorder SEM headless e COM fast_mode
        recorder = Recorder(
            output_path=yaml_path,
            initial_url=ODOO_URL,
            headless=False,  # Modo visível
            fast_mode=True    # Fast mode apenas para gravação
        )
        
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
                            print("✅ Recorder iniciado!")
                            break
                    except:
                        pass
            except:
                pass
            await asyncio.sleep(0.2)
        
        if not (page and hasattr(recorder, 'is_recording') and recorder.is_recording):
            print("⚠️  Recorder pode não estar totalmente pronto, continuando...")
            if page:
                try:
                    await asyncio.wait_for(
                        page.wait_for_load_state('networkidle', timeout=5000),
                        timeout=6.0
                    )
                except:
                    pass
        
        # Executar comandos
        handlers = recorder.command_handlers
        
        async def run_with_timeout(coro, timeout_seconds, step_name):
            try:
                result = await asyncio.wait_for(coro, timeout=timeout_seconds)
                return result  # Retorna o resultado estruturado do handler
            except asyncio.TimeoutError:
                return {
                    'success': False,
                    'element_found': False,
                    'action_worked': False,
                    'error': f"Timeout após {timeout_seconds}s",
                    'warnings': []
                }
            except Exception as e:
                return {
                    'success': False,
                    'element_found': False,
                    'action_worked': False,
                    'error': str(e),
                    'warnings': []
                }
        
        # Processar comandos
        failed_commands = []
        retry_commands = []
        
        for i, cmd_line in enumerate(flow_commands, 1):
            if not cmd_line.strip() or cmd_line.strip().startswith('#'):
                continue
            
            cmd_parts = cmd_line.strip().split(None, 1)
            if not cmd_parts:
                continue
            
            cmd = cmd_parts[0]
            args = cmd_parts[1] if len(cmd_parts) > 1 else ""
            
            print(f"  {i}. Executando: {cmd} {args[:50] if args else ''}")
            
            try:
                result = None
                if cmd == "pw-click":
                    # Aguardar um pouco antes de clicar
                    await asyncio.sleep(0.5)
                    result = await run_with_timeout(
                        handlers.handle_pw_click(args.strip('"')),
                        timeout_seconds=15.0,
                        step_name=f"click {args}"
                    )
                    
                    # Se falhou, tentar aguardar mais e tentar novamente
                    if result and not result.get('success') and result.get('element_found') and page:
                        print(f"    ⚠️  Elemento encontrado mas ação não funcionou, aguardando e tentando novamente...")
                        try:
                            await asyncio.wait_for(
                                page.wait_for_load_state('networkidle', timeout=3000),
                                timeout=4.0
                            )
                            await asyncio.sleep(1.0)  # Aguardar mais tempo
                            # Tentar novamente
                            result = await run_with_timeout(
                                handlers.handle_pw_click(args.strip('"')),
                                timeout_seconds=15.0,
                                step_name=f"click {args} (retry)"
                            )
                            if result and result.get('success'):
                                retry_commands.append((i, cmd, args, "Retry successful"))
                            else:
                                retry_commands.append((i, cmd, args, "Retry failed"))
                        except:
                            pass
                    
                    # Validar resultado
                    if result:
                        if not result.get('success'):
                            if not result.get('element_found'):
                                failed_commands.append((i, cmd, args, f"Element not found: {result.get('error', 'Unknown error')}"))
                            elif not result.get('action_worked'):
                                failed_commands.append((i, cmd, args, f"Element found but action didn't work: {result.get('warnings', [])}"))
                        else:
                            print(f"    ✅ Sucesso: elemento encontrado e ação funcionou")
                            
                elif cmd == "pw-type":
                    # Parse "texto" into "campo"
                    if ' into ' in args:
                        text_part, field_part = args.split(' into ', 1)
                        text = text_part.strip().strip('"')
                        field = field_part.strip().strip('"')
                        full_cmd = f'"{text}" into "{field}"'
                    else:
                        full_cmd = args
                    result = await run_with_timeout(
                        handlers.handle_pw_type(full_cmd),
                        timeout_seconds=10.0,
                        step_name=f"type {args}"
                    )
                    
                    # Validar resultado
                    if result:
                        if not result.get('success'):
                            if not result.get('element_found'):
                                failed_commands.append((i, cmd, args, f"Field not found: {result.get('error', 'Unknown error')}"))
                            elif not result.get('action_worked'):
                                failed_commands.append((i, cmd, args, f"Field found but value didn't change: {result.get('warnings', [])}"))
                        else:
                            print(f"    ✅ Sucesso: campo encontrado e valor alterado")
                            
                elif cmd == "pw-submit":
                    result = await run_with_timeout(
                        handlers.handle_pw_submit(args.strip('"')),
                        timeout_seconds=10.0,
                        step_name=f"submit {args}"
                    )
                    
                    # Validar resultado
                    if result:
                        if not result.get('success'):
                            if not result.get('element_found'):
                                failed_commands.append((i, cmd, args, f"Submit button not found: {result.get('error', 'Unknown error')}"))
                            elif not result.get('action_worked'):
                                failed_commands.append((i, cmd, args, f"Button found but form may not have submitted: {result.get('warnings', [])}"))
                        else:
                            print(f"    ✅ Sucesso: botão encontrado e formulário submetido")
                            
                    # Aguardar página carregar após submit (já feito no handler, mas garantir)
                    if result and result.get('success') and page:
                        try:
                            await asyncio.wait_for(
                                page.wait_for_load_state('networkidle', timeout=5000),
                                timeout=6.0
                            )
                        except:
                            pass
                elif cmd == "subtitle":
                    await handlers.handle_subtitle(args.strip('"'))
                    # Metadata commands always succeed
                elif cmd == "audio-step":
                    await handlers.handle_audio_step(args.strip('"'))
                    # Metadata commands always succeed
                elif cmd == "wait":
                    # Adicionar step wait no YAML
                    try:
                        wait_time = float(args)
                        # Criar step wait manualmente
                        if hasattr(recorder, 'yaml_writer'):
                            recorder.yaml_writer.add_step({
                                'action': 'wait',
                                'seconds': wait_time,
                                'description': f'Aguardando {wait_time} segundos'
                            })
                        await asyncio.sleep(wait_time)
                    except ValueError:
                        await asyncio.sleep(1.0)
                    # Wait commands always succeed
                elif cmd == "start":
                    # Start command always succeeds
                    pass
                elif cmd == "save":
                    await handlers.handle_save('')
                    # Save command always succeeds
                else:
                    print(f"    ⚠️  Comando desconhecido: {cmd}")
                
                # Pequeno delay entre comandos
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"    ⚠️  Exceção: {e}")
                failed_commands.append((i, cmd, args, f"Exception: {str(e)}"))
                continue
        
        # Reportar comandos que falharam
        if failed_commands or retry_commands:
            print(f"\n{'='*80}")
            print(f"  RELATÓRIO DE VALIDAÇÃO")
            print(f"{'='*80}\n")
            
            if retry_commands:
                print(f"✅ Comandos que precisaram retry ({len(retry_commands)}):")
                for cmd_num, cmd, args, status in retry_commands:
                    print(f"  {cmd_num}. {cmd} {args[:50]} - {status}")
                print()
            
            if failed_commands:
                print(f"❌ Comandos que falharam ({len(failed_commands)}):")
                for cmd_num, cmd, args, reason in failed_commands:
                    print(f"  {cmd_num}. {cmd} {args[:50]}")
                    print(f"     Motivo: {reason}")
                print()
            else:
                print("✅ Todos os comandos executados com sucesso!\n")
        
        # Salvar e parar
        print("💾 Salvando YAML...")
        try:
            await handlers.handle_save('')
            await asyncio.sleep(1.0)
        except:
            pass
        
        recorder.is_recording = False
        try:
            await asyncio.wait_for(recorder.stop(save=False), timeout=3.0)
        except:
            pass
        recorder_task.cancel()
        try:
            await asyncio.wait_for(recorder_task, timeout=0.5)
        except:
            pass
        
        # Verificar se YAML foi gerado
        if yaml_path.exists():
            print(f"✅ YAML gerado: {yaml_path}")
            # Adicionar configuração de vídeo
            add_video_config_to_yaml(yaml_path, flow_name, display_name)
            return True
        else:
            print(f"❌ YAML não foi gerado!")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao gerar YAML: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Executa gravação de YAML a partir do MD."""
    if len(sys.argv) < 2:
        print("Uso: python3 record_yaml_from_md.py <nome_do_fluxo>")
        print("\nFluxos disponíveis:")
        for flow_name, (md_file, display_name) in FLOW_MAP.items():
            print(f"  {flow_name} - {display_name}")
        sys.exit(1)
    
    flow_name = sys.argv[1]
    
    if flow_name not in FLOW_MAP:
        print(f"❌ Fluxo não encontrado: {flow_name}")
        print("\nFluxos disponíveis:")
        for name in FLOW_MAP.keys():
            print(f"  {name}")
        sys.exit(1)
    
    md_filename, display_name = FLOW_MAP[flow_name]
    md_file = FLUXOS_DIR / md_filename
    
    if not md_file.exists():
        print(f"❌ MD não encontrado: {md_file}")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"  GRAVAÇÃO DE YAML: {display_name}")
    print(f"{'='*80}\n")
    
    # Extrair comandos
    commands = parse_commands_from_md(md_file)
    
    if not commands:
        print(f"❌ Nenhum comando encontrado no MD")
        sys.exit(1)
    
    print(f"📋 Comandos encontrados: {len(commands)}\n")
    
    # Gravar YAML
    success = await record_yaml_from_md(flow_name, commands, display_name)
    
    if success:
        print(f"\n✅ YAML gravado com sucesso!")
        print(f"📁 Arquivo: {YAMLS_DIR / f'{flow_name}.yaml'}")
    else:
        print(f"\n❌ Falha ao gravar YAML")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

