# CLI Avançado

O playwright-simple fornece um CLI completo com todas as opções de configuração.

## Instalação

Após instalar o playwright-simple, o CLI estará disponível:

```bash
playwright-simple --help
```

## Comandos

### Executar Teste

```bash
playwright-simple run test.yaml
```

## Opções de Logging

### Nível de Log

```bash
# DEBUG - Todas as informações
playwright-simple run test.yaml --log-level DEBUG

# INFO - Informações gerais (padrão)
playwright-simple run test.yaml --log-level INFO

# WARNING - Apenas avisos e erros
playwright-simple run test.yaml --log-level WARNING

# ERROR - Apenas erros
playwright-simple run test.yaml --log-level ERROR
```

### Arquivo de Log

```bash
# Salvar logs em arquivo
playwright-simple run test.yaml --log-file logs/test.log

# Formato JSON
playwright-simple run test.yaml --log-file logs/test.log --json-log

# Sem logs no console
playwright-simple run test.yaml --log-file logs/test.log --no-console-log
```

## Opções de Browser

### Modo Headless

```bash
# Headless (sem interface)
playwright-simple run test.yaml --headless

# Com interface (padrão)
playwright-simple run test.yaml --no-headless
```

### Viewport

```bash
# Tamanho customizado
playwright-simple run test.yaml --viewport 1920x1080
playwright-simple run test.yaml --viewport 1366x768
```

### Performance

```bash
# Delay entre ações (em ms)
playwright-simple run test.yaml --slow-mo 100

# Timeout padrão (em ms)
playwright-simple run test.yaml --timeout 30000
```

## Opções de Vídeo

### Básico

```bash
# Habilitar vídeo
playwright-simple run test.yaml --video

# Desabilitar vídeo
playwright-simple run test.yaml --no-video
```

### Qualidade e Codec

```bash
# Qualidade
playwright-simple run test.yaml --video --video-quality high
playwright-simple run test.yaml --video --video-quality medium
playwright-simple run test.yaml --video --video-quality low

# Codec
playwright-simple run test.yaml --video --video-codec mp4
playwright-simple run test.yaml --video --video-codec webm
```

### Velocidade e Diretório

```bash
# Velocidade (1.0 = normal, 2.0 = 2x mais rápido)
playwright-simple run test.yaml --video --video-speed 1.5

# Diretório
playwright-simple run test.yaml --video --video-dir videos/custom
```

## Opções de Áudio

### Básico

```bash
# Habilitar áudio/narração
playwright-simple run test.yaml --audio

# Desabilitar áudio
playwright-simple run test.yaml --no-audio
```

### Idioma e Engine

```bash
# Idioma
playwright-simple run test.yaml --audio --audio-lang pt-BR
playwright-simple run test.yaml --audio --audio-lang en-US

# Engine TTS
playwright-simple run test.yaml --audio --audio-engine gtts
playwright-simple run test.yaml --audio --audio-engine pyttsx3

# Falar devagar
playwright-simple run test.yaml --audio --audio-slow
```

## Opções de Legendas

```bash
# Habilitar legendas
playwright-simple run test.yaml --subtitles

# Desabilitar legendas
playwright-simple run test.yaml --no-subtitles

# Queimar legendas no vídeo (hard subtitles)
playwright-simple run test.yaml --subtitles --hard-subtitles
```

## Opções de Debug

### Modo Debug

```bash
# Habilitar debug (pausa em erros)
playwright-simple run test.yaml --debug

# Desabilitar debug
playwright-simple run test.yaml --no-debug
```

### Pausa em Erros

```bash
# Pausar em erros
playwright-simple run test.yaml --debug --pause-on-error

# Não pausar em erros
playwright-simple run test.yaml --debug --no-pause-on-error
```

### Modo Interativo

```bash
# Modo interativo (permite inspecionar HTML, elementos, etc)
playwright-simple run test.yaml --debug --interactive
```

### Hot Reload

```bash
# Habilitar hot reload de YAML
playwright-simple run test.yaml --debug --hot-reload
```

### Diretório de Debug

```bash
# Diretório para arquivos de debug
playwright-simple run test.yaml --debug --debug-dir debug_files
```

## Opções de Cursor

