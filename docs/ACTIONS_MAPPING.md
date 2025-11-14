# Mapeamento Completo de Ações - playwright-simple

**Data:** 2025-01-XX  
**Objetivo:** Mapear todas as ações disponíveis e identificar quais não usam cursor (DEPRECATED)

---

## Ações que USAM cursor (✅ Mantidas)

### Core Interactions (`core/interactions.py`)
- ✅ `click(selector, description)` - Usa cursor_manager.move_to() e show_click_effect()
- ✅ `double_click(selector, description)` - Usa cursor_manager.move_to() e show_click_effect()
- ✅ `right_click(selector, description)` - Usa cursor_manager.move_to() e show_click_effect()
- ✅ `type(selector, text, description)` - Usa cursor_manager.move_to() e show_click_effect()
- ✅ `select(selector, option, description)` - Usa cursor_manager.move_to() e show_click_effect()
- ✅ `hover(selector, description)` - Usa cursor_manager.move_to() e show_hover_effect()
- ✅ `drag(source, target, description)` - Usa cursor_manager (via ensure_cursor())
- ✅ `scroll(selector, direction, amount)` - Usa cursor_manager (via ensure_cursor())

### Odoo Text Interactions (`odoo/text_interactions.py`)
- ✅ `hover(text, context)` - Delega para super().hover() que usa cursor
- ✅ `double_click(text, context)` - Delega para super().double_click() que usa cursor
- ✅ `right_click(text, context)` - Delega para super().right_click() que usa cursor
- ✅ `drag_and_drop(from_text, to_text)` - Delega para super().drag() que usa cursor
- ✅ `scroll_down(amount)` - Delega para super().scroll() que usa cursor
- ✅ `scroll_up(amount)` - Delega para super().scroll() que usa cursor

### Odoo Forms (`odoo/forms.py`)
- ✅ `fill(label_value_string, context)` - Usa cursor via test.click_button() e test.type()
- ✅ `click_button(text, context)` - Usa cursor via test.click()
- ✅ `add_line(button_text)` - Usa cursor via test.click_button()

### Odoo Navigation (`odoo/navigation.py`)
- ✅ `go_to(menu_path)` - Usa cursor via navigate_with_cursor()
- ✅ `navigate_with_cursor(menu_path)` - Usa cursor_manager.move_to()

### Odoo Menus (`odoo/menus.py`)
- ✅ `open_apps_menu()` - Usa cursor via test.click() quando disponível
- ✅ `navigate_menu(menu_path)` - Usa cursor_manager.move_to() e show_click_effect()

---

## Ações que NÃO USAM cursor (❌ DEPRECATED)

### Odoo Menus (`odoo/menus.py`)
- ❌ `page.keyboard.press("Alt")` - Linha 96 - DEPRECATED: Não usa cursor
- ❌ `page.keyboard.press("Escape")` - Linha 110 - DEPRECATED: Não usa cursor
- ❌ `page.mouse.click(x, y)` - Linha 299 - DEPRECATED: Não usa cursor_manager
- ❌ `element.click()` - Linha 302 - DEPRECATED: Não usa cursor_manager
- ❌ `page.mouse.click(x, y)` - Linha 397 - DEPRECATED: Não usa cursor_manager
- ❌ `element.click()` - Linha 401, 404, 408, 437, 441 - DEPRECATED: Não usa cursor_manager
- ❌ `search_input.fill(search_text)` - Linha 479 - DEPRECATED: Não usa cursor
- ❌ `result.click()` - Linha 492 - DEPRECATED: Não usa cursor_manager
- ❌ `btn.click()` - Linha 564 - DEPRECATED: Não usa cursor_manager

### Odoo Filters (`odoo/specific/filters.py`)
- ❌ `page.mouse.click(x, y)` - Linha 89 - DEPRECATED: Usa cursor mas depois page.mouse.click direto
- ❌ `filter_btn.click()` - Linha 92 - DEPRECATED: Fallback sem cursor
- ❌ `filter_btn.click()` - Linha 138 - DEPRECATED: Não usa cursor_manager
- ❌ `filter_option.click()` - Linha 175, 182, 189, 206 - DEPRECATED: Não usa cursor_manager
- ❌ `page.keyboard.press('Escape')` - Linha 214 - DEPRECATED: Não usa cursor

### Odoo Logo (`odoo/specific/logo.py`)
- ❌ `element.click()` - Linha 382 - DEPRECATED: Não usa cursor_manager
- ❌ `page.mouse.click(x, y)` - Linha 485, 553, 701, 786 - DEPRECATED: Não usa cursor_manager

### Odoo YAML Parser (`odoo/yaml_parser/action_parser.py`)
- ❌ `page.keyboard.press(key)` - Linha 147 - DEPRECATED: Não usa cursor

### Core Interactions (`core/interactions.py`)
- ⚠️ `element.click()` - Linha 142 - **USO INTERNO**: Chamado após mover cursor, OK
- ⚠️ `element.click(button="right")` - Linha 302 - **USO INTERNO**: Chamado após mover cursor, OK
- ⚠️ `element.click()` - Linha 365, 369 - **USO INTERNO**: Chamado após mover cursor, OK
- ⚠️ `element.type(char, delay)` - Linha 381 - **USO INTERNO**: Chamado após mover cursor, OK
- ⚠️ `element.hover()` - Linha 535 - **USO INTERNO**: Chamado após mover cursor, OK

### Core Navigation (`core/navigation.py`)
- ❌ `link_element.click()` - Linha 169 - DEPRECATED: Não usa cursor_manager

### Odoo List View (`odoo/views/list_view.py`)
- ❌ `page.keyboard.press("Escape")` - Linha 197 - DEPRECATED: Não usa cursor
- ❌ `name_element.click(timeout=10000)` - Linha 219 - DEPRECATED: Não usa cursor_manager

### Odoo Relational Fields (`odoo/fields/relational_fields.py`)
- ❌ `page.keyboard.press("Enter")` - Linha 90 - DEPRECATED: Não usa cursor

---

## Resumo

### Total de Ações Mapeadas: ~50+

### Ações que USAM cursor: ~30 ✅
- Todas as ações principais de interação (click, type, select, hover, drag, scroll)
- Ações de navegação de menu com cursor
- Ações de formulário que delegam para métodos com cursor

### Ações que NÃO USAM cursor: ~20 ❌ DEPRECATED
- Uso direto de `page.mouse.click()` - ~10 ocorrências
- Uso direto de `element.click()` sem cursor - ~8 ocorrências
- Uso direto de `page.keyboard.press()` - ~5 ocorrências
- Uso direto de `element.fill()` - ~1 ocorrência

---

## Plano de Ação

1. ✅ Mapear todas as ações (FEITO)
2. ✅ Adicionar warnings de deprecation em todas as ações que não usam cursor (FEITO)
3. ✅ Documentar alternativas recomendadas (FEITO)
4. ✅ Criar script de detecção automática (FEITO)

## Status Final

- **Total de ações mapeadas:** ~50+
- **Ações com cursor:** ~30 ✅
- **Ações deprecated (sem cursor):** ~20 ❌ (com warnings adicionados)
- **Script de detecção:** `scripts/map_deprecated_actions.py`
- **Relatório gerado:** `docs/DEPRECATED_ACTIONS_REPORT.md`

Todas as ações que não usam cursor agora geram warnings nos logs quando executadas.

