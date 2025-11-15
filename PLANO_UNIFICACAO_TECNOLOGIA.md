# Plano: Unificação da Tecnologia de Gravação e Reprodução

## Objetivo

Garantir que a gravação e a reprodução usem **exatamente a mesma classe `CursorController`** para executar ações (click, type, submit).

## Situação Atual

### Gravação
- **Classe Principal**: `CursorController` (em `recorder/cursor_controller/`)
- **Métodos**: `click_by_text()`, `type_text()`, `click()`, `press_key()`
- **Tecnologia Interna**: `page.mouse.click()` / `page.keyboard.type()` (via `CursorInteraction`)
- **Caminho**: 
  - Comandos console (`click`, `type`) → `CursorController.click_by_text()` / `CursorController.type_text()`
  - Comandos CLI (`pw-click`, `pw-type`) → `unified_click()` / `unified_type()` → `PlaywrightCommands` (com `cursor_controller` opcional)
  - Eventos DOM capturados → `ActionConverter` → YAML (não executa, apenas grava)

### Reprodução (YAML)
- **Classe Atual**: `ActionMapper` → `_execute_click()` / `_execute_type()` → `unified_click()` / `unified_type()` → `PlaywrightCommands`
- **Cursor**: Usa `CursorManager` (apenas visualização, não executa ações)
- **Caminho**: YAML → `ActionMapper._execute_click()` → `unified_click()` → `PlaywrightCommands`
- ❌ **NÃO USA `CursorController`** - usa `PlaywrightCommands` diretamente!

### Testes Python Diretos (SimpleTestBase)
- **Tecnologia**: `SimpleTestBase` → `InteractionMixin` → `ClickInteractionMixin` → `element.click()` (que é `page.locator().click()`)
- **Caminho**: `test.click()` → `ClickInteractionMixin.click()` → `element.click()` → `page.locator().click()`
- ❌ **NÃO USA `CursorController`** - usa implementação diferente!

### Análise

❌ **PROBLEMA PRINCIPAL**: A gravação usa `CursorController` para executar ações, mas a reprodução usa `PlaywrightCommands` diretamente.

⚠️ **PROBLEMA SECUNDÁRIO**: Há três tecnologias diferentes:
1. `CursorController` → `page.mouse.click()` / `page.keyboard.type()` (gravação - comandos console)
2. `PlaywrightCommands` → `page.mouse.click()` / `page.keyboard.type()` (gravação CLI / reprodução YAML)
3. `ClickInteractionMixin` → `element.click()` / `element.fill()` (testes Python diretos)

## Plano de Unificação

### Fase 1: Auditoria Completa

1. **Verificar todos os pontos de execução de click/type/submit**
   - [ ] Buscar todas as chamadas diretas a `page.click()`, `page.fill()`, `page.mouse.click()`, `page.keyboard.type()`
   - [ ] Identificar código que não usa `PlaywrightCommands` ou `unified_*`
   - [ ] Documentar todos os pontos de entrada

2. **Verificar se há classes/implementações alternativas**
   - [ ] Verificar se há `ActionRegistry` ou classes similares
   - [ ] Verificar se há implementações antigas de click/type
   - [ ] Verificar se há código que contorna `PlaywrightCommands`

### Fase 2: Unificação Completa - Usar `CursorController` na Reprodução

3. **Modificar `ActionMapper` para usar `CursorController` diretamente**
   - [ ] Inicializar `CursorController` no executor de testes (similar ao `Recorder`)
   - [ ] Modificar `_execute_click()` para usar `CursorController.click_by_text()` em vez de `unified_click()`
   - [ ] Modificar `_execute_type()` para usar `CursorController.type_text()` em vez de `unified_type()`
   - [ ] Modificar `_execute_submit()` para usar `CursorController` (se houver método correspondente)
   - [ ] Garantir que `CursorController` seja inicializado antes de executar ações
   - [ ] Garantir que `CursorController` seja limpo após execução

4. **Modificar `ClickInteractionMixin` para usar `CursorController`**
   - [ ] Modificar `ClickInteractionMixin.click()` para usar `CursorController.click_by_text()` ou `CursorController.click()`
   - [ ] Modificar `KeyboardInteractionMixin.type()` para usar `CursorController.type_text()`
   - [ ] Garantir que `SimpleTestBase` inicialize `CursorController` (além de `CursorManager`)
   - [ ] Manter compatibilidade com a API existente (mesmos parâmetros)

8. **Verificar que comandos CLI também podem usar `CursorController` (opcional)**
   - [x] `handle_pw_click()` já pode receber `cursor_controller` como parâmetro ✅
   - [x] `handle_pw_type()` já pode receber `cursor_controller` como parâmetro ✅
   - [ ] Verificar se comandos CLI da gravação já usam `CursorController` diretamente
   - [ ] Considerar usar `CursorController` diretamente nos handlers CLI em vez de passar para `unified_*`