```bash
# Estilo
playwright-simple run test.yaml --cursor-style arrow
playwright-simple run test.yaml --cursor-style dot
playwright-simple run test.yaml --cursor-style circle

# Cor
playwright-simple run test.yaml --cursor-color "#007bff"
playwright-simple run test.yaml --cursor-color "#ff0000"

# Tamanho
playwright-simple run test.yaml --cursor-size small
playwright-simple run test.yaml --cursor-size medium
playwright-simple run test.yaml --cursor-size large
```

## Opções de Screenshots

```bash
# Habilitar screenshots automáticos
playwright-simple run test.yaml --screenshots

# Desabilitar screenshots
playwright-simple run test.yaml --no-screenshots

# Diretório
playwright-simple run test.yaml --screenshots --screenshot-dir screenshots/custom
```

## Opções Gerais

### URL Base

```bash
playwright-simple run test.yaml --base-url https://example.com
```

### Arquivo de Configuração

```bash
# Carregar configuração de arquivo
playwright-simple run test.yaml --config config.yaml
```

### Diretório de Saída

```bash
# Diretório único para todos os outputs
playwright-simple run test.yaml --output-dir output/
# Cria: output/videos/, output/screenshots/, output/logs/
```

### Execução Paralela

```bash
# Executar múltiplos testes em paralelo
playwright-simple run test.yaml --parallel --workers 4
```

### Listar Testes

```bash
# Listar testes disponíveis no YAML
playwright-simple run test.yaml --list-tests
```

### Dry Run

```bash
# Simular execução sem executar
playwright-simple run test.yaml --dry-run
```

## Exemplos Completos

### Teste Completo com Tudo

```bash
playwright-simple run test.yaml \
  --log-level DEBUG \
  --log-file logs/test.log \
  --video \
  --video-quality high \
  --video-codec mp4 \
  --audio \
  --audio-lang pt-BR \
  --subtitles \
  --hard-subtitles \
  --debug \
  --interactive \
  --no-headless \
  --viewport 1920x1080
```

### Teste Rápido para Desenvolvimento

```bash
playwright-simple run test.yaml \
  --log-level DEBUG \
  --debug \
  --interactive \
  --hot-reload \
  --no-headless \
  --no-video
```

### Teste para Produção

```bash
playwright-simple run test.yaml \
  --log-level INFO \
  --log-file logs/production.log \
  --headless \
  --video \
  --video-quality high \
  --video-codec mp4 \
  --audio \
  --subtitles \
  --output-dir production_output/
```

### Teste com Configuração de Arquivo

```bash
# config.yaml contém todas as configurações
playwright-simple run test.yaml --config config.yaml

# Sobrescrever algumas opções
playwright-simple run test.yaml \
  --config config.yaml \
  --log-level DEBUG \
  --debug
```

## Prioridade de Configuração

As configurações são aplicadas na seguinte ordem (maior prioridade primeiro):

1. **Argumentos CLI** - Sempre sobrescrevem tudo
2. **Arquivo de configuração** (`--config`)
3. **Variáveis de ambiente**
4. **Valores padrão**

## Ajuda

```bash
# Ajuda geral
playwright-simple --help

# Ajuda do comando run
playwright-simple run --help

# Ajuda de grupos específicos
playwright-simple run --help | grep -A 10 "Video options"
```

## Integração com Scripts

```bash
#!/bin/bash
# Exemplo de script usando CLI

# Executar teste com todas as opções
playwright-simple run test.yaml \
  --log-level DEBUG \
  --video \
  --audio \
  --subtitles \
  --debug \
  --output-dir "output/$(date +%Y%m%d_%H%M%S)"

# Verificar resultado
if [ $? -eq 0 ]; then
  echo "✅ Teste passou"
else
  echo "❌ Teste falhou"
  exit 1
fi
```

## Variáveis de Ambiente

O CLI também respeita variáveis de ambiente:

```bash
export PLAYWRIGHT_SIMPLE_LOG_LEVEL=DEBUG
export PLAYWRIGHT_SIMPLE_HEADLESS=true
export PLAYWRIGHT_SIMPLE_VIDEO_ENABLED=true

playwright-simple run test.yaml
```

