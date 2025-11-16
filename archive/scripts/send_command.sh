#!/bin/bash
# Script para enviar comandos ao servidor em background

COMMAND_PIPE="/tmp/playwright_commands"
RESPONSE_PIPE="/tmp/playwright_responses"

if [ ! -p "$COMMAND_PIPE" ]; then
    echo "❌ Pipe de comandos não existe: $COMMAND_PIPE"
    echo "💡 Inicie o servidor primeiro: python3 scripts/command_server.py &"
    exit 1
fi

# Get command from arguments or stdin
if [ $# -eq 0 ]; then
    echo "Uso: $0 <comando>"
    echo "Exemplos:"
    echo "  $0 reload"
    echo "  $0 pause"
    echo "  $0 continue"
    echo "  $0 status"
    exit 1
fi

COMMAND="$1"

# Send command
echo "$COMMAND" > "$COMMAND_PIPE"

# Wait a bit for response
sleep 0.1

# Read response if available
if [ -p "$RESPONSE_PIPE" ]; then
    timeout 1 cat "$RESPONSE_PIPE" 2>/dev/null || true
fi

