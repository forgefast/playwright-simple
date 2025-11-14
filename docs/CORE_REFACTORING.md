# Refatoração do Core - Core Enxuto

## Objetivo

Criar um **core mínimo e enxuto** que:
- Facilita escrita de testes em YAML
- Funcionalidades simples e genéricas para qualquer aplicação web
- Tudo que não for essencial vira extensão

---

## Core Mínimo (o que DEVE ficar)

### 1. YAML Parser
- `yaml_parser.py` - Parser básico para YAML
- Suporta ações core apenas
- Extensível para ações de extensões

### 2. Interações Básicas
- `interactions.py` - click, type, fill, select, hover, drag, scroll
- Genérico para qualquer aplicação web
- Usa cursor visual (essencial para visualização)

### 3. Navegação Básica
- `navigation.py` - go_to, navigate, go_to_url, back, forward, refresh
- Genérico para qualquer aplicação web

### 4. Autenticação Básica
- `auth.py` - login, logout (genérico)
- Apenas o básico (username, password, URL)

### 5. Esperas
- `wait.py` - wait, wait_for, wait_for_url, wait_for_text
- Genérico para qualquer aplicação web

### 6. Assertions
- `assertions.py` - assert_text, assert_visible, assert_count, assert_attr
- Genérico para qualquer aplicação web

### 7. Screenshot Básico
- `screenshot.py` - screenshot simples
- Apenas captura básica

### 8. Cursor Visual
- `cursor.py` - Visualização do cursor (essencial para visualização)
- `cursor_movement.py`, `cursor_effects.py`, etc.

### 9. Helpers Essenciais
- `helpers.py` - TestBaseHelpers (preparação de elementos)
- `selectors.py` - SelectorManager (busca de elementos)
- `exceptions.py` - Exceções customizadas
- `config.py` - Configuração básica

### 10. Base Class
- `base.py` - SimpleTestBase (mínimo)
- Apenas o essencial, sem dependências de extensões

---

## O que DEVE VIRAR EXTENSÃO

### ❌ Vídeo
- `video.py` → `extensions/video/extension.py`
- Gravação de vídeo não é essencial

### ❌ Áudio/TTS
- `tts.py` → `extensions/audio/extension.py`
- Text-to-Speech não é essencial

### ❌ Legendas
- `runner/subtitle_generator.py` → `extensions/subtitles/extension.py`
- Legendas não são essenciais

### ❌ Processamento de Vídeo/Áudio
- `runner/video_processor.py` → `extensions/video/processor.py`
- `runner/audio_processor.py` → `extensions/audio/processor.py`
- Processamento não é essencial

### ❌ Runner Complexo
- `runner/` → Simplificar ou mover para extensão
- Runner básico pode ficar, mas complexo vira extensão

### ❌ Odoo Específico
- `odoo/` → Já é extensão (específica)
- Não deve estar no core

### ❌ ForgeERP Específico
- `forgeerp/` → Já é extensão (específica)
- Não deve estar no core

### ❌ Funcionalidades Avançadas
- Acessibilidade → `extensions/accessibility/`
- Performance → `extensions/performance/`
- HTMX → `extensions/htmx/` (se necessário)

---

## Estrutura Final Proposta

```
playwright_simple/
├── core/                          # Core mínimo
│   ├── __init__.py
│   ├── base.py                    # SimpleTestBase (mínimo)
│   ├── yaml_parser.py             # Parser YAML básico
│   ├── interactions.py             # click, type, fill, select, hover
│   ├── navigation.py              # go_to, navigate, go_to_url
│   ├── auth.py                    # login, logout (básico)
│   ├── wait.py                    # wait, wait_for
│   ├── assertions.py              # assert_text, assert_visible
│   ├── screenshot.py              # screenshot básico
│   ├── cursor.py                  # Cursor visual (essencial)
│   ├── cursor_movement.py
│   ├── cursor_effects.py
│   ├── cursor_elements.py
│   ├── cursor_injection.py
│   ├── cursor_styles.py
│   ├── helpers.py                 # TestBaseHelpers
│   ├── selectors.py               # SelectorManager
│   ├── queries.py                 # get_text, get_attr, is_visible
│   ├── forms.py                   # fill_form (genérico)
│   ├── ui_helpers.py              # wait_for_modal, click_button (genérico)
│   ├── config.py                  # TestConfig (básico)
│   ├── constants.py
│   ├── exceptions.py
│   └── session.py                 # SessionManager (básico)
│
├── extensions/                     # Extensões opcionais
│   ├── __init__.py                # Extension base, ExtensionRegistry
│   ├── video/
│   │   ├── __init__.py
│   │   ├── extension.py
│   │   └── processor.py
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── extension.py
│   │   └── tts.py
│   ├── subtitles/
│   │   ├── __init__.py
│   │   └── extension.py
│   ├── accessibility/
│   │   └── extension.py
│   └── performance/
│       └── extension.py
│
├── odoo/                          # Extensão Odoo (específica)
│   └── ...
│
└── forgeerp/                      # Extensão ForgeERP (específica)
    └── ...
```

