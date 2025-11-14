# Extensão Odoo - YAML Actions

Esta pasta contém todas as ações Odoo implementadas em YAML usando apenas ações core.

## Princípio: YAML-First

Todas as funcionalidades Odoo são implementadas como YAMLs que usam apenas ações core (`click`, `type`, `press`, etc.). Isso torna a extensão:
- ✅ **Aderível**: Fácil de entender e modificar
- ✅ **Composável**: YAMLs podem usar outros YAMLs
- ✅ **Extensível**: Fácil adicionar novas funcionalidades
- ✅ **Sem Python**: Não precisa escrever código Python para funcionalidades comuns

## Ações Disponíveis

### Autenticação
- `login.yaml` - Login no Odoo
  - Parâmetros: `login`, `password`, `database`, `otp` (opcional)

### Navegação
- `navigate_menu.yaml` - Navegar por menu hierárquico
  - Parâmetros: `menu_path` (array ou string com ">")
  - Exemplo: `menu_path: ["Vendas", "Pedidos"]` ou `menu_path: "Vendas > Pedidos"`

### Busca e Filtros
- `search.yaml` - Buscar registros
  - Parâmetros: `search_text`, `wait_for_results` (opcional)
- `filter_by.yaml` - Aplicar filtro
  - Parâmetros: `filter_text`, `filter_button` (opcional)

### CRUD (Create, Read, Update, Delete)
- `create_record.yaml` - Criar novo registro
  - Parâmetros: `fields` (dict com campos)
- `open_record.yaml` - Abrir registro existente
  - Parâmetros: `record_text` (texto do registro)
- `edit_record.yaml` - Editar registro
  - Parâmetros: `record_text` (opcional), `fields` (dict)
- `delete_record.yaml` - Deletar registro
  - Parâmetros: `confirm` (opcional, default true)

### Formulários
- `fill_field.yaml` - Preencher campo específico
  - Parâmetros: `field_label`, `field_value`
- `click_button.yaml` - Clicar em botão
  - Parâmetros: `button_text`, `context` (opcional)

### Views
- `switch_view.yaml` - Trocar entre List/Form/Kanban
  - Parâmetros: `view_type` (list, form, kanban)

## Como Usar

### Exemplo 1: Login e Navegação
```yaml
steps:
  - action: login
    login: admin@example.com
    password: admin
    database: devel
  
  - action: navigate_menu
    menu_path: ["Vendas", "Pedidos"]
```

### Exemplo 2: Criar Registro
```yaml
steps:
  - action: create_record
    fields:
      Cliente: "João Silva"
      Data: "01/01/2024"
      Produto: "Produto 1"
      Quantidade: 10
```

### Exemplo 3: Buscar e Editar
```yaml
steps:
  - action: search
    search_text: "João Silva"
  
  - action: edit_record
    record_text: "João Silva"
    fields:
      - label: "Quantidade"
        value: "20"
```

### Exemplo 4: Composição
```yaml
steps:
  - compose: odoo/login.yaml
    params:
      login: admin@example.com
      password: admin
  
  - compose: odoo/navigate_menu.yaml
    params:
      menu_path: ["Vendas", "Pedidos"]
  
  - compose: odoo/create_record.yaml
    params:
      fields:
        - label: "Cliente"
          value: "Teste"
```

## Adicionando Novas Ações

Para adicionar uma nova ação Odoo:

1. Crie um arquivo YAML em `examples/odoo/`
2. Use apenas ações core (`click`, `type`, `press`, etc.)
3. Documente os parâmetros no cabeçalho
4. Use `compose` para reutilizar outras ações se necessário

Exemplo:
```yaml
name: Minha Nova Ação
description: Descrição da ação

# Recebe parâmetros: param1, param2

steps:
  - action: click
    text: "{{ param1 }}"
  - action: type
    text: "{{ param2 }}"
```

## Vantagens

1. **Sem Python**: Funcionalidades comuns não precisam de código Python
2. **Fácil de Manter**: YAML é legível e fácil de modificar
3. **Composável**: YAMLs podem usar outros YAMLs
4. **Extensível**: Fácil adicionar novas funcionalidades
5. **Testável**: Cada YAML pode ser testado independentemente

