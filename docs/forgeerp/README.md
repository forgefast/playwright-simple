# ForgeERP Extension - Documentation

The ForgeERP extension provides specialized functionality for testing ForgeERP applications with HTMX, Tailwind CSS, and Alpine.js.

## Installation

```bash
pip install playwright-simple[forgeerp]
```

## Quick Start

```python
from playwright_simple.forgeerp import ForgeERPTestBase
from playwright_simple import TestConfig

async def test_provision(page, test: ForgeERPTestBase):
    await test.go_to_provision()
    await test.fill_provision_form("my-client", "dev")
    await test.submit_form()
    await test.assert_no_errors()
```

## Features

### Navigation

Navigate to ForgeERP pages easily:

```python
await test.go_to_setup()
await test.go_to_provision()
await test.go_to_status("my-client", "dev")
await test.go_to_deploy()
await test.go_to_diagnostics()
await test.navigate_menu("Provision")
```

### Form Interactions

Fill forms with helper methods:

```python
# Provisioning form
await test.fill_provision_form(
    client_name="my-client",
    environment="dev",
    database_type="postgresql",
    namespace="my-namespace"
)

# Deployment form
await test.fill_deploy_form(
    client_name="my-client",
    environment="dev",
    chart_name="generic",
    chart_version="1.0.0"
)

# Diagnostics form
await test.fill_diagnostics_form("my-client", "dev")
```

### HTMX Interactions

Wait for HTMX swaps and detect errors (using HTMXHelper from core):

```python
# Wait for HTMX swap (via test.htmx)
await test.htmx.wait_for_htmx_swap("#provision-result")

# Wait for loading to complete
await test.htmx.wait_for_htmx_loading("#provision-loading")

# Detect errors
error = await test.htmx.detect_htmx_error("#provision-result")
if error:
    print(f"Error detected: {error}")

# Get HTMX result
result = await test.htmx.get_htmx_result("provision-result")
```

### Component Helpers

Interact with UI components (generic methods from SimpleTestBase):

```python
# Click button by text (from SimpleTestBase)
await test.click_button("Provision Client")

# Fill input by label (from SimpleTestBase)
await test.fill_by_label("Client Name", "my-client")

# Select option by label (from SimpleTestBase)
await test.select_by_label("Environment", "dev")

# Wait for and close modal (from SimpleTestBase)
await test.wait_for_modal()
await test.close_modal()

# Get card content (from SimpleTestBase)
content = await test.get_card_content(".status-card")
```

### Workflows

Use high-level workflow methods for complete operations:

```python
# Complete provisioning workflow
await test.provision_client("my-client", "dev", database_type="postgresql")
await test.assert_provision_success("my-client")

# Complete deployment workflow
await test.deploy_application("my-client", "dev", "generic")
await test.assert_no_errors()

# Check status
await test.check_status("my-client", "dev")
await test.assert_status_display("my-client", "dev")

# Run diagnostics
await test.run_diagnostics()  # Summary
await test.run_diagnostics("my-client", "dev")  # Client-specific
```

### Validation

Assert expected states:

```python
# Assert no errors
await test.assert_no_errors()

# Assert success message
await test.assert_success_message("Client provisioned successfully")

# Assert status display
await test.assert_status_display("my-client", "dev")

# Assert provisioning success
await test.assert_provision_success("my-client")
```

## Configuration

Configure ForgeERP-specific settings:

```python
from playwright_simple import TestConfig

config = TestConfig(
    base_url="http://localhost:8000",
    cursor_color="#6366f1",  # ForgeERP indigo theme
    cursor_style="arrow",
)
```

## YAML Support

ForgeERP extension supports YAML test definitions for QAs without programming experience:

```yaml
name: provision_client_test
base_url: http://localhost:8000

steps:
  - go_to_provision:
  - fill_provision_form:
      client_name: "my-client"
      environment: "dev"
      database_type: "postgresql"
  - submit_form:
  - assert_no_errors:
```

Load and run YAML tests:

```python
from playwright_simple.forgeerp import ForgeERPYAMLParser

# Load single test
test_name, test_func = ForgeERPYAMLParser.load_test("test.yaml")

# Load all tests from directory
tests = ForgeERPYAMLParser.load_tests("tests/yaml/")
```

## Examples

See:
- [examples/forgeerp_basic.py](../../examples/forgeerp_basic.py) - Python examples
- [examples/forgeerp_workflows.py](../../examples/forgeerp_workflows.py) - Workflow examples
- [examples/forgeerp_yaml_example.yaml](../../examples/forgeerp_yaml_example.yaml) - YAML example

## API Reference

See [API.md](API.md) for complete API documentation.

