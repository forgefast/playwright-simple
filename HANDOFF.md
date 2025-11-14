# HANDOFF - Playwright Simple

## Contexto do Projeto

**Playwright Simple** é uma biblioteca Python para automação web simplificada, projetada para facilitar a escrita de testes e automações em YAML, sem necessidade de conhecimento profundo de programação. A biblioteca suporta:

- ✅ **Testes Automatizados** (QA, E2E, regressão)
- ✅ **Automação de Tarefas** (scripts, bots, workflows)
- ✅ **Monitoramento** (verificar status, coletar dados)
- ✅ **Integração** (conectar sistemas, sincronizar dados)
- ✅ **Web Scraping** (coletar informações de sites)
- ✅ **Relatórios Automatizados** (gerar e enviar relatórios)

### Arquitetura Core/Extensions

A biblioteca segue uma arquitetura **core enxuto + extensões**:

- **Core**: Funcionalidades simples e genéricas que servem para qualquer aplicação web
- **Extensions**: Funcionalidades específicas de aplicações (Odoo, ForgeERP, etc.)
- **YAML-first**: Extensões são compostas principalmente de arquivos YAML que usam ações do core

## Estado Atual

### Refatoração Recente (Concluída)

#### 1. `yaml_parser.py` - Reduzido de 1279 para 254 linhas (~80%)

**O que foi feito:**
- Extraída lógica de configuração para `yaml_config.py` (123 linhas)
- Removido código duplicado (métodos já movidos para outros módulos)
- Mantidos wrappers de compatibilidade para retrocompatibilidade

**Estrutura atual:**
- `playwright_simple/core/yaml_parser.py` (254 linhas) - Orquestrador principal
- `playwright_simple/core/yaml_config.py` (123 linhas) - Gerenciamento de configuração
- `playwright_simple/core/yaml_expressions.py` - Avaliação de expressões
- `playwright_simple/core/yaml_resolver.py` - Resolução de dependências YAML
- `playwright_simple/core/yaml_actions.py` - Mapeamento de ações
- `playwright_simple/core/yaml_executor.py` (433 linhas) - Execução de steps

#### 2. `interactions.py` - Dividido em módulos menores

**O que foi feito:**
- Dividido arquivo monolítico de 1065 linhas em módulos focados
- Cada módulo trata de um tipo específico de interação

**Estrutura atual:**
- `playwright_simple/core/interactions/__init__.py` (38 linhas) - Combina todos os mixins
- `playwright_simple/core/interactions/base.py` (47 linhas) - Funcionalidade base compartilhada
- `playwright_simple/core/interactions/click_interactions.py` (116 linhas) - Cliques
- `playwright_simple/core/interactions/keyboard_interactions.py` (173 linhas) - Teclado
- `playwright_simple/core/interactions/mouse_interactions.py` (90 linhas) - Mouse
- `playwright_simple/core/interactions/form_interactions.py` (44 linhas) - Formulários

**Total:** 508 linhas divididas em módulos menores e mais fáceis de manter.

### Arquivos Grandes Restantes

Arquivos que ainda podem ser refatorados (mas não são críticos):

- `playwright_simple/core/runner.py` (1712 linhas)
- `playwright_simple/core/runner/video_processor.py` (1029 linhas)
- `playwright_simple/core/runner/test_executor.py` (785 linhas)
- `playwright_simple/core/tts.py` (636 linhas)

## Migração de Testes Odoo Racco (✅ CONCLUÍDA)

### Status Atual

**✅ 29 de 29 testes migrados** (100% completo)

### Testes Migrados

#### Lote 1 - Testes Básicos (6/6 ✅)
- ✅ `test_simple_login.yaml`
- ✅ `test_colaborador_portal.yaml`
- ✅ `test_consumer_portal.yaml`
- ✅ `test_reseller_portal.yaml`
- ✅ `test_intro.yaml`
- ✅ `test_architecture.yaml`
- ✅ `common_login.yaml`

