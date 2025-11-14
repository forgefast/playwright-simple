# Validação FASE 0: Preparação e Infraestrutura Base

**Fase**: 0  
**Status**: ✅ Completa  
**Última Validação**: [A ser preenchido]

---

## 1. O que Deveria Funcionar

### Funcionalidades Objetivas

1. **Estrutura de Diretórios**
   - Diretório `tests/unit/core/` existe
   - Diretório `tests/integration/core_yaml/` existe
   - Diretório `tests/e2e/generic/` existe
   - Diretório `playwright_simple/core/recorder/` existe

2. **Configuração pytest**
   - Arquivo `pytest.ini` existe
   - Configuração está correta
   - Testes podem ser coletados com `pytest --collect-only`

3. **CI/CD**
   - Arquivo `.github/workflows/ci.yml` existe
   - Workflow está configurado corretamente
   - Jobs de teste e lint estão definidos

4. **Imports Básicos**
   - `from playwright_simple import SimpleTestBase` funciona
   - `from playwright_simple.core.yaml_parser import YAMLParser` funciona
   - `from playwright_simple import TestConfig` funciona

### Critérios de Sucesso Mensuráveis

- ✅ Todos os diretórios obrigatórios existem
- ✅ `pytest.ini` existe e é válido
- ✅ `.github/workflows/ci.yml` existe e é válido
- ✅ Imports básicos funcionam sem erros
- ✅ `pytest --collect-only` executa sem erros

---

## 2. Como Você Valida (Manual)

### Passo 1: Verificar Estrutura de Diretórios

```bash
# Verificar diretórios obrigatórios
ls -d tests/unit/core
ls -d tests/integration/core_yaml
ls -d tests/e2e/generic
ls -d playwright_simple/core/recorder
```

**Resultado Esperado**: Todos os diretórios devem existir.

### Passo 2: Verificar pytest.ini

```bash
# Verificar se arquivo existe
test -f pytest.ini && echo "✅ pytest.ini existe" || echo "❌ pytest.ini não existe"

# Verificar conteúdo básico
grep -q "testpaths" pytest.ini && echo "✅ testpaths configurado" || echo "❌ testpaths não configurado"
```

**Resultado Esperado**: Arquivo existe e tem configuração básica.

### Passo 3: Verificar CI/CD

```bash
# Verificar se arquivo existe
test -f .github/workflows/ci.yml && echo "✅ CI/CD existe" || echo "❌ CI/CD não existe"

# Verificar se tem jobs de teste
grep -q "test:" .github/workflows/ci.yml && echo "✅ Job de teste existe" || echo "❌ Job de teste não existe"
```

**Resultado Esperado**: Arquivo existe e tem jobs configurados.

### Passo 4: Verificar Imports

```bash
# Testar imports básicos
python3 -c "from playwright_simple import SimpleTestBase; print('✅ SimpleTestBase importado')"
python3 -c "from playwright_simple.core.yaml_parser import YAMLParser; print('✅ YAMLParser importado')"
python3 -c "from playwright_simple import TestConfig; print('✅ TestConfig importado')"
```

**Resultado Esperado**: Todos os imports funcionam sem erros.

### Passo 5: Verificar Coleta de Testes

```bash
# Coletar testes sem executar
pytest --collect-only -q 2>&1 | head -20
```

**Resultado Esperado**: Pytest consegue coletar testes sem erros.

### Como Identificar Problemas

- **Diretório não existe**: Criar diretório faltante
- **pytest.ini não existe**: Criar arquivo com configuração básica
- **CI/CD não existe**: Criar workflow básico
- **Import falha**: Verificar se módulo existe e está acessível
- **Coleta de testes falha**: Verificar configuração do pytest

---

## 3. Como Eu Valido (Automático)

### Scripts de Validação

O script `validation/scripts/validate_phase0.py` executa:

1. **Verificação de Estrutura**
   - Verifica existência de todos os diretórios obrigatórios
   - Retorna erro se algum diretório não existir

2. **Verificação de pytest.ini**
   - Verifica existência do arquivo
   - Verifica configuração básica (testpaths, python_files, etc.)
   - Retorna erro se configuração estiver incorreta

3. **Verificação de CI/CD**
   - Verifica existência do arquivo
   - Valida sintaxe YAML
   - Verifica presença de jobs obrigatórios
   - Retorna erro se houver problemas

