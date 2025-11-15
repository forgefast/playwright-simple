# Análise da Stack Funcional

## Stack Funcional - Árvore de Chamadas

### Nível 0: Scripts de Teste (Funcionando ✅)

#### test_full_cycle.py
- **Função**: Orquestrador principal do ciclo completo
- **Chama**:
  - `test_odoo_interactive.py` (geração de YAML)
  - `test_replay_yaml.py` (reprodução de YAML)
- **Validações**:
  - Valida YAML gerado para cliques duplicados
  - Valida saída da reprodução para problemas conhecidos

#### test_full_cycle_with_video.py
- **Função**: Orquestrador completo com gravação de vídeo
- **Chama**:
  - `Recorder` em modo 'write' (geração de YAML)
  - `test_replay_yaml_with_video.py` (reprodução de YAML com vídeo)
- **Funcionalidades**:
  - Gera YAML via Recorder diretamente
  - Adiciona configuração de vídeo ao YAML gerado
  - Executa reprodução com gravação de vídeo
  - Valida que vídeo foi gerado corretamente
- **Configurações**:
  - Suporta modo headless configurável
  - Configura vídeo via YAML (enabled, quality, codec, dir)

#### test_odoo_interactive.py
- **Função**: Geração de YAML através de interação automatizada
- **Usa**:
  - `Recorder` em modo 'write'
  - `CommandHandlers` para interações programáticas
- **Fluxo**:
  1. Cria Recorder com `initial_url='http://localhost:18069'`
  2. Aguarda recorder estar pronto
  3. Usa `command_handlers` para:
     - `handle_find()`: Encontrar elementos
     - `handle_pw_click()`: Clicar em elementos
     - `handle_pw_type()`: Digitar em campos
     - `handle_pw_submit()`: Submeter formulários
     - `handle_save()`: Salvar YAML
  4. Gera `test_odoo_login_real.yaml`

#### test_replay_yaml.py
- **Função**: Reprodução de YAML gerado
- **Usa**:
  - `Recorder` em modo 'read'
- **Fluxo**:
  1. Carrega YAML do arquivo
  2. Cria Recorder em modo 'read'
  3. Executa steps do YAML automaticamente

#### test_replay_yaml_with_video.py
- **Função**: Reprodução de YAML com gravação de vídeo
- **Usa**:
  - `Recorder` em modo 'read' com configuração de vídeo do YAML
- **Funcionalidades**:
  - Carrega configuração de vídeo do YAML (config.video)
  - Cria Recorder que detecta e habilita vídeo automaticamente
  - Grava vídeo no mesmo browser instance que executa os steps
  - Suporta modo headless configurável via CLI
- **Fluxo**:
  1. Carrega YAML do arquivo
  2. Cria Recorder em modo 'read' (detecta vídeo do YAML)
  3. Recorder configura browser_manager com vídeo
  4. Executa steps do YAML (vídeo gravado simultaneamente)
  5. Finaliza e renomeia vídeo após execução

#### playwright_simple/cli/run_handlers.py
- **Função**: Handler CLI para comando `run`
- **Usa**:
  - `Recorder` em modo 'read'
- **Mesmo padrão** que `test_replay_yaml.py`

### Nível 1: Recorder (Funcionando ✅)

#### playwright_simple/core/recorder/recorder.py
- **Classe**: `Recorder`
- **Modos**:
  - `'write'`: Grava interações do usuário
  - `'read'`: Executa YAML steps (com suporte a vídeo)
- **Componentes principais**:
  - `BrowserManager`: Gerencia browser (com suporte a vídeo)
  - `EventCapture`: Captura eventos (modo write)
  - `ActionConverter`: Converte eventos em ações
  - `YAMLWriter`: Escreve YAML (modo write)
  - `ConsoleInterface`: Interface de console
  - `EventHandlers`: Handlers de eventos
  - `CommandHandlers`: Handlers de comandos
  - `CommandServer`: Servidor de comandos externos
  - `VideoManager`: Gerencia gravação de vídeo (modo read, opcional)
  - `VideoConfig`: Configuração de vídeo (modo read, opcional)