---

## Ações YAML Core (mínimas)

### Navegação
```yaml
- action: go_to
  url: "/path"

- action: navigate
  menu_path: ["Menu", "Submenu"]

- action: go_to_url
  url: "https://example.com"
```

### Interações
```yaml
- action: click
  selector: "button"
  description: "Botão submit"

- action: type
  selector: "input"
  text: "texto"

- action: fill
  value: "Campo = Valor"

- action: select
  selector: "select"
  option: "opção"

- action: hover
  selector: "element"
```

### Autenticação
```yaml
- action: login
  username: "user"
  password: "pass"
  url: "/login"

- action: logout
```

### Esperas
```yaml
- action: wait
  seconds: 1.0

- action: wait_for
  selector: ".element"
  timeout: 5000
```

### Assertions
```yaml
- action: assert_text
  selector: ".message"
  expected: "Sucesso"

- action: assert_visible
  selector: ".element"

- action: assert_count
  selector: ".items"
  expected: 5
```

### Screenshot
```yaml
- action: screenshot
  name: "tela-inicial"
```

---

## Plano de Refatoração

### Fase 1: Limpar Core
1. ✅ Identificar dependências de extensões no core
2. ⏳ Remover imports de vídeo/áudio/legendas do core
3. ⏳ Simplificar `SimpleTestBase` removendo dependências opcionais
4. ⏳ Mover `VideoManager` → `VideoExtension`
5. ⏳ Mover `TTSManager` → `AudioExtension`
6. ⏳ Mover `SubtitleGenerator` → `SubtitleExtension`

### Fase 2: Sistema de Extensões
1. ✅ Criar estrutura base de extensões
2. ⏳ Implementar `ExtensionRegistry` no `SimpleTestBase`
3. ⏳ Atualizar YAML parser para suportar ações de extensões
4. ⏳ Criar extensões de vídeo/áudio/legendas

### Fase 3: Simplificar YAML Parser
1. ⏳ Manter apenas ações core no parser base
2. ⏳ Permitir extensões registrarem suas ações
3. ⏳ Simplificar estrutura de steps

### Fase 4: Testes e Documentação
1. ⏳ Testar core isolado
2. ⏳ Testar extensões isoladas
3. ⏳ Documentar uso de extensões
4. ⏳ Criar exemplos

---

## Princípios do Core

1. **Mínimo necessário**: Apenas o essencial para testes web genéricos
2. **Genérico**: Funciona para qualquer aplicação web
3. **Simples**: Fácil de entender e usar
4. **YAML-first**: Focado em facilitar escrita de testes em YAML
5. **Extensível**: Fácil adicionar extensões sem modificar core

---

## Checklist de Limpeza

- [ ] Remover `VideoManager` do core
- [ ] Remover `TTSManager` do core
- [ ] Remover `SubtitleGenerator` do core
- [ ] Remover processadores de vídeo/áudio do core
- [ ] Simplificar `TestConfig` (remover configs de extensões)
- [ ] Atualizar `SimpleTestBase` para usar extensões
- [ ] Atualizar YAML parser para suportar extensões
- [ ] Mover código específico de Odoo/ForgeERP para suas extensões
- [ ] Documentar core mínimo
- [ ] Criar exemplos de uso do core isolado

