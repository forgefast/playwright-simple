#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Argument Parser.

Handles all argument parsing and subcommand definitions.
"""

import argparse
from typing import Optional


def parse_viewport(viewport_str: str) -> dict:
    """Parse viewport string (WIDTHxHEIGHT) into dict."""
    try:
        width, height = viewport_str.split('x')
        return {'width': int(width), 'height': int(height)}
    except ValueError:
        raise argparse.ArgumentTypeError(f"Viewport deve ser no formato WIDTHxHEIGHT (ex: 1920x1080)")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all options."""
    parser = argparse.ArgumentParser(
        description="playwright-simple - Automação web simplificada",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Executar teste YAML básico
  playwright-simple run test.yaml

  # Executar com debug e logging detalhado
  playwright-simple run test.yaml --log-level DEBUG --debug

  # Executar com vídeo, áudio e legendas
  playwright-simple run test.yaml --video --audio --subtitles

  # Executar em modo não-headless com viewport customizado
  playwright-simple run test.yaml --no-headless --viewport 1920x1080

  # Executar com configuração de arquivo
  playwright-simple run test.yaml --config config.yaml
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Executar teste YAML')
    run_parser.add_argument('yaml_file', type=str, help='Arquivo YAML do teste')
    
    # Record command
    record_parser = subparsers.add_parser('record', help='Gravar interações e gerar YAML')
    record_parser.add_argument('output', type=str, help='Arquivo YAML de saída')
    
    # Command commands (for controlling active recording)
    _add_command_parsers(subparsers)
    
    # Record arguments
    record_parser.add_argument(
        '--url',
        '--site',
        type=str,
        dest='url',
        help='URL inicial para abrir (default: about:blank). Exemplo: --url https://example.com'
    )
    record_parser.add_argument(
        '--headless',
        action='store_true',
        help='Executar browser em modo headless (não recomendado para gravação)'
    )
    record_parser.add_argument(
        '--debug',
        action='store_true',
        help='Habilitar modo debug - logging verboso de todos os eventos'
    )
    
    # Logging options
    _add_logging_options(parser)
    
    # Browser options
    _add_browser_options(run_parser)
    
    # Video options
    _add_video_options(run_parser)
    
    # Audio options
    _add_audio_options(run_parser)
    
    # Subtitle options
    _add_subtitle_options(run_parser)
    
    # Debug options
    _add_debug_options(run_parser)
    
    # Config options
    _add_config_options(run_parser)
    
    return parser


def _add_command_parsers(subparsers):
    """Add parsers for command commands (find, click, type, etc.)."""
    command_parser = subparsers.add_parser('find', help='Encontrar elemento em gravação ativa')
    command_parser.add_argument('text', type=str, help='Texto do elemento a encontrar')
    command_parser.add_argument('--selector', type=str, help='Seletor CSS (em vez de texto)')
    command_parser.add_argument('--role', type=str, help='Role ARIA (em vez de texto)')
    
    click_parser = subparsers.add_parser('click', help='Clicar em elemento em gravação ativa')
    click_parser.add_argument('text', type=str, nargs='?', help='Texto do elemento a clicar')
    click_parser.add_argument('--selector', type=str, help='Seletor CSS')
    click_parser.add_argument('--role', type=str, help='Role ARIA')
    click_parser.add_argument('--index', type=int, default=0, help='Índice se múltiplos elementos')
    
    type_parser = subparsers.add_parser('type', help='Digitar texto em campo em gravação ativa')
    type_parser.add_argument('text', type=str, help='Texto a digitar')
    type_parser.add_argument('--into', type=str, help='Campo onde digitar (label, placeholder, etc)')
    type_parser.add_argument('--selector', type=str, help='Seletor CSS do campo')
    
    submit_parser = subparsers.add_parser('submit', help='Submeter formulário em gravação ativa')
    submit_parser.add_argument('button_text', type=str, nargs='?', help='Texto do botão submit (opcional)')
    
    wait_parser = subparsers.add_parser('wait', help='Esperar elemento aparecer em gravação ativa')
    wait_parser.add_argument('text', type=str, nargs='?', help='Texto do elemento')
    wait_parser.add_argument('--selector', type=str, help='Seletor CSS')
    wait_parser.add_argument('--role', type=str, help='Role ARIA')
    wait_parser.add_argument('--timeout', type=int, default=5, help='Timeout em segundos')
    
    info_parser = subparsers.add_parser('info', help='Mostrar informações da página em gravação ativa')
    
    html_parser = subparsers.add_parser('html', help='Obter HTML da página ou elemento em gravação ativa')
    html_parser.add_argument('--selector', type=str, help='Seletor CSS do elemento (opcional, se omitido retorna HTML da página)')
    html_parser.add_argument('--pretty', '-p', action='store_true', help='Formatar HTML com indentação')
    html_parser.add_argument('--max-length', '--max', type=int, help='Comprimento máximo do HTML a retornar')
    
    # Recording control commands
    save_parser = subparsers.add_parser('save', help='Salvar gravação YAML (continua gravando)')
    
    exit_parser = subparsers.add_parser('exit', help='Sair da gravação sem salvar')
    
    pause_parser = subparsers.add_parser('pause', help='Pausar gravação')
    
    resume_parser = subparsers.add_parser('resume', help='Retomar gravação')
    
    start_parser = subparsers.add_parser('start', help='Iniciar gravação')
    
    # Metadata commands
    caption_parser = subparsers.add_parser('caption', help='Adicionar legenda/subtítulo (cria step separado)')
    caption_parser.add_argument('text', type=str, help='Texto da legenda')
    
    subtitle_parser = subparsers.add_parser('subtitle', help='Adicionar legenda ao último step (para vídeo)')
    subtitle_parser.add_argument('text', type=str, nargs='?', default='', help='Texto da legenda (vazio para limpar)')
    
    audio_parser = subparsers.add_parser('audio', help='Adicionar narração de áudio (cria step separado)')
    audio_parser.add_argument('text', type=str, help='Texto para narração')
    
    audio_step_parser = subparsers.add_parser('audio-step', help='Adicionar áudio ao último step (para vídeo)')
    audio_step_parser.add_argument('text', type=str, nargs='?', default='', help='Texto do áudio (vazio para limpar)')
    
    screenshot_parser = subparsers.add_parser('screenshot', help='Tirar screenshot')
    screenshot_parser.add_argument('--name', type=str, help='Nome do screenshot (opcional)')
    
    # Video config commands
    video_enable_parser = subparsers.add_parser('video-enable', help='Habilitar gravação de vídeo no YAML')
    video_disable_parser = subparsers.add_parser('video-disable', help='Desabilitar gravação de vídeo no YAML')
    
    video_quality_parser = subparsers.add_parser('video-quality', help='Definir qualidade do vídeo no YAML')
    video_quality_parser.add_argument('quality', choices=['low', 'medium', 'high'], help='Qualidade do vídeo')
    
    video_codec_parser = subparsers.add_parser('video-codec', help='Definir codec do vídeo no YAML')
    video_codec_parser.add_argument('codec', choices=['webm', 'mp4'], help='Codec do vídeo')
    
    video_dir_parser = subparsers.add_parser('video-dir', help='Definir diretório de vídeos no YAML')
    video_dir_parser.add_argument('dir', type=str, help='Diretório para salvar vídeos')
    
    video_speed_parser = subparsers.add_parser('video-speed', help='Definir velocidade do vídeo no YAML')
    video_speed_parser.add_argument('speed', type=float, help='Velocidade do vídeo (1.0 = normal, 2.0 = 2x mais rápido)')
    
    video_subtitles_parser = subparsers.add_parser('video-subtitles', help='Habilitar/desabilitar legendas no YAML')
    video_subtitles_parser.add_argument('enabled', choices=['true', 'false', 'enable', 'disable'], help='Habilitar ou desabilitar legendas')
    
    video_audio_parser = subparsers.add_parser('video-audio', help='Habilitar/desabilitar áudio no YAML')
    video_audio_parser.add_argument('enabled', choices=['true', 'false', 'enable', 'disable'], help='Habilitar ou desabilitar áudio')


def _add_logging_options(parser):
    """Add logging argument group."""
    logging_group = parser.add_argument_group('Logging')
    logging_group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Nível de logging (default: INFO)'
    )
    logging_group.add_argument(
        '--log-file',
        type=str,
        help='Arquivo para salvar logs'
    )
    logging_group.add_argument(
        '--json-log',
        action='store_true',
        help='Usar formato JSON para logs'
    )
    logging_group.add_argument(
        '--no-console-log',
        action='store_true',
        help='Desabilitar logs no console'
    )


