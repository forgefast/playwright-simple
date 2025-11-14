#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced CLI for playwright-simple.

Provides command-line interface with all configuration options.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional, List

from playwright_simple import TestRunner, TestConfig
from playwright_simple.core.yaml_parser import YAMLParser
from playwright_simple.core.logger import get_logger, set_logger, StructuredLogger
from playwright_simple.extensions.debug import DebugExtension, DebugConfig
from playwright_simple.extensions.video import VideoExtension, VideoConfig
from playwright_simple.extensions.audio import AudioExtension, AudioConfig
from playwright_simple.extensions.subtitles import SubtitleExtension, SubtitleConfig


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
    
    # Browser options
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
    
    # Video options
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
    
    # Audio options
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
    
    # Subtitle options
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
    
    # Debug options
    debug_group = run_parser.add_argument_group('Debug')
    debug_group.add_argument(
        '--debug',
        action='store_true',
        help='Habilitar modo debug (pausa em erros)'
    )
    debug_group.add_argument(
        '--no-debug',
        action='store_true',
        dest='no_debug',
        help='Desabilitar modo debug'
    )
    debug_group.add_argument(
        '--pause-on-error',
        action='store_true',
        help='Pausar em erros (requer --debug)'
    )
    debug_group.add_argument(
        '--no-pause-on-error',
        action='store_true',
        dest='no_pause_on_error',
        help='Não pausar em erros'
    )
    debug_group.add_argument(
        '--interactive',
        action='store_true',
        help='Modo interativo (requer --debug)'
    )
    debug_group.add_argument(
        '--hot-reload',
        action='store_true',
        help='Habilitar hot reload de YAML'
    )
    debug_group.add_argument(
        '--debug-dir',
        type=str,
        help='Diretório para arquivos de debug'
    )
    debug_group.add_argument(
        '--step-timeout',
        type=float,
        default=1.0,
        help='Timeout em segundos para pausa em cada passo (padrão: 1.0s para execução automática, use 0 para espera indefinida)'
    )
    
    # Cursor options
    cursor_group = run_parser.add_argument_group('Cursor')
    cursor_group.add_argument(
        '--cursor-style',
        choices=['arrow', 'dot', 'circle', 'custom'],
        help='Estilo do cursor'
    )
    cursor_group.add_argument(
        '--cursor-color',
        type=str,
        help='Cor do cursor (hex, ex: #007bff)'
    )
    cursor_group.add_argument(
        '--cursor-size',
        choices=['small', 'medium', 'large'],
        help='Tamanho do cursor'
    )
    
    # Screenshot options
    screenshot_group = run_parser.add_argument_group('Screenshots')
    screenshot_group.add_argument(
        '--screenshots',
        action='store_true',
        help='Habilitar screenshots automáticos'
    )
    screenshot_group.add_argument(
        '--no-screenshots',
        action='store_true',
        dest='no_screenshots',
        help='Desabilitar screenshots automáticos'
    )
    screenshot_group.add_argument(
        '--screenshot-dir',
        type=str,
        help='Diretório para salvar screenshots'
    )
    
    # General options
    general_group = run_parser.add_argument_group('General')
    general_group.add_argument(
        '--base-url',
        type=str,
        help='URL base para testes'
    )
    general_group.add_argument(
        '--config',
        type=str,
        help='Arquivo de configuração YAML/JSON'
    )
    general_group.add_argument(
        '--output-dir',
        type=str,
        help='Diretório de saída (videos, screenshots, logs)'
    )
    general_group.add_argument(
        '--parallel',
        action='store_true',
        help='Executar testes em paralelo'
    )
    general_group.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Número de workers para execução paralela'
    )
    general_group.add_argument(
        '--list-tests',
        action='store_true',
        help='Listar testes disponíveis no YAML'
    )
    general_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular execução sem executar (dry run)'
    )
    
    return parser


def parse_viewport(viewport_str: str) -> dict:
    """Parse viewport string (e.g., '1920x1080') to dict."""
    try:
        width, height = viewport_str.split('x')
        return {'width': int(width), 'height': int(height)}
    except ValueError:
        raise argparse.ArgumentTypeError(f"Viewport deve ser no formato WIDTHxHEIGHT (ex: 1920x1080)")