#### Lote 2 - Fluxos de Negócio (8/8 ✅)
- ✅ `test_sale_flow.yaml`
- ✅ `test_product_catalog.yaml`
- ✅ `test_partner_management.yaml`
- ✅ `test_commissions_system.yaml`
- ✅ `test_ingress_criteria.yaml`
- ✅ `test_level_escalation.yaml`
- ✅ `test_complete_mlm_flow.yaml`
- ✅ `test_network.yaml`

#### Lote 3 - Gamificação e Treinamento (8/8 ✅)
- ✅ `test_training.yaml`
- ✅ `test_gamification.yaml`
- ✅ `test_badges_achievements.yaml`
- ✅ `test_challenges_completion.yaml`
- ✅ `test_training_certification.yaml`
- ✅ `test_all_badges.yaml`
- ✅ `test_all_challenges.yaml`
- ✅ `test_all_courses.yaml`

#### Lote 4 - Revendedores e Níveis (5/5 ✅)
- ✅ `test_reseller_prata.yaml`
- ✅ `test_reseller_ouro.yaml`
- ✅ `test_reseller_platinum.yaml`
- ✅ `test_diretor_rede.yaml`
- ✅ `test_level_comparison.yaml`

#### Lote 5 - Testes Especiais (3/3 ✅)
- ✅ `test_demo_orders.yaml`
- ✅ `test_cursor_debug.yaml`
- ✅ `common_login.yaml`

### Localização dos Testes Migrados

Todos os testes migrados estão em: `playwright-simple/examples/racco/`

### Configuração Padrão

Todos os testes migrados incluem:
- ✅ Vídeo habilitado (qualidade alta, codec mp4)
- ✅ Áudio/narração habilitado (pt-BR, gtts)
- ✅ Legendas habilitadas (soft subtitles)
- ✅ Debug habilitado (pause on error, interactive mode, hot reload)
- ✅ Logging estruturado (nível DEBUG)

### Próximos Passos

1. ✅ **Migração concluída** - Todos os 29 testes foram migrados
2. ⏳ **Validar execução** - Executar testes e corrigir problemas encontrados
3. ⏳ **Usar debugging avançado** - Hot reload e logging para iterar rapidamente
4. ⏳ **Documentar** - Problemas e soluções encontradas durante execução

### Como Executar os Testes Migrados

Todos os testes estão em `playwright-simple/examples/racco/` e podem ser executados com:

```bash
cd /home/gabriel/softhill/playwright-simple
timeout 300 playwright-simple run examples/racco/test_XXX.yaml \
  --log-level DEBUG \
  --debug \
  --interactive \
  --hot-reload \
  --no-headless \
  --video \
  --audio \
  --subtitles \
  --slow-mo 50
```

### Estrutura de Migração

- **Sintaxe antiga**: `login:`, `go_to:`, `click:`, `fill:`, etc.
- **Sintaxe nova**: `action: login`, `action: navigate_menu`, `action: click_button`, `action: fill_field`, etc.
- **Configuração padrão**: Todos incluem vídeo, áudio, legendas, debug e logging estruturado
- **Compatibilidade**: Mantida compatibilidade com sintaxe simplificada quando suportada

### Arquivo de Teste Inicial

**Localização:** `playwright-simple/examples/test_racco_odoo_simple.yaml`

**Conteúdo atual:**
```yaml
name: Teste Odoo Racco - Simples
description: Teste básico do portal colaborador com debug

base_url: https://odoo.racco.com.br

config:
  logging:
    level: DEBUG
    console_output: true
  debug:
    enabled: true
    pause_on_error: true
    interactive_mode: true
    hot_reload_enabled: true
  video:
    enabled: false  # Começar sem vídeo
  browser:
    headless: false
    slow_mo: 50

steps:
  # Login
  - action: login
    login: maria.santos@racco.com.br
    password: demo123
    database: devel
    description: "Login no sistema Odoo"
```

