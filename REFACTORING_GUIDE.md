# Guia de Refatoração: Boas Práticas e Padrões para playwright-simple

## 📋 Índice
1. [Princípios Fundamentais](#princípios-fundamentais)
2. [Padrões de Design](#padrões-de-design)
3. [Boas Práticas Python](#boas-práticas-python)
4. [Arquitetura e Organização](#arquitetura-e-organização)
5. [Performance e Otimização](#performance-e-otimização)
6. [Checklist de Refatoração](#checklist-de-refatoração)

---

## 🎯 Princípios Fundamentais

### SOLID Principles

#### 1. Single Responsibility Principle (SRP)
- **Cada classe deve ter apenas uma razão para mudar**
- ✅ **Bom**: `CursorManager` gerencia apenas cursor, `VideoManager` apenas vídeo
- ❌ **Ruim**: Uma classe que gerencia cursor, vídeo e screenshots

#### 2. Open/Closed Principle (OCP)
- **Aberto para extensão, fechado para modificação**
- ✅ **Bom**: Usar herança ou composição para estender funcionalidades
- ❌ **Ruim**: Modificar código existente para adicionar features

#### 3. Liskov Substitution Principle (LSP)
- **Subclasses devem ser substituíveis por suas classes base**
- ✅ **Bom**: `OdooTestBase` pode ser usado onde `SimpleTestBase` é esperado
- ❌ **Ruim**: Subclasse que quebra comportamento da classe base

#### 4. Interface Segregation Principle (ISP)
- **Clientes não devem depender de interfaces que não usam**
- ✅ **Bom**: Interfaces pequenas e específicas
- ❌ **Ruim**: Interface gigante com muitos métodos não utilizados

#### 5. Dependency Inversion Principle (DIP)
- **Depender de abstrações, não de implementações concretas**
- ✅ **Bom**: Injetar dependências via construtor
- ❌ **Ruim**: Criar dependências diretamente dentro das classes

### DRY (Don't Repeat Yourself)
- **Eliminar duplicação de código**
- ✅ **Bom**: Métodos helper reutilizáveis (`_prepare_element_interaction`)
- ❌ **Ruim**: Código duplicado em múltiplos métodos

### KISS (Keep It Simple, Stupid)
- **Manter código simples e direto**
- ✅ **Bom**: Solução simples que resolve o problema
- ❌ **Ruim**: Solução complexa desnecessária

### YAGNI (You Aren't Gonna Need It)
- **Não implementar funcionalidades que não são necessárias agora**
- ✅ **Bom**: Implementar apenas o que é necessário
- ❌ **Ruim**: Over-engineering com features não usadas

---

## 🏗️ Padrões de Design

### 1. Factory Pattern
**Quando usar**: Criar objetos de forma flexível e desacoplada

```python
# ✅ Bom exemplo
class TestInstanceFactory:
    @staticmethod
    def create(page: Page, config: TestConfig, test_func: Callable) -> SimpleTestBase:
        # Detecta tipo de teste e cria instância apropriada
        if is_odoo_test(test_func):
            return OdooTestBase(page, config)
        elif is_forgeerp_test(test_func):
            return ForgeERPTestBase(page, config)
        return SimpleTestBase(page, config)
```

### 2. Strategy Pattern
**Quando usar**: Diferentes algoritmos para mesma tarefa

```python
# ✅ Bom exemplo
class VideoProcessor:
    def __init__(self, strategy: ProcessingStrategy):
        self.strategy = strategy
    
    def process(self, video_path: Path) -> Path:
        return self.strategy.process(video_path)

class SpeedProcessingStrategy(ProcessingStrategy):
    def process(self, video_path: Path) -> Path:
        # Implementação específica
        pass
```

### 3. Builder Pattern
**Quando usar**: Construir objetos complexos passo a passo

```python
# ✅ Bom exemplo
class TestConfigBuilder:
    def __init__(self):
        self.config = TestConfig()
    
    def with_video(self, enabled: bool = True) -> 'TestConfigBuilder':
        self.config.video.enabled = enabled
        return self
    
    def with_cursor(self, style: str = "pointer") -> 'TestConfigBuilder':
        self.config.cursor.style = style
        return self
    
    def build(self) -> TestConfig:
        return self.config
```

### 4. Observer Pattern
**Quando usar**: Notificar múltiplos objetos sobre mudanças

```python
# ✅ Bom exemplo
class TestEventEmitter:
    def __init__(self):
        self._listeners = []
    
    def subscribe(self, listener: Callable):
        self._listeners.append(listener)
    
    def emit(self, event: str, data: Any):
        for listener in self._listeners:
            listener(event, data)
```

### 5. Decorator Pattern
**Quando usar**: Adicionar funcionalidades dinamicamente

```python
# ✅ Bom exemplo
def with_retry(max_attempts: int = 3):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
        return wrapper
    return decorator
```

### 6. Singleton Pattern (usar com cuidado)
**Quando usar**: Apenas uma instância necessária (ex: logger global)

```python
# ✅ Bom exemplo (usando módulo Python)
# logger.py
class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

---

## 🐍 Boas Práticas Python

### 1. Type Hints
```python
# ✅ Bom
async def click(self, selector: str, description: str = "") -> 'SimpleTestBase':
    pass

# ❌ Ruim
async def click(self, selector, description=""):
    pass
```

### 2. Docstrings
```python
# ✅ Bom
async def click(self, selector: str, description: str = "") -> 'SimpleTestBase':
    """
    Click on an element.
    
    Args:
        selector: CSS selector or text of element
        description: Description of element (for logs)
        
    Returns:
        Self for method chaining
        
    Raises:
        Exception: If element is not found
        
    Example:
        await test.click('button:has-text("Submit")')
    """
    pass
```

### 3. Error Handling
```python
# ✅ Bom
try:
    result = await element.click()
except PlaywrightTimeoutError as e:
    logger.error(f"Timeout clicking element: {selector}")
    raise ElementNotFoundError(f"Element not found: {selector}") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# ❌ Ruim
try:
    result = await element.click()
except:
    pass  # Silently ignore all errors
```

### 4. Async/Await Best Practices
```python
# ✅ Bom - usar asyncio.gather para operações paralelas
results = await asyncio.gather(
    task1(),
    task2(),
    task3(),
    return_exceptions=True
)

# ✅ Bom - evitar bloqueios
async def process_data():
    data = await fetch_data()  # Não bloqueia
    return process(data)

# ❌ Ruim - bloqueios
async def process_data():
    time.sleep(5)  # Bloqueia a thread!
    return process(data)
```

### 5. Context Managers
```python
# ✅ Bom
async with page.context() as context:
    # Automatic cleanup
    pass

# ✅ Bom - criar context managers customizados
@contextmanager
def video_processing(video_path: Path):
    temp_path = video_path.parent / f"{video_path.stem}_temp{video_path.suffix}"
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            temp_path.unlink()
```

### 6. Property Decorators
```python
# ✅ Bom
class CursorManager:
    @property
    def is_visible(self) -> bool:
        return self._injected and self._visible
    
    @is_visible.setter
    def is_visible(self, value: bool):
        self._visible = value
        if value:
            self._ensure_cursor_exists()
```

### 7. Dataclasses
```python
# ✅ Bom
@dataclass
class VideoConfig:
    enabled: bool = True
    quality: str = "high"
    codec: str = "webm"
    
    def __post_init__(self):
        if self.quality not in ["low", "medium", "high"]:
            raise ValueError(f"Invalid quality: {self.quality}")
```

---

## 📁 Arquitetura e Organização

### 1. Estrutura de Diretórios
```
playwright_simple/
├── core/                      # Funcionalidades genéricas
│   ├── base.py                # SimpleTestBase (com Dependency Injection)
│   ├── extensions/            # Interfaces para extensões
│   │   ├── __init__.py        # IExtensionAuth, IExtensionWait, IExtensionNavigation
│   │   ├── auth.py            # Interface de autenticação
│   │   ├── wait.py            # Interface de esperas
│   │   └── navigation.py      # Interface de navegação
│   ├── interactions.py        # Interações genéricas
│   ├── navigation.py          # Navegação genérica
│   ├── forms.py               # Formulários genéricos
│   ├── auth.py                # Autenticação genérica
│   ├── wait.py                # Esperas genéricas
│   └── managers/              # Managers separados
│       ├── cursor.py
│       ├── video.py
│       └── screenshot.py
├── odoo/                      # Extensão Odoo
│   ├── base.py                # OdooTestBase (com Dependency Injection)
│   ├── specific/               # Ações muito específicas do Odoo
│   │   ├── __init__.py
│   │   ├── logo.py            # LogoNavigator
│   │   └── filters.py         # FilterHelper
│   ├── auth.py                # Autenticação Odoo
│   ├── wait.py                # Esperas Odoo
│   ├── navigation.py          # Navegação Odoo
│   ├── fields/                # Campos Odoo
│   └── views/                 # Views Odoo
├── forgeerp/                  # Extensão ForgeERP (futuro)
└── utils/                      # Utilitários compartilhados
```

### 1.1. Arquitetura de Bibliotecas Python

**Princípios**:
- **Core**: Funcionalidades genéricas, sem dependências de plataformas específicas
- **Extensões**: Funcionalidades específicas, dependem do core
- **Interfaces**: Definem contratos para extensões (`core/extensions/`)
- **Dependency Injection**: Permite customização e testes

**Como criar uma nova extensão**:
1. Criar diretório `playwright_simple/nova_extensao/`
2. Criar `base.py` que herda de `SimpleTestBase`
3. Implementar interfaces de `core/extensions/` se necessário
4. Adicionar funcionalidades específicas
5. Exportar em `__init__.py`

### 2. Separation of Concerns
- **Managers**: Gerenciam recursos específicos (cursor, video, screenshots)
- **Base Classes**: Fornecem funcionalidades comuns
- **Parsers**: Convertem formatos (YAML → código)
- **Runners**: Executam testes

### 3. Dependency Injection
```python
# ✅ Bom
class SimpleTestBase:
    def __init__(
        self,
        page: Page,
        config: Optional[TestConfig] = None,
        cursor_manager: Optional[CursorManager] = None,
        screenshot_manager: Optional[ScreenshotManager] = None
    ):
        self.page = page
        self.config = config or TestConfig()
        self.cursor_manager = cursor_manager or CursorManager(page, self.config.cursor)
        self.screenshot_manager = screenshot_manager or ScreenshotManager(...)
```

### 4. Interface Segregation
```python
# ✅ Bom - interfaces pequenas e específicas
class ICursorManager(ABC):
    @abstractmethod
    async def move_to(self, x: float, y: float):
        pass

class IVideoProcessor(ABC):
    @abstractmethod
    async def process(self, video_path: Path) -> Path:
        pass
```

---

## ⚡ Performance e Otimização

### 1. Lazy Loading
```python
# ✅ Bom
class CursorManager:
    @property
    async def cursor_element(self):
        if not hasattr(self, '_cursor_element'):
            self._cursor_element = await self._get_cursor()
        return self._cursor_element
```

### 2. Caching
```python
# ✅ Bom
from functools import lru_cache

@lru_cache(maxsize=128)
def parse_selector(selector: str) -> ParsedSelector:
    # Expensive parsing operation
    return ParsedSelector(selector)
```

### 3. Batch Operations
```python
# ✅ Bom - processar múltiplos itens de uma vez
async def process_videos(self, video_paths: List[Path]) -> List[Path]:
    tasks = [self._process_video(path) for path in video_paths]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### 4. Avoid Premature Optimization
- ✅ Medir antes de otimizar
- ✅ Otimizar apenas bottlenecks reais
- ❌ Otimizar código que não é crítico

---

## ✅ Checklist de Refatoração

### Fase 1: Análise e Identificação

- [ ] **Identificar Code Smells**
  - [ ] Duplicação de código
  - [ ] Funções/classes muito longas (>200 linhas)
  - [ ] Muitos parâmetros (>5)
  - [ ] Nomes não descritivos
  - [ ] Comentários desnecessários (código auto-explicativo)
  - [ ] Magic numbers/strings

- [ ] **Mapear Dependências**
  - [ ] Identificar acoplamento forte
  - [ ] Identificar dependências circulares
  - [ ] Identificar dependências desnecessárias

- [ ] **Identificar Oportunidades de Padrões**
  - [ ] Onde aplicar Factory Pattern?
  - [ ] Onde aplicar Strategy Pattern?
  - [ ] Onde aplicar Builder Pattern?
  - [ ] Onde aplicar Observer Pattern?

### Fase 2: Refatoração Estrutural

- [ ] **Aplicar SOLID**
  - [ ] Cada classe tem uma única responsabilidade?
  - [ ] Classes estão abertas para extensão?
  - [ ] Subclasses são substituíveis?
  - [ ] Interfaces são segregadas?
  - [ ] Dependências são invertidas?

- [ ] **Eliminar Duplicação**
  - [ ] Extrair métodos comuns
  - [ ] Criar classes base quando apropriado
  - [ ] Usar composition over inheritance

- [ ] **Melhorar Nomenclatura**
  - [ ] Nomes descritivos e consistentes
  - [ ] Evitar abreviações
  - [ ] Usar verbos para métodos, substantivos para classes

- [ ] **Reduzir Complexidade**
  - [ ] Quebrar funções grandes
  - [ ] Reduzir níveis de aninhamento
  - [ ] Simplificar condições complexas

### Fase 3: Melhorias de Código

- [ ] **Type Hints**
  - [ ] Adicionar type hints em todos os métodos públicos
  - [ ] Usar `Optional`, `Union`, `List`, `Dict` apropriadamente
  - [ ] Usar `Protocol` para interfaces

- [ ] **Docstrings**
  - [ ] Docstrings em todas as classes e métodos públicos
  - [ ] Documentar parâmetros, retornos e exceções
  - [ ] Incluir exemplos de uso

- [ ] **Error Handling**
  - [ ] Exceções específicas ao invés de genéricas
  - [ ] Mensagens de erro descritivas
  - [ ] Logging apropriado
  - [ ] Cleanup em finally blocks

- [ ] **Async/Await**
  - [ ] Usar `asyncio.gather` para operações paralelas
  - [ ] Evitar bloqueios (time.sleep → asyncio.sleep)
  - [ ] Usar context managers para recursos

### Fase 4: Arquitetura

- [ ] **Organização de Arquivos**
  - [ ] Estrutura de diretórios clara
  - [ ] Separação de concerns
  - [ ] Módulos coesos

- [ ] **Dependency Injection**
  - [ ] Injetar dependências via construtor
  - [ ] Evitar criação direta de dependências
  - [ ] Usar factories quando apropriado

- [ ] **Interfaces e Abstrações**
  - [ ] Definir interfaces claras
  - [ ] Usar ABC para classes abstratas
  - [ ] Implementar Protocol para duck typing

### Fase 5: Performance

- [ ] **Otimizações**
  - [ ] Processar em lote quando possível
  - [ ] Usar lazy loading
  - [ ] Implementar caching onde apropriado
  - [ ] Evitar processamento redundante

- [ ] **Async Performance**
  - [ ] Operações I/O são async
  - [ ] Usar gather para paralelismo
  - [ ] Evitar bloqueios

### Fase 6: Testes e Validação

- [ ] **Testes**
  - [ ] Testes unitários para novas funcionalidades
  - [ ] Testes de integração para fluxos completos
  - [ ] Manter cobertura de testes

- [ ] **Validação**
  - [ ] Executar todos os testes existentes
  - [ ] Verificar que comportamento não mudou
  - [ ] Validar performance não degradou

### Fase 7: Documentação

- [ ] **Documentação de Código**
  - [ ] Docstrings atualizadas
  - [ ] Comentários explicando "porquê" não "o quê"
  - [ ] Type hints completos

- [ ] **Documentação Externa**
  - [ ] README atualizado
  - [ ] CHANGELOG atualizado
  - [ ] Exemplos de uso atualizados

---

## 🎯 Prioridades de Refatoração

### Alta Prioridade
1. ✅ Eliminar duplicação de código (já feito parcialmente)
2. ⚠️ Aplicar type hints completos
3. ⚠️ Melhorar error handling
4. ⚠️ Separar concerns (managers em módulos separados)

### Média Prioridade
1. Aplicar padrões de design apropriados
2. Melhorar documentação (docstrings)
3. Otimizar performance (async, batching)
4. Implementar interfaces/abstrações

### Baixa Prioridade
1. Refatorar estrutura de diretórios
2. Adicionar testes unitários
3. Implementar logging estruturado
4. Adicionar métricas/telemetria

---

## 📚 Referências

- **Clean Code** - Robert C. Martin
- **Design Patterns** - Gang of Four
- **Refactoring** - Martin Fowler
- **Python Best Practices** - PEP 8, PEP 484, PEP 526
- **SOLID Principles** - Robert C. Martin
- **Async Python** - Real Python, asyncio documentation

---

## 🔄 Processo Iterativo

1. **Identificar** área para refatoração
2. **Analisar** código atual e dependências
3. **Planejar** mudanças (usar este checklist)
4. **Refatorar** em pequenos passos
5. **Testar** após cada mudança
6. **Validar** que comportamento não mudou
7. **Documentar** mudanças
8. **Revisar** e iterar

---

**Última atualização**: 2024-11-13
**Versão**: 1.0

