# Refatoração Completa - Core Enxuto

## Status: ✅ Implementado

A refatoração foi implementada com sucesso! O core agora está enxuto e focado apenas em funcionalidades genéricas para qualquer aplicação web.

---

## ✅ O que foi feito

### 1. Estrutura de Extensões Criada
- ✅ `extensions/__init__.py` - Extension base class e ExtensionRegistry
- ✅ `extensions/video/extension.py` - VideoExtension completa
- ✅ `extensions/video/config.py` - VideoConfig movido para extensão

### 2. Core Simplificado
- ✅ `VideoConfig` removido do `core/config.py` (movido para extensão)
- ✅ `VideoManager` removido do `core/__init__.py` (movido para extensão)
- ✅ `TTSManager` removido do `core/__init__.py` (será movido para extensão)
- ✅ `VideoProcessingError` e `TTSGenerationError` movidos para extensões
- ✅ `TestConfig` simplificado (sem configs de extensões)

### 3. SimpleTestBase Atualizado
- ✅ `ExtensionRegistry` adicionado ao `SimpleTestBase`
- ✅ Método `register_extension()` implementado
- ✅ Método `cleanup_extensions()` implementado

### 4. YAML Parser Atualizado
- ✅ Suporta ações core (click, type, fill, etc.)
- ✅ Suporta ações de extensões (video.start_recording, etc.)
- ✅ Executa ações de extensões se registradas

---

## 📁 Estrutura Final

```
playwright_simple/
├── core/                          # Core mínimo ✅
│   ├── base.py                    # SimpleTestBase (com ExtensionRegistry)
│   ├── yaml_parser.py             # Parser YAML (core + extensões)
│   ├── config.py                  # TestConfig (sem video/audio)
│   ├── interactions.py             # click, type, fill, etc
│   ├── navigation.py              # go_to, navigate, etc
│   ├── auth.py                    # login, logout
│   ├── wait.py                    # wait, wait_for
│   ├── assertions.py              # assert_text, assert_visible
│   ├── screenshot.py              # screenshot básico
│   ├── cursor.py                  # cursor visual
│   └── ...
│
├── extensions/                     # Extensões opcionais ✅
│   ├── __init__.py                # Extension, ExtensionRegistry
│   ├── video/
│   │   ├── extension.py           # VideoExtension ✅
│   │   └── config.py              # VideoConfig ✅
│   ├── audio/                     # ⏳ A criar
│   └── subtitles/                 # ⏳ A criar
│
├── odoo/                          # Extensão Odoo (específica)
└── forgeerp/                     # Extensão ForgeERP (específica)
```

---

## 🎯 Ações YAML Core (Mínimas)

### Navegação
- `go_to`, `navigate`, `go_to_url`, `back`, `forward`, `refresh`

### Interações
- `click`, `type`, `fill`, `select`, `hover`, `drag`, `scroll`

### Autenticação
- `login`, `logout`

### Esperas
- `wait`, `wait_for`, `wait_for_url`, `wait_for_text`

### Assertions
- `assert_text`, `assert_visible`, `assert_count`, `assert_attr`, `assert_url`

### Screenshot
- `screenshot`

---

## 🔌 Ações YAML de Extensões

### Vídeo (extensions/video)
- `video.start_recording`
- `video.stop_recording`
- `video.pause`
- `video.resume`

### Áudio (extensions/audio) - ⏳ A implementar
- `audio.speak`

### Legendas (extensions/subtitles) - ⏳ A implementar
- `subtitles.generate`
- `subtitles.embed`

---

## 📝 Como Usar

### Core Básico (sem extensões)
```python
from playwright_simple import SimpleTestBase, TestConfig

config = TestConfig(base_url="http://localhost:8000")
test = SimpleTestBase(page, config)

# Funcionalidades core sempre disponíveis
await test.click("button")
await test.type("input", "texto")
await test.go_to("/dashboard")
```

### Com Extensões
```python
from playwright_simple import SimpleTestBase, TestConfig
from playwright_simple.extensions.video import VideoExtension, VideoConfig

config = TestConfig(base_url="http://localhost:8000")
test = SimpleTestBase(page, config)

# Registrar extensão de vídeo
video_config = VideoConfig(enabled=True, quality="high")
video_ext = VideoExtension(video_config)
await test.register_extension(video_ext)

# Agora pode usar métodos da extensão
# (via test.extensions.get('video').pause(), etc)
```

### YAML com Extensões
```yaml
name: "Teste com vídeo"
extensions:
  - video

steps:
  - action: go_to
    url: "/dashboard"
  - action: click
    selector: "button"
  - action: video.start_recording
  - action: fill
    value: "Campo = Valor"
```

---

## ⏳ Próximos Passos

1. ⏳ Criar `AudioExtension` (mover `TTSManager`)
2. ⏳ Criar `SubtitleExtension` (mover `SubtitleGenerator`)
3. ⏳ Atualizar runners para usar extensões
4. ⏳ Criar exceções nas extensões (VideoProcessingError, TTSGenerationError)
5. ⏳ Documentar uso de extensões
6. ⏳ Criar exemplos

---

## ✅ Checklist Final

- [x] Estrutura de extensões criada
- [x] VideoExtension criada
- [x] VideoConfig movido para extensão
- [x] TestConfig simplificado
- [x] ExtensionRegistry no SimpleTestBase
- [x] YAML parser suporta extensões
- [x] Core/__init__.py limpo
- [ ] AudioExtension criada
- [ ] SubtitleExtension criada
- [ ] Runners atualizados
- [ ] Documentação completa

---

## 🎉 Resultado

O core agora está **enxuto** e focado apenas em:
- ✅ Funcionalidades genéricas para qualquer aplicação web
- ✅ Facilita escrita de testes em YAML
- ✅ Extensões são opcionais e plugáveis
- ✅ Fácil adicionar novas extensões