### Credenciais Odoo Racco

- **URL:** https://odoo.racco.com.br
- **Login:** maria.santos@racco.com.br
- **Senha:** demo123
- **Database:** devel

### Extensões Odoo Disponíveis

A extensão Odoo já possui vários arquivos YAML prontos em `playwright-simple/examples/odoo/`:

- `login.yaml` - Login no Odoo
- `navigate_menu.yaml` - Navegação por menus
- `search.yaml` - Buscar registros
- `open_record.yaml` - Abrir registro específico
- `create_record.yaml` - Criar novo registro
- `edit_record.yaml` - Editar registro existente
- `delete_record.yaml` - Deletar registro
- `switch_view.yaml` - Trocar entre views (List, Form, Kanban)
- `fill_field.yaml` - Preencher campo por label
- `click_button.yaml` - Clicar em botão por texto
- `filter_by.yaml` - Filtrar por texto

### Teste Completo de Referência

**Arquivo:** `playwright-simple/examples/test_colaborador_portal_completo.yaml`

Este arquivo contém um teste completo que inclui:
- Login
- Navegação para Dashboard
- Navegação para Contatos
- Filtros
- Navegação para Vendas > Pedidos
- Navegação para Vendas > Produtos
- Navegação para Portal
- Screenshots em cada etapa

**Configuração completa:**
- Vídeo habilitado
- Áudio/narração habilitado
- Legendas habilitadas
- Cursor visual
- Browser não-headless

## Sistema de Debug e Logging

### Debug Extension

**Localização:** `playwright_simple/extensions/debug/`

**Recursos:**
- **Pause on error**: Pausa execução quando ocorre erro
- **Interactive mode**: Shell Python interativo para inspecionar estado
- **Hot reload**: Recarrega YAML sem reiniciar o teste
- **State saving**: Salva estado da página (HTML, URL, cursor position)
- **HTML snapshots**: Captura HTML em cada passo para inspeção

**Configuração:**
```yaml
config:
  debug:
    enabled: true
    pause_on_error: true
    interactive_mode: true
    hot_reload_enabled: true
    state_dir: "debug_states"
    html_snapshot_dir: "debug_html"
    checkpoint_dir: "debug_checkpoints"
```

### Structured Logging

**Localização:** `playwright_simple/core/logger.py`

**Níveis de log:**
- `DEBUG` - Detalhes técnicos
- `INFO` - Informações gerais
- `WARNING` - Avisos
- `ERROR` - Erros
- `CRITICAL` - Erros críticos
- `ACTION` (25) - Ações executadas
- `STATE` (22) - Mudanças de estado
- `ELEMENT` (18) - Interações com elementos

**Uso:**
```python
from playwright_simple.core.logger import get_logger

logger = get_logger()
logger.action("Clique executado", action="click", selector="button")
logger.state("Estado mudou", url_changed=True)
logger.element("Elemento encontrado", x=100, y=200)
```

## CLI Avançado

**Localização:** `playwright_simple/cli.py`

**Comando principal:**
```bash
playwright-simple run <arquivo.yaml> [opções]
```

**Opções principais:**
- `--log-level DEBUG|INFO|WARNING|ERROR|CRITICAL`
- `--debug` - Habilita modo debug
- `--interactive` - Modo interativo
- `--hot-reload` - Hot reload de YAML
- `--no-headless` - Executa com interface gráfica
- `--video` - Habilita vídeo
- `--audio` - Habilita áudio/narração
- `--subtitles` - Habilita legendas
- `--viewport 1920x1080` - Define tamanho da viewport
- `--slow-mo 50` - Atraso entre ações (ms)

**Exemplo completo:**
```bash
playwright-simple run examples/test_racco_odoo_simple.yaml \
  --log-level DEBUG \
  --debug \
  --interactive \
  --no-headless \
  --slow-mo 50
```

## YAML Language Features

A biblioteca implementa uma "linguagem completa" em YAML com:

