# Plano de Refatoração Incremental - Playwright-Simple

## Objetivo
Refatorar e atualizar o código do playwright-simple para implementar todas as funcionalidades documentadas nas fases de validação (phase0 a phase13), partindo da base funcional do `recorder.py` e da stack do `test_full_cycle.py`.

## Base Funcional - Stack Funcional (O que está funcionando ✅)

### Árvore de Chamadas

#### Nível 0: Scripts de Teste (Funcionando ✅)
- **test_full_cycle.py**: Orquestrador principal
  - Chama `test_odoo_interactive.py` (geração)
  - Chama `test_replay_yaml.py` (reprodução)
  - Valida YAML gerado
  - Valida saída da reprodução

- **test_odoo_interactive.py**: Geração de YAML
  - Usa `Recorder` em modo 'write'
  - Usa `CommandHandlers` para interações programáticas
  - Gera `test_odoo_login_real.yaml`

- **test_replay_yaml.py**: Reprodução de YAML
  - Usa `Recorder` em modo 'read'
  - Executa steps do YAML carregado

- **playwright_simple/cli/run_handlers.py**: Handler CLI
  - Usa `Recorder` em modo 'read'
  - Mesmo padrão que `test_replay_yaml.py`

#### Nível 1: Recorder (Funcionando ✅)
- **playwright_simple/core/recorder/recorder.py**: Classe principal
  - Modo 'write': Grava interações
  - Modo 'read': Executa YAML
  - Coordena todos os componentes

#### Nível 2: Componentes do Recorder (Funcionando ✅)

**Core Components:**
- `event_capture.py`: Captura eventos do browser
- `action_converter.py`: Converte eventos em ações YAML
- `yaml_writer.py`: Escreve YAML incrementalmente
- `console_interface.py`: Interface de console para comandos
- `event_handlers.py`: Handlers de eventos (click, input, blur, navigation, scroll, keydown)
- `element_identifier.py`: Identifica elementos por texto, label, placeholder, ARIA

**Command Handlers (Modular):**
- `command_handlers/handlers.py`: Coordenador principal
  - `recording_handlers.py`: start, save, exit, pause, resume
  - `metadata_handlers.py`: caption, audio, screenshot
  - `cursor_handlers.py`: cursor, click, type, press (se cursor disponível)
  - `playwright_handlers.py`: find, find-all, pw-click, pw-type, pw-submit, pw-wait, pw-info, pw-html

**Utilities:**
- `utils/browser.py`: BrowserManager (gerencia ciclo de vida do browser)
- `command_server.py`: Servidor de comandos externos (opcional)

**Opcionais (se disponíveis):**
- `cursor_controller.py`: Controle visual do cursor
- `../video.py`: VideoManager (gravação de vídeo)
- `../extensions/video/config.py`: VideoConfig

#### Nível 3: Dependências Externas (Funcionando ✅)
- `playwright_simple/core/logger.py`: Sistema de logging estruturado
- `playwright` (biblioteca externa): API do Playwright

### Tabela de Arquivos Funcionais

| Arquivo | Status | Função | Usado Por |
|---------|--------|--------|-----------|
| `test_full_cycle.py` | ✅ Funcionando | Orquestrador de testes | - |
| `test_odoo_interactive.py` | ✅ Funcionando | Geração de YAML | test_full_cycle.py |
| `test_replay_yaml.py` | ✅ Funcionando | Reprodução de YAML | test_full_cycle.py |
| `playwright_simple/cli/run_handlers.py` | ✅ Funcionando | Handler CLI run | CLI |
| `playwright_simple/core/recorder/recorder.py` | ✅ Funcionando | Classe principal do recorder | Todos os scripts acima |
| `playwright_simple/core/recorder/event_capture.py` | ✅ Funcionando | Captura eventos do browser | recorder.py |
| `playwright_simple/core/recorder/action_converter.py` | ✅ Funcionando | Converte eventos em ações | recorder.py, event_handlers.py |
| `playwright_simple/core/recorder/yaml_writer.py` | ✅ Funcionando | Escreve YAML | recorder.py, event_handlers.py, command_handlers |
| `playwright_simple/core/recorder/console_interface.py` | ✅ Funcionando | Interface de console | recorder.py |
| `playwright_simple/core/recorder/event_handlers.py` | ✅ Funcionando | Handlers de eventos | recorder.py |
| `playwright_simple/core/recorder/element_identifier.py` | ✅ Funcionando | Identifica elementos | action_converter.py |
| `playwright_simple/core/recorder/command_handlers/handlers.py` | ✅ Funcionando | Coordenador de handlers | recorder.py |
| `playwright_simple/core/recorder/command_handlers/recording_handlers.py` | ✅ Funcionando | Handlers de gravação | handlers.py |
| `playwright_simple/core/recorder/command_handlers/metadata_handlers.py` | ✅ Funcionando | Handlers de metadata | handlers.py |
| `playwright_simple/core/recorder/command_handlers/cursor_handlers.py` | ✅ Funcionando | Handlers de cursor | handlers.py |
| `playwright_simple/core/recorder/command_handlers/playwright_handlers.py` | ✅ Funcionando | Handlers Playwright diretos | handlers.py, test_odoo_interactive.py |
| `playwright_simple/core/recorder/utils/browser.py` | ✅ Funcionando | Gerenciamento de browser | recorder.py |
| `playwright_simple/core/recorder/command_server.py` | ✅ Funcionando | Servidor de comandos | recorder.py |
| `playwright_simple/core/logger.py` | ✅ Funcionando | Sistema de logging | Todos os módulos |

