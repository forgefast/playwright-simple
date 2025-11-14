# Testes do Playwright Simple

## Por que Testes?

Os testes previnem **regressões** - quando você corrige um bug ou adiciona uma funcionalidade, os testes garantem que nada quebrou.

## Executando os Testes

### Instalação

```bash
pip install pytest pytest-asyncio
```

### Executar Todos os Testes

```bash
# Opção 1: Usando pytest diretamente
pytest tests/ -v

# Opção 2: Usando o script
./tests/run_tests.sh
```

### Executar Testes Específicos

```bash
# Apenas testes de interações
pytest tests/test_element_interactions.py -v

# Apenas testes de integração
pytest tests/test_integration.py -v

# Apenas um teste específico
pytest tests/test_element_interactions.py::test_click_by_text -v
```

## Adicionando Novos Testes

### Quando Adicionar Testes

1. **Ao corrigir um bug**: Adicione um teste que reproduz o bug e valida a correção
2. **Ao adicionar funcionalidade**: Adicione testes que validam a nova funcionalidade
3. **Ao refatorar**: Execute os testes existentes para garantir que nada quebrou

### Exemplo de Teste

```python
@pytest.mark.asyncio
async def test_my_new_feature(browser_page: Page):
    """Test my new feature."""
    await browser_page.set_content("<html><body><button>Click</button></body></html>")
    
    interactions = ElementInteractions(browser_page, fast_mode=True)
    result = await interactions.click(text="Click")
    
    assert result is True, "Click should succeed"
```

## Estrutura dos Testes

- **test_element_interactions.py**: Testes unitários para click, type, submit
- **test_element_finder.py**: Testes para busca de elementos
- **test_integration.py**: Testes end-to-end de fluxos completos

## CI/CD

Os testes devem passar antes de cada commit. Se um teste falhar:

1. **Não commite** até corrigir
2. **Investigue** o que quebrou
3. **Corrija** o problema
4. **Execute os testes novamente**
5. **Só então** faça o commit

