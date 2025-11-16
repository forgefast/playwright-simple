# Matriz de Decisão: Core vs Odoo

## Princípios de Decisão

1. **Core**: Funcionalidades que funcionam para qualquer aplicação web
2. **Odoo**: Funcionalidades que dependem de estrutura/API específica do Odoo

## Matriz Completa

| Funcionalidade | Localização Atual | Decisão | Justificativa | Ação |
|---------------|-------------------|---------|---------------|------|
| **Autenticação** |
| Login genérico (username/password) | `core/auth.py` | ✅ Core | Funciona para qualquer web app | Manter |
| Login Odoo (com database selector) | `odoo/auth.py` | ✅ Odoo | Específico do Odoo | Manter |
| Logout genérico | Não existe | ⚠️ Core | Deveria existir em core | Criar se necessário |
| Logout Odoo | `odoo/auth.py` | ✅ Odoo | Específico do Odoo | Manter |
| **Formulários** |
| fill_form (por selectors) | `core/forms.py` | ✅ Core | Genérico | Manter |
| fill_by_label (HTML padrão) | `core/forms.py` | ✅ Core | Busca por label HTML padrão | Manter |
| fill (com detecção Odoo) | `odoo/forms.py` | ✅ Odoo | Usa FieldHelper Odoo | Manter |
| select_by_label (HTML padrão) | `core/forms.py` | ✅ Core | Genérico | Manter |
| **Esperas** |
| wait, wait_for, wait_for_url | `core/wait.py` | ✅ Core | Genérico | Manter |
| wait_until_ready (detectores Odoo) | `odoo/wait.py` | ✅ Odoo | Detecta .o_loading, etc | Manter |
| **Navegação** |
| go_to (URL), back, forward, refresh | `core/navigation.py` | ✅ Core | Genérico | Manter |
| navigate (menu genérico) | `core/navigation.py` | ✅ Core | Menu genérico | Manter |
| go_to_menu (menus Odoo) | `odoo/navigation.py` | ✅ Odoo | MenuNavigator Odoo | Manter |
| go_to_dashboard (Odoo) | `odoo/navigation.py` | ✅ Odoo | Dashboard Odoo | Manter |
| **Interações** |
| click, type, hover, drag, scroll | `core/interactions.py` | ✅ Core | Genérico | Manter |
| click_button (com wizard detection) | `odoo/forms.py` | ✅ Odoo | Detecta wizard Odoo | Manter |
| **Campos** |
| Campos genéricos | Não existe | ⚠️ Core | Deveria ter helpers genéricos | Opcional |
| FieldHelper (many2one, etc) | `odoo/fields/` | ✅ Odoo | Específico do Odoo | Manter |
| **Views** |
| ViewHelper (list, form, kanban) | `odoo/views/` | ✅ Odoo | Específico do Odoo | Manter |
| **Wizards** |
| WizardHelper | `odoo/wizards.py` | ✅ Odoo | Específico do Odoo | Manter |
| **Workflows** |
| WorkflowHelper | `odoo/workflows.py` | ✅ Odoo | Específico do Odoo | Manter |
| **CRUD** |
| CRUD genérico | Não existe | ⚠️ Core | Poderia ter helpers genéricos | Opcional |
| OdooCRUDMixin | `odoo/crud.py` | ✅ Odoo | Específico do Odoo | Manter |
| **YAML Parser** |
| YAMLParser base | `core/yaml_parser.py` | ✅ Core | Genérico | Manter |
| OdooYAMLParser | `odoo/yaml_parser/` | ✅ Odoo | Ações Odoo-específicas | Manter |
| **Selectors** |
| SelectorManager genérico | `core/selectors.py` | ✅ Core | Genérico | Manter |
| Selectors Odoo | `odoo/selectors.py` | ✅ Odoo | Selectors Odoo | Manter |
| **Version Detection** |
| detect_version, detect_edition | `odoo/version_detector.py` | ✅ Odoo | Específico do Odoo | Manter |

## Funcionalidades Compartilhadas que Precisam de Abstração

### Nenhuma identificada
- Core e Odoo estão bem separados
- Odoo usa composição de funcionalidades core quando apropriado
- Não há necessidade de interfaces de extensão no momento

## Ações Recomendadas

### Alta Prioridade
1. ✅ Verificar que core não tem lógica Odoo (CONCLUÍDO - não tem)
2. ✅ Verificar que odoo não tem código genérico no lugar errado (CONCLUÍDO - não tem)
3. Criar `odoo/specific/` para ações muito específicas (logo, filtros)

### Média Prioridade
1. Criar interfaces de extensão (opcional, para facilitar novas extensões)
2. Melhorar type hints e docstrings
3. Aplicar Dependency Injection

### Baixa Prioridade
1. Criar helpers genéricos de CRUD (se necessário)
2. Criar helpers genéricos de campos (se necessário)

## Auditoria Recente (2025-01-XX)

### Verificação Core
- ✅ `core/interactions.py` - Sem referências a Odoo
- ✅ `core/navigation.py` - Sem referências a Odoo
- ✅ `core/forms.py` - Sem referências a Odoo
- ✅ `core/helpers.py` - Sem referências a Odoo

### Verificação Odoo
- ✅ `odoo/base.py` - Herda corretamente de `SimpleTestBase`, usa Dependency Injection
- ✅ `odoo/navigation.py` - Usa `super().go_to()` para funcionalidades genéricas
- ✅ `odoo/forms.py` - Usa `field.fill_field()` que delega para core quando apropriado

### Melhorias Recentes
- ✅ Logging detalhado adicionado em `core/interactions.py` e `core/navigation.py`
- ✅ Detecção de mudança de estado implementada em `core/helpers.py`
- ✅ Logs diferenciados para passos estáticos em `odoo/yaml_parser/action_validator.py`

## Conclusão

A separação atual está **correta e validada**. Não há necessidade de mover código entre core e odoo. As melhorias devem focar em:
1. Organização interna (módulo `odoo/specific/`)
2. Qualidade de código (type hints, docstrings)
3. Arquitetura (Dependency Injection, interfaces)
4. Logging e observabilidade (já implementado)