def create_config_from_args(args: argparse.Namespace) -> TestConfig:
    """Create TestConfig from command-line arguments."""
    # Load base config from file if provided
    if args.config:
        config = TestConfig.from_file(args.config)
    else:
        config = TestConfig()
    
    # Override with CLI arguments
    
    # Base URL
    if args.base_url:
        config.base_url = args.base_url
    
    # Logging - Always set logger with CLI level
    logger = StructuredLogger(
        name="playwright_simple",
        level=args.log_level,
        log_file=Path(args.log_file) if args.log_file else None,
        json_log=args.json_log,
        console_output=not args.no_console_log
    )
    set_logger(logger)
    
    # Browser
    if args.headless:
        config.browser.headless = True
    elif args.no_headless:
        config.browser.headless = False
    
    if args.viewport:
        config.browser.viewport = parse_viewport(args.viewport)
    
    if args.slow_mo is not None:
        config.browser.slow_mo = args.slow_mo
    
    if args.timeout is not None:
        config.browser.timeout = args.timeout
    
    # Video
    if args.video:
        config.video.enabled = True
    elif args.no_video:
        config.video.enabled = False
    
    if args.video_quality:
        config.video.quality = args.video_quality
    
    if args.video_codec:
        config.video.codec = args.video_codec
    
    if args.video_speed is not None:
        config.video.speed = args.video_speed
    
    if args.video_dir:
        config.video.dir = args.video_dir
    
    # Audio
    if args.audio:
        config.video.audio = True
        config.video.narration = True
    elif args.no_audio:
        config.video.audio = False
        config.video.narration = False
    
    if args.audio_lang:
        config.video.audio_lang = args.audio_lang
        config.video.narration_lang = args.audio_lang
    
    if args.audio_engine:
        config.video.audio_engine = args.audio_engine
        config.video.narration_engine = args.audio_engine
    
    if args.audio_slow:
        config.video.narration_slow = True
    
    # Subtitles
    if args.subtitles:
        config.video.subtitles = True
    elif args.no_subtitles:
        config.video.subtitles = False
    
    if args.hard_subtitles:
        config.video.hard_subtitles = True
    
    # Screenshots
    if args.screenshots:
        config.screenshots.auto = True
    elif args.no_screenshots:
        config.screenshots.auto = False
    
    if args.screenshot_dir:
        config.screenshots.dir = args.screenshot_dir
    
    # Cursor
    if args.cursor_style:
        config.cursor.style = args.cursor_style
    
    if args.cursor_color:
        config.cursor.color = args.cursor_color
    
    if args.cursor_size:
        config.cursor.size = args.cursor_size
    
    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        config.video.dir = str(output_dir / "videos")
        config.screenshots.dir = str(output_dir / "screenshots")
        if args.log_file is None:
            log_file = output_dir / "logs" / "test.log"
            logger = StructuredLogger(
                name="playwright_simple",
                level=args.log_level,
                log_file=log_file,
                json_log=args.json_log,
                console_output=not args.no_console_log
            )
            set_logger(logger)
    
    return config


