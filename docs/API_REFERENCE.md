# API Reference - Playwright Simple

**Versão**: 1.0.0  
**Data**: Novembro 2024

---

## 📚 Índice

- [Core API](#core-api)
- [Odoo Extension API](#odoo-extension-api)
- [Recorder API](#recorder-api)
- [Video Processing API](#video-processing-api)

---

## Core API

### SimpleTestBase

Classe base para testes genéricos.

```python
from playwright_simple.core.base import SimpleTestBase
from playwright_simple.core.config import TestConfig
from playwright.async_api import Page

test = SimpleTestBase(page, config)
```

#### Métodos Principais

##### `click(text_or_selector: str, description: str = "")`

Clica em um elemento.

```python
await test.click("Botão")
await test.click("#button-id")
```

##### `type(text: str, selector: str = None, description: str = "")`

Digita texto em um campo.

```python
await test.type("texto", selector="#input")
```

##### `fill(selector: str, text: str, description: str = "")`

Preenche um campo.

```python
await test.fill("#input", "valor")
```

##### `go_to(url: str, description: str = "")`

Navega para uma URL.

```python
await test.go_to("http://example.com")
```

##### `wait(seconds: float, description: str = "")`

Aguarda um tempo.

```python
await test.wait(2.0)
```

##### `wait_for(selector: str, timeout: int = 5000, description: str = "")`

Aguarda elemento aparecer.

```python
await test.wait_for(".element", timeout=5000)
```

##### `assert_text(selector: str, text: str, description: str = "")`

Verifica texto em elemento.

```python
await test.assert_text(".message", "Sucesso")
```

##### `assert_visible(selector: str, description: str = "")`

Verifica se elemento está visível.

```python
await test.assert_visible(".dashboard")
```

---

## Odoo Extension API

### OdooTestBase

Classe base para testes Odoo.

```python
from playwright_simple.odoo import OdooTestBase

test = OdooTestBase(page, config)
```

#### Métodos Principais

##### `login(login: str, password: str, database: str = None)`

Faz login no Odoo.

```python
await test.login("admin", "admin", database="devel")
```

##### `go_to(menu_path: str)`

Navega por menu.

```python
await test.go_to("Vendas > Pedidos")
```

##### `fill(label_or_assignment: str, value: str = None, context: str = None)`

Preenche campo Odoo.

```python
await test.fill("Cliente = João Silva")
await test.fill("Cliente", "João Silva")
```

##### `click_button(text: str, context: str = None)`

Clica em botão Odoo.

```python
await test.click_button("Criar")
```

##### `create_record(model_name: str = None, fields: dict = None)`

Cria registro.

```python
await test.create_record("res.partner", {"name": "Test"})
```

##### `open_record(search_text: str, position: str = None)`

Abre registro.

```python
await test.open_record("João Silva")
```

---

## Recorder API

### Recorder

Grava interações e gera YAML.

```python
from playwright_simple.core.recorder import Recorder

recorder = Recorder(
    output_path=Path("test.yaml"),
    initial_url="http://example.com",
    headless=False,
    debug=False
)

await recorder.start()
```

#### Métodos

##### `start()`

Inicia gravação.

```python
await recorder.start()
```

##### `stop()`

Para gravação.

```python
await recorder.stop()
```

##### `pause()`

Pausa gravação.

```python
await recorder.pause()
```

##### `resume()`

Retoma gravação.

```python
await recorder.resume()
```

---

## Video Processing API

### VideoProcessor

Processa vídeos com legendas e áudio.

```python
from playwright_simple.core.runner.video_processor import VideoProcessor

processor = VideoProcessor(config)
```

#### Métodos

##### `process_all_in_one(...)`

Processa vídeo completo em uma passada.

```python
video_path = await processor.process_all_in_one(
    video_path=Path("video.webm"),
    test_steps=steps,
    start_time=start_time,
    subtitle_generator=subtitle_gen,
    audio_processor=audio_proc
)
```

---

## YAML Parser API

### YAMLParser

Parseia arquivos YAML.

```python
from playwright_simple.core.yaml_parser import YAMLParser

# Parsear arquivo
yaml_data = YAMLParser.parse_file(Path("test.yaml"))

# Converter para função
test_func = YAMLParser.to_python_function(yaml_data)
await test_func(page, test)
```

---

## Performance API

### PerformanceProfiler

Profiling de performance.

```python
from playwright_simple.core.performance import PerformanceProfiler

profiler = PerformanceProfiler(enabled=True)

with profiler.measure("operation"):
    # código
    pass

profiler.print_summary()
```

---

## Config API

### TestConfig

Configuração de testes.

```python
from playwright_simple.core.config import TestConfig

config = TestConfig(
    base_url="http://localhost:8069",
    headless=False,
    video=True,
    subtitles=True
)
```

---

**Última Atualização**: Novembro 2024