### Funcionalidades Implementadas na Stack Funcional

1. **Gravação (Write Mode)**
   - ✅ Captura de eventos (click, input, blur, navigation, scroll, keydown)
   - ✅ Conversão de eventos em ações YAML
   - ✅ Escrita incremental de YAML
   - ✅ Comandos interativos (start, save, exit, pause, resume, caption, audio, screenshot)
   - ✅ Comandos Playwright diretos (find, pw-click, pw-type, pw-submit, pw-wait, pw-info, pw-html)
   - ✅ Identificação de elementos (text, label, placeholder, ARIA, fallback)

2. **Reprodução (Read Mode)**
   - ✅ Leitura de YAML
   - ✅ Execução de steps (go_to, click, type, submit)
   - ✅ Navegação automática
   - ✅ Suporte a fast_mode

3. **Infraestrutura**
   - ✅ Gerenciamento de browser (BrowserManager)
   - ✅ Sistema de logging estruturado
   - ✅ Limpeza de processos órfãos
   - ✅ Suporte a video (opcional)
   - ✅ Suporte a cursor visual (opcional)

## Estrutura do Plano

### Fase 0: Preparação e Infraestrutura
**Status**: Validar estrutura existente
- Verificar estrutura de diretórios (tests/, playwright_simple/core/)
- Validar pytest.ini e CI/CD
- Verificar imports básicos funcionando
- **Arquivos a verificar**: `pytest.ini`, `.github/workflows/ci.yml`, estrutura de diretórios

### Fase 1: Core Básico - Interações Genéricas
**Status**: Implementar/atualizar ações básicas
- **click()**: Usar stack do recorder (command_handlers.handle_pw_click)
- **type()**: Usar stack do recorder (command_handlers.handle_pw_type)
- **fill()**: Implementar usando base do type()
- **go_to()**: Já funciona via recorder._execute_yaml_steps
- **wait()**: Implementar wait básico
- **assert_text() / assert_visible()**: Verificar se existe em assertions.py
- **Arquivos a atualizar**: `playwright_simple/core/interactions/`, `playwright_simple/core/base.py`

### Fase 2: Integração do Recorder (já implementado)
**Status**: Validar e documentar
- ElementIdentifier: ✅ Funcionando
- Recorder completo: ✅ Funcionando
- EventCapture: ✅ Funcionando
- ActionConverter: ✅ Funcionando
- YAMLWriter: ✅ Funcionando
- ConsoleInterface: ✅ Funcionando
- Modularização: ✅ Já modularizado
- **Ação**: Validar que tudo funciona, documentar

### Fase 3: Melhorias no Auto-Fix
**Status**: Implementar/atualizar
- Auto-fix com contexto completo (page_state, html_analyzer, action_history)
- HTML Analyzer: Verificar se existe e funciona
- Integração em yaml_executor/yaml_parser
- **Arquivos a verificar/atualizar**: `playwright_simple/core/auto_fixer.py`, `playwright_simple/core/html_analyzer.py`

### Fase 4: Comparação Visual de Screenshots
**Status**: Implementar/atualizar
- VisualComparison: Verificar se existe
- Comparação pixel a pixel
- Gerenciamento de baseline
- **Arquivos a verificar/atualizar**: `playwright_simple/core/visual_comparison.py`

### Fase 5: Documentação do Fluxo Híbrido
**Status**: Criar documentação
- Criar HYBRID_WORKFLOW.md
- Documentar fluxo: gravar → editar → executar
- Exemplos práticos
- **Arquivo a criar**: `docs/HYBRID_WORKFLOW.md`

### Fase 6-13: Extensões e Funcionalidades Avançadas
**Status**: Implementar conforme necessário
- Fase 6: Extensão Odoo (se aplicável)
- Fase 7-13: Outras funcionalidades avançadas
- **Ação**: Validar cada fase individualmente

## Estratégia de Implementação

### 1. Análise da Base Funcional
- ✅ Documentar stack do test_full_cycle.py (FEITO)
- ✅ Mapear arquivos do recorder.py e dependências (FEITO)
- Identificar código antigo que não se comunica

### 2. Implementação Incremental
- Para cada fase:
  1. Analisar o que já existe
  2. Identificar o que precisa ser atualizado
  3. Implementar/testar incrementalmente
  4. Validar com testes baseados no test_full_cycle.py
  5. Documentar resultados

### 3. Testes Progressivos
- Usar padrão do test_full_cycle.py:
  - Script de geração (se aplicável)
  - Script de reprodução/validação
  - Validação de saída
- Criar testes para cada funcionalidade implementada

## Próximos Passos Imediatos

1. **Validar Fase 0**
   - Verificar infraestrutura
   - Garantir que base está sólida

2. **Implementar Fase 1**
   - Atualizar ações básicas usando stack do recorder
   - Testar cada ação individualmente
   - Validar com testes baseados no test_full_cycle.py

3. **Validar Fase 2**
   - Documentar que recorder já está implementado
   - Criar testes de validação

## Critérios de Sucesso

- Cada fase implementada deve ter testes funcionando
- Código deve seguir padrão do recorder.py (modular, testável)
- Testes devem usar stack do test_full_cycle.py como referência
- Documentação deve ser atualizada conforme implementação progride

## Notas Importantes

⚠️ **Código Antigo**: Todo código que não está na stack funcional acima deve ser considerado "não testado" e pode ser usado apenas como referência/ideias, não como base de implementação.

✅ **Base Confiável**: Apenas os arquivos listados na tabela acima são garantidos como funcionando e testados.

