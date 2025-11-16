#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar todos os vídeos dos fluxos Racco.

Este script automatiza a geração de YAMLs e vídeos para todos os 10 fluxos documentados.
"""

import asyncio
import sys
import subprocess
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Diretórios
FLUXOS_DIR = Path(__file__).parent
YAMLS_DIR = project_root / "yaml_fluxos_racco"
VIDEOS_DIR = project_root / "videos_fluxos_racco"
ODOO_URL = "http://localhost:18069"
HEADLESS = True  # Modo headless para geração de vídeos

# Criar diretórios
YAMLS_DIR.mkdir(exist_ok=True)
VIDEOS_DIR.mkdir(exist_ok=True)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step_num: int, description: str):
    """Print a formatted step."""
    print(f"\n{'─' * 80}")
    print(f"  FLUXO {step_num}: {description}")
    print(f"{'─' * 80}\n")


async def generate_yaml_for_flow(flow_name: str, flow_commands: List[str]) -> bool:
    """Gera YAML para um fluxo específico usando comandos programáticos."""
    yaml_path = YAMLS_DIR / f"{flow_name}.yaml"
    
    print(f"📝 Gerando YAML: {yaml_path.name}")
    
    # Limpar YAML anterior
    if yaml_path.exists():
        yaml_path.unlink()
    
    try:
        from playwright_simple.core.recorder.recorder import Recorder
        
        # Criar recorder com fast_mode apenas para gravação de YAML
        recorder = Recorder(
            output_path=yaml_path,
            initial_url=ODOO_URL,
            headless=HEADLESS,
            fast_mode=True  # Fast mode apenas para gravação
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
                    # Aguardar um pouco antes de clicar (especialmente após navegação)
                    await asyncio.sleep(0.5)
                    result = await run_with_timeout(
                        handlers.handle_pw_click(args.strip('"')),
                        timeout_seconds=15.0,  # Aumentar timeout
                        step_name=f"click {args}"
                    )
                    # Se falhou, tentar aguardar mais e tentar novamente
                    if result and not result.get('success') and result.get('element_found') and page:
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
                        except:
                            pass
                    success = result.get('success', False) if result else False
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
                    success = result.get('success', False) if result else False
                elif cmd == "pw-submit":
                    result = await run_with_timeout(
                        handlers.handle_pw_submit(args.strip('"')),
                        timeout_seconds=10.0,
                        step_name=f"submit {args}"
                    )
                    success = result.get('success', False) if result else False
                    # Aguardar página carregar após submit (já feito no handler, mas garantir)
                    if success and page:
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
                
                # Validar resultado se houver
                if result and not result.get('success'):
                    error_msg = result.get('error', 'Unknown error')
                    warnings = result.get('warnings', [])
                    print(f"    ❌ Erro: {error_msg}")
                    if warnings:
                        for warning in warnings:
                            print(f"    ⚠️  Aviso: {warning}")
                    # Continuar mesmo com erro
                
                # Pequeno delay entre comandos
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"    ⚠️  Exceção: {e}")
                continue
        
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
            add_video_config_to_yaml(yaml_path, flow_name)
            return True
        else:
            print(f"❌ YAML não foi gerado!")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao gerar YAML: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_video_config_to_yaml(yaml_path: Path, flow_name: str = None):
    """Adiciona configuração de vídeo ao YAML e atualiza nome do teste."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)
        
        # Atualizar nome do teste (usado como nome do vídeo)
        if flow_name:
            # Converter fluxo_01_consumidor para "Fluxo 01 - Consumidor"
            display_name = flow_name.replace('fluxo_', 'Fluxo ').replace('_', ' ').title()
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
                'dir': str(VIDEOS_DIR),
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
            video_config['dir'] = str(VIDEOS_DIR)
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
        
        print(f"✅ Configuração de vídeo adicionada (nome: {yaml_content.get('name', 'N/A')})")
    except Exception as e:
        print(f"⚠️  Erro ao adicionar configuração de vídeo: {e}")


