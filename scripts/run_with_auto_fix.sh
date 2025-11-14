#!/bin/bash
# Script wrapper para executar teste com auto-fix em background

YAML_FILE="$1"
BASE_URL="${2:-http://localhost:18069}"
MAX_FIXES="${3:-10}"

if [ -z "$YAML_FILE" ]; then
    echo "Uso: $0 <arquivo.yaml> [base_url] [max_fixes]"
    echo "Exemplo: $0 examples/racco/test_simple_login.yaml http://localhost:18069 10"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Executar com auto-fix
python3 "$SCRIPT_DIR/auto_fix_runner.py" \
    "$YAML_FILE" \
    --base-url "$BASE_URL" \
    --max-fixes "$MAX_FIXES"