### 1. Loops (`for`)
```yaml
- for: item in items
  steps:
    - action: click
      text: "{{ item }}"
```

### 2. Conditionals (`if/else/elif`)
```yaml
- if: "{{ user.role == 'admin' }}"
  then:
    - action: click
      text: "Admin Panel"
  else:
    - action: click
      text: "User Panel"
```

### 3. Variables (`set`)
```yaml
- set: count = "{{ len(items) }}"
- set: message = "Total: {{ count }}"
```

### 4. Try/Catch/Finally
```yaml
- try:
    - action: click
      text: "Unreliable Button"
  catch:
    - action: click
      text: "Fallback Button"
  finally:
    - action: screenshot
      name: "after_try_catch"
```

### 5. Expression Evaluation
```yaml
- if: "{{ count > 10 and status == 'active' }}"
- set: total = "{{ price * quantity }}"
- if: "{{ 'error' in message.lower() }}"
```

### 6. Compose (YAML Composition)
```yaml
- compose: odoo/login.yaml
  params:
    login: "user@example.com"
    password: "pass123"
```

## Estrutura de Diretórios

```
playwright-simple/
├── playwright_simple/
│   ├── core/                    # Core enxuto
│   │   ├── base.py             # SimpleTestBase
│   │   ├── interactions/       # Interações (dividido em módulos)
│   │   ├── yaml_parser.py     # Parser YAML (orquestrador)
│   │   ├── yaml_config.py     # Configuração YAML
│   │   ├── yaml_expressions.py # Expressões
│   │   ├── yaml_resolver.py   # Resolução de dependências
│   │   ├── yaml_actions.py    # Mapeamento de ações
│   │   ├── yaml_executor.py   # Execução de steps
│   │   ├── logger.py          # Structured logging
│   │   ├── state.py           # WebState e TestStep (state machine)
│   │   └── ...
│   ├── extensions/             # Extensões
│   │   ├── video/             # Vídeo
│   │   ├── audio/             # Áudio/TTS
│   │   ├── subtitles/         # Legendas
│   │   └── debug/             # Debug avançado
│   ├── odoo/                   # Extensão Odoo (específica)
│   └── cli.py                  # CLI avançado
├── examples/
│   ├── odoo/                   # YAMLs de ações Odoo
│   │   ├── login.yaml
│   │   ├── navigate_menu.yaml
│   │   └── ...
│   ├── automation/             # Exemplos de automação
│   ├── test_racco_odoo_simple.yaml
│   └── test_colaborador_portal_completo.yaml
└── docs/                       # Documentação
```

## Como Executar Testes

### 1. Instalação
```bash
cd /home/gabriel/softhill/playwright-simple
pip install -e .
```

### 2. Executar Teste Simples (com debug)
```bash
playwright-simple run examples/test_racco_odoo_simple.yaml \
  --log-level DEBUG \
  --debug \
  --interactive \
  --no-headless
```

### 3. Executar Teste Completo (com vídeo/áudio/legendas)
```bash
playwright-simple run examples/test_colaborador_portal_completo.yaml \
  --video \
  --audio \
  --subtitles \
  --no-headless
```

## Autonomia e Debugging

### Hot Reload

Quando `hot_reload_enabled: true`, a biblioteca monitora mudanças nos arquivos YAML e recarrega automaticamente, permitindo iterar rapidamente sem reiniciar o teste.

### Interactive Mode

Quando `interactive_mode: true` e ocorre um erro, o sistema:
1. Pausa a execução
2. Salva o estado atual (HTML, URL, contexto)
3. Abre um shell Python interativo com:
   - `page`: Objeto Playwright Page
   - `test`: Instância SimpleTestBase
   - `current_web_state`: WebState capturado
   - `debug_ext`: Instância da extensão de debug

**Comandos no shell:**
- `continue_test()` - Retoma execução
- `exit_test()` - Encerra o teste

### State Inspection

