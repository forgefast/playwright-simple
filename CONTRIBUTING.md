# Contribuindo para Playwright Simple

## Prevenção de Regressões

### Executar Testes Antes de Commitar

Sempre execute os testes antes de fazer commit:

```bash
# Instalar dependências de teste (se necessário)
pip install pytest pytest-asyncio

# Executar todos os testes
pytest tests/ -v

# Ou usar o script
./tests/run_tests.sh
```

### Adicionar Novos Testes

Ao adicionar nova funcionalidade ou corrigir um bug:

1. **Adicione um teste** que valida a funcionalidade
2. **Execute os testes** para garantir que passam
3. **Commit** apenas se todos os testes passarem

### Estrutura de Testes

- `tests/test_element_interactions.py`: Testes unitários para interações com elementos
- `tests/test_element_finder.py`: Testes para busca de elementos
- `tests/test_integration.py`: Testes de integração end-to-end

## Sistema de Logging

### Uso Padrão

O framework usa logging padronizado automaticamente:

```python
from playwright_simple.core.logging_config import FrameworkLogger

# Configurar (geralmente feito no __init__.py)
FrameworkLogger.configure(level='DEBUG', debug=True)

# Obter logger
logger = FrameworkLogger.get_logger(__name__)
logger.debug("Mensagem de debug")
logger.info("Mensagem de info")
```

### Funções de Conveniência

```python
from playwright_simple.core.logging_config import (
    log_action,
    log_mouse_action,
    log_keyboard_action,
    log_cursor_action,
    log_element_action,
    log_error
)

# Log de ações
log_action("click", {"element": "button", "text": "Submit"})

# Log de mouse
log_mouse_action("click", x=100, y=200)

# Log de teclado
log_keyboard_action("type", text="Hello World")

# Log de cursor
log_cursor_action("move", x=100, y=200)

# Log de elementos
log_element_action("click", {"text": "Submit", "tag": "button"})

# Log de erros
try:
    # código
except Exception as e:
    log_error(e, context="click_handler", element="button")
```

## Checklist Antes de Commitar

- [ ] Todos os testes passam (`pytest tests/`)
- [ ] Não há erros de sintaxe (`python -m py_compile`)
- [ ] Imports funcionam (`python -c "from playwright_simple import ..."`)
- [ ] Logs estão padronizados (usando FrameworkLogger)
- [ ] Código segue o padrão do projeto