def _add_browser_options(run_parser):
    """Add browser argument group."""
    browser_group = run_parser.add_argument_group('Browser')
    browser_group.add_argument(
        '--headless',
        action='store_true',
        help='Executar em modo headless'
    )
    browser_group.add_argument(
        '--no-headless',
        action='store_true',
        dest='no_headless',
        help='Executar com browser visível (padrão)'
    )
    browser_group.add_argument(
        '--viewport',
        type=str,
        help='Tamanho do viewport (ex: 1920x1080)'
    )
    browser_group.add_argument(
        '--slow-mo',
        type=int,
        help='Delay entre ações em milissegundos'
    )
    browser_group.add_argument(
        '--timeout',
        type=int,
        help='Timeout padrão em milissegundos'
    )


def _add_video_options(run_parser):
    """Add video argument group."""
    video_group = run_parser.add_argument_group('Video')
    video_group.add_argument(
        '--video',
        action='store_true',
        help='Habilitar gravação de vídeo'
    )
    video_group.add_argument(
        '--no-video',
        action='store_true',
        dest='no_video',
        help='Desabilitar gravação de vídeo'
    )
    video_group.add_argument(
        '--video-quality',
        choices=['low', 'medium', 'high'],
        help='Qualidade do vídeo'
    )
    video_group.add_argument(
        '--video-codec',
        choices=['webm', 'mp4'],
        help='Codec do vídeo'
    )
    video_group.add_argument(
        '--video-speed',
        type=float,
        help='Velocidade do vídeo (1.0 = normal, 2.0 = 2x mais rápido)'
    )
    video_group.add_argument(
        '--video-dir',
        type=str,
        help='Diretório para salvar vídeos'
    )


