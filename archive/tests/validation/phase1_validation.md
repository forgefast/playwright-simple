# Validação FASE 1: Core Básico - Interações Genéricas

**Fase**: 1  
**Status**: ✅ Completa  
**Última Validação**: [A ser preenchido]

---

## 1. O que Deveria Funcionar

### Funcionalidades Objetivas

1. **click()**
   - Clica em elementos por texto ou seletor
   - Retorna sem erros quando elemento existe
   - Lança exceção quando elemento não existe
   - Tempo de execução < 2 segundos

2. **type()**
   - Digita texto em campos
   - Limpa campo antes de digitar
   - Suporta delay entre caracteres
   - Tempo de execução < 1 segundo por caractere

3. **fill()**
   - Preenche campos com valores
   - Limpa campo antes de preencher
   - Funciona com inputs, textareas, selects
   - Tempo de execução < 1 segundo

4. **go_to()**
   - Navega para URLs absolutas
   - Navega para URLs relativas (com base_url)
   - Aguarda navegação completar
   - Tempo de execução < 5 segundos

5. **wait() / wait_for()**
   - wait() aguarda tempo especificado
   - wait_for() aguarda elemento aparecer
   - Respeita timeout configurado
   - Tempo de execução conforme especificado

6. **assert_text() / assert_visible()**
   - assert_text() verifica texto em elemento
   - assert_visible() verifica visibilidade
   - Lança exceção quando assertion falha
   - Tempo de execução < 1 segundo

### Critérios de Sucesso Mensuráveis

- ✅ Todas as ações executam sem erros em páginas mock
- ✅ Tempos de execução dentro dos thresholds
- ✅ Erros são lançados quando apropriado
- ✅ Testes unitários passam (100%)
- ✅ Testes E2E passam (100%)

---

## 2. Como Você Valida (Manual)

### Passo 1: Testar click()

```bash
# Criar teste YAML
cat > test_click.yaml << 'EOF'
name: Test Click
steps:
  - action: go_to
    url: data:text/html,<html><body><button id="btn">Click Me</button></body></html>
  - action: click
    selector: "#btn"
EOF

# Executar teste
playwright-simple run test_click.yaml
```

**Resultado Esperado**: Teste executa sem erros, botão é clicado.

### Passo 2: Testar type()

```bash
# Criar teste YAML
cat > test_type.yaml << 'EOF'
name: Test Type
steps:
  - action: go_to
    url: data:text/html,<html><body><input id="input" type="text" /></body></html>
  - action: type
    selector: "#input"
    text: "Hello World"
EOF

# Executar teste
playwright-simple run test_type.yaml
```

**Resultado Esperado**: Texto é digitado no campo.

### Passo 3: Testar fill()

```bash
# Criar teste YAML
cat > test_fill.yaml << 'EOF'
name: Test Fill
steps:
  - action: go_to
    url: data:text/html,<html><body><input id="input" type="text" /></body></html>
  - action: fill
    selector: "#input"
    text: "Filled Value"
EOF

# Executar teste
playwright-simple run test_fill.yaml
```

**Resultado Esperado**: Campo é preenchido com valor.

### Passo 4: Testar go_to()

```bash
# Criar teste YAML
cat > test_goto.yaml << 'EOF'
name: Test Go To
steps:
  - action: go_to
    url: https://example.com
EOF

# Executar teste
playwright-simple run test_goto.yaml
```

**Resultado Esperado**: Navega para URL especificada.

### Passo 5: Testar wait()

```bash
# Criar teste YAML
cat > test_wait.yaml << 'EOF'
name: Test Wait
steps:
  - action: wait
    seconds: 1
EOF

# Executar teste e medir tempo
time playwright-simple run test_wait.yaml
```

**Resultado Esperado**: Aguarda aproximadamente 1 segundo.

### Passo 6: Testar assert_visible()

```bash
# Criar teste YAML
cat > test_assert.yaml << 'EOF'
name: Test Assert
steps:
  - action: go_to
    url: data:text/html,<html><body><div id="elem">Visible</div></body></html>
  - action: assert_visible
    selector: "#elem"
EOF

# Executar teste
playwright-simple run test_assert.yaml
```

**Resultado Esperado**: Assertion passa, elemento é visível.

### Como Identificar Problemas

- **Ação não executa**: Verificar seletor/elemento
- **Erro inesperado**: Verificar logs e stack trace
- **Tempo muito longo**: Verificar timeouts e waits
- **Assertion falha**: Verificar se elemento existe e está visível

---

## 3. Como Eu Valido (Automático)

### Scripts de Validação

O script `validation/scripts/validate_phase1.py` executa:

1. **Teste de click()**
   - Cria página mock com botão
   - Executa click()
   - Verifica que botão foi clicado
   - Mede tempo de execução

2. **Teste de type()**
   - Cria página mock com input
   - Executa type()
   - Verifica que texto foi digitado
   - Mede tempo de execução

3. **Teste de fill()**
   - Cria página mock com input
   - Executa fill()
   - Verifica que valor foi preenchido
   - Mede tempo de execução

