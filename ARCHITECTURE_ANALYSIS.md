# Análise Arquitetural - playwright-simple

## Objetivo
Mapear funcionalidades atuais e identificar o que é genérico (core) vs específico (extensões).

## Classes e Mixins Identificados

### Core (`playwright_simple/core/`)

#### Managers (Gerenciamento de Recursos)
- `CursorManager` - Gerenciamento de cursor visual (genérico)
- `VideoManager` - Gerenciamento de vídeo (genérico)
- `ScreenshotManager` - Gerenciamento de screenshots (genérico)
- `SelectorManager` - Gerenciamento de seletores (genérico)
- `SessionManager` - Gerenciamento de sessão (genérico)
- `TTSManager` - Text-to-Speech (genérico)

#### Mixins (Funcionalidades)
- `InteractionMixin` - click, type, hover, drag, scroll (genérico)
- `AssertionMixin` - assert_text, assert_visible, assert_url (genérico)
- `WaitMixin` - wait, wait_for, wait_for_url (genérico)
- `NavigationMixin` - go_to, back, forward, refresh (genérico)
- `FormsMixin` - fill_form, fill_by_label, select_by_label (genérico)
- `QueryMixin` - get_text, get_attr, is_visible (genérico)
- `UIHelpersMixin` - wait_for_modal, close_modal (genérico)
- `AuthMixin` - login genérico (genérico)

#### Base Classes
- `SimpleTestBase` - Classe base genérica (genérico)

#### Parsers
- `YAMLParser` - Parser YAML base (genérico)

### Odoo (`playwright_simple/odoo/`)

#### Mixins Específicos
- `OdooAuthMixin` - login com database selector (Odoo-específico)
- `OdooWaitMixin` - wait_until_ready com detectores Odoo (Odoo-específico)
- `OdooNavigationMixin` - go_to_menu, go_to_dashboard (Odoo-específico)
- `OdooTextInteractionMixin` - interações de texto Odoo (Odoo-específico)
- `OdooCRUDMixin` - create_record, search_and_open (Odoo-específico)
- `OdooFormsMixin` - fill com detecção Odoo (Odoo-específico)

#### Helpers Específicos
- `MenuNavigator` - Navegação de menus Odoo (Odoo-específico)
- `FieldHelper` - Campos Odoo (many2one, many2many, etc) (Odoo-específico)
- `ViewHelper` - Views Odoo (list, form, kanban) (Odoo-específico)
- `WizardHelper` - Wizards Odoo (Odoo-específico)
- `WorkflowHelper` - Workflows Odoo (Odoo-específico)

#### Base Classes
- `OdooTestBase` - Classe base Odoo (Odoo-específico)

#### Parsers
- `OdooYAMLParser` - Parser YAML com ações Odoo (Odoo-específico)

## Análise de Funcionalidades

### `core/auth.py` - AuthMixin
**Status:** ✅ Genérico
- Login genérico com seletores comuns
- Sem lógica Odoo-específica
- **Ação:** Manter como está

### `core/forms.py` - FormsMixin
**Status:** ✅ Genérico
- `fill_form` - genérico
- `fill_by_label` - genérico (busca por label HTML padrão)
- `select_by_label` - genérico
- Sem lógica Odoo-específica
- **Ação:** Manter como está

### `core/wait.py` - WaitMixin
**Status:** ✅ Genérico
- `wait` - genérico
- `wait_for` - genérico
- `wait_for_url` - genérico
- `wait_for_text` - genérico
- Sem lógica Odoo-específica
- **Ação:** Manter como está

### `core/navigation.py` - NavigationMixin
**Status:** ⚠️ Parcialmente genérico
- `go_to` - genérico (navegação por URL)
- `back`, `forward`, `refresh` - genéricos
- `navigate` - genérico (navegação por menu genérico)
- **Ação:** Manter como está (já é genérico)

### `odoo/auth.py` - OdooAuthMixin
**Status:** ✅ Odoo-específico
- Login com database selector
- Lógica específica de Odoo
- **Ação:** Manter em odoo/

### `odoo/wait.py` - OdooWaitMixin
**Status:** ✅ Odoo-específico
- `wait_until_ready` com detectores Odoo (.o_loading, etc)
- Lógica específica de Odoo
- **Ação:** Manter em odoo/

### `odoo/forms.py` - OdooFormsMixin
**Status:** ✅ Odoo-específico
- `fill` com detecção de campos Odoo
- `click_button` com detecção de wizard/form
- Lógica específica de Odoo
- **Ação:** Manter em odoo/

### `odoo/navigation.py` - OdooNavigationMixin
**Status:** ✅ Odoo-específico
- `go_to_menu` - navegação por menus Odoo
- `go_to_dashboard` - dashboard Odoo
- Lógica específica de Odoo
- **Ação:** Manter em odoo/

## Matriz de Decisão

| Funcionalidade | Localização Atual | Decisão | Justificativa |
|---------------|-------------------|---------|---------------|
| Login genérico | `core/auth.py` | ✅ Manter | Genérico para qualquer web app |
| Login Odoo | `odoo/auth.py` | ✅ Manter | Específico do Odoo (database selector) |
| Fill genérico | `core/forms.py` | ✅ Manter | Genérico (busca por label HTML) |
| Fill Odoo | `odoo/forms.py` | ✅ Manter | Específico (detecção de campos Odoo) |
| Wait genérico | `core/wait.py` | ✅ Manter | Genérico (wait_for, wait_for_url) |
| Wait Odoo | `odoo/wait.py` | ✅ Manter | Específico (detectores Odoo) |
| Navigation genérico | `core/navigation.py` | ✅ Manter | Genérico (URLs, back, forward) |
| Navigation Odoo | `odoo/navigation.py` | ✅ Manter | Específico (menus Odoo) |

## Código Duplicado Identificado

### Nenhum código duplicado significativo encontrado
- Core e Odoo têm responsabilidades bem separadas
- Odoo usa composição de funcionalidades core quando apropriado

## Funcionalidades no Lugar Errado

### Nenhuma funcionalidade identificada no lugar errado
- A separação atual está correta
- Core contém apenas funcionalidades genéricas
- Odoo contém apenas funcionalidades específicas

## Dependências Mapeadas

### Core → Odoo
- `OdooTestBase` herda de `SimpleTestBase` ✅
- `OdooYAMLParser` herda de `YAMLParser` ✅
- Odoo usa mixins core quando apropriado ✅

### Odoo → Core
- Odoo não tem dependências diretas problemáticas ✅
- Usa composição corretamente ✅

## Conclusões

1. **Separação atual está correta**: Core e Odoo estão bem separados
2. **Nenhuma refatoração crítica necessária**: Não há código no lugar errado
3. **Melhorias possíveis**:
   - Criar interfaces para extensões (opcional)
   - Melhorar type hints e docstrings
   - Criar módulo `odoo/specific/` para ações muito específicas

## Próximos Passos

1. ✅ Análise completa - CONCLUÍDA
2. Criar matriz de decisão formal
3. Prosseguir com melhorias arquiteturais (type hints, docstrings)
4. Criar módulo `odoo/specific/` se necessário

