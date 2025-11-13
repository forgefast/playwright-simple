# Playwright Simple

A simple and intuitive library for writing Playwright tests, designed for QAs without deep programming knowledge.

## Features

- 🎯 **Simple API**: Easy-to-use methods that read like natural language
- 🎨 **Customizable Cursor**: Visual cursor with customizable style, color, and size
- 🎥 **Video Recording**: Automatic video recording with quality and codec options
- 📸 **Screenshots**: Automatic and manual screenshots with smart organization
- 🔍 **Smart Selectors**: Intelligent element location with automatic fallback
- 📝 **Multiple Formats**: Write tests in Python or YAML
- ⚙️ **Flexible Configuration**: YAML/JSON config files, environment variables, or code

## Installation

### Basic Installation

```bash
pip install playwright-simple
```

### With Extras

Install with optional extras for specific frameworks:

```bash
# Odoo support
pip install playwright-simple[odoo]

# ForgeERP support
pip install playwright-simple[forgeerp]

# Development dependencies
pip install playwright-simple[dev]
```

### From Source

```bash
git clone https://github.com/forgeerp/playwright-simple.git
cd playwright-simple
pip install -e .
```

Don't forget to install Playwright browsers:

```bash
playwright install chromium
```

## Extras

### Odoo Extra

The `[odoo]` extra provides specialized functionality for testing Odoo applications:

```python
from playwright_simple.odoo import OdooTestBase

async def test_odoo(page, test: OdooTestBase):
    await test.login("admin", "admin", database="devel")
    await test.go_to_menu("Vendas", "Pedidos")
    await test.create_record("sale.order", {
        "partner_id": "Cliente Teste"
    })
```

**Features:**
- Automatic version detection (Odoo 14-18)
- Menu navigation (Community/Enterprise)
- Field interaction (Many2one, Many2many, One2many, etc.)
- View manipulation (List, Kanban, Form, etc.)
- Wizard and dialog handling
- YAML support for QAs

See [Odoo Documentation](docs/odoo/README.md) for more details.

### ForgeERP Extra

The `[forgeerp]` extra provides specialized functionality for testing ForgeERP applications:

```python
from playwright_simple.forgeerp import ForgeERPTestBase

async def test_forgeerp(page, test: ForgeERPTestBase):
    await test.go_to_provision()
    await test.fill_provision_form("my-client", "dev")
    await test.submit_form()
    await test.assert_no_errors()
```

**Features:**
- HTMX interaction helpers (wait for swaps, detect errors)
- Form helpers (provision, deploy, diagnostics)
- Navigation helpers (setup, provision, status, deploy, diagnostics)
- Component helpers (modals, cards, buttons)
- Complete workflows (provision, deploy, check status, diagnostics)
- Automatic error detection and validation
- ForgeERP-specific selectors

See [ForgeERP Documentation](docs/forgeerp/README.md) for more details.

## Quick Start

### Python Format

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
    await test.type('input[name="name"]', "Item Teste")
    await test.assert_text(".success-message", "Item criado com sucesso")

# Run test
runner = TestRunner(config=config)
await runner.run_all([("01_login", test_login)])
```

### YAML Format (Coming Soon)

```yaml
name: "Login Test"
steps:
  - action: login
    username: "admin"
    password: "senha123"
  - action: go_to
    url: "/dashboard"
  - action: click
    selector: 'button:has-text("Criar")'
```

## Documentation

- [Full Documentation](docs/README.md)
- [API Reference](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Examples](docs/EXAMPLES.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## Requirements

- Python 3.8+
- Playwright 1.40+

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## Support

- Issues: [GitHub Issues](https://github.com/forgeerp/playwright-simple/issues)
- Documentation: [docs/](docs/)


