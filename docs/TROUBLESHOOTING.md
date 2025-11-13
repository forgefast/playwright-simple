# Troubleshooting

Common issues and solutions when using Playwright Simple.

## Installation Issues

### PyYAML Not Available

**Error**: `ImportError: PyYAML is required for YAML support`

**Solution**: Install PyYAML
```bash
pip install pyyaml
```

### Playwright Browsers Not Installed

**Error**: Browser not found

**Solution**: Install Playwright browsers
```bash
playwright install chromium
```

## Configuration Issues

### Invalid Configuration Value

**Error**: `ValueError: Invalid cursor style: invalid`

**Solution**: Check valid values in [Configuration Guide](CONFIGURATION.md)
- Cursor style: `arrow`, `dot`, `circle`, `custom`
- Video quality: `low`, `medium`, `high`
- Video codec: `webm`, `mp4`

### Config File Not Found

**Error**: `FileNotFoundError: Config file not found`

**Solution**: Check file path and extension
```python
# Use absolute or relative path
config = TestConfig.from_file("config.yaml")  # Relative to current directory
config = TestConfig.from_file("/path/to/config.yaml")  # Absolute path
```

## Test Execution Issues

### Element Not Found

**Error**: `Element not found: selector`

**Solution**:
1. Check selector is correct
2. Wait for element to appear: `await test.wait_for(selector)`
3. Use smart selectors: `data-testid`, `role`, etc.
4. Check if element is in iframe (not supported yet)

### Timeout Errors

**Error**: `TimeoutError: Element not found (timeout: 30000ms)`

**Solution**:
1. Increase timeout: `await test.wait_for(selector, timeout=60000)`
2. Check if element actually exists on page
3. Wait for page to load: `await test.wait(2)`

### Video Not Recording

**Issue**: No video files created

**Solution**:
1. Check video is enabled: `config.video.enabled = True`
2. Check video directory exists and is writable
3. Ensure context is properly closed (videos finalize on context close)

### Screenshots Not Saving

**Issue**: Screenshots not being saved

**Solution**:
1. Check screenshots are enabled: `config.screenshots.auto = True`
2. Check screenshot directory exists and is writable
3. Verify test name is set for organization

## Cursor Issues

### Cursor Not Visible

**Issue**: Cursor overlay not showing

**Solution**:
1. Ensure cursor is injected: `await test._ensure_cursor()`
2. Check cursor color contrasts with page background
3. Try different cursor style: `cursor_style="dot"` (more visible)

### Cursor Animation Too Fast/Slow

**Issue**: Cursor moves too quickly or slowly

**Solution**: Adjust animation speed
```python
config.cursor.animation_speed = 0.5  # Slower (0.5 seconds)
config.cursor.animation_speed = 0.1  # Faster (0.1 seconds)
```

## Performance Issues

### Tests Running Slowly

**Issue**: Tests take too long to execute

**Solution**:
1. Reduce `slow_mo`: `config.browser.slow_mo = 0`
2. Disable video if not needed: `config.video.enabled = False`
3. Disable auto screenshots: `config.screenshots.auto = False`
4. Use headless mode: `config.browser.headless = True`

### High Memory Usage

**Issue**: High memory consumption

**Solution**:
1. Close contexts properly after tests
2. Reduce video quality: `config.video.quality = "low"`
3. Limit parallel workers: `runner.run_all(tests, workers=2)`

## YAML Parser Issues

### YAML Syntax Error

**Error**: `yaml.scanner.ScannerError`

**Solution**: Validate YAML syntax
- Use online YAML validator
- Check indentation (YAML is space-sensitive)
- Ensure proper quotes for strings with special characters

### Unknown Action in YAML

**Error**: `Unknown action: invalid_action`

**Solution**: Check supported actions in [API Reference](API.md)
- Valid actions: `login`, `go_to`, `click`, `type`, `select`, etc.

## Browser Issues

### Browser Not Launching

**Error**: Browser launch failed

**Solution**:
1. Install browsers: `playwright install chromium`
2. Check system dependencies (varies by OS)
3. Try different browser: `browser = await p.firefox.launch()`

### Headless Mode Issues

**Issue**: Tests fail in headless but pass in headed mode

**Solution**:
1. Check if page requires JavaScript
2. Verify viewport size matches expectations
3. Check for browser-specific features not available in headless

## Getting Help

If you encounter an issue not covered here:

1. Check the [API Reference](API.md) for method details
2. Review [Examples](EXAMPLES.md) for similar use cases
3. Check [Configuration Guide](CONFIGURATION.md) for settings
4. Open an issue on GitHub with:
   - Error message and traceback
   - Configuration used
   - Minimal reproducible example
   - Environment details (OS, Python version, Playwright version)


