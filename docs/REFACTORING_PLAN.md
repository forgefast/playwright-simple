# Plano de Refatoração - Core + Extensões

## Objetivo

Simplificar o core e separar funcionalidades avançadas em extensões.

---

## Funções CORE (devem estar no YAML)

### Navegação (simples)
- `go_to: "menu > submenu"` - Navegação simples por texto
- `navigate: ["menu", "submenu"]` - Navegação por array
- `go_to_url: "/path"` - Navegação direta por URL

### Interações Básicas
- `click: "texto ou seletor"` - Clicar em elemento
- `type: { selector: "...", text: "..." }` - Digitar texto
- `fill: "Campo = Valor"` - Preencher campo (formato amigável)
- `select: { selector: "...", option: "..." }` - Selecionar opção
- `hover: "texto ou seletor"` - Passar mouse sobre elemento

### Autenticação
- `login: { username: "...", password: "..." }` - Login básico
- `logout: true` - Logout

### Esperas
- `wait: 1.0` - Espera simples (segundos)
- `wait_for: { selector: "...", timeout: 5000 }` - Esperar elemento aparecer

### Assertions
- `assert_text: { selector: "...", expected: "..." }` - Verificar texto
- `assert_visible: "seletor"` - Verificar visibilidade
- `assert_count: { selector: "...", expected: 2 }` - Verificar quantidade

### Screenshots
- `screenshot: "nome"` - Captura de tela básica

---

## Funcionalidades que DEVEM SER EXTENSÕES

### Extensão de Vídeo
- Gravação de vídeo
- Processamento de vídeo
- Configuração de codec, qualidade, etc.

### Extensão de Áudio
- Text-to-Speech (TTS)
- Narração automática
- Processamento de áudio

### Extensão de Legendas
- Geração de legendas
- Sincronização com vídeo
- Estilização de legendas

### Extensão de Acessibilidade
- Análise de acessibilidade
- Geração de relatórios
- Validação de ARIA

### Extensão de Performance
- Métricas de performance
- Análise de tempo de carregamento
- Lighthouse integration

### Extensão de Odoo (específica)
- Navegação de menus Odoo
- Preenchimento de campos Odoo
- Workflows específicos

### Extensão de ForgeERP (específica)
- Workflows de provisionamento
- Workflows de deploy
- Integração com ForgeERP

---

## Estrutura Proposta

```
playwright_simple/
├── core/                    # Core mínimo e simples
│   ├── base.py             # SimpleTestBase (mínimo)
│   ├── interactions.py     # click, type, fill, select, hover
│   ├── navigation.py       # go_to, navigate, go_to_url
│   ├── auth.py             # login, logout (básico)
│   ├── wait.py             # wait, wait_for
│   ├── assertions.py       # assert_text, assert_visible, etc
│   ├── screenshot.py       # screenshot básico
│   ├── yaml_parser.py      # Parser YAML core
│   └── config.py           # Configuração básica
│
├── extensions/              # Extensões opcionais
│   ├── __init__.py
│   ├── video/              # Extensão de vídeo
│   │   ├── __init__.py
│   │   ├── recorder.py     # Gravação
│   │   ├── processor.py    # Processamento
│   │   └── config.py       # Config de vídeo
│   │
│   ├── audio/              # Extensão de áudio
│   │   ├── __init__.py
│   │   ├── tts.py          # Text-to-Speech
│   │   ├── processor.py    # Processamento
│   │   └── config.py
│   │
│   ├── subtitles/           # Extensão de legendas
│   │   ├── __init__.py
│   │   ├── generator.py    # Geração
│   │   ├── sync.py         # Sincronização
│   │   └── config.py
│   │
│   ├── accessibility/      # Extensão de acessibilidade
│   │   ├── __init__.py
│   │   ├── analyzer.py     # Análise
│   │   └── reporter.py     # Relatórios
│   │
│   └── performance/        # Extensão de performance
│       ├── __init__.py
│       ├── metrics.py       # Métricas
│       └── reporter.py
│
├── odoo/                    # Extensão Odoo (específica)
│   ├── base.py             # OdooTestBase
│   ├── navigation.py       # Navegação Odoo
│   ├── forms.py            # Formulários Odoo
│   └── yaml_parser.py      # Parser YAML Odoo
│
└── forgeerp/               # Extensão ForgeERP (específica)
    ├── base.py
    ├── workflows.py
    └── yaml_parser.py
```

---

## Como Funciona

### Core (obrigatório)
```python
from playwright_simple import SimpleTestBase

test = SimpleTestBase(page, config)
await test.click("Botão")
await test.type("input", "texto")
await test.go_to("Menu > Submenu")
```

### Extensões (opcionais)
```python
from playwright_simple import SimpleTestBase
from playwright_simple.extensions.video import VideoExtension
from playwright_simple.extensions.audio import AudioExtension

# Registrar extensões
test = SimpleTestBase(page, config)
test.register_extension(VideoExtension(config.video))
test.register_extension(AudioExtension(config.audio))

# Agora test tem métodos de vídeo e áudio
await test.start_recording()
await test.speak("Texto para narração")
```

### YAML com Extensões
```yaml
name: "Teste com vídeo e áudio"
extensions:
  - video
  - audio
  - subtitles

steps:
  - action: go_to
    value: "Menu > Submenu"
  - action: click
    value: "Criar"
  - action: fill
    value: "Campo = Valor"
  - action: video.start_recording  # Ação da extensão
  - action: audio.speak
    text: "Preenchendo formulário"
```

---

## Library vs Framework

### Library
- Fornece funções/classes que você chama
- Você controla o fluxo
- Exemplo: `requests`, `pandas`

### Framework
- Define a estrutura do seu código
- Controla o fluxo de execução
- Você preenche os "buracos"
- Exemplo: `Django`, `Flask`, `Playwright` (é um framework!)

### playwright-simple: Library com Extensões
- **Core**: Library pura (você chama métodos)
- **Extensões**: Sistema opcional de plugins
- **YAML**: Parser que converte YAML em chamadas de métodos

**Não é um framework** porque:
- Você controla quando chamar os métodos
- Não há "lifecycle" obrigatório
- Extensões são opcionais e plugáveis

**É uma library** porque:
- Fornece classes e métodos reutilizáveis
- Você decide quando e como usar
- Pode ser usada em qualquer contexto

---

## Vantagens da Abordagem de Extensões

1. **Core simples**: Fácil de entender e manter
2. **Extensibilidade**: Adicione apenas o que precisa
3. **Separação de responsabilidades**: Cada extensão tem seu propósito
4. **Testabilidade**: Teste core e extensões separadamente
5. **Performance**: Não carrega código desnecessário
6. **Manutenibilidade**: Mudanças em extensões não afetam core

---

## Próximos Passos

1. ✅ Mapear funções core (FEITO)
2. ⏳ Criar estrutura de extensões
3. ⏳ Mover vídeo/áudio/legendas para extensões
4. ⏳ Simplificar core
5. ⏳ Criar sistema de registro de extensões
6. ⏳ Atualizar YAML parser para suportar extensões

