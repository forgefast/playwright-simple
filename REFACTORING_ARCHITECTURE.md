# Arquitetura Final - playwright-simple

**Versão**: 2.0  
**Última atualização**: 2025-01-XX

## Visão Geral

playwright-simple segue uma arquitetura modular com separação clara entre funcionalidades genéricas (core) e específicas (extensões).

## Princípios Arquiteturais

### 1. Separação Core vs Extensões
- **Core**: Funcionalidades genéricas para qualquer aplicação web
- **Extensões**: Funcionalidades específicas de cada plataforma (Odoo, ForgeERP, etc)

### 2. Dependency Injection
- Managers e helpers podem ser injetados via construtor
- Facilita testes e customização
- Mantém compatibilidade com defaults

### 3. Composition over Inheritance
- Preferir composição para flexibilidade
- Mixins para funcionalidades compartilhadas
- Helpers para lógica específica

### 4. Interface Segregation
- Interfaces pequenas e específicas
- Facilita implementação de novas extensões
- Define contratos claros

## Estrutura de Diretórios

```
playwright_simple/
├── core/                      # Funcionalidades genéricas
│   ├── base.py                # SimpleTestBase
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
│   ├── assertions.py          # Assertions genéricas
│   ├── queries.py             # Queries genéricas
│   ├── ui_helpers.py          # UI helpers genéricos
│   ├── cursor.py              # CursorManager
│   ├── video.py               # VideoManager
│   ├── screenshot.py          # ScreenshotManager
│   ├── selectors.py           # SelectorManager
│   ├── session.py             # SessionManager
│   └── yaml_parser.py         # YAMLParser base
│
├── odoo/                      # Extensão Odoo
│   ├── base.py                # OdooTestBase
│   ├── specific/               # Ações muito específicas do Odoo
│   │   ├── __init__.py
│   │   ├── logo.py            # LogoNavigator
│   │   └── filters.py         # FilterHelper
│   ├── auth.py                # Autenticação Odoo
│   ├── wait.py                # Esperas Odoo
│   ├── navigation.py          # Navegação Odoo
│   ├── forms.py               # Forms Odoo
│   ├── crud.py                # CRUD Odoo
│   ├── text_interactions.py   # Interações de texto Odoo
│   ├── fields/                # Campos Odoo
│   │   ├── __init__.py
│   │   ├── field_helper.py
│   │   ├── basic_fields.py
│   │   ├── relational_fields.py
│   │   └── special_fields.py
│   ├── views/                 # Views Odoo
│   │   ├── __init__.py
│   │   ├── view_helper.py
│   │   ├── view_switcher.py
│   │   ├── list_view.py
│   │   └── form_view.py
│   ├── yaml_parser/           # YAML Parser Odoo
│   │   ├── __init__.py
│   │   ├── yaml_parser.py
│   │   ├── action_parser.py
│   │   ├── action_validator.py
│   │   └── step_executor.py
│   ├── menus.py               # MenuNavigator
│   ├── wizards.py             # WizardHelper
│   ├── workflows.py           # WorkflowHelper
│   ├── selectors.py           # Selectors Odoo
│   └── version_detector.py    # Version detection
│
└── forgeerp/                  # Extensão ForgeERP (futuro)
    └── ...
```

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    SimpleTestBase                       │
│  (Core - Funcionalidades genéricas)                     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ CursorManager│  │VideoManager   │  │ScreenshotMgr │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │InteractionMx │  │NavigationMx  │  │FormsMixin    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ extends
                          │
┌─────────────────────────────────────────────────────────┐
│                    OdooTestBase                         │
│  (Extensão Odoo - Funcionalidades específicas)          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │OdooAuthMixin │  │OdooWaitMixin │  │OdooNavMixin  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │FieldHelper   │  │ViewHelper    │  │MenuNavigator│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │LogoNavigator │  │FilterHelper  │                     │
│  │(specific/)   │  │(specific/)   │                     │
│  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## Fluxo de Dependências

