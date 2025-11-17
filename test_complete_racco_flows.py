#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simples para executar comandos do arquivo MD.

Apenas lê o arquivo MD, identifica comandos (pw-click, pw-type, etc.) e executa.
"""

import asyncio
import sys
import re
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from playwright.async_api import async_playwright
from playwright_simple.core.recorder.utils.browser import BrowserManager
from playwright_simple.core.recorder.command_handlers.handlers import CommandHandlers
from playwright_simple.core.recorder.yaml_writer import YAMLWriter
from playwright_simple.core.recorder.action_converter import ActionConverter
from playwright_simple.core.recorder.event_handlers import EventHandlers
from playwright_simple.core.recorder.cursor_controller.controller import CursorController
from playwright_simple.core.recorder.config import SpeedLevel

# Configuração
BASE_URL = "http://localhost:18069"
HEADLESS = False
MD_FILE = project_root / "test_complete_racco_flows.md"


def parse_validated_flows(md_file: Path) -> set[str]:
    """Lê fluxos validados da seção YAML do arquivo MD"""
    if not md_file.exists() or not YAML_AVAILABLE:
        return set()
    
    validated_flows = set()
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procurar bloco YAML com validated_flows
    lines = content.split('\n')
    in_yaml_block = False
    yaml_lines = []
    
    for line in lines:
        if '```yaml' in line:
            in_yaml_block = True
            continue
        if in_yaml_block:
            if line.strip() == '```':
                break
            yaml_lines.append(line)
    
    if yaml_lines:
        try:
            yaml_content = '\n'.join(yaml_lines)
            data = yaml.safe_load(yaml_content)
            if data and 'validated_flows' in data:
                validated_flows = set(data['validated_flows'])
        except Exception:
            pass
    
    return validated_flows


def parse_commands_from_md(md_file: Path, validated_flows: set[str] = None) -> list[str]:
    """Lê comandos do arquivo MD - apenas linhas que começam com pw-"""
    if not md_file.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {md_file}")
    
    if validated_flows is None:
        validated_flows = set()
    
    commands = []
    in_bash_block = False
    current_flow = None
    flow_pattern = re.compile(r'#\s*FLUXO\s+(\d+):', re.IGNORECASE)
    
    with open(md_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Detectar início do bloco bash
            if line == '```bash':
                in_bash_block = True
                continue
            
            # Detectar fim do bloco bash
            if line == '```' and in_bash_block:
                in_bash_block = False
                continue
            
            if in_bash_block:
                # Verificar se é marcador de fluxo
                match = flow_pattern.search(line)
                if match:
                    flow_num = match.group(1).zfill(2)
                    current_flow = f"fluxo_{flow_num}"
                    # Se o fluxo está validado, pular
                    if current_flow in validated_flows:
                        continue
                
                # Se estamos em um fluxo validado, pular comandos
                if current_flow and current_flow in validated_flows:
                    continue
                
                # Dentro do bloco bash, pegar apenas comandos pw-*
                if line.startswith('pw-'):
                    commands.append(line)
    
    return commands


async def main():
    """Função principal - lê MD e executa comandos"""
    
    # Ler fluxos validados
    validated_flows = parse_validated_flows(MD_FILE)
    if validated_flows:
        print(f"⏭️  Fluxos validados (serão pulados): {', '.join(sorted(validated_flows))}\n")
    
    # Ler comandos do MD (pulando fluxos validados)
    print(f"📖 Lendo comandos de {MD_FILE}...")
    commands = parse_commands_from_md(MD_FILE, validated_flows)
    print(f"✅ {len(commands)} comandos encontrados\n")
    
    if not commands:
        print("❌ Nenhum comando encontrado no arquivo MD")
        return 1
    
    # Inicializar browser (sem recorder completo para evitar bloqueio)
    browser_manager = BrowserManager(headless=HEADLESS)
    page = await browser_manager.start()
    await page.goto(BASE_URL)
    
    # Inicializar componentes necessários para handlers
    yaml_writer = YAMLWriter(output_path=project_root / "temp_test.yaml")
    action_converter = ActionConverter()
    event_handlers = EventHandlers(yaml_writer, action_converter)
    
    # Inicializar cursor controller com ULTRA_FAST mode para execução rápida
    cursor_controller = CursorController(page, speed_level=SpeedLevel.ULTRA_FAST)
    await cursor_controller.start()
    
    # Criar handlers - usar getters para compatibilidade
    def get_page():
        return page
    
    def get_cursor_controller():
        return cursor_controller
    
    handlers = CommandHandlers(
        yaml_writer=yaml_writer,
        page_getter=get_page,
        cursor_controller_getter=get_cursor_controller,
        recorder=None,
        recorder_logger=None
    )
    
    # Criar diretório para HTMLs de erro
    error_html_dir = project_root / "screenshots" / "test_complete_racco_flows"
    error_html_dir.mkdir(parents=True, exist_ok=True)
    
    # Executar comandos
    print("▶️  Executando comandos...\n")
    for i, command in enumerate(commands, 1):
        print(f"[{i}/{len(commands)}] {command}")
        
        # Parsear comando
        parts = command.split(None, 1)
        cmd = parts[0]  # pw-click, pw-type, etc.
        args = parts[1] if len(parts) > 1 else ""
        
        # Parsear args - remover aspas externas mas preservar estrutura
        # Para "selector ...", remover aspas do seletor mas manter "selector"
        if args.startswith('selector '):
            # Exemplo: selector "button.o_grid_apps_menu__button"
            # Separar "selector" do resto
            selector_part = args[9:].strip()  # Remove "selector "
            # Remover aspas do seletor
            selector_part = selector_part.strip('"\'')
            args = f"selector {selector_part}"
        else:
            # Para outros casos, remover aspas
            args = args.strip('"\'')
        
        # Executar comando
        try:
            if cmd == "pw-click":
                result = await handlers.handle_pw_click(args)
            elif cmd == "pw-type":
                result = await handlers.handle_pw_type(args)
            elif cmd == "pw-submit":
                result = await handlers.handle_pw_submit(args)
            elif cmd == "pw-press":
                result = await handlers.handle_pw_press(args)
            elif cmd == "pw-wait":
                # Ignorar - biblioteca lida com waits automaticamente
                continue
            else:
                print(f"  ⚠️  Comando desconhecido: {cmd}")
                continue
            
            if not result.get('success', False):
                error = result.get('error', 'Erro desconhecido')
                print(f"  ❌ Erro: {error}")
                
                # Capturar HTML da página de erro
                try:
                    html_content = await page.content()
                    error_html_file = error_html_dir / f"error_step_{i}.html"
                    error_html_file.write_text(html_content, encoding='utf-8')
                    print(f"  📄 HTML da página de erro salvo: {error_html_file}")
                except Exception as html_error:
                    print(f"  ⚠️  Erro ao capturar HTML: {html_error}")
                
                return 1
            
            print(f"  ✅ Sucesso")
        except Exception as e:
            print(f"  ❌ Exceção: {e}")
            
            # Capturar HTML da página de erro
            try:
                html_content = await page.content()
                error_html_file = error_html_dir / f"error_step_{i}.html"
                error_html_file.write_text(html_content, encoding='utf-8')
                print(f"  📄 HTML da página de erro salvo: {error_html_file}")
            except Exception as html_error:
                print(f"  ⚠️  Erro ao capturar HTML: {html_error}")
            
            return 1
    
    print(f"\n✅ Todos os {len(commands)} comandos executados com sucesso!")
    
    # Fechar browser
    await browser_manager.stop()
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