4. **Verificação de Imports**
   - Tenta importar módulos básicos
   - Captura erros de import
   - Retorna erro se algum import falhar

5. **Verificação de Coleta de Testes**
   - Executa `pytest --collect-only`
   - Verifica se executa sem erros
   - Retorna erro se coleta falhar

### Métricas a Verificar

- **Número de diretórios encontrados**: Deve ser >= 4
- **Arquivos de configuração encontrados**: Deve ser >= 2
- **Imports bem-sucedidos**: Deve ser >= 3
- **Testes coletados**: Deve ser > 0

### Critérios de Pass/Fail

- ✅ **PASSA**: Todos os checks passam
- ❌ **FALHA**: Qualquer check falha

---

## 4. Testes Automatizados

### Testes Unitários

**Arquivo**: `validation/tests/test_phase0_validation.py`

#### test_structure_exists()

```python
def test_structure_exists():
    """Verifica que estrutura de diretórios existe."""
    required_dirs = [
        "tests/unit/core",
        "tests/integration/core_yaml",
        "tests/e2e/generic",
        "playwright_simple/core/recorder"
    ]
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Diretório {dir_path} não existe"
```

**Critério de Pass**: Todos os diretórios existem.

#### test_pytest_config()

```python
def test_pytest_config():
    """Verifica que pytest.ini existe e está configurado."""
    pytest_ini = Path("pytest.ini")
    assert pytest_ini.exists(), "pytest.ini não existe"
    
    # Verificar configuração básica
    content = pytest_ini.read_text()
    assert "testpaths" in content or "python_files" in content, "pytest.ini sem configuração básica"
```

**Critério de Pass**: Arquivo existe e tem configuração.

#### test_ci_workflow()

```python
def test_ci_workflow():
    """Verifica que CI/CD workflow existe e está configurado."""
    ci_file = Path(".github/workflows/ci.yml")
    assert ci_file.exists(), "CI/CD workflow não existe"
    
    # Verificar sintaxe YAML básica
    import yaml
    with open(ci_file) as f:
        data = yaml.safe_load(f)
        assert "jobs" in data or "on" in data, "CI/CD sem configuração válida"
```

**Critério de Pass**: Arquivo existe e é YAML válido.

#### test_basic_imports()

```python
def test_basic_imports():
    """Verifica que imports básicos funcionam."""
    from playwright_simple import SimpleTestBase
    from playwright_simple.core.yaml_parser import YAMLParser
    from playwright_simple import TestConfig
    
    # Se chegou aqui, imports funcionaram
    assert True
```

**Critério de Pass**: Todos os imports funcionam sem erros.

### Testes E2E

Não aplicável para FASE 0 (infraestrutura).

### Testes de Regressão

**Arquivo**: `validation/scripts/check_regression.py` (genérico)

Verifica que estrutura não foi quebrada em mudanças futuras.

### Como Executar

```bash
# Executar testes unitários
pytest validation/tests/test_phase0_validation.py -v

# Executar script de validação
python validation/scripts/validate_phase0.py

# Executar validação completa
python validation/scripts/validate_phase.py phase0
```

---

## 5. Garantia de Funcionamento Futuro

### Testes de Regressão

- Testes unitários executam em cada commit
- CI/CD verifica estrutura em cada PR
- Script de validação executa automaticamente

### CI/CD Integration

O workflow `.github/workflows/ci.yml` já inclui:
- Execução de testes
- Verificação de linting
- Verificação de type checking

**Adicionar**:
- Job de validação que executa `validate_phase0.py`
- Verificação de estrutura em cada PR

### Monitoramento Contínuo

- Script `check_regression.py` compara estrutura atual com baseline
- Alerta se estrutura for quebrada
- Sugere correções automáticas quando possível

---

## 6. Relatório de Validação

### Métricas Coletadas

- **Diretórios encontrados**: [número]
- **Arquivos de configuração**: [número]
- **Imports bem-sucedidos**: [número]
- **Testes coletados**: [número]
- **Tempo de validação**: [segundos]

### Status Final

- ✅ **PASSOU**: Todos os checks passaram
- ❌ **FALHOU**: [Lista de checks que falharam]

### Próximos Passos

Se validação passou:
- Prosseguir para FASE 1

Se validação falhou:
- Corrigir problemas identificados
- Re-executar validação
- Documentar correções

---

**Última Atualização**: [Data]  
**Validador**: [Nome]

