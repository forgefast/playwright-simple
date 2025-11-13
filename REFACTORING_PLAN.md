# Plano de Refatoração Arquitetural - playwright-simple

## Objetivo

Refatorar o projeto separando funcionalidades específicas do Odoo (em `odoo/`) de funcionalidades generalizáveis (em `core/`), aplicando boas práticas de arquitetura Python e padrões de design para bibliotecas extensíveis.

## Princípios Arquiteturais

### 1. Separação Core vs Extensões
- **Core (`playwright_simple/core/`)**: Funcionalidades genéricas para qualquer aplicação web
- **Extensões (`playwright_simple/odoo/`, `playwright_simple/forgeerp/`)**: Funcionalidades específicas de cada plataforma

### 2. Padrões de Design
- **Composition over Inheritance**: Preferir composição para flexibilidade
- **Dependency Injection**: Injetar dependências via construtor
- **Strategy Pattern**: Para diferentes estratégias de processamento
- **Factory Pattern**: Para criação de instâncias de teste
- **Interface Segregation**: Interfaces pequenas e específicas

### 3. Boas Práticas Python
- Type hints completos
- Docstrings seguindo Google/NumPy style
- Exceções específicas
- Context managers para recursos
- Async/await apropriado

## Estrutura Arquitetural

```
playwright_simple/
├── core/                      # Funcionalidades genéricas
│   ├── base.py                # SimpleTestBase (com Dependency Injection)
│   ├── extensions/            # Interfaces para extensões
│   │   ├── __init__.py        # IExtensionAuth, IExtensionWait, IExtensionNavigation
│   │   ├── auth.py            # Interface de autenticação
│   │   ├── wait.py            # Interface de esperas
│   │   └── navigation.py      # Interface de navegação
│   ├── interactions.py        # Interações genéricas (click, type, etc)
│   ├── navigation.py          # Navegação genérica (go_to, back, forward)
│   ├── forms.py               # Formulários genéricos
│   ├── auth.py                # Autenticação genérica
│   ├── wait.py                # Esperas genéricas
│   └── ...                    # Outros módulos genéricos
│
├── odoo/                      # Extensão Odoo
│   ├── base.py                # OdooTestBase (com Dependency Injection)
│   ├── specific/               # Ações muito específicas do Odoo
│   │   ├── __init__.py
│   │   ├── logo.py            # LogoNavigator (clique no logo)
│   │   └── filters.py         # FilterHelper (menu de filtros)
│   ├── auth.py                # Autenticação Odoo
│   ├── wait.py                # Esperas Odoo
│   ├── navigation.py          # Navegação Odoo
│   ├── fields/                # Campos Odoo (many2one, etc)
│   ├── views/                 # Views Odoo (list, form, kanban)
│   └── ...                    # Outros módulos Odoo
│
└── forgeerp/                  # Extensão ForgeERP (futuro)
    └── ...
```

## Análise de Funcionalidades

### Funcionalidades Genéricas (devem estar em `core/`)
1. **Interações básicas**: click, type, hover, drag, scroll
2. **Navegação genérica**: go_to, back, forward, refresh
3. **Formulários genéricos**: fill_form, fill_by_label (sem lógica Odoo)
4. **Autenticação genérica**: login básico (sem lógica Odoo)
5. **Esperas genéricas**: wait, wait_for, wait_for_url
6. **Assertions**: assert_text, assert_visible, assert_url
7. **Queries**: get_text, get_attr, is_visible
8. **UI Helpers genéricos**: wait_for_modal, close_modal
9. **Gerenciamento de recursos**: CursorManager, VideoManager, ScreenshotManager
10. **YAML parser base**: YAMLParser (sem ações Odoo-específicas)

### Funcionalidades Odoo-específicas (devem estar em `odoo/`)
1. **Autenticação Odoo**: login com database selector, logout Odoo
2. **Navegação Odoo**: go_to_menu, go_to_dashboard, MenuNavigator
3. **Campos Odoo**: FieldHelper, many2one, many2many, one2many
4. **Views Odoo**: ViewHelper, list_view, form_view, kanban
5. **Wizards Odoo**: WizardHelper
6. **Workflows Odoo**: WorkflowHelper
7. **Esperas Odoo**: wait_until_ready com detectores Odoo (.o_loading, etc)
8. **CRUD Odoo**: create_record, search_and_open com lógica Odoo
9. **Forms Odoo**: fill com detecção de campos Odoo
10. **YAML Parser Odoo**: OdooYAMLParser com ações Odoo-específicas
11. **Selectors Odoo**: get_field_selectors, get_view_selectors
12. **Version Detection**: detect_version, detect_edition
13. **Ações específicas**: LogoNavigator, FilterHelper (em `odoo/specific/`)

