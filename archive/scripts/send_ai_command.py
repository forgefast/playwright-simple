#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script para enviar comandos para a AI Control Interface.
"""

import json
import sys
from pathlib import Path

COMMAND_FILE = Path("/tmp/ai_commands.json")
RESPONSE_FILE = Path("/tmp/ai_response.json")


def send_command(command: dict):
    """Envia comando para a interface."""
    COMMAND_FILE.write_text(json.dumps(command, indent=2), encoding='utf-8')
    print(f"✅ Comando enviado: {command.get('command')}")


def wait_for_response(timeout: float = 10.0):
    """Aguarda resposta da interface."""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if RESPONSE_FILE.exists():
            try:
                response = json.loads(RESPONSE_FILE.read_text(encoding='utf-8'))
                RESPONSE_FILE.unlink()  # Limpar após ler
                return response
            except Exception as e:
                print(f"Erro ao ler resposta: {e}")
        
        time.sleep(0.2)
    
    return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 send_ai_command.py <comando_json>")
        print("\nExemplos:")
        print('  python3 send_ai_command.py \'{"command": "get_elements"}\'')
        print('  python3 send_ai_command.py \'{"command": "move_cursor", "text": "Entrar"}\'')
        print('  python3 send_ai_command.py \'{"command": "click", "text": "Entrar"}\'')
        sys.exit(1)
    
    command_json = sys.argv[1]
    command = json.loads(command_json)
    
    send_command(command)
    response = wait_for_response()
    
    if response:
        print(f"\n📥 Resposta:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        print("\n⏳ Timeout aguardando resposta")

