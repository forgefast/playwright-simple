# Fase 1: Core Básico - Interações Genéricas

## Objetivo
Implementar/atualizar ações básicas usando a stack funcional do recorder.

## Ações a Implementar/Atualizar

### 1. click()
- **Status**: ✅ Já existe via `command_handlers.handle_pw_click`
- **Localização**: `playwright_simple/core/recorder/command_handlers/playwright_handlers.py`
- **Ação**: Verificar se pode ser exposto em `playwright_simple/core/interactions/` ou `base.py`

### 2. type()
- **Status**: ✅ Já existe via `command_handlers.handle_pw_type`
- **Localização**: `playwright_simple/core/recorder/command_handlers/playwright_handlers.py`
- **Ação**: Verificar se pode ser exposto em `playwright_simple/core/interactions/` ou `base.py`

### 3. fill()
- **Status**: ⚠️ Precisa implementar
- **Base**: Usar `type()` como base
- **Ação**: Implementar usando stack do recorder

### 4. go_to()
- **Status**: ✅ Já funciona via `recorder._execute_yaml_steps`
- **Localização**: `playwright_simple/core/recorder/recorder.py`
- **Ação**: Verificar se pode ser exposto

### 5. wait()
- **Status**: ⚠️ Precisa implementar
- **Ação**: Implementar wait básico usando Playwright

### 6. assert_text() / assert_visible()
- **Status**: ⚠️ Verificar se existe
- **Localização**: `playwright_simple/core/assertions.py`
- **Ação**: Verificar e atualizar se necessário

## Plano de Implementação

1. Analisar código existente em `playwright_simple/core/interactions/` e `base.py`
2. Identificar o que precisa ser atualizado
3. Usar stack do recorder como base
4. Implementar/testar incrementalmente
5. Validar com testes baseados no test_full_cycle.py

## Análise do Código Existente

### 1. click()
- **Status**: ✅ Existe em código antigo
- **Localização Antiga**: `playwright_simple/core/interactions/click_interactions.py`
- **Stack Funcional**: `command_handlers.handle_pw_click()` em `playwright_handlers.py`
- **Decisão**: Código antigo usa CursorController, stack funcional também usa. Manter ambos, mas documentar que stack funcional é a base.

### 2. type()
- **Status**: ✅ Existe em código antigo
- **Localização Antiga**: `playwright_simple/core/interactions/keyboard_interactions.py`
- **Stack Funcional**: `command_handlers.handle_pw_type()` em `playwright_handlers.py`
- **Decisão**: Stack funcional já implementa type completo. Código antigo pode ser atualizado para usar stack funcional.

### 3. fill()
- **Status**: ✅ Existe
- **Localização**: `playwright_simple/core/forms.py`
- **Métodos**: `fill_by_label()` e `fill_form()`
- **Decisão**: Já implementado. Manter como está.

### 4. go_to()
- **Status**: ✅ Já funciona via `recorder._execute_yaml_steps`
- **Localização**: `playwright_simple/core/recorder/recorder.py` (linha ~594)
- **Decisão**: Funcionalidade já existe e funciona. Pode ser exposta se necessário.

### 5. wait()
- **Status**: ✅ Existe
- **Localização**: `playwright_simple/core/wait.py`
- **Métodos**: `wait()`, `wait_for()`, `wait_for_url()`, `wait_for_text()`
- **Decisão**: Já implementado. Manter como está.

### 6. assert_text() / assert_visible()
- **Status**: ✅ Existe
- **Localização**: `playwright_simple/core/assertions.py`
- **Decisão**: Já implementado e funcional. Manter como está.

## Resultados da Implementação

### Status Atual
- ✅ **click()**: Existe em código antigo e na stack funcional. Stack funcional é a base.
- ✅ **type()**: Existe em código antigo e na stack funcional. Stack funcional é a base.
- ✅ **fill()**: Existe como `fill_by_label()` e `fill_form()` em `forms.py`
- ✅ **go_to()**: Já funciona via recorder `_execute_yaml_steps`
- ✅ **wait()**: Existe com múltiplos métodos em `wait.py`
- ✅ **assert_text() / assert_visible()**: Já existem e funcionam em `assertions.py`

## Conclusão

✅ **FASE 1 VALIDADA**: Todas as ações básicas já estão implementadas:
- Algumas na stack funcional (click, type via command_handlers)
- Outras no código antigo (fill, wait, assert)
- go_to funciona via recorder

**Recomendação**: Manter implementações existentes. Stack funcional pode ser usada como referência para melhorias futuras, mas código atual está funcional.

