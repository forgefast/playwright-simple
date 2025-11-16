# Validação FASE 6: Extensão Odoo - Ações Básicas

**Fase**: 6  
**Status**: ✅ Completa  
**Última Validação**: [A ser preenchido]

---

## 1. O que Deveria Funcionar

### Funcionalidades Objetivas

1. **Login Odoo**
   - Método `login()` existe em `OdooTestBase`
   - Aceita usuário e senha
   - Navega para página de login
   - Preenche campos e submete formulário

2. **Navegação por Menu**
   - Método `go_to()` funciona com menus Odoo
   - Suporta navegação hierárquica
   - Detecta menus corretamente

3. **Preenchimento de Campos**
   - Método `fill()` funciona com campos Odoo
   - Suporta diferentes tipos de campos
   - Detecta campos por label/placeholder

4. **Clique em Elementos**
   - Método `click()` funciona com elementos Odoo
   - Suporta botões, links, menus
   - Detecta elementos corretamente

5. **Integração com Core**
   - Usa composição do core (não duplica código)
   - Separação clara: core genérico vs extensão Odoo
   - Testes específicos para Odoo

### Critérios de Sucesso Mensuráveis

- ✅ Classe `OdooTestBase` existe
- ✅ Métodos `login()`, `go_to()`, `fill()`, `click()` existem
- ✅ Testes unitários passando
- ✅ Integração com core funciona
- ✅ Separação de responsabilidades clara

---

## 2. Como Você Valida (Manual)

### Passo 1: Verificar Classe OdooTestBase

```python
from playwright_simple.odoo import OdooTestBase

# Verificar que classe existe
assert OdooTestBase is not None
```

**Resultado Esperado**: Classe pode ser importada.

### Passo 2: Testar Login

```python
# Criar instância
test = OdooTestBase(page, config)

# Testar login
await test.login("admin", "admin")
```

**Resultado Esperado**: Login funciona (em ambiente Odoo real).

### Passo 3: Testar Navegação

```python
# Testar navegação
await test.go_to("Vendas", "Pedidos", "Pedidos de Venda")
```

**Resultado Esperado**: Navegação funciona.

### Passo 4: Testar Preenchimento

```python
# Testar preenchimento
await test.fill("Cliente", "Test Company")
```

**Resultado Esperado**: Campo é preenchido.

### Como Identificar Problemas

- **Classe não existe**: Verificar import
- **Métodos não funcionam**: Verificar implementação
- **Testes falham**: Verificar ambiente Odoo
- **Integração quebrada**: Verificar composição do core

---

## 3. Como Eu Valido (Automático)

### Scripts de Validação

O script `validation/scripts/validate_phase6.py` executa:

1. **Verificação de Classe**
   - Verifica que `OdooTestBase` existe
   - Verifica que pode ser importada
   - Verifica métodos principais

2. **Verificação de Métodos**
   - Verifica que `login()` existe
   - Verifica que `go_to()` existe
   - Verifica que `fill()` existe
   - Verifica que `click()` existe

3. **Verificação de Testes**
   - Verifica que testes existem
   - Executa testes unitários
   - Verifica taxa de sucesso

4. **Verificação de Integração**
   - Verifica que usa core genérico
   - Verifica separação de responsabilidades

### Métricas a Verificar

- **Classe existe**: Sim/Não
- **Métodos implementados**: >= 4
- **Testes passando**: >= 80%
- **Integração com core**: Funciona

### Critérios de Pass/Fail

- ✅ **PASSA**: Classe existe, métodos funcionam, testes passam
- ❌ **FALHA**: Classe não existe, métodos faltando, testes falham

---

## 4. Testes Automatizados

### Testes Unitários

**Arquivo**: `validation/tests/test_phase6_validation.py`

#### test_odoo_test_base_exists()

```python
def test_odoo_test_base_exists():
    """Verifica que OdooTestBase pode ser importado."""
    from playwright_simple.odoo import OdooTestBase
    assert OdooTestBase is not None
```

**Critério de Pass**: Classe pode ser importada.

#### test_odoo_methods_exist()

```python
def test_odoo_methods_exist():
    """Verifica que métodos principais existem."""
    from playwright_simple.odoo import OdooTestBase
    
    required_methods = ['login', 'go_to', 'fill', 'click']
    for method in required_methods:
        assert hasattr(OdooTestBase, method), f"Método {method} não existe"
```

**Critério de Pass**: Todos os métodos existem.

#### test_odoo_inherits_core()

```python
def test_odoo_inherits_core():
    """Verifica que OdooTestBase herda do core."""
    from playwright_simple.odoo import OdooTestBase
    from playwright_simple import SimpleTestBase
    
    assert issubclass(OdooTestBase, SimpleTestBase), "OdooTestBase deve herdar de SimpleTestBase"
```

**Critério de Pass**: Herança está correta.

### Testes E2E

Não aplicável para validação básica (requer ambiente Odoo).

### Testes de Regressão

Verificam que métodos continuam funcionando.

### Como Executar

```bash
# Executar testes unitários
pytest validation/tests/test_phase6_validation.py -v

# Executar script de validação
python validation/scripts/validate_phase6.py

# Executar validação completa
python validation/scripts/validate_phase.py phase6
```

---

## 5. Garantia de Funcionamento Futuro

### Testes de Regressão

- Testes executam em cada commit
- CI/CD verifica extensão Odoo
- Script de validação executa automaticamente

### CI/CD Integration

Workflow executa testes da extensão Odoo.

### Monitoramento Contínuo

- Script verifica que métodos não foram removidos
- Alerta se interface mudar
- Sugere atualizações quando necessário

---

## 6. Relatório de Validação

### Métricas Coletadas

- **Classe existe**: Sim/Não
- **Métodos implementados**: [número]
- **Testes passando**: [número]/[total]
- **Taxa de sucesso**: [%]

### Status Final

- ✅ **PASSOU**: Extensão Odoo funciona corretamente
- ❌ **FALHOU**: [Lista de problemas]

### Próximos Passos

Se validação passou:
- Prosseguir para FASE 7

Se validação falhou:
- Corrigir problemas identificados
- Re-executar validação
- Documentar correções

---

**Última Atualização**: [Data]  
**Validador**: [Nome]