4. **Teste de go_to()**
   - Executa go_to() com URL mock
   - Verifica que navegação ocorreu
   - Mede tempo de execução

5. **Teste de wait()**
   - Executa wait() com tempo conhecido
   - Mede tempo real de execução
   - Verifica que está dentro da tolerância

6. **Teste de assertions**
   - Cria página mock com elementos
   - Executa assert_text() e assert_visible()
   - Verifica que assertions passam
   - Testa que falham quando apropriado

### Métricas a Verificar

- **Tempo médio de click()**: < 2s
- **Tempo médio de type()**: < 1s por caractere
- **Tempo médio de fill()**: < 1s
- **Tempo médio de go_to()**: < 5s
- **Taxa de sucesso**: 100%
- **Taxa de erro correta**: 100% (quando elemento não existe)

### Critérios de Pass/Fail

- ✅ **PASSA**: Todos os checks passam e tempos estão dentro dos thresholds
- ❌ **FALHA**: Qualquer check falha ou tempo excede threshold

---

## 4. Testes Automatizados

### Testes Unitários

**Arquivo**: `validation/tests/test_phase1_validation.py`

#### test_click_action()

```python
@pytest.mark.asyncio
async def test_click_action():
    """Testa que click() funciona corretamente."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content('<html><body><button id="btn">Click</button></body></html>')
        
        config = TestConfig(base_url="about:blank")
        test = SimpleTestBase(page, config)
        
        start_time = time.time()
        await test.click("#btn")
        elapsed = time.time() - start_time
        
        assert elapsed < 2.0, f"click() muito lento: {elapsed}s"
        
        await context.close()
        await browser.close()
```

**Critério de Pass**: click() executa em < 2s.

#### test_type_action()

```python
@pytest.mark.asyncio
async def test_type_action():
    """Testa que type() funciona corretamente."""
    # Similar ao test_click_action mas testa type()
    # Verifica que texto foi digitado
    # Verifica tempo < 1s por caractere
```

**Critério de Pass**: type() executa e texto é digitado.

#### test_fill_action()

```python
@pytest.mark.asyncio
async def test_fill_action():
    """Testa que fill() funciona corretamente."""
    # Similar mas testa fill()
    # Verifica que valor foi preenchido
    # Verifica tempo < 1s
```

**Critério de Pass**: fill() executa e valor é preenchido.

#### test_go_to_action()

```python
@pytest.mark.asyncio
async def test_go_to_action():
    """Testa que go_to() funciona corretamente."""
    # Testa navegação
    # Verifica que URL mudou
    # Verifica tempo < 5s
```

**Critério de Pass**: go_to() navega corretamente.

#### test_wait_actions()

```python
@pytest.mark.asyncio
async def test_wait_actions():
    """Testa que wait() e wait_for() funcionam."""
    # Testa wait() com tempo conhecido
    # Verifica que tempo real está dentro da tolerância
    # Testa wait_for() com elemento que aparece
```

**Critério de Pass**: wait() e wait_for() funcionam corretamente.

#### test_assert_actions()

```python
@pytest.mark.asyncio
async def test_assert_actions():
    """Testa que assertions funcionam."""
    # Testa assert_text() com texto existente
    # Testa assert_visible() com elemento visível
    # Testa que falham quando apropriado
```

**Critério de Pass**: Assertions funcionam corretamente.

#### test_e2e_basic_flow()

```python
@pytest.mark.asyncio
async def test_e2e_basic_flow():
    """Teste E2E completo com todas as ações."""
    # Cria página mock complexa
    # Executa fluxo completo: go_to -> click -> type -> fill -> assert
    # Verifica que tudo funciona
```

**Critério de Pass**: Fluxo E2E completo funciona.

### Testes E2E

Já existem em `tests/e2e/test_core_e2e.py` - serão reutilizados.

### Testes de Regressão

Verificam que ações não quebram em mudanças futuras.

### Como Executar

```bash
# Executar testes unitários
pytest validation/tests/test_phase1_validation.py -v

# Executar script de validação
python validation/scripts/validate_phase1.py

# Executar validação completa
python validation/scripts/validate_phase.py phase1
```

---

## 5. Garantia de Funcionamento Futuro

### Testes de Regressão

- Testes executam em cada commit
- CI/CD verifica ações em cada PR
- Script de validação executa automaticamente

### CI/CD Integration

Workflow executa testes de validação automaticamente.

### Monitoramento Contínuo

- Script verifica tempos de execução
- Alerta se performance degradar
- Sugere otimizações quando necessário

---

## 6. Relatório de Validação

### Métricas Coletadas

- **Ações testadas**: [número]
- **Taxa de sucesso**: [%]
- **Tempo médio por ação**: [segundos]
- **Tempo total de validação**: [segundos]

### Status Final

- ✅ **PASSOU**: Todas as ações funcionam e tempos estão OK
- ❌ **FALHOU**: [Lista de ações que falharam]

### Próximos Passos

Se validação passou:
- Prosseguir para FASE 6

Se validação falhou:
- Corrigir ações que falharam
- Re-executar validação
- Documentar correções

---

**Última Atualização**: [Data]  
**Validador**: [Nome]