## Status da Refatoração

### ✅ Fase 1: Análise e Mapeamento - CONCLUÍDA
- [x] Identificar todas as classes, mixins e helpers
- [x] Mapear dependências entre módulos
- [x] Identificar código duplicado
- [x] Identificar funcionalidades no lugar errado
- [x] Criar matriz de decisão Core vs Odoo

**Resultado**: Separação atual está correta. Não há código no lugar errado.

### ✅ Fase 2: Refatoração Core - CONCLUÍDA
- [x] Verificar `core/auth.py` (sem lógica Odoo - OK)
- [x] Verificar `core/forms.py` (sem lógica Odoo - OK)
- [x] Verificar `core/wait.py` (sem lógica Odoo - OK)
- [x] Verificar `core/navigation.py` (sem lógica Odoo - OK)
- [x] Criar `core/extensions/` com interfaces base

**Resultado**: Core está limpo e genérico. Interfaces de extensão criadas.

### ✅ Fase 3: Refatoração Odoo - CONCLUÍDA
- [x] Verificar `odoo/auth.py` (completo e específico)
- [x] Verificar `odoo/wait.py` (completo e específico)
- [x] Verificar `odoo/navigation.py` (completo e específico)
- [x] Criar `odoo/specific/` para ações muito específicas
  - [x] `logo.py` - LogoNavigator
  - [x] `filters.py` - FilterHelper
- [x] Refatorar `go_to_dashboard` para usar LogoNavigator
- [x] Refatorar `open_filter_menu` e `filter_records` para usar FilterHelper

**Resultado**: Odoo está bem organizado com módulo específico para ações muito específicas.

### ✅ Fase 4: Melhorias Arquiteturais - CONCLUÍDA
- [x] Aplicar Dependency Injection em `SimpleTestBase`
- [x] Aplicar Dependency Injection em `OdooTestBase`
- [ ] Melhorar type hints (em progresso)
- [ ] Melhorar docstrings (em progresso)
- [ ] Melhorar error handling (em progresso)

**Resultado**: Dependency Injection implementado. Type hints e docstrings em progresso.

### ⏳ Fase 5: Documentação - EM PROGRESSO
- [x] Atualizar REFACTORING_PLAN.md
- [ ] Atualizar REFACTORING_CHECKLIST.md
- [ ] Atualizar REFACTORING_GUIDE.md
- [ ] Atualizar REFACTORING_STATUS.md
- [ ] Criar REFACTORING_ARCHITECTURE.md

### ⏳ Fase 6: Testes e Validação - PENDENTE
- [ ] Executar todos os testes após cada fase
- [ ] Validar que comportamento não mudou
- [ ] Corrigir regressões
- [ ] Criar testes de integração

## Decisões Arquiteturais

### 1. Dependency Injection
**Decisão**: Implementar DI em `SimpleTestBase` e `OdooTestBase` para permitir customização de managers e helpers.

**Justificativa**: Facilita testes, permite mock de dependências, melhora flexibilidade.

**Implementação**: Construtores aceitam managers e helpers opcionais, criando defaults se não fornecidos.

### 2. Módulo `odoo/specific/`
**Decisão**: Criar módulo para ações muito específicas do Odoo (logo, filtros).

**Justificativa**: Separa ações muito específicas de funcionalidades mais gerais, facilita manutenção.

**Implementação**: `LogoNavigator` e `FilterHelper` extraídos de `menus.py` e `list_view.py`.

### 3. Interfaces de Extensão
**Decisão**: Criar interfaces em `core/extensions/` para facilitar criação de novas extensões.

**Justificativa**: Define contratos claros, facilita implementação de novas extensões (ForgeERP, etc).

**Implementação**: `IExtensionAuth`, `IExtensionWait`, `IExtensionNavigation` usando `Protocol`.

## Próximos Passos

1. Completar melhorias de type hints e docstrings
2. Melhorar error handling
3. Atualizar documentação completa
4. Executar testes e validar
5. Criar testes de integração

## Referências

- `ARCHITECTURE_ANALYSIS.md` - Análise detalhada da arquitetura atual
- `CORE_VS_ODOO_MATRIX.md` - Matriz de decisão Core vs Odoo
- `REFACTORING_ARCHITECTURE.md` - Arquitetura final proposta (a ser criado)