O sistema salva automaticamente:
- **Estado JSON**: `debug_states/state_step_{N}_{timestamp}.json`
- **HTML Snapshot**: `debug_html/html_step_{N}_{timestamp}.html`

## Problemas Conhecidos / Pendências

### 1. Arquivos Grandes Restantes
- `runner.py` (1712 linhas) - Pode ser dividido em módulos menores
- `video_processor.py` (1029 linhas) - Pode ser refatorado
- `test_executor.py` (785 linhas) - Pode ser simplificado

### 2. Teste Odoo Racco
- Arquivo inicial criado (`test_racco_odoo_simple.yaml`)
- Precisa ser executado e incrementado gradualmente
- Começar com login apenas, depois adicionar mais passos

### 3. Melhorias Futuras
- Implementar interface de debug interativa (HTML viewer, element inspector)
- Melhorar hot reload (monitoramento de arquivos)
- Adicionar mais exemplos de automação

## Comandos Úteis

### Verificar tamanho dos arquivos
```bash
cd /home/gabriel/softhill/playwright-simple
find playwright_simple -name "*.py" -type f -exec wc -l {} + | sort -rn | head -20
```

### Testar importação
```bash
python3 -c "from playwright_simple.core.interactions import InteractionMixin; print('OK')"
```

### Executar teste com timeout
```bash
timeout 60 playwright-simple run examples/test_racco_odoo_simple.yaml --debug --no-headless
```

### Ver logs detalhados
```bash
playwright-simple run examples/test_racco_odoo_simple.yaml \
  --log-level DEBUG \
  --log-file /tmp/test.log \
  --json-log
```

## Informações Importantes

### Servidores Contabo Disponíveis
- **IP 1:** 161.97.123.192
- **IP 2:** 207.244.252.217
- Ambos disponíveis para acesso SSH
- Podem ser usados para testes em ambiente real

### Regras do Usuário
- Sempre executar comandos com `timeout`
- Sempre criar arquivos em inglês
- Sempre responder em Português (BR)

### Princípios da Biblioteca
1. **Core enxuto**: Apenas funcionalidades genéricas e simples
2. **YAML-first**: Extensões compostas principalmente de YAML
3. **Não travar o usuário**: Sempre permitir acesso direto ao Playwright
4. **Facilitar, não restringir**: Tornar fácil, mas não remover funcionalidades avançadas

## Próximos Passos Recomendados

1. **Executar teste inicial:**
   ```bash
   cd /home/gabriel/softhill/playwright-simple
   playwright-simple run examples/test_racco_odoo_simple.yaml \
     --log-level DEBUG \
     --debug \
     --interactive \
     --no-headless
   ```

2. **Incrementar passos gradualmente:**
   - Adicionar navegação para Dashboard
   - Adicionar screenshot
   - Adicionar mais navegação
   - Corrigir problemas conforme aparecem

3. **Usar debug para iterar:**
   - Quando erro ocorrer, usar modo interativo
   - Inspecionar HTML salvo
   - Corrigir YAML ou código
   - Hot reload e continuar

4. **Adicionar recursos depois:**
   - Quando teste básico funcionar, adicionar vídeo
   - Depois adicionar áudio/narração
   - Por último adicionar legendas

## Referências

- **Documentação CLI:** `docs/CLI.md`
- **Documentação Debug:** `docs/DEBUGGING.md`
- **Documentação Automação:** `docs/AUTOMATION.md`
- **YAML Language Features:** `docs/YAML_LANGUAGE_FEATURES.md`
- **Playwright Direct Access:** `docs/PLAYWRIGHT_ACCESS.md`
- **State Machine:** `docs/STATE_MACHINE.md`

## Contato e Contexto

- **Projeto:** Playwright Simple
- **Diretório:** `/home/gabriel/softhill/playwright-simple`
- **Última refatoração:** Divisão de `yaml_parser.py` e `interactions.py`
- **Status:** Pronto para começar testes Odoo Racco

---

**Boa sorte com os testes! 🚀**