```
core/
  ├── base.py (SimpleTestBase)
  │   └── usa → managers (CursorManager, VideoManager, etc)
  │   └── usa → mixins (InteractionMixin, NavigationMixin, etc)
  │
  └── extensions/
      └── define → interfaces (IExtensionAuth, IExtensionWait, etc)

odoo/
  ├── base.py (OdooTestBase)
  │   └── extends → SimpleTestBase
  │   └── usa → mixins Odoo (OdooAuthMixin, OdooWaitMixin, etc)
  │   └── usa → helpers Odoo (FieldHelper, ViewHelper, etc)
  │
  └── specific/
      └── LogoNavigator, FilterHelper (ações muito específicas)
```

## Como Adicionar uma Nova Extensão

### Passo 1: Criar estrutura básica
```python
# playwright_simple/nova_extensao/__init__.py
from .base import NovaExtensaoTestBase

__all__ = ['NovaExtensaoTestBase']
```

### Passo 2: Criar classe base
```python
# playwright_simple/nova_extensao/base.py
from ..core.base import SimpleTestBase
from ..core.config import TestConfig
from typing import Optional
from playwright.async_api import Page

class NovaExtensaoTestBase(SimpleTestBase):
    """Base class for NovaExtensao tests."""
    
    def __init__(
        self,
        page: Page,
        config: Optional[TestConfig] = None,
        test_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(page, config, test_name, **kwargs)
        # Inicializar helpers específicos
```

### Passo 3: Implementar interfaces (opcional)
```python
# Se precisar de autenticação específica
from ..core.extensions import IExtensionAuth

class NovaExtensaoAuthMixin:
    async def login(self, username: str, password: str, **kwargs):
        # Implementação específica
        pass
```

### Passo 4: Adicionar funcionalidades específicas
```python
# Adicionar métodos específicos da extensão
class NovaExtensaoTestBase(SimpleTestBase, NovaExtensaoAuthMixin):
    async def acao_especifica(self):
        # Implementação
        pass
```

## Decisões de Design

### 1. Dependency Injection
**Decisão**: Implementar DI em `SimpleTestBase` e `OdooTestBase`

**Justificativa**: 
- Facilita testes (mock de dependências)
- Permite customização
- Mantém compatibilidade (defaults)

**Implementação**:
```python
def __init__(
    self,
    page: Page,
    config: Optional[TestConfig] = None,
    cursor_manager: Optional[CursorManager] = None,
    # ... outros managers opcionais
):
    self.cursor_manager = cursor_manager or CursorManager(...)
```

### 2. Módulo `odoo/specific/`
**Decisão**: Criar módulo para ações muito específicas

**Justificativa**:
- Separa ações muito específicas de funcionalidades gerais
- Facilita manutenção
- Evita poluir módulos principais

**Exemplos**:
- `LogoNavigator` - clique no logo Odoo
- `FilterHelper` - menu de filtros Odoo

### 3. Interfaces de Extensão
**Decisão**: Criar interfaces em `core/extensions/`

**Justificativa**:
- Define contratos claros
- Facilita implementação de novas extensões
- Documenta expectativas

**Interfaces**:
- `IExtensionAuth` - autenticação
- `IExtensionWait` - esperas
- `IExtensionNavigation` - navegação

## Boas Práticas

### 1. Separação de Responsabilidades
- Core: apenas funcionalidades genéricas
- Extensões: apenas funcionalidades específicas
- Specific: apenas ações muito específicas

### 2. Dependency Injection
- Sempre aceitar dependências opcionais
- Criar defaults se não fornecidas
- Documentar dependências

### 3. Type Hints
- Adicionar type hints em todos os métodos públicos
- Usar `Optional` para parâmetros opcionais
- Usar `Protocol` para interfaces

### 4. Docstrings
- Seguir Google/NumPy style
- Documentar parâmetros, retornos e exceções
- Incluir exemplos de uso

## Referências

- `ARCHITECTURE_ANALYSIS.md` - Análise detalhada
- `CORE_VS_ODOO_MATRIX.md` - Matriz de decisão
- `REFACTORING_PLAN.md` - Plano de refatoração
- `REFACTORING_STATUS.md` - Status atual

