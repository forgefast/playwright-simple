# Análise de Duplicações - Extensão ForgeERP

## Comparação: fill_input_by_label() vs fill_by_label()

### Core (SimpleTestBase.fill_by_label)
- **Localização**: `playwright_simple/core/base.py` linhas 799-921
- **Características**:
  - Tenta múltiplos seletores de label (label:has-text, [for*], text=)
  - Suporta context por texto (busca em fieldset, section, .form-group)
  - Trata input, textarea, select automaticamente
  - Detecta tag e usa select_option() para selects
  - Screenshots automáticos se configurado
  - Retorna self para method chaining
  - Mensagens de erro em português
  - Tratamento robusto de múltiplos campos encontrados

### Extensão (ForgeERPComponents.fill_input_by_label)
- **Localização**: `playwright_simple/forgeerp/components.py` linhas 294-336
- **Características**:
  - Apenas um seletor: `label:has-text("{label}")`
  - Context é seletor CSS (não texto)
  - Trata input, textarea, select
  - Detecta tag e usa select_option() para selects
  - Sem screenshots automáticos
  - Não retorna nada (void)
  - Mensagens de erro em inglês
  - Não trata múltiplos campos

### Conclusão
**O core é superior**. A extensão deve usar `fill_by_label()` do core.

---

## Comparação: select_option_by_label() vs select_by_label()

### Core (SimpleTestBase.select_by_label)
- **Localização**: `playwright_simple/core/base.py` linhas 923-993
- **Características**:
  - Tenta múltiplos seletores de label
  - Suporta context por texto
  - Busca select por atributo "for" ou próximo ao label
  - Screenshots automáticos se configurado
  - Retorna self para method chaining
  - Mensagens de erro em português

### Extensão (ForgeERPComponents.select_option_by_label)
- **Localização**: `playwright_simple/forgeerp/components.py` linhas 338-375
- **Características**:
  - Apenas um seletor: `label:has-text("{label}")`
  - Context é seletor CSS
  - Busca select por atributo "for" ou próximo ao label
  - Sem screenshots automáticos
  - Não retorna nada (void)
  - Mensagens de erro em inglês

### Conclusão
**O core é superior**. A extensão deve usar `select_by_label()` do core.

---

## Análise de Funcionalidades Genéricas

### HTMX Helpers
- **Localização**: `playwright_simple/forgeerp/htmx.py`
- **Métodos**:
  - `wait_for_htmx_swap()` - Genérico (qualquer app HTMX)
  - `wait_for_htmx_loading()` - Genérico
  - `detect_htmx_error()` - Genérico (padrões comuns de erro)
  - `get_htmx_result()` - Genérico
  - `wait_for_htmx_response()` - Genérico
  - `is_htmx_swapping()` - Genérico
- **Dependências**: Apenas Playwright, sem dependências específicas do ForgeERP
- **Decisão**: **MIGRAR PARA CORE** como módulo opcional (HTMX está se tornando popular)

### Modal Helpers
- **Localização**: `playwright_simple/forgeerp/components.py` linhas 235-254
- **Seletores usados**:
  - MODAL: `.modal, [role="dialog"], .o_dialog`
  - MODAL_CLOSE: `button[aria-label*="Close"], button:has-text("Close")`
- **Análise**: Seletores são genéricos (`.modal`, `[role="dialog"]` são padrões web comuns)
- **Decisão**: **ADICIONAR AO CORE** (genérico o suficiente)

### click_button() Genérico
- **Localização**: `playwright_simple/forgeerp/components.py` linhas 272-292
- **Funcionalidade**: Clica em botão por texto visível
- **Análise**: Genérico, complementa `fill_by_label()` existente
- **Decisão**: **ADICIONAR AO CORE**

### get_card_content()
- **Localização**: `playwright_simple/forgeerp/components.py` linhas 256-270
- **Funcionalidade**: Obtém conteúdo de texto de um card
- **Análise**: Genérico, útil para qualquer app web
- **Decisão**: **ADICIONAR AO CORE**

---

## Resumo de Decisões

### Migrar para Core
1. ✅ HTMX Helpers → `core/htmx.py` (módulo opcional)
2. ✅ Modal Helpers → `SimpleTestBase` (wait_for_modal, close_modal)
3. ✅ click_button() → `SimpleTestBase`
4. ✅ get_card_content() → `SimpleTestBase`

### Remover da Extensão
1. ✅ `fill_input_by_label()` - usar do core
2. ✅ `select_option_by_label()` - usar do core

### Manter na Extensão
1. ✅ Seletores específicos do ForgeERP
2. ✅ Form helpers específicos (fill_provision_form, etc.)
3. ✅ Workflows específicos
4. ✅ Navegação específica

