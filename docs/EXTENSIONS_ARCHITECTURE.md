# Arquitetura de Extensões - playwright-simple

## Resumo

A biblioteca está sendo refatorada para ter um **core simples** e **extensões opcionais**.

---

## Library vs Framework

### Quando uma Library vira um Framework?

**Library (Biblioteca):**
- Você controla o fluxo de execução
- Você decide quando chamar as funções
- Não impõe estrutura no seu código
- Exemplos: `requests`, `pandas`, `numpy`

**Framework:**
- Controla o fluxo de execução
- Define a estrutura do seu código
- Você preenche os "buracos" (callbacks, hooks)
- Exemplos: `Django`, `Flask`, `Playwright` (é um framework!)

### playwright-simple: Library com Sistema de Extensões

**playwright-simple é uma LIBRARY**, não um framework, porque:

1. ✅ **Você controla o fluxo**: Você decide quando chamar `test.click()`, `test.type()`, etc.
2. ✅ **Sem lifecycle obrigatório**: Não há hooks obrigatórios como `beforeEach`, `afterEach`
3. ✅ **Extensões são opcionais**: O core funciona sem extensões
4. ✅ **Uso direto**: Você pode usar os métodos diretamente sem seguir uma estrutura pré-definida

**Sistema de Extensões não torna uma Library em Framework:**
- Extensões são plugins opcionais
- Você escolhe quais usar
- Não há "inversão de controle" (você não implementa interfaces obrigatórias)
- É similar ao sistema de plugins do `pytest` ou `click` - ainda são libraries

---

## Estrutura Atual vs Proposta

### Estrutura Atual (Monolítica)
```
core/
├── base.py              # SimpleTestBase (com tudo)
├── video.py             # VideoManager (obrigatório)
├── tts.py               # TTSManager (obrigatório)
├── runner/
│   ├── video_processor.py
│   ├── audio_processor.py
│   └── subtitle_generator.py
└── ...
```

**Problemas:**
- Core carregado com funcionalidades que podem não ser usadas
- Difícil de manter
- Dependências desnecessárias

### Estrutura Proposta (Core + Extensões)
```
core/                    # Core mínimo
├── base.py              # SimpleTestBase (mínimo)
├── interactions.py      # click, type, fill, etc
├── navigation.py        # go_to, navigate
├── auth.py              # login, logout
├── wait.py              # wait, wait_for
├── assertions.py        # assert_text, assert_visible
├── screenshot.py        # screenshot básico
└── yaml_parser.py       # Parser YAML core

extensions/              # Extensões opcionais
├── __init__.py          # Extension base class
├── video/
│   └── extension.py     # VideoExtension
├── audio/
│   └── extension.py     # AudioExtension
└── subtitles/
    └── extension.py     # SubtitleExtension
```

**Vantagens:**
- ✅ Core simples e focado
- ✅ Extensões carregadas apenas se necessárias
- ✅ Fácil adicionar novas extensões
- ✅ Separação clara de responsabilidades

---

## Como Funciona

### 1. Core (obrigatório)
```python
from playwright_simple import SimpleTestBase

test = SimpleTestBase(page, config)

# Funcionalidades core sempre disponíveis
await test.click("Botão")
await test.type("input", "texto")
await test.go_to("Menu > Submenu")
await test.assert_text(".message", "Sucesso")
```

### 2. Extensões (opcionais)
```python
from playwright_simple import SimpleTestBase
from playwright_simple.extensions.video import VideoExtension
from playwright_simple.extensions.audio import AudioExtension

# Criar test
test = SimpleTestBase(page, config)

# Registrar extensões (opcional)
if config.video.enabled:
    video_ext = VideoExtension(config.video)
    test.extensions.register(video_ext)

if config.audio.enabled:
    audio_ext = AudioExtension(config.audio)
    test.extensions.register(audio_ext)

# Agora métodos de extensões estão disponíveis
# (via test.extensions.get('video').pause(), etc)
```

### 3. YAML com Extensões
```yaml
name: "Teste com vídeo"
extensions:
  - video
  - audio

steps:
  - action: go_to
    value: "Menu > Submenu"
  - action: click
    value: "Criar"
  - action: video.start_recording  # Ação da extensão
  - action: fill
    value: "Campo = Valor"
  - action: audio.speak
    text: "Preenchendo formulário"
```

---

## Funções Core (devem estar no YAML)

### Navegação
- `go_to: "menu > submenu"` - Navegação simples
- `navigate: ["menu", "submenu"]` - Navegação por array
- `go_to_url: "/path"` - Navegação direta

### Interações
- `click: "texto ou seletor"` - Clicar
- `type: { selector: "...", text: "..." }` - Digitar
- `fill: "Campo = Valor"` - Preencher campo
- `select: { selector: "...", option: "..." }` - Selecionar
- `hover: "texto ou seletor"` - Passar mouse

### Autenticação
- `login: { username: "...", password: "..." }` - Login
- `logout: true` - Logout

### Esperas
- `wait: 1.0` - Espera simples
- `wait_for: { selector: "...", timeout: 5000 }` - Esperar elemento

### Assertions
- `assert_text: { selector: "...", expected: "..." }` - Verificar texto
- `assert_visible: "seletor"` - Verificar visibilidade
- `assert_count: { selector: "...", expected: 2 }` - Verificar quantidade

### Screenshots
- `screenshot: "nome"` - Captura básica

---

## Funcionalidades que DEVEM SER EXTENSÕES

### ✅ Extensão de Vídeo
- Gravação de vídeo
- Processamento de vídeo
- Configuração de codec/qualidade

### ✅ Extensão de Áudio
- Text-to-Speech (TTS)
- Narração automática
- Processamento de áudio

### ✅ Extensão de Legendas
- Geração de legendas
- Sincronização com vídeo
- Estilização

### ⏳ Extensão de Acessibilidade
- Análise de acessibilidade
- Relatórios
- Validação de ARIA

### ⏳ Extensão de Performance
- Métricas de performance
- Análise de tempo de carregamento
- Lighthouse integration

---

## Status da Refatoração

### ✅ Feito
1. ✅ Estrutura base de extensões criada
2. ✅ `Extension` base class
3. ✅ `ExtensionRegistry` para gerenciar extensões
4. ✅ `VideoExtension` criada (movendo código de `VideoManager`)

### ⏳ Em Progresso
1. ⏳ Mover `VideoManager` → `VideoExtension`
2. ⏳ Mover `TTSManager` → `AudioExtension`
3. ⏳ Mover `SubtitleGenerator` → `SubtitleExtension`
4. ⏳ Atualizar `SimpleTestBase` para suportar extensões
5. ⏳ Atualizar YAML parser para suportar ações de extensões

### 📋 Próximos Passos
1. Completar migração de vídeo/áudio/legendas
2. Atualizar runners para usar extensões
3. Simplificar core removendo dependências
4. Documentar uso de extensões
5. Criar exemplos de extensões customizadas

---

## Vantagens da Abordagem

1. **Core simples**: Fácil de entender e manter
2. **Extensibilidade**: Adicione apenas o que precisa
3. **Performance**: Não carrega código desnecessário
4. **Manutenibilidade**: Mudanças em extensões não afetam core
5. **Testabilidade**: Teste core e extensões separadamente
6. **Flexibilidade**: Fácil criar extensões customizadas

---

## Conclusão

**playwright-simple continua sendo uma LIBRARY**, mesmo com extensões:
- Você controla o fluxo
- Extensões são opcionais
- Não há inversão de controle
- É um sistema de plugins, não um framework

O sistema de extensões torna a library mais **modular** e **flexível**, mas não a transforma em framework.

