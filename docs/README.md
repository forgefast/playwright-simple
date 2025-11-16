# Playwright Simple - Documentation

Welcome to the Playwright Simple documentation!

## Table of Contents

- [Getting Started](README.md#getting-started)
- [Configuration](CONFIGURATION.md)
- [API Reference](API.md)
- [Examples](EXAMPLES.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Architecture](ARCHITECTURE_INDEX.md) - **Nova arquitetura do framework**

## Getting Started

### Installation

```bash
pip install playwright-simple
playwright install chromium
```

### Quick Example

```python
from playwright_simple import TestRunner, TestConfig

# Configuration
config = TestConfig(
    base_url="http://localhost:8000",
    cursor_style="arrow",
    cursor_color="#007bff",
)

# Test function
async def test_login(page, test):
    await test.login("admin", "senha123")
    await test.go_to("/dashboard")
    await test.click('button:has-text("Criar")')
    await test.assert_text(".success-message", "Item criado")

# Run test
runner = TestRunner(config=config)
await runner.run_all([("01_login", test_login)])
```

## Core Concepts

### TestConfig

Configuration object that controls all aspects of test execution:
- Base URL
- Cursor appearance
- Video recording
- Screenshots
- Browser settings

### SimpleTestBase

Base class that provides all test methods:
- Navigation: `go_to()`, `back()`, `forward()`, `refresh()`, `navigate()`
- Interaction: `click()`, `type()`, `select()`, `hover()`, `drag()`, `scroll()`
- Waiting: `wait()`, `wait_for()`, `wait_for_url()`, `wait_for_text()`
- Assertions: `assert_text()`, `assert_visible()`, `assert_url()`, etc.
- Helpers: `login()`, `fill_form()`, `screenshot()`, etc.

### TestRunner

Executes tests and manages resources:
- Video recording
- Screenshot capture
- Test execution
- Results reporting

## Architecture

**🚀 Nova Arquitetura do Framework (v2.0)**

O playwright-simple está evoluindo de uma biblioteca para um framework completo com GUI, tornando-o acessível a profissionais de negócios.

- **[Architecture Index](ARCHITECTURE_INDEX.md)** - Índice completo da documentação de arquitetura
- **[Architecture Overview](ARCHITECTURE.md)** - Visão geral da arquitetura
- **[Migration Strategy](ARCHITECTURE_MIGRATION_STRATEGY.md)** - Estratégia de migração

**Principais mudanças:**
- ✅ Arquitetura em camadas (Clean Architecture)
- ✅ API REST + GUI Web
- ✅ Comunicação em tempo real (WebSocket)
- ✅ Assistente de IA com linguagem natural
- ✅ Templates e wizards
- ✅ Abstrações simplificadas para não-técnicos

## Next Steps

- Read the [Configuration Guide](CONFIGURATION.md) to customize your tests
- Check the [API Reference](API.md) for all available methods
- See [Examples](EXAMPLES.md) for real-world use cases
- Visit [Troubleshooting](TROUBLESHOOTING.md) if you encounter issues
- Explore the [Architecture Documentation](ARCHITECTURE_INDEX.md) for framework evolution