async def generate_video_for_flow(flow_name: str) -> bool:
    """Gera vídeo a partir do YAML."""
    yaml_path = YAMLS_DIR / f"{flow_name}.yaml"
    
    if not yaml_path.exists():
        print(f"❌ YAML não encontrado: {yaml_path}")
        return False
    
    print(f"📹 Gerando vídeo: {flow_name}")
    
    headless_flag = "--headless" if HEADLESS else "--no-headless"
    
    try:
        result = subprocess.run(
            ["python3", "test_replay_yaml_with_video.py", str(yaml_path), headless_flag],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos por vídeo
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        success = result.returncode == 0
        
        if success:
            print(f"✅ Vídeo gerado para: {flow_name}")
        else:
            print(f"❌ Erro ao gerar vídeo para: {flow_name}")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"⏱️  Timeout ao gerar vídeo: {flow_name}")
        return False
    except Exception as e:
        print(f"❌ Erro ao gerar vídeo: {e}")
        return False


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


async def process_flow(flow_num: int, flow_name: str, md_file: Path):
    """Processa um fluxo completo: gera YAML e vídeo."""
    print_step(flow_num, flow_name)
    
    # Extrair comandos do MD
    commands = parse_commands_from_md(md_file)
    
    if not commands:
        print(f"⚠️  Nenhum comando encontrado no MD: {md_file}")
        return False
    
    print(f"📋 Comandos encontrados: {len(commands)}")
    
    # Gerar YAML
    yaml_success = await generate_yaml_for_flow(flow_name, commands)
    
    if not yaml_success:
        print(f"❌ Falha ao gerar YAML para {flow_name}")
        return False
    
    # Gerar vídeo
    video_success = await generate_video_for_flow(flow_name)
    
    if not video_success:
        print(f"❌ Falha ao gerar vídeo para {flow_name}")
        return False
    
    return True


async def main():
    """Executa geração de todos os vídeos."""
    print_section("GERAÇÃO DE VÍDEOS - FLUXOS RACCO")
    
    # Lista de fluxos
    flows = [
        (1, "fluxo_01_consumidor", "fluxo_01_criterios_ingresso_consumidor.md"),
        (2, "fluxo_02_revendedor", "fluxo_02_criterios_ingresso_revendedor.md"),
        (3, "fluxo_03_escalonamento", "fluxo_03_escalonamento_niveis.md"),
        (4, "fluxo_04_treinamento", "fluxo_04_jornada_treinamento.md"),
        (5, "fluxo_05_gamificacao", "fluxo_05_gamificacao.md"),
        (6, "fluxo_06_venda", "fluxo_06_venda_revendedor.md"),
        (7, "fluxo_07_comissoes", "fluxo_07_sistema_comissoes.md"),
        (8, "fluxo_08_portal_consumidor", "fluxo_08_portal_consumidor.md"),
        (9, "fluxo_09_portal_revendedor", "fluxo_09_portal_revendedor.md"),
        (10, "fluxo_10_gestao_parceiros", "fluxo_10_gestao_parceiros.md"),
    ]
    
    results = []
    
    for flow_num, flow_name, md_filename in flows:
        md_file = FLUXOS_DIR / md_filename
        
        if not md_file.exists():
            print(f"⚠️  MD não encontrado: {md_file}")
            results.append((flow_name, False))
            continue
        
        success = await process_flow(flow_num, flow_name, md_file)
        results.append((flow_name, success))
        
        # Pequeno delay entre fluxos
        await asyncio.sleep(2.0)
    
    # Resumo final
    print_section("RESUMO FINAL")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n✅ Sucesso: {success_count}/{total_count}")
    print(f"❌ Falhas: {total_count - success_count}/{total_count}\n")
    
    for flow_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {flow_name}")
    
    print(f"\n📁 YAMLs gerados em: {YAMLS_DIR}")
    print(f"📹 Vídeos gerados em: {VIDEOS_DIR}")
    
    return 0 if success_count == total_count else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