- **Funcionalidades de Vídeo (modo read)**:
  - Carrega configuração de vídeo do YAML (`config.video`)
  - Configura `BrowserManager` com `record_video=True`
  - Usa mesmo browser instance para vídeo e execução de steps
  - Finaliza vídeo corretamente após execução
  - Renomeia vídeo para nome do teste
  - Logs de debug detalhados para rastreamento

### Nível 2: Componentes do Recorder (Funcionando ✅)

#### Core Components

**event_capture.py**
- Captura eventos do browser (click, input, blur, navigation, scroll, keydown)
- Injeta script de captura na página
- Faz polling de eventos
- Reinjeta script em navegações

**action_converter.py**
- Converte eventos do browser em ações YAML
- Acumula inputs até blur/Enter
- Detecta botões de submit
- Usa `ElementIdentifier` para identificar elementos

**yaml_writer.py**
- Escreve YAML incrementalmente
- Adiciona steps ao YAML
- Salva arquivo YAML final
- Suporta metadata

**console_interface.py**
- Interface de console assíncrona
- Registra comandos
- Processa comandos em background

**event_handlers.py**
- Handlers de eventos:
  - `handle_click()`: Processa cliques
  - `handle_input()`: Acumula inputs
  - `handle_blur()`: Finaliza inputs
  - `handle_navigation()`: Processa navegações
  - `handle_scroll()`: Processa scrolls
  - `handle_keydown()`: Processa teclas (Enter, Tab, etc.)

**element_identifier.py**
- Identifica elementos usando múltiplas estratégias:
  1. Texto visível
  2. Label (para inputs)
  3. Placeholder (para inputs)
  4. ARIA label
  5. Type + contexto
  6. Posição (fallback)

#### Command Handlers (Modular)

**command_handlers/handlers.py**
- Coordenador principal de todos os handlers
- Delega para módulos especializados:
  - `RecordingHandlers`: Controle de gravação
  - `MetadataHandlers`: Metadata (caption, audio, screenshot)
  - `CursorHandlers`: Controle de cursor (se disponível)
  - `PlaywrightHandlers`: Comandos Playwright diretos

**command_handlers/recording_handlers.py**
- `handle_start()`: Inicia gravação
- `handle_save()`: Salva YAML
- `handle_exit()`: Sai da gravação
- `handle_pause()`: Pausa gravação
- `handle_resume()`: Retoma gravação

**command_handlers/metadata_handlers.py**
- `handle_caption()`: Adiciona legenda
- `handle_audio()`: Adiciona narração
- `handle_screenshot()`: Tira screenshot

**command_handlers/cursor_handlers.py**
- `handle_cursor()`: Controla cursor visual
- `handle_cursor_click()`: Clique via cursor
- `handle_type()`: Digitação via cursor
- `handle_press()`: Pressiona tecla

**command_handlers/playwright_handlers.py**
- `handle_find()`: Encontra elemento
- `handle_find_all()`: Encontra todos os elementos
- `handle_pw_click()`: Clique Playwright direto
- `handle_pw_type()`: Digitação Playwright direta
- `handle_pw_submit()`: Submit Playwright direto
- `handle_pw_wait()`: Wait Playwright direto
- `handle_pw_info()`: Info do elemento
- `handle_pw_html()`: HTML do elemento

#### Utilities

**utils/browser.py**
- `BrowserManager`: Gerencia ciclo de vida do browser
  - `start()`: Inicia browser (com suporte a vídeo se configurado)
  - `stop()`: Para browser
  - **Suporte a vídeo**:
    - `record_video`: Flag para habilitar gravação
    - `video_dir`: Diretório para salvar vídeos
    - `viewport`: Tamanho do viewport (usado para vídeo)
    - Cria context com `record_video_dir` e `record_video_size`
    - Logs de debug para verificar configuração de vídeo

**command_server.py**
- Servidor de comandos externos
- Permite comandos via IPC
- Limpa processos órfãos

#### Opcionais (se disponíveis)

**cursor_controller.py**
- Controle visual do cursor
- Movimento animado
- Feedback visual

**../video.py**
- `VideoManager`: Gerencia gravação de vídeo
  - `get_context_options()`: Retorna opções de context para Playwright
  - `register_context()`: Registra context para gerenciamento
  - `get_video_path()`: Encontra vídeo gerado por nome do teste
  - `validate_video()`: Valida integridade do vídeo
