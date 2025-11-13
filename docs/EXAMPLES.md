# Examples

Real-world examples of using Playwright Simple.

## Basic Examples

### Simple Login Test

```python
from playwright_simple import TestRunner, TestConfig

async def test_login(page, test):
    await test.go_to("/login")
    await test.type('input[name="username"]', "admin")
    await test.type('input[name="password"]', "password123")
    await test.click('button[type="submit"]')
    await test.assert_url("/dashboard")

config = TestConfig(base_url="http://localhost:8000")
runner = TestRunner(config=config)
await runner.run_all([("login", test_login)])
```

### Form Filling

```python
async def test_form(page, test):
    await test.go_to("/contact")
    await test.fill_form({
        'input[name="name"]': "John Doe",
        'input[name="email"]': "john@example.com",
        'textarea[name="message"]': "Hello, world!",
    })
    await test.click('button[type="submit"]')
    await test.assert_text(".success", "Message sent")
```

## Advanced Examples

### Drag and Drop

```python
async def test_kanban(page, test):
    await test.go_to("/kanban")
    await test.drag(
        source='[data-status="todo"] .task:first-child',
        target='[data-status="done"]'
    )
    await test.assert_count('[data-status="done"] .task', 1)
```

### Scrolling and Waiting

```python
async def test_infinite_scroll(page, test):
    await test.go_to("/products")
    
    # Scroll down multiple times
    for _ in range(3):
        await test.scroll(direction="down", amount=500)
        await test.wait(1)
    
    # Wait for new content
    await test.wait_for('.new-product', state="visible")
```

### Complex Assertions

```python
async def test_product_list(page, test):
    await test.go_to("/products")
    
    # Assert visibility
    await test.assert_visible('.product-grid')
    
    # Assert count
    await test.assert_count('.product-item', 12)
    
    # Assert text
    await test.assert_text('.page-title', "Products")
    
    # Assert attribute
    await test.assert_attr(
        '.product-item:first-child',
        'data-category',
        'electronics'
    )
```

## YAML Examples

### Basic YAML Test

```yaml
name: "Login Test"
base_url: "http://localhost:8000"
steps:
  - action: go_to
    url: "/login"
  
  - action: type
    selector: 'input[name="username"]'
    text: "admin"
  
  - action: type
    selector: 'input[name="password"]'
    text: "password123"
  
  - action: click
    selector: 'button[type="submit"]'
  
  - action: assert_url
    pattern: "/dashboard"
```

### Running YAML Tests

```python
from pathlib import Path
from playwright_simple import TestRunner, TestConfig, YAMLParser

# Load YAML tests
tests = YAMLParser.load_tests(Path("tests/yaml/"))

# Run tests
config = TestConfig(base_url="http://localhost:8000")
runner = TestRunner(config=config)
await runner.run_all(tests)
```

## Configuration Examples

### Custom Cursor

```python
config = TestConfig(
    base_url="http://localhost:8000",
    cursor_style="dot",
    cursor_color="#ff0000",
    cursor_size="large",
    cursor_animation_speed=0.5,
)
```

### Video and Screenshots

```python
config = TestConfig(
    video_enabled=True,
    video_quality="high",
    video_codec="webm",
    screenshots_auto=True,
    screenshots_on_failure=True,
    screenshots_full_page=True,
)
```

### Browser Settings

```python
config = TestConfig(
    browser_headless=False,
    browser_slow_mo=50,  # Slow down for visibility
    browser_timeout=60000,  # 60 seconds
    browser_viewport={"width": 1920, "height": 1080},
)
```

## Integration Examples

### Odoo Integration

See `examples/odoo_example.py` for complete Odoo integration example.

### E-commerce Checkout

See `examples/ecommerce_example.py` for complete e-commerce checkout flow.

## Best Practices

1. **Use descriptive test names**: `test_login_as_admin` instead of `test1`
2. **Add descriptions**: `await test.click(selector, "Login button")`
3. **Use smart selectors**: Prefer `data-testid` over CSS classes
4. **Organize screenshots**: Let the library organize by test name
5. **Configure appropriately**: Use headless for CI, visible for debugging


