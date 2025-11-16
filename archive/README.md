# Archive - Arquivos Antigos e Não Utilizados

Este diretório contém arquivos antigos, código legado e documentação desatualizada que não são mais utilizados pela stack funcional atual do projeto.

## Estrutura

```
archive/
├── code/              # Código legado
│   ├── core_legacy/   # Código antigo do core (base.py, runner.py, etc)
│   ├── odoo_legacy/   # Extensão Odoo (não usada pela stack funcional)
│   ├── forgeerp_legacy/ # Extensão ForgeERP (não usada pela stack funcional)
│   ├── cli_legacy/    # CLI antiga (não usada pela stack funcional)
│   └── backups/       # Arquivos .backup
├── docs/              # Documentação antiga/desatualizada
│   ├── handoff/       # Documentos HANDOFF*.md
│   ├── implementation/ # Documentos IMPLEMENTATION*.md
│   ├── refactoring/    # Documentos REFACTORING*.md e refactoring_plan/
│   ├── analysis/      # Análises e investigações (ANALYSIS*.md, etc)
│   └── other/         # Outros documentos desatualizados
├── tests/             # Testes antigos
│   ├── old_tests/     # Testes antigos da raiz (test_*.py, test_*.yaml, test_*.log)
│   └── validation/     # Pasta validation/ (se não usada)
└── scripts/           # Scripts antigos
```

## Stack Funcional Atual

A stack funcional atual utiliza apenas:

- `playwright_simple/core/recorder/` - Módulo de gravação/reprodução
- `playwright_simple/core/video/` - Processamento de vídeo
- `playwright_simple/core/tts.py` - Text-to-Speech
- `test_full_cycle_with_video.py` - Teste principal
- `test_replay_yaml_with_video.py` - Script de reprodução

## Como Consultar

Para encontrar arquivos específicos:

1. **Código legado**: Procure em `code/core_legacy/`, `code/odoo_legacy/`, etc.
2. **Documentação**: Procure em `docs/handoff/`, `docs/implementation/`, etc.
3. **Testes antigos**: Procure em `tests/old_tests/`
4. **Scripts**: Procure em `scripts/`

## Nota

Estes arquivos são mantidos apenas para referência histórica e consulta. Eles não são mais utilizados pela stack funcional e podem ser removidos no futuro se necessário.

