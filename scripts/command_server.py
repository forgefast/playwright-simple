#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Server - Permite enviar comandos para um processo em background via named pipe.

Uso:
1. Inicie o servidor em background:
   python3 scripts/command_server.py &
   
2. Envie comandos:
   echo "reload" > /tmp/playwright_commands
   echo "pause" > /tmp/playwright_commands
   echo "continue" > /tmp/playwright_commands
   echo "status" > /tmp/playwright_commands
"""

import os
import sys
import signal
import asyncio
from pathlib import Path
from typing import Optional, Callable, Dict

# Named pipe path
COMMAND_PIPE = "/tmp/playwright_commands"
RESPONSE_PIPE = "/tmp/playwright_responses"

# Global state
running = True
command_handlers: Dict[str, Callable] = {}


def signal_handler(sig, frame):
    """Handle SIGINT/SIGTERM gracefully."""
    global running
    print("\n🛑 Encerrando servidor de comandos...")
    running = False
    # Cleanup pipes
    for pipe in [COMMAND_PIPE, RESPONSE_PIPE]:
        if os.path.exists(pipe):
            try:
                os.unlink(pipe)
            except:
                pass
    sys.exit(0)


def setup_pipes():
    """Create named pipes if they don't exist."""
    for pipe_path in [COMMAND_PIPE, RESPONSE_PIPE]:
        pipe = Path(pipe_path)
        if pipe.exists():
            if pipe.is_fifo():
                print(f"✅ Pipe já existe: {pipe_path}")
            else:
                print(f"⚠️  Removendo arquivo existente: {pipe_path}")
                pipe.unlink()
                os.mkfifo(pipe_path)
                print(f"✅ Pipe criado: {pipe_path}")
        else:
            os.mkfifo(pipe_path)
            print(f"✅ Pipe criado: {pipe_path}")


def register_command(command: str, handler: Callable):
    """Register a command handler."""
    command_handlers[command.lower()] = handler


def default_handler(command: str) -> str:
    """Default command handler."""
    return f"Comando recebido: {command}"


async def process_command(command: str) -> str:
    """Process a command and return response."""
    command = command.strip().lower()
    
    if not command:
        return "Comando vazio"
    
    # Check if command has a handler
    if command in command_handlers:
        try:
            result = command_handlers[command]()
            return result if isinstance(result, str) else str(result)
        except Exception as e:
            return f"Erro ao executar comando '{command}': {e}"
    
    # Default handler
    return default_handler(command)


async def command_server():
    """Main command server loop."""
    global running
    
    setup_pipes()
    
    print(f"🚀 Servidor de comandos iniciado!")
    print(f"📝 Pipe de comandos: {COMMAND_PIPE}")
    print(f"📤 Pipe de respostas: {RESPONSE_PIPE}")
    print(f"💡 Envie comandos com: echo 'comando' > {COMMAND_PIPE}")
    print(f"💡 Leia respostas com: cat {RESPONSE_PIPE}")
    print(f"🛑 Para parar: kill {os.getpid()}")
    print()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while running:
        try:
            # Open command pipe for reading (blocks until writer opens)
            with open(COMMAND_PIPE, 'r') as cmd_pipe:
                print("⏳ Aguardando comandos...")
                command = cmd_pipe.read().strip()
                
                if command:
                    print(f"📨 Comando recebido: {command}")
                    response = await process_command(command)
                    print(f"📤 Resposta: {response}")
                    
                    # Write response to response pipe
                    with open(RESPONSE_PIPE, 'w') as resp_pipe:
                        resp_pipe.write(response + "\n")
                        resp_pipe.flush()
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            await asyncio.sleep(1)
    
    print("👋 Servidor encerrado")


# Example command handlers
def handle_reload():
    """Handle reload command."""
    print("🔄 Executando reload...")
    # Aqui você pode adicionar lógica de reload
    return "Reload executado com sucesso"


def handle_pause():
    """Handle pause command."""
    print("⏸️  Pausando...")
    return "Pausado"


def handle_continue():
    """Handle continue command."""
    print("▶️  Continuando...")
    return "Continuando"


def handle_status():
    """Handle status command."""
    return f"Status: Rodando (PID: {os.getpid()})"


def handle_quit():
    """Handle quit command."""
    global running
    running = False
    return "Encerrando..."


if __name__ == "__main__":
    # Register default commands
    register_command("reload", handle_reload)
    register_command("pause", handle_pause)
    register_command("continue", handle_continue)
    register_command("status", handle_status)
    register_command("quit", handle_quit)
    register_command("exit", handle_quit)
    
    # Run server
    try:
        asyncio.run(command_server())
    except KeyboardInterrupt:
        signal_handler(None, None)

