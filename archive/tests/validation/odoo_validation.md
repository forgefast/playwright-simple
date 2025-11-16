# Validação Extensão Odoo

**Status**: Em desenvolvimento  
**Última Validação**: [A ser preenchido]

---

## 1. O que Deveria Funcionar

### Funcionalidades Objetivas

#### 1.1 Autenticação
- `login(username, password, database)` - Login no Odoo
- `logout()` - Logout do sistema
- Métodos retornam self para chaining
- Suporta database opcional

#### 1.2 Navegação
- `go_to(menu_path)` - Navegação por menu (ex: "Vendas > Pedidos")
- `go_to_menu(menu, submenu)` - Navegação direta por menu
- `go_to_dashboard()` - Ir para dashboard
- `go_to_home()` - Ir para home
- `go_to_model(model_name, view_type)` - Ir para modelo específico
- Suporta URLs, menu paths, e texto user-friendly

#### 1.3 Interações Básicas
- `click(text/selector)` - Clicar em elemento
- `click_button(button_text, context)` - Clicar em botão específico
- `fill(field_label, value)` - Preencher campo (formato "Label = Valor")
- `type(text, into)` - Digitar texto em campo
- Métodos retornam self para chaining

#### 1.4 Busca e Filtros
- `search(search_text)` - Buscar registros
- `open_filters()` - Abrir menu de filtros
- `search_records(search_text)` - Buscar e retornar registros
- Retorna lista de registros encontrados

#### 1.5 CRUD
- `create_record(model_name, fields)` - Criar registro
- `open_record(record_text, position)` - Abrir registro
- `search_and_open(model_name, search_text)` - Buscar e abrir registro
- `add_line(line_text)` - Adicionar linha em formulário
- `assert_record_exists(model_name, search_text)` - Verificar existência

#### 1.6 Campos Especiais
- `fill_many2one(field_name, value)` - Preencher campo many2one
- `fill_many2many(field_name, values)` - Preencher campo many2many
- `fill_one2many(field_name, records)` - Preencher campo one2many
- `fill_char/integer/float/date/datetime/html` - Campos básicos
- `fill_field(label, value)` - Preenchimento automático por tipo

#### 1.7 Views
- `switch_view(view_type)` - Trocar entre List/Form/Kanban
- `search_records(search_text)` - Buscar na view

#### 1.8 Wizards
- `fill_wizard_form(fields)` - Preencher formulário de wizard
- `click_action_button(button_text)` - Clicar em botão de ação

#### 1.9 YAML Parser
- `ActionParser.parse_odoo_action()` - Parser de ações YAML
- `ActionValidator.validate()` - Validação de ações
- `StepExecutor.execute()` - Execução de steps
- Suporta setup, steps, teardown
- Suporta herança (extends) e composição (includes)

### Critérios de Sucesso Mensuráveis

- ✅ Todos os métodos existem e são callable
- ✅ Métodos retornam self para chaining
- ✅ Testes unitários passam (100%)
- ✅ Scripts de validação passam
- ✅ Cobertura de testes > 80%

---

## 2. Como Você Valida (Manual)

### Passo 1: Executar Testes Unitários

```bash
# Executar todos os testes Odoo
pytest playwright-simple/tests/odoo/validation/ -v

# Executar testes específicos
pytest playwright-simple/tests/odoo/validation/test_odoo_auth.py -v
pytest playwright-simple/tests/odoo/validation/test_odoo_navigation.py -v
pytest playwright-simple/tests/odoo/validation/test_odoo_interactions.py -v
```

**Resultado Esperado**: Todos os testes passam.

### Passo 2: Executar Scripts de Validação

```bash
# Validar autenticação
python playwright-simple/validation/scripts/validate_odoo_auth.py

# Validar navegação
python playwright-simple/validation/scripts/validate_odoo_navigation.py

# Validar ações
python playwright-simple/validation/scripts/validate_odoo_actions.py
```

**Resultado Esperado**: Todos os scripts passam sem erros.

### Passo 3: Testar com Odoo Real (Opcional)

```bash
# Garantir que Odoo está rodando
cd doodba-18-racco && docker compose up -d

# Executar testes de integração
pytest playwright-simple/tests/odoo/integration/ -v
```

**Resultado Esperado**: Testes de integração passam com Odoo real.

---

## 3. Como Eu Valido (Automático)

### Scripts de Validação

Scripts em `validation/scripts/`:
- `validate_odoo_auth.py` - Valida autenticação
- `validate_odoo_navigation.py` - Valida navegação
- `validate_odoo_actions.py` - Valida todas as ações

### Testes Unitários

Testes em `tests/odoo/validation/`:
- `test_odoo_auth.py` - Testes de autenticação
- `test_odoo_navigation.py` - Testes de navegação
- `test_odoo_interactions.py` - Testes de interações básicas
- `test_odoo_search.py` - Testes de busca e filtros
- `test_odoo_crud.py` - Testes de CRUD
- `test_odoo_fields.py` - Testes de campos especiais
- `test_odoo_yaml_parser.py` - Testes de YAML parser

### Métricas a Verificar

- **Métodos testados**: >= 30
- **Taxa de sucesso**: 100%
- **Cobertura de código**: > 80%
- **Tempo de execução**: < 5 minutos

### Critérios de Pass/Fail

- ✅ **PASSA**: Todos os testes passam e scripts executam sem erros
- ❌ **FALHA**: Qualquer teste falha ou script retorna erro

---

## 4. Testes Automatizados

### Testes Unitários

Cada arquivo de teste segue o padrão TDD:
1. Testa existência do método
2. Testa que método é callable
3. Testa retorno self para chaining
4. Testa parâmetros aceitos
5. Testa casos de erro (quando aplicável)

### Testes de Integração

Testes em `tests/odoo/integration/` (a criar):
- Testes com Odoo real
- Testes de fluxos completos
- Testes de performance

### Como Executar

```bash
# Executar todos os testes
pytest playwright-simple/tests/odoo/ -v

# Executar com cobertura
pytest playwright-simple/tests/odoo/ --cov=playwright_simple.odoo --cov-report=html

# Executar scripts de validação
python playwright-simple/validation/scripts/validate_odoo_*.py
```

---

## 5. Garantia de Funcionamento Futuro

### Testes de Regressão

- Testes executam em cada commit
- CI/CD verifica extensão Odoo em cada PR
- Scripts de validação executam automaticamente

### CI/CD Integration

Workflow executa validação de extensão Odoo automaticamente.

### Monitoramento Contínuo

- Scripts verificam métodos disponíveis
- Alerta se métodos forem removidos
- Sugere correções quando necessário

---

## 6. Relatório de Validação

### Métricas Coletadas

- **Métodos testados**: [número]
- **Taxa de sucesso**: [%]
- **Cobertura de código**: [%]
- **Tempo de validação**: [segundos]

### Status Final

- ✅ **PASSOU**: Todos os testes passam
- ❌ **FALHOU**: [Lista de testes que falharam]

### Próximos Passos

Se validação passou:
- Prosseguir para testes de integração
- Adicionar mais casos de teste

Se validação falhou:
- Corrigir métodos que falharam
- Re-executar validação
- Documentar correções

---

## 7. Ordem de Prioridade

1. **Crítico para vídeos**: login, go_to, fill, search, click ✅
2. **Importante**: CRUD, campos especiais ✅
3. **Complementar**: wizards, views avançadas (pendente)

---

**Última Atualização**: [Data]  
**Validador**: [Nome]

