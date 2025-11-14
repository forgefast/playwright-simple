# Relatório de Ações Deprecated (Sem Cursor)
**Total de arquivos escaneados:** 77
**Total de issues encontradas:** 56

---

## element.click() - uso direto sem cursor_manager
**Ocorrências:** 8

- `playwright_simple/odoo/menus.py:317`  ```python  await element.click()  ```
- `playwright_simple/odoo/menus.py:421`  ```python  await element.click()  ```
- `playwright_simple/odoo/menus.py:425`  ```python  "DEPRECATED: element.click() usado como fallback sem cursor. "  ```
- `playwright_simple/odoo/menus.py:428`  ```python  await element.click()  ```
- `playwright_simple/odoo/menus.py:433`  ```python  "DEPRECATED: element.click() usado em exception handler sem cursor. "  ```
- `playwright_simple/odoo/menus.py:436`  ```python  await element.click()  ```
- `playwright_simple/odoo/menus.py:465`  ```python  await element.click()  ```
- `playwright_simple/odoo/menus.py:469`  ```python  await element.click()  ```

## element.fill() - uso direto sem cursor
**Ocorrências:** 26

- `playwright_simple/core/forms.py:234`  ```python  await field.fill(str(value))  ```
- `playwright_simple/odoo/forms.py:28`  ```python  1. `await test.fill("Cliente", "João Silva")`  ```
- `playwright_simple/odoo/forms.py:29`  ```python  2. `await test.fill("Cliente = João Silva")`  ```
- `playwright_simple/odoo/forms.py:44`  ```python  await test.fill("Cliente", "João Silva")  ```
- `playwright_simple/odoo/forms.py:45`  ```python  await test.fill("Cliente = João Silva")  ```
- `playwright_simple/odoo/forms.py:46`  ```python  await test.fill("Data", "01/01/2024", context="Seção Datas")  ```
- `playwright_simple/odoo/yaml_parser/action_parser.py:163`  ```python  await test.fill(fill_value, context=context)  ```
- `playwright_simple/odoo/yaml_parser/action_parser.py:168`  ```python  await test.fill(label, value, context)  ```
- `playwright_simple/odoo/views/list_view.py:57`  ```python  await search_input.fill("")  ```
- `playwright_simple/odoo/views/list_view.py:61`  ```python  await search_input.fill(search_text)  ```

*... e mais 16 ocorrências*

## element.type() - uso direto sem cursor
**Ocorrências:** 10

- `playwright_simple/core/interactions.py:381`  ```python  await element.type(char, delay=TYPE_CHAR_DELAY)  ```
- `playwright_simple/core/auth.py:107`  ```python  await self.type(selector, username, "Username field")  ```
- `playwright_simple/core/auth.py:131`  ```python  await self.type(selector, password, "Password field")  ```
- `playwright_simple/core/forms.py:99`  ```python  await self.type(selector, str(value), f"Form field: {selector}")  ```
- `playwright_simple/odoo/base.py:172`  ```python  await self.type('input[name="db"]', database, "Campo Database")  ```
- `playwright_simple/odoo/base.py:175`  ```python  await self.type('input[name="login"]', username, "Campo Login")  ```
- `playwright_simple/odoo/base.py:178`  ```python  await self.type('input[name="password"]', password, "Campo Senha")  ```
- `playwright_simple/odoo/auth.py:52`  ```python  await self.type('input[name="db"]', database, "Campo Database")  ```
- `playwright_simple/odoo/auth.py:56`  ```python  await self.type('input[name="login"]', username, "Campo Login")  ```
- `playwright_simple/odoo/auth.py:60`  ```python  await self.type('input[name="password"]', password, "Campo Senha")  ```

## page.keyboard.press() - uso direto sem cursor
**Ocorrências:** 12

- `playwright_simple/odoo/menus.py:97`  ```python  "DEPRECATED: page.keyboard.press() usado sem cursor. "  ```
- `playwright_simple/odoo/menus.py:101`  ```python  await self.page.keyboard.press("Alt")  ```
- `playwright_simple/odoo/menus.py:116`  ```python  "DEPRECATED: page.keyboard.press() usado sem cursor. "  ```
- `playwright_simple/odoo/menus.py:120`  ```python  await self.page.keyboard.press("Escape")  ```
- `playwright_simple/odoo/yaml_parser/action_parser.py:150`  ```python  f"DEPRECATED: page.keyboard.press('{key}') usado sem cursor. "  ```
- `playwright_simple/odoo/yaml_parser/action_parser.py:154`  ```python  await test.page.keyboard.press(key)  ```
- `playwright_simple/odoo/specific/filters.py:245`  ```python  "DEPRECATED: page.keyboard.press() usado sem cursor. "  ```
- `playwright_simple/odoo/specific/filters.py:248`  ```python  await self.page.keyboard.press('Escape')  ```
- `playwright_simple/odoo/views/list_view.py:200`  ```python  "DEPRECATED: page.keyboard.press('Escape') usado sem cursor. "  ```
- `playwright_simple/odoo/views/list_view.py:203`  ```python  await self.page.keyboard.press("Escape")  ```

*... e mais 2 ocorrências*

