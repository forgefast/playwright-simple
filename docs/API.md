# API Reference

Complete API reference for Playwright Simple.

## TestConfig

Configuration class for test settings.

### Methods

#### `TestConfig(...)`

Create configuration with parameters.

```python
config = TestConfig(
    base_url="http://localhost:8000",
    cursor_style="arrow",
    video_enabled=True,
)
```

#### `TestConfig.from_file(path)`

Load configuration from YAML or JSON file.

```python
config = TestConfig.from_file("config.yaml")
```

#### `TestConfig.from_env()`

Load configuration from environment variables.

```python
config = TestConfig.from_env()
```

#### `TestConfig.load(config_file, use_env, **kwargs)`

Load configuration with priority: kwargs > env > file > defaults.

```python
config = TestConfig.load(
    config_file="config.yaml",
    use_env=True,
    base_url="http://custom:8000"
)
```

## SimpleTestBase

Base class for writing tests.

### Navigation Methods

#### `go_to(url) -> SimpleTestBase`

Navigate to URL.

```python
await test.go_to("/dashboard")
await test.go_to("https://example.com")
```

#### `back() -> SimpleTestBase`

Navigate back in browser history.

```python
await test.back()
```

#### `forward() -> SimpleTestBase`

Navigate forward in browser history.

```python
await test.forward()
```

#### `refresh() -> SimpleTestBase`

Refresh current page.

```python
await test.refresh()
```

#### `navigate(menu_path: List[str]) -> SimpleTestBase`

Navigate through menu path.

```python
await test.navigate(["Menu", "Submenu", "Item"])
```

### Interaction Methods

#### `click(selector, description="") -> SimpleTestBase`

Click on element.

```python
await test.click('button:has-text("Submit")')
await test.click('[data-testid="login"]', "Login button")
```

#### `type(selector, text, description="") -> SimpleTestBase`

Type text into field.

```python
await test.type('input[name="username"]', "admin")
await test.type('#password', "secret", "Password field")
```

#### `select(selector, option, description="") -> SimpleTestBase`

Select option in dropdown.

```python
await test.select('select[name="country"]', "Brazil")
```

#### `hover(selector, description="") -> SimpleTestBase`

Hover over element.

```python
await test.hover('.tooltip-trigger')
```

#### `drag(source, target, description="") -> SimpleTestBase`

Drag and drop from source to target.

```python
await test.drag('.source-item', '.target-area', "Move item")
```

#### `scroll(selector=None, direction="down", amount=500) -> SimpleTestBase`

Scroll page or element.

```python
await test.scroll(direction="down", amount=500)
await test.scroll(selector=".scrollable", direction="up")
```

### Wait Methods

#### `wait(seconds=1.0) -> SimpleTestBase`

Wait for specified time.

```python
await test.wait(2.5)
```

#### `wait_for(selector, state="visible", timeout=None, description="") -> SimpleTestBase`

Wait for element to appear.

```python
await test.wait_for('.dynamic-content', state="visible")
```

#### `wait_for_url(url_pattern, timeout=None) -> SimpleTestBase`

Wait for URL to match pattern.

```python
await test.wait_for_url("/dashboard")
```

#### `wait_for_text(selector, text, timeout=None, description="") -> SimpleTestBase`

Wait for element to contain text.

```python
await test.wait_for_text('.status', "Loaded")
```

### Assertion Methods

#### `assert_text(selector, expected, description="") -> SimpleTestBase`

Assert element contains expected text.

```python
await test.assert_text('.message', "Success")
```

#### `assert_visible(selector, description="") -> SimpleTestBase`

Assert element is visible.

```python
await test.assert_visible('.dashboard')
```

#### `assert_url(pattern) -> SimpleTestBase`

Assert current URL matches pattern.

```python
await test.assert_url("/dashboard")
```

#### `assert_count(selector, expected_count, description="") -> SimpleTestBase`

Assert number of elements.

```python
await test.assert_count('.item', 5)
```

#### `assert_attr(selector, attribute, expected, description="") -> SimpleTestBase`

Assert element attribute value.

```python
await test.assert_attr('.product', 'data-id', "123")
```

### Helper Methods

#### `login(username, password, login_url="/login", show_process=False) -> SimpleTestBase`

Login to system.

```python
await test.login("admin", "senha123")
```

#### `fill_form(fields: Dict[str, str]) -> SimpleTestBase`

Fill form with multiple fields.

```python
await test.fill_form({
    'input[name="name"]': "John",
    'input[name="email"]': "john@example.com",
})
```

#### `get_text(selector, description="") -> str`

Get text content of element.

```python
text = await test.get_text('.title')
```

#### `get_attr(selector, attribute, description="") -> Optional[str]`

Get attribute value.

```python
value = await test.get_attr('.link', 'href')
```

#### `is_visible(selector, description="") -> bool`

Check if element is visible.

```python
if await test.is_visible('.modal'):
    await test.click('.close-button')
```

#### `is_enabled(selector, description="") -> bool`

Check if element is enabled.

```python
if await test.is_enabled('.submit-button'):
    await test.click('.submit-button')
```

#### `screenshot(name=None, full_page=None, element=None) -> Path`

Take screenshot.

```python
path = await test.screenshot("after_login")
path = await test.screenshot(element=".widget")
path = await test.screenshot(name="full", full_page=True)
```

## TestRunner

Test execution runner.

### Methods

#### `TestRunner(config, base_url, videos_dir, headless, viewport)`

Initialize test runner.

```python
runner = TestRunner(config=config)
```

#### `run_test(test_name, test_func, browser, context) -> Dict`

Execute single test.

```python
result = await runner.run_test("login", test_login, browser=browser)
```

#### `run_all(tests, parallel=False, workers=1) -> List[Dict]`

Execute all tests.

```python
results = await runner.run_all([
    ("01_login", test_login),
    ("02_checkout", test_checkout),
], parallel=True, workers=4)
```

#### `get_results() -> List[Dict]`

Get test execution results.

```python
results = runner.get_results()
```

#### `get_summary() -> Dict`

Get execution summary.

```python
summary = runner.get_summary()
print(f"Passed: {summary['passed']}/{summary['total']}")
```

## YAMLParser

Parser for YAML test definitions.

### Methods

#### `YAMLParser.load_test(yaml_path) -> tuple[str, Callable]`

Load test from YAML file.

```python
test_name, test_func = YAMLParser.load_test(Path("test.yaml"))
```

#### `YAMLParser.load_tests(yaml_dir) -> List[tuple[str, Callable]]`

Load all tests from YAML directory.

```python
tests = YAMLParser.load_tests(Path("tests/"))
```


