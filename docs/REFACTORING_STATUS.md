# Status da Refatoração - Core Enxuto

## Objetivo

Criar um core mínimo e enxuto focado em facilitar escrita de testes YAML com funcionalidades genéricas para qualquer aplicação web.

---

## ✅ Feito

1. ✅ Documentação criada:
   - `CORE_REFACTORING.md` - Plano completo de refatoração
   - `CORE_MINIMAL_ACTIONS.md` - Ações YAML core mínimas
   - `EXTENSIONS_ARCHITECTURE.md` - Arquitetura de extensões

2. ✅ Estrutura de extensões criada:
   - `extensions/__init__.py` - Extension base class e ExtensionRegistry
   - `extensions/video/extension.py` - VideoExtension (estrutura criada)

3. ✅ Limpeza inicial:
   - Removido `VideoProcessingError` do import em `base.py`

---

## ⏳ Em Progresso

1. ⏳ Remover dependências de extensões do core:
   - [ ] Remover `VideoManager` do `__init__.py` do core
   - [ ] Remover `TTSManager` do `__init__.py` do core
   - [ ] Remover `VideoConfig` do `config.py` (mover para extensão)
   - [ ] Remover `VideoProcessingError` de `exceptions.py` (mover para extensão)
   - [ ] Remover `TTSGenerationError` de `exceptions.py` (mover para extensão)

2. ⏳ Adicionar sistema de extensões ao SimpleTestBase:
   - [ ] Adicionar `ExtensionRegistry` ao `SimpleTestBase`
   - [ ] Método `register_extension()` no `SimpleTestBase`
   - [ ] Inicializar extensões no `__init__`

3. ⏳ Atualizar YAML parser:
   - [ ] Suportar apenas ações core
   - [ ] Permitir extensões registrarem ações
   - [ ] Executar ações de extensões se registradas

---

## 📋 Próximos Passos

### Fase 1: Limpar Core (Prioridade Alta)
1. Mover `VideoConfig` para `extensions/video/config.py`
2. Mover `VideoManager` para `extensions/video/extension.py` (já iniciado)
3. Mover `TTSManager` para `extensions/audio/extension.py`
4. Mover `SubtitleGenerator` para `extensions/subtitles/extension.py`
5. Remover exports de extensões do `core/__init__.py`
6. Simplificar `TestConfig` removendo configs de extensões

### Fase 2: Sistema de Extensões (Prioridade Alta)
1. Adicionar `ExtensionRegistry` ao `SimpleTestBase`
2. Implementar registro de extensões
3. Atualizar YAML parser para suportar ações de extensões
4. Criar extensões completas (video, audio, subtitles)

### Fase 3: Simplificar YAML Parser (Prioridade Média)
1. Manter apenas ações core no parser base
2. Permitir extensões registrarem suas ações
3. Simplificar estrutura de steps

### Fase 4: Testes e Documentação (Prioridade Baixa)
1. Testar core isolado
2. Testar extensões isoladas
3. Documentar uso de extensões
4. Criar exemplos

---

## Estrutura Final Desejada

```
core/
├── base.py              # SimpleTestBase (com ExtensionRegistry)
├── yaml_parser.py       # Parser YAML (core + extensões)
├── config.py            # TestConfig (sem configs de extensões)
├── interactions.py       # click, type, fill, etc
├── navigation.py        # go_to, navigate, etc
├── auth.py              # login, logout
├── wait.py              # wait, wait_for
├── assertions.py        # assert_text, assert_visible
├── screenshot.py        # screenshot básico
├── cursor.py            # cursor visual
└── ... (outros módulos core)

extensions/
├── video/
│   ├── extension.py     # VideoExtension
│   └── config.py        # VideoConfig
├── audio/
│   ├── extension.py     # AudioExtension
│   └── tts.py           # TTSManager movido
└── subtitles/
    └── extension.py     # SubtitleExtension
```

---

## Checklist de Limpeza

### Core
- [ ] Remover `VideoManager` do `core/__init__.py`
- [ ] Remover `TTSManager` do `core/__init__.py`
- [ ] Remover `VideoConfig` do `core/config.py`
- [ ] Remover `VideoProcessingError` do `core/exceptions.py`
- [ ] Remover `TTSGenerationError` do `core/exceptions.py`
- [ ] Simplificar `TestConfig` (remover configs de extensões)
- [ ] Adicionar `ExtensionRegistry` ao `SimpleTestBase`

### Extensões
- [ ] Completar `VideoExtension` (mover código de `VideoManager`)
- [ ] Criar `AudioExtension` (mover código de `TTSManager`)
- [ ] Criar `SubtitleExtension` (mover código de `SubtitleGenerator`)
- [ ] Criar configs de extensões separadas

### YAML Parser
- [ ] Suportar apenas ações core
- [ ] Permitir extensões registrarem ações
- [ ] Executar ações de extensões

---

## Notas

- Core deve ser **mínimo** e **genérico**
- Extensões são **opcionais** e **pluggáveis**
- YAML parser deve ser **simples** e **extensível**

