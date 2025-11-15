# Locais que Podem Aproveitar `CursorController`

## Resumo

A classe `CursorController` (usada na gravação) pode ser aproveitada em **todos os lugares** onde ações de click, type e submit são executadas, garantindo unificação completa.

## Categorias de Arquivos

### 1. Execução de YAML e Testes (PRIORIDADE ALTA)
- ✅ `core/yaml_actions.py` - Executa ações do YAML
- ✅ `core/yaml_executor.py` - Executa steps do YAML
- ✅ `core/runner/test_executor.py` - Executa testes Python

### 2. Mixins de Interação (PRIORIDADE ALTA)
- ✅ `core/interactions/click_interactions.py` - Método `click()`
- ✅ `core/interactions/keyboard_interactions.py` - Método `type()`
- ✅ `core/base.py` - `SimpleTestBase` (inicialização)

### 3. Helpers e Forms (PRIORIDADE MÉDIA)
- ✅ `core/ui_helpers.py` - Método `click_button()`
- ✅ `core/forms.py` - Método `submit()`, `fill_by_label()`

### 4. Módulos Odoo (PRIORIDADE MÉDIA)
- ✅ `odoo/forms.py` - Métodos `click_button()`, `fill()`
- ⚠️ `odoo/auth.py` - Verificar se executa ações
- ⚠️ `odoo/menus.py` - Verificar se executa ações
- ⚠️ `odoo/fields/*.py` - Verificar se executam ações
- ⚠️ `odoo/views/*.py` - Verificar se executam ações
- ⚠️ `odoo/workflows.py` - Verificar se executa ações
- ⚠️ `odoo/wizards.py` - Verificar se executa ações

### 5. Módulos ForgeERP (PRIORIDADE BAIXA)
- ⚠️ `forgeerp/*.py` - Verificar se executam ações

### 6. Comandos CLI (OPCIONAL)
- ⚠️ `core/recorder/command_handlers/playwright_handlers.py` - Já aceita `cursor_controller`, mas pode usar diretamente

## Estratégia de Implementação

### Fase 1: Core (Crítico)
1. `yaml_actions.py` - Reprodução YAML
2. `yaml_executor.py` / `test_executor.py` - Inicialização
3. `interactions/*.py` - Mixins principais
4. `base.py` - Inicialização em `SimpleTestBase`

### Fase 2: Helpers (Importante)
5. `ui_helpers.py` - Helpers de UI
6. `forms.py` - Forms genéricos

### Fase 3: Módulos Específicos (Opcional)
7. `odoo/forms.py` - Forms Odoo
8. Outros módulos Odoo (conforme necessário)
9. Módulos ForgeERP (conforme necessário)

## Benefícios

1. **Unificação Total**: Todas as ações usam a mesma classe
2. **Consistência**: Comportamento idêntico entre gravação e reprodução
3. **Manutenibilidade**: Uma única implementação para manter
4. **Testabilidade**: Mais fácil testar quando há uma única fonte de verdade