### Fase 3: Validação

6. **Testes de unificação**
   - [ ] Testar que gravação e reprodução produzem o mesmo comportamento
   - [ ] Testar que comandos CLI produzem o mesmo comportamento
   - [ ] Verificar que não há diferenças visuais ou funcionais

9. **Documentação**
   - [ ] Documentar que TODAS as ações devem usar `CursorController`
   - [ ] Adicionar comentários no código indicando que é a única forma permitida
   - [ ] Criar guia de desenvolvimento para evitar regressões

## Arquivos a Verificar/Modificar

### Arquivos Principais (Já OK - apenas validação)
- `playwright_simple/core/yaml_actions.py` - ActionMapper (reprodução) ✅
- `playwright_simple/core/recorder/command_handlers/playwright_handlers.py` - Handlers CLI (gravação) ✅
- `playwright_simple/core/playwright_commands/unified.py` - Funções unificadas ✅
- `playwright_simple/core/playwright_commands/commands.py` - PlaywrightCommands ✅
- `playwright_simple/core/playwright_commands/element_interactions.py` - Implementação real ✅

### Arquivos a MODIFICAR (Unificação necessária)

#### Core - Execução de Ações
- `playwright_simple/core/yaml_actions.py` - **MODIFICAR** `_execute_click()`, `_execute_type()`, `_execute_submit()` para usar `CursorController` diretamente
- `playwright_simple/core/yaml_executor.py` - **MODIFICAR** para inicializar `CursorController` antes de executar steps
- `playwright_simple/core/runner/test_executor.py` - **MODIFICAR** para inicializar `CursorController` ao criar instância de teste

#### Core - Mixins de Interação
- `playwright_simple/core/interactions/click_interactions.py` - **MODIFICAR** `click()` para usar `CursorController.click_by_text()` ou `CursorController.click()`
- `playwright_simple/core/interactions/keyboard_interactions.py` - **MODIFICAR** `type()` para usar `CursorController.type_text()`
- `playwright_simple/core/base.py` - **MODIFICAR** `SimpleTestBase` para inicializar `CursorController` (além de `CursorManager`)

#### Core - Helpers e Forms
- `playwright_simple/core/ui_helpers.py` - **MODIFICAR** `click_button()` para usar `CursorController.click_by_text()`
- `playwright_simple/core/forms.py` - **MODIFICAR** `submit()` para usar `CursorController` (se houver método correspondente) ou manter `unified_submit()` mas passar `CursorController`

#### Odoo - Módulos Específicos
- `playwright_simple/odoo/forms.py` - **MODIFICAR** `click_button()` e `fill()` para usar `CursorController`
- `playwright_simple/odoo/auth.py` - **VERIFICAR** se executa ações que podem usar `CursorController`
- `playwright_simple/odoo/menus.py` - **VERIFICAR** se executa ações que podem usar `CursorController`
- `playwright_simple/odoo/fields/*.py` - **VERIFICAR** se executam ações que podem usar `CursorController`
- `playwright_simple/odoo/views/*.py` - **VERIFICAR** se executam ações que podem usar `CursorController`
- `playwright_simple/odoo/workflows.py` - **VERIFICAR** se executa ações que podem usar `CursorController`
- `playwright_simple/odoo/wizards.py` - **VERIFICAR** se executa ações que podem usar `CursorController`

#### ForgeERP - Módulos Específicos
- `playwright_simple/forgeerp/*.py` - **VERIFICAR** se executam ações que podem usar `CursorController`

### Arquivos a Auditar
- `playwright_simple/core/yaml_executor.py` - Executor de YAML
- `playwright_simple/core/runner/test_executor.py` - Executor de testes
- `playwright_simple/core/forms.py` - FormsMixin (já usa `unified_submit()` ✅)

## Critérios de Sucesso

1. ✅ **Reprodução YAML** usa `CursorController` diretamente (mesma classe da gravação)
2. ✅ **Testes Python** usam `CursorController` diretamente (mesma classe da gravação)
3. ✅ **Todas as ações** passam por `CursorController` (click, type, submit)
4. ✅ **Gravação e reprodução** usam exatamente a mesma classe (`CursorController`)
5. ✅ **Testes passam** sem regressões
6. ✅ **API de `SimpleTestBase`** permanece compatível (mesmos métodos, mesma assinatura)

## Próximos Passos

1. Executar auditoria completa (Fase 1)
2. Identificar pontos que precisam ser unificados
3. Implementar unificação (Fase 2)
4. Validar (Fase 3)

