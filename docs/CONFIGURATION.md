# Configuration Guide

Playwright Simple supports multiple ways to configure your tests.

## Configuration Priority

1. **Runtime parameters** (highest priority)
2. **Environment variables**
3. **Config file** (YAML/JSON)
4. **Default values** (lowest priority)

## Configuration Methods

### 1. Code Configuration

```python
from playwright_simple import TestConfig

config = TestConfig(
    base_url="http://localhost:8000",
    cursor_style="arrow",
    cursor_color="#007bff",
    video_enabled=True,
    screenshots_auto=True,
)
```

### 2. YAML Config File

Create `config.yaml`:

```yaml
base_url: "http://localhost:8000"
viewport:
  width: 1920
  height: 1080

cursor:
  style: "arrow"  # arrow, dot, circle, custom
  color: "#007bff"
  size: "medium"  # small, medium, large
  animation_speed: 0.3

video:
  enabled: true
  quality: "high"  # low, medium, high
  codec: "webm"    # webm, mp4
  dir: "videos"

screenshots:
  auto: true
  on_failure: true
  dir: "screenshots"
  format: "png"   # png, jpeg
  full_page: false

browser:
  headless: false
  slow_mo: 10
  timeout: 30000
  locale: "pt-BR"
```

Load it:

```python
config = TestConfig.from_file("config.yaml")
```

### 3. JSON Config File

Create `config.json`:

```json
{
  "base_url": "http://localhost:8000",
  "cursor": {
    "style": "arrow",
    "color": "#007bff"
  },
  "video": {
    "enabled": true,
    "quality": "high"
  }
}
```

Load it:

```python
config = TestConfig.from_file("config.json")
```

### 4. Environment Variables

Set environment variables:

```bash
export PLAYWRIGHT_SIMPLE_BASE_URL="http://localhost:8000"
export PLAYWRIGHT_SIMPLE_CURSOR_STYLE="arrow"
export PLAYWRIGHT_SIMPLE_CURSOR_COLOR="#007bff"
export PLAYWRIGHT_SIMPLE_VIDEO_ENABLED="true"
export PLAYWRIGHT_SIMPLE_HEADLESS="false"
```

Load them:

```python
config = TestConfig.from_env()
```

### 5. Combined Configuration

```python
# Load from file, override with env vars, then runtime params
config = TestConfig.load(
    config_file="config.yaml",
    use_env=True,
    base_url="http://custom-url:8000",  # Runtime override
    cursor_style="dot"
)
```

## Configuration Options

### Base Configuration

- `base_url` (str): Base URL for tests (default: "http://localhost:8000")

### Cursor Configuration

- `cursor.style` (str): Cursor style - "arrow", "dot", "circle", "custom" (default: "arrow")
- `cursor.color` (str): Cursor color in hex format (default: "#007bff")
- `cursor.size` (str/int): Cursor size - "small", "medium", "large", or pixels (default: "medium")
- `cursor.animation_speed` (float): Animation speed in seconds (default: 0.3)
- `cursor.click_effect` (bool): Show click effect (default: True)
- `cursor.click_effect_color` (str): Click effect color (default: "#007bff")
- `cursor.hover_effect` (bool): Show hover effect (default: True)
- `cursor.hover_effect_color` (str): Hover effect color (default: "#0056b3")

### Video Configuration

- `video.enabled` (bool): Enable video recording (default: True)
- `video.quality` (str): Video quality - "low", "medium", "high" (default: "high")
- `video.codec` (str): Video codec - "webm", "mp4" (default: "webm")
- `video.dir` (str): Directory for videos (default: "videos")
- `video.record_per_test` (bool): One video per test vs global (default: True)
- `video.pause_on_failure` (bool): Pause video on failure (default: False)

### Screenshot Configuration

- `screenshots.auto` (bool): Automatic screenshots on actions (default: True)
- `screenshots.on_failure` (bool): Screenshot on test failure (default: True)
- `screenshots.dir` (str): Directory for screenshots (default: "screenshots")
- `screenshots.format` (str): Screenshot format - "png", "jpeg" (default: "png")
- `screenshots.full_page` (bool): Full page vs viewport only (default: False)

### Browser Configuration

- `browser.headless` (bool): Run in headless mode (default: True)
- `browser.slow_mo` (int): Slow down operations in milliseconds (default: 10)
- `browser.timeout` (int): Default timeout in milliseconds (default: 30000)
- `browser.navigation_timeout` (int): Navigation timeout in milliseconds (default: 30000)
- `browser.locale` (str): Browser locale (default: "pt-BR")
- `browser.viewport` (dict): Viewport size - `{"width": 1920, "height": 1080}`

## Saving Configuration

Save your configuration to a file:

```python
config = TestConfig(...)
config.save("my_config.yaml", format="yaml")
config.save("my_config.json", format="json")
```

## Validation

Configuration is automatically validated on creation. Invalid values will raise `ValueError` with clear error messages.

Example:

```python
# This will raise ValueError
config = TestConfig(cursor_style="invalid")  # Must be: arrow, dot, circle, custom
```