async def run_test(yaml_file: str, config: TestConfig, args: argparse.Namespace) -> None:
    """Run a test from YAML file."""
    yaml_path = Path(yaml_file)
    
    if not yaml_path.exists():
        print(f"❌ Arquivo YAML não encontrado: {yaml_file}")
        sys.exit(1)
    
    # Load test
    test_name, test_func = YAMLParser.load_test(yaml_path)
    
    # Wrap test function to inject debug extension if CLI args provided
    if args.debug or getattr(args, 'pause_on_error', False) or getattr(args, 'interactive', False):
        original_func = test_func
        step_timeout = getattr(args, 'step_timeout', None)
        
        async def test_func_with_debug(page, test, **kwargs):
            # Register debug extension if not already registered
            if not test.extensions.has('debug'):
                debug_config = DebugConfig(
                    enabled=True,
                    pause_on_error=getattr(args, 'pause_on_error', False) or args.debug,
                    pause_on_element_not_found=getattr(args, 'pause_on_error', False) or args.debug,
                    interactive_mode=getattr(args, 'interactive', False) or args.debug,
                    hot_reload_enabled=getattr(args, 'hot_reload', False),
                    state_dir=getattr(args, 'debug_dir', None) or "debug_states",
                    html_snapshot_dir=getattr(args, 'debug_dir', None) or "debug_html",
                    checkpoint_dir=getattr(args, 'debug_dir', None) or "debug_checkpoints"
                )
                debug_ext = DebugExtension(debug_config)
                await test.register_extension(debug_ext)
            
            # Store step_timeout in test instance for yaml_executor to use
            # If step_timeout is 0, set to None (wait indefinitely)
            # Otherwise use the provided timeout or default 1.0 (for automatic execution)
            if step_timeout == 0:
                test._debug_step_timeout = None
            else:
                test._debug_step_timeout = step_timeout if step_timeout is not None else 1.0
            
            await original_func(page, test, **kwargs)
        test_func = test_func_with_debug
    
    # Create runner
    runner = TestRunner(config=config)
    
    # Dry run
    if args.dry_run:
        print(f"🔍 Dry run: Teste '{test_name}' seria executado")
        print(f"   Arquivo: {yaml_path}")
        print(f"   Configuração:")
        print(f"     - Headless: {config.browser.headless}")
        print(f"     - Video: {config.video.enabled}")
        print(f"     - Audio: {config.video.audio}")
        print(f"     - Subtitles: {config.video.subtitles}")
        print(f"     - Debug: {args.debug}")
        return
    
    # List tests
    if args.list_tests:
        print(f"📋 Testes disponíveis em {yaml_path}:")
        print(f"   - {test_name}")
        return
    
    # Run test
    print(f"🎬 Executando teste: {test_name}")
    print(f"   Arquivo: {yaml_path}")
    print(f"   Log level: {args.log_level}")
    
    # Create browser and run test
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=config.browser.headless,
            slow_mo=config.browser.slow_mo
        )
        try:
            result = await runner.run_test(test_name, test_func, browser=browser)
        finally:
            await browser.close()
    
    # Print result
    if result['status'] == 'passed':
        print(f"✅ Teste '{test_name}' passou")
    elif result['status'] == 'failed':
        print(f"❌ Teste '{test_name}' falhou: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    elif result['status'] == 'continued':
        print(f"🔄 Teste '{test_name}' continuou após debug")
    
    if result.get('video_path'):
        print(f"📹 Vídeo salvo: {result['video_path']}")


async def record_interactions(output_path: str, initial_url: str = None, headless: bool = False, debug: bool = False) -> None:
    """Record user interactions and generate YAML."""
    from playwright_simple.core.recorder.recorder import Recorder
    
    output = Path(output_path).resolve()
    
    print(f"🎬 Iniciando gravação...")
    print(f"   Arquivo de saída: {output}")
    if initial_url:
        print(f"   Iniciando em: {initial_url}")
    else:
        print(f"   Iniciando em: about:blank (use --url para iniciar em um site específico)")
    print(f"\n📝 Comandos do console:")
    print(f"   start - Iniciar gravação")
    print(f"   save - Salvar YAML sem parar (continua gravando)")
    print(f"   exit - Sair sem salvar")
    print(f"   pause - Pausar gravação")
    print(f"   resume - Retomar gravação")
    print(f'   caption "texto" - Adicionar legenda')
    print(f'   audio "texto" - Adicionar narração')
    print(f"   screenshot - Tirar screenshot")
    print(f"   help - Mostrar ajuda")
    print(f"\n💡 Dica: Digite 'exit' no console quando terminar\n")
    
    recorder = Recorder(output_path=output, initial_url=initial_url, headless=headless, debug=debug)
    await recorder.start()


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'run':
        # Create config
        config = create_config_from_args(args)
        
        # Run test
        asyncio.run(run_test(args.yaml_file, config, args))
    elif args.command == 'record':
        # Record interactions
        asyncio.run(record_interactions(
            output_path=args.output,
            initial_url=getattr(args, 'url', None),
            headless=args.headless,
            debug=args.debug
        ))
    elif args.command in ['find', 'click', 'type', 'wait', 'info', 'html']:
        # Command commands - send to active recording session
        from playwright_simple.core.recorder.command_server import send_command
        
        if args.command == 'find':
            if args.selector:
                result = send_command('find', f'selector {args.selector}')
            elif args.role:
                result = send_command('find', f'role {args.role}')
            else:
                result = send_command('find', args.text)
            
            if result.get('success'):
                element = result.get('result', {}).get('element')
                if element:
                    print(f"✅ Elemento encontrado:")
                    print(f"   Tag: {element.get('tag', 'N/A')}")
                    print(f"   Texto: {element.get('text', 'N/A')[:100]}")
                    print(f"   ID: {element.get('id', 'N/A')}")
                    print(f"   Classe: {element.get('className', 'N/A')[:50]}")
                    print(f"   Visível: {element.get('visible', False)}")
                else:
                    print("❌ Elemento não encontrado")
            else:
                print(f"❌ Erro: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        
        elif args.command == 'click':
            if args.selector:
                cmd_args = f'selector {args.selector}'
            elif args.role:
                cmd_args = f'role {args.role} [{args.index}]'
            elif args.text:
                cmd_args = args.text
            else:
                print("❌ Especifique --selector, --role ou texto")
                sys.exit(1)
            
            result = send_command('click', cmd_args)
            if result.get('success') and result.get('result', {}).get('success'):
                print("✅ Clicado com sucesso")
            else:
                print(f"❌ Erro ao clicar: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        
        elif args.command == 'type':
            if not args.into and not args.selector:
                print("❌ Especifique --into ou --selector")
                sys.exit(1)
            
            if args.selector:
                cmd_args = f'{args.text} into selector {args.selector}'
            else:
                cmd_args = f'{args.text} into {args.into}'
            
            result = send_command('type', cmd_args)
            if result.get('success') and result.get('result', {}).get('success'):
                print(f"✅ Texto '{args.text}' digitado com sucesso")
            else:
                print(f"❌ Erro ao digitar: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        
        elif args.command == 'wait':
            if args.selector:
                cmd_args = f'selector {args.selector} {args.timeout}'
            elif args.role:
                cmd_args = f'role {args.role} {args.timeout}'
            elif args.text:
                cmd_args = f'{args.text} {args.timeout}'
            else:
                print("❌ Especifique --selector, --role ou texto")
                sys.exit(1)
            
            result = send_command('wait', cmd_args)
            if result.get('success') and result.get('result', {}).get('success'):
                print("✅ Elemento apareceu")
            else:
                print(f"❌ Elemento não apareceu: {result.get('error', 'Timeout')}")
                sys.exit(1)
        
        elif args.command == 'info':
            result = send_command('info', '')
            if result.get('success'):
                info = result.get('result', {}).get('info', {})
                print(f"📄 Informações da página:")
                print(f"   URL: {info.get('url', 'N/A')}")
                print(f"   Título: {info.get('title', 'N/A')}")
                print(f"   Estado: {info.get('ready_state', 'N/A')}")
            else:
                print(f"❌ Erro: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        
        elif args.command == 'html':
            # Build command arguments
            cmd_args = []
            if args.selector:
                cmd_args.append(f'selector {args.selector}')
            if args.pretty:
                cmd_args.append('--pretty')
            if args.max_length:
                cmd_args.append(f'--max-length {args.max_length}')
            
            result = send_command('html', ' '.join(cmd_args))
            if result.get('success'):
                html_data = result.get('result', {})
                html = html_data.get('html', '')
                length = html_data.get('length', len(html))
                
                if args.max_length and length > args.max_length:
                    print(f"📄 HTML ({length} caracteres, truncado):")
                else:
                    print(f"📄 HTML ({length} caracteres):")
                print("-" * 60)
                print(html)
                print("-" * 60)
                
                # Suggest saving to file if long
                if length > 1000:
                    print(f"\n💡 Dica: HTML é grande ({length} caracteres). Considere salvar em arquivo:")
                    selector_part = f' --selector "{args.selector}"' if args.selector else ''
                    print(f"   playwright-simple html{selector_part} > page.html")
            else:
                print(f"❌ Erro: {result.get('error', 'Unknown error')}")
                sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