- Suporta diferentes codecs (webm, mp4)
- Gera vídeos com subtítulos (opcional)
- **Integração com Recorder**:
  - Carregado automaticamente em modo 'read' se YAML tiver `config.video`
  - Configura `BrowserManager` para gravar vídeo
  - Gerencia ciclo de vida do vídeo (início, finalização, renomeação)

**../extensions/video/config.py**
- `VideoConfig`: Configuração de vídeo
  - `enabled`: Habilita/desabilita vídeo
  - `quality`: Qualidade (low, medium, high)
  - `codec`: Codec (webm, mp4)
  - `dir`: Diretório para salvar vídeos
  - `speed`: Velocidade de reprodução
  - `subtitles`: Habilita legendas
  - `audio`: Habilita áudio
- **Carregamento**:
  - Lido do YAML em `config.video`
  - Criado automaticamente pelo Recorder em modo 'read'

### Nível 3: Dependências Externas (Funcionando ✅)

**playwright_simple/core/logger.py**
- Sistema de logging estruturado
- Suporta múltiplos formatos (console, JSON, file)
- Contexto de logging
- Níveis customizados (ACTION, STATE, ELEMENT)

**playwright** (biblioteca externa)
- API do Playwright
- Browser automation
- Page, Element, etc.

## Funcionalidades Implementadas

### Gravação (Write Mode)
1. ✅ Captura de eventos do browser
2. ✅ Conversão de eventos em ações YAML
3. ✅ Escrita incremental de YAML
4. ✅ Comandos interativos (start, save, exit, pause, resume)
5. ✅ Comandos de metadata (caption, audio, screenshot)
6. ✅ Comandos Playwright diretos (find, pw-click, pw-type, pw-submit, etc.)
7. ✅ Identificação inteligente de elementos

### Reprodução (Read Mode)
1. ✅ Leitura de YAML
2. ✅ Execução de steps (go_to, click, type, submit)
3. ✅ Navegação automática
4. ✅ Suporte a fast_mode
5. ✅ Limpeza de processos órfãos
6. ✅ **Gravação de vídeo** (se configurado no YAML)
   - Carrega configuração de vídeo do YAML (`config.video`)
   - Configura browser com vídeo no mesmo context dos steps
   - Grava vídeo durante execução completa dos steps
   - Finaliza e renomeia vídeo corretamente
   - Valida geração do vídeo

### Infraestrutura
1. ✅ Gerenciamento de browser
2. ✅ Sistema de logging estruturado
3. ✅ Limpeza de processos órfãos
4. ✅ **Suporte a video (testado e funcional)**
   - Gravação de vídeo no modo read
   - Configuração via YAML
   - Mesmo browser instance para vídeo e steps
   - Finalização e renomeação automática
   - Logs de debug detalhados
5. ✅ Suporte a cursor visual (opcional)

## Padrões de Uso

### Gravação
```python
recorder = Recorder(
    output_path=Path('test.yaml'),
    initial_url='http://localhost:18069',
    headless=False,
    fast_mode=True,
    mode='write'
)
await recorder.start()
# Interações são capturadas automaticamente
# Ou use command_handlers para interações programáticas
```

### Reprodução
```python
recorder = Recorder(
    output_path=Path('test.yaml'),
    initial_url=None,  # Lido do YAML
    headless=False,
    fast_mode=True,
    mode='read'
)
await recorder.start()
# Steps são executados automaticamente
```

### Reprodução com Vídeo
```python
# YAML deve ter config.video:
# config:
#   video:
#     enabled: true
#     quality: high
#     codec: webm
#     dir: videos

recorder = Recorder(
    output_path=Path('test.yaml'),  # YAML com config.video
    initial_url=None,
    headless=False,
    fast_mode=True,
    mode='read'  # Recorder detecta vídeo automaticamente
)
await recorder.start()
# Steps executados + vídeo gravado simultaneamente
# Vídeo finalizado e renomeado automaticamente
```

## Notas Importantes

⚠️ **Código Antigo**: Todo código que não está nesta stack deve ser considerado "não testado" e usado apenas como referência.

✅ **Base Confiável**: Apenas os arquivos documentados aqui são garantidos como funcionando.

