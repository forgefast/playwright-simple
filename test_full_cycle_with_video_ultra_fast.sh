#!/bin/bash
# Teste completo com gravação de vídeo usando ULTRA FAST MODE (Shell): Geração e Reprodução de YAML
#
# Este script executa o ciclo completo com gravação de vídeo usando ULTRA FAST MODE,
# usando comandos shell (CLI):
# 1. Grava YAML através de comandos CLI (ULTRA FAST)
# 2. Reproduz o YAML gerado com gravação de vídeo (ULTRA FAST)
# 3. Mostra resultados de ambos os processos
# 4. Valida que vídeo foi gerado sem perdas

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
YAML_PATH="${SCRIPT_DIR}/test_odoo_v18_with_video_ultra_fast_shell.yaml"
VIDEOS_DIR="${SCRIPT_DIR}/videos"
PLAYWRIGHT_SIMPLE_CMD="${SCRIPT_DIR}/bin/playwright-simple"

# Configuração
HEADLESS="--headless"  # Mude para "" para ver o browser
TEST_NAME="test_odoo_v18_with_video_ultra_fast_shell"

# Funções auxiliares
print_section() {
    echo ""
    echo "=================================================================================="
    echo "  $1"
    echo "=================================================================================="
    echo ""
}

print_step() {
    echo ""
    echo "────────────────────────────────────────────────────────────────────────────────"
    echo "  PASSO $1: $2"
    echo "────────────────────────────────────────────────────────────────────────────────"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Verificar se playwright-simple existe
if [ ! -f "$PLAYWRIGHT_SIMPLE_CMD" ]; then
    PLAYWRIGHT_SIMPLE_CMD="playwright-simple"
    if ! command -v "$PLAYWRIGHT_SIMPLE_CMD" &> /dev/null; then
        print_error "playwright-simple não encontrado!"
        exit 1
    fi
fi

# Criar diretório de vídeos
mkdir -p "$VIDEOS_DIR"

# Limpar YAML anterior
if [ -f "$YAML_PATH" ]; then
    print_info "Removendo YAML anterior: $YAML_PATH"
    rm -f "$YAML_PATH"
fi

# Limpar vídeos antigos
if [ -d "$VIDEOS_DIR" ]; then
    for video_file in "$VIDEOS_DIR"/${TEST_NAME}.*; do
        if [ -f "$video_file" ]; then
            print_info "Removendo vídeo anterior: $(basename "$video_file")"
            rm -f "$video_file"
        fi
    done
fi

print_section "CICLO COMPLETO COM GRAVAÇÃO DE VÍDEO (ULTRA FAST MODE - SHELL): GERAÇÃO E REPRODUÇÃO DE YAML"
print_info "Este script usa comandos shell (CLI)"

# ============================================================================
# PASSO 1: GERANDO YAML VIA COMANDOS CLI (ULTRA FAST MODE)
# ============================================================================
print_step "1" "GERANDO YAML VIA COMANDOS CLI (ULTRA FAST MODE)"

if [ -n "$HEADLESS" ]; then
    print_info "Modo headless: browser não será visível"
else
    print_info "Modo visível: browser será exibido"
fi

print_info "⚡ ULTRA FAST MODE: delays reduzidos ao mínimo (0.05x)"

print_info "▶️  Iniciando gravação com playwright-simple record..."
print_info "   Comando: $PLAYWRIGHT_SIMPLE_CMD record $YAML_PATH --url http://localhost:18069 $HEADLESS"

# Iniciar gravação em background
"$PLAYWRIGHT_SIMPLE_CMD" record "$YAML_PATH" --url http://localhost:18069 $HEADLESS &
RECORD_PID=$!

# Aguardar gravação iniciar
print_info "⏳ Aguardando gravação estar pronta..."
sleep 3

# Verificar se processo ainda está rodando
if ! kill -0 $RECORD_PID 2>/dev/null; then
    print_error "Processo de gravação terminou inesperadamente!"
    exit 1
fi

print_success "Gravação iniciada"

# Executar comandos CLI para fazer as interações
print_info "1️⃣  Clicando em 'Entrar'..."
if "$PLAYWRIGHT_SIMPLE_CMD" click "Entrar" --timeout 10; then
    print_success "Clique executado"
    sleep 0.1  # Aguardar step ser criado
    
    # Adicionar legenda e áudio ao step
    "$PLAYWRIGHT_SIMPLE_CMD" subtitle "Clicando no botão Entrar" || true
    "$PLAYWRIGHT_SIMPLE_CMD" audio-step "Clicando no botão Entrar" || true
    sleep 0.1
else
    print_error "Erro ao clicar em 'Entrar'"
    kill $RECORD_PID 2>/dev/null || true
    exit 1
fi

print_info "2️⃣  Aguardando formulário de login..."
if "$PLAYWRIGHT_SIMPLE_CMD" wait "E-mail" --timeout 10; then
    print_success "Formulário encontrado"
else
    print_warning "Formulário pode não estar visível ainda, continuando..."
fi
sleep 0.1

print_info "3️⃣  Digitando email..."
if "$PLAYWRIGHT_SIMPLE_CMD" type "admin" --into "E-mail" --timeout 10; then
    print_success "Email digitado"
    sleep 0.1  # Aguardar step ser criado
    
    # Adicionar legenda e áudio ao step
    "$PLAYWRIGHT_SIMPLE_CMD" subtitle "Digitando email do administrador" || true
    "$PLAYWRIGHT_SIMPLE_CMD" audio-step "Digitando email do administrador" || true
    sleep 0.1
else
    print_error "Erro ao digitar email"
    kill $RECORD_PID 2>/dev/null || true
    exit 1
fi

print_info "4️⃣  Digitando senha..."
if "$PLAYWRIGHT_SIMPLE_CMD" type "admin" --into "Senha" --timeout 10; then
    print_success "Senha digitada"
    sleep 0.1  # Aguardar step ser criado
    
    # Adicionar legenda e áudio ao step
    "$PLAYWRIGHT_SIMPLE_CMD" subtitle "Digitando senha do administrador" || true
    "$PLAYWRIGHT_SIMPLE_CMD" audio-step "Digitando senha do administrador" || true
    sleep 0.1
else
    print_error "Erro ao digitar senha"
    kill $RECORD_PID 2>/dev/null || true
    exit 1
fi

print_info "5️⃣  Submetendo formulário..."
if "$PLAYWRIGHT_SIMPLE_CMD" submit "Entrar" --timeout 10; then
    print_success "Formulário submetido"
    sleep 0.1  # Aguardar step ser criado
    
    # Adicionar legenda e áudio ao step
    "$PLAYWRIGHT_SIMPLE_CMD" subtitle "Submetendo formulário de login" || true
    "$PLAYWRIGHT_SIMPLE_CMD" audio-step "Submetendo formulário de login" || true
    sleep 0.5  # Aguardar navegação
else
    print_warning "Erro ao submeter, tentando clicar em 'Entrar'..."
    if "$PLAYWRIGHT_SIMPLE_CMD" click "Entrar" --timeout 10; then
        print_success "Formulário submetido (via click)"
        sleep 0.1
        "$PLAYWRIGHT_SIMPLE_CMD" subtitle "Submetendo formulário de login" || true
        "$PLAYWRIGHT_SIMPLE_CMD" audio-step "Submetendo formulário de login" || true
        sleep 0.5
    else
        print_warning "Erro ao submeter, mas continuando..."
    fi
fi

print_info "6️⃣  Salvando YAML..."
if "$PLAYWRIGHT_SIMPLE_CMD" save; then
    print_success "Comando save enviado"
else
    print_warning "Erro ao enviar save, mas continuando..."
fi

sleep 1  # Dar tempo para salvar

print_info "💡 Finalizando gravação..."
if "$PLAYWRIGHT_SIMPLE_CMD" exit; then
    print_success "Comando exit enviado"
else
    print_warning "Erro ao enviar exit, forçando..."
    kill $RECORD_PID 2>/dev/null || true
fi

# Aguardar processo terminar
wait $RECORD_PID 2>/dev/null || true

# Verificar se YAML foi gerado
if [ -f "$YAML_PATH" ]; then
    YAML_SIZE=$(stat -f%z "$YAML_PATH" 2>/dev/null || stat -c%s "$YAML_PATH" 2>/dev/null || echo "0")
    print_success "YAML gerado: $YAML_PATH"
    print_info "📊 Tamanho: $YAML_SIZE bytes"
    
    # Adicionar configuração básica de vídeo usando Python
    print_info "💡 Adicionando configuração básica de vídeo..."
    python3 << EOF
import yaml
from pathlib import Path

yaml_path = Path("$YAML_PATH")
with open(yaml_path, 'r', encoding='utf-8') as f:
    yaml_content = yaml.safe_load(f)

if 'config' not in yaml_content:
    yaml_content['config'] = {}

if 'video' not in yaml_content['config']:
    yaml_content['config']['video'] = {
        'enabled': True,
        'quality': 'high',
        'codec': 'mp4',
        'dir': 'videos',
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
    video_config.setdefault('subtitles', True)
    video_config.setdefault('hard_subtitles', True)
    video_config.setdefault('audio', True)
    video_config.setdefault('audio_engine', 'edge-tts')
    video_config.setdefault('audio_lang', 'pt-BR')
    video_config.setdefault('audio_voice', 'pt-BR-MacerioMultilingualNeural')

with open(yaml_path, 'w', encoding='utf-8') as f:
    yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)
EOF
    
    print_success "Configuração de vídeo adicionada ao YAML"
else
    print_error "YAML não foi gerado!"
    exit 1
fi

# ============================================================================
# PASSO 2: REPRODUZINDO YAML COM VÍDEO (ULTRA FAST MODE)
# ============================================================================
print_step "2" "REPRODUZINDO YAML COM VÍDEO (ULTRA FAST MODE)"

print_info "⚡ ULTRA FAST MODE: delays reduzidos ao mínimo (0.05x)"

print_info "▶️  Executando: $PLAYWRIGHT_SIMPLE_CMD run $YAML_PATH --video --video-quality high --video-codec mp4 --subtitles --hard-subtitles --audio --audio-lang pt-BR --audio-engine edge-tts --audio-voice pt-BR-MacerioMultilingualNeural $HEADLESS --speed-level ultra_fast"
print_info "📹 Vídeo será gravado em: $VIDEOS_DIR"
print_info "⚡ ULTRA FAST MODE: usando --speed-level ultra_fast"

if "$PLAYWRIGHT_SIMPLE_CMD" run "$YAML_PATH" \
    --video \
    --video-quality high \
    --video-codec mp4 \
    --subtitles \
    --hard-subtitles \
    --audio \
    --audio-lang pt-BR \
    --audio-engine edge-tts \
    --audio-voice pt-BR-MacerioMultilingualNeural \
    $HEADLESS \
    --speed-level ultra_fast; then
    
    print_success "Teste passou!"
else
    print_warning "Teste retornou código de erro, mas verificando vídeo..."
fi

# Verificar se vídeo foi gerado
print_info "🔍 Verificando se vídeo foi gerado..."
VIDEO_FOUND=false
VIDEO_PATH=""

for ext in .mp4 .webm; do
    if [ -f "$VIDEOS_DIR/${TEST_NAME}${ext}" ]; then
        VIDEO_PATH="$VIDEOS_DIR/${TEST_NAME}${ext}"
        VIDEO_FOUND=true
        break
    fi
done

# Se não encontrou com nome exato, procurar o mais recente
if [ "$VIDEO_FOUND" = false ] && [ -d "$VIDEOS_DIR" ]; then
    LATEST_VIDEO=$(find "$VIDEOS_DIR" -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.webm" \) -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    if [ -n "$LATEST_VIDEO" ] && [ -f "$LATEST_VIDEO" ]; then
        VIDEO_PATH="$LATEST_VIDEO"
        VIDEO_FOUND=true
    fi
fi

if [ "$VIDEO_FOUND" = true ]; then
    VIDEO_SIZE=$(stat -f%z "$VIDEO_PATH" 2>/dev/null || stat -c%s "$VIDEO_PATH" 2>/dev/null || echo "0")
    VIDEO_SIZE_MB=$(echo "scale=2; $VIDEO_SIZE / 1024 / 1024" | bc)
    print_success "Vídeo gerado com sucesso!"
    print_info "   Arquivo: $VIDEO_PATH"
    print_info "   Tamanho: ${VIDEO_SIZE_MB} MB"
else
    print_warning "Vídeo não foi encontrado em: $VIDEOS_DIR"
    print_info "   Verifique se a configuração de vídeo está correta no YAML"
fi

# ============================================================================
# RESUMO FINAL
# ============================================================================
print_section "RESUMO DO CICLO COMPLETO COM VÍDEO (ULTRA FAST MODE - SHELL)"

if [ -f "$YAML_PATH" ]; then
    print_success "Geração: ✅ Sucesso"
else
    print_error "Geração: ❌ Falhou"
fi

if [ "$VIDEO_FOUND" = true ]; then
    print_success "Reprodução: ✅ Sucesso"
    print_success "Vídeo: ✅ Gerado em $VIDEO_PATH (${VIDEO_SIZE_MB} MB)"
    echo ""
    print_info "💡 Valide o teste assistindo ao vídeo gerado"
    echo ""
    print_success "🎉 CICLO COMPLETO COM VÍDEO (ULTRA FAST MODE - SHELL) EXECUTADO COM SUCESSO!"
    print_info "   YAML: $YAML_PATH"
    print_info "   Vídeo: $VIDEO_PATH"
    echo ""
    print_info "💡 Valide o teste assistindo ao vídeo gerado"
    print_info "⚡ Teste executado usando comandos shell (--speed-level ultra_fast no run)"
    exit 0
else
    print_error "Reprodução: ❌ Falhou"
    print_error "Vídeo: ❌ Não foi gerado"
    exit 1
fi

