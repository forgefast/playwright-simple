#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Handlers for CLI Commands.

Handles execution of command commands (find, click, type, submit, etc.)
that interact with an active recording session.
"""

import sys
from playwright_simple.core.recorder.command_server import send_command


def handle_command_commands(args) -> None:
    """Handle command commands (find, click, type, submit, wait, info, html)."""
    if args.command == 'find':
        _handle_find(args)
    elif args.command == 'click':
        _handle_click(args)
    elif args.command == 'type':
        _handle_type(args)
    elif args.command == 'submit':
        _handle_submit(args)
    elif args.command == 'wait':
        _handle_wait(args)
    elif args.command == 'info':
        _handle_info(args)
    elif args.command == 'html':
        _handle_html(args)


def _handle_find(args):
    """Handle find command."""
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


def _handle_click(args):
    """Handle click command."""
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


def _handle_type(args):
    """Handle type command."""
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


def _handle_submit(args):
    """Handle submit command."""
    button_text = args.button_text if args.button_text else ''
    result = send_command('submit', button_text)
    if result.get('success') and result.get('result', {}).get('success'):
        if button_text:
            print(f"✅ Formulário submetido (botão: '{button_text}')")
        else:
            print("✅ Formulário submetido")
    else:
        if button_text:
            print(f"❌ Erro ao submeter formulário (botão '{button_text}' não encontrado)")
        else:
            print("❌ Erro ao submeter formulário (nenhum botão submit encontrado)")
        sys.exit(1)


def _handle_wait(args):
    """Handle wait command."""
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


def _handle_info(args):
    """Handle info command."""
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


def _handle_html(args):
    """Handle html command."""
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