def _add_audio_options(run_parser):
    """Add audio argument group."""
    audio_group = run_parser.add_argument_group('Audio')
    audio_group.add_argument(
        '--audio',
        action='store_true',
        help='Habilitar áudio/narração'
    )
    audio_group.add_argument(
        '--no-audio',
        action='store_true',
        dest='no_audio',
        help='Desabilitar áudio/narração'
    )
    audio_group.add_argument(
        '--audio-lang',
        type=str,
        help='Idioma do áudio (ex: pt-BR, en-US)'
    )
    audio_group.add_argument(
        '--audio-engine',
        choices=['gtts', 'pyttsx3'],
        help='Engine de TTS'
    )
    audio_group.add_argument(
        '--audio-slow',
        action='store_true',
        help='Falar mais devagar'
    )


def _add_subtitle_options(run_parser):
    """Add subtitle argument group."""
    subtitle_group = run_parser.add_argument_group('Subtitles')
    subtitle_group.add_argument(
        '--subtitles',
        action='store_true',
        help='Habilitar legendas'
    )
    subtitle_group.add_argument(
        '--no-subtitles',
        action='store_true',
        dest='no_subtitles',
        help='Desabilitar legendas'
    )
    subtitle_group.add_argument(
        '--hard-subtitles',
        action='store_true',
        help='Queimar legendas no vídeo (hard subtitles)'
    )


def _add_debug_options(run_parser):
    """Add debug argument group."""
    debug_group = run_parser.add_argument_group('Debug')
    debug_group.add_argument(
        '--debug',
        action='store_true',
        help='Habilitar modo debug'
    )
    debug_group.add_argument(
        '--screenshot-on-failure',
        action='store_true',
        help='Tirar screenshot quando teste falhar'
    )
    debug_group.add_argument(
        '--pause-on-failure',
        action='store_true',
        help='Pausar quando teste falhar'
    )


def _add_config_options(run_parser):
    """Add config argument group."""
    config_group = run_parser.add_argument_group('Config')
    config_group.add_argument(
        '--config',
        type=str,
        help='Arquivo de configuração YAML'
    )
    config_group.add_argument(
        '--base-url',
        type=str,
        help='URL base para testes'
    )

