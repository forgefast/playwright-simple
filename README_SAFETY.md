# Sistema de Segurança do Projeto

Este projeto usa um sistema universal de prevenção de erros automáticos.

## Setup

O sistema já foi configurado. Para aplicar em outros projetos:

```bash
~/.cursor/scripts/setup-project-safety.sh /path/to/project
```

## Validação Manual

Execute validações manualmente:

```bash
~/.cursor/scripts/validate.sh /path/to/project
```

## Testes Críticos

Os testes críticos estão em `tests/test_critical_paths.py`. Estes testes DEVEM SEMPRE passar.

Execute-os com:

```bash
pytest tests/test_critical_paths.py -v
```

## Pre-commit Hook

O pre-commit hook valida automaticamente antes de cada commit:
- Testes críticos
- Sintaxe Python
- Imports
- Linting básico
- Type checking básico

## Configuração

Edite `.project-safety.json` para ajustar validações.

## Documentação

- `docs/CRITICAL_AREAS.md`: Áreas críticas do projeto
- `~/.cursor/docs/DEVELOPMENT_STANDARDS.md`: Padrões universais
