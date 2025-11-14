# Playwright Simple

**Automação web simplificada com YAML e Python**

[![Status](https://img.shields.io/badge/status-completo-success)](IMPLEMENTATION_STATUS.md)
[![Fases](https://img.shields.io/badge/fases-12%2F12-success)](IMPLEMENTATION_PLAN.md)

---

## 🚀 Início Rápido

```bash
# Instalar
pip install -e ".[dev]"
playwright install chromium

# Gravar um teste
playwright-simple record meu_teste.yaml --url https://example.com

# Executar um teste
playwright-simple run meu_teste.yaml --video
```

📖 **[Quick Start →](QUICK_START.md)** | 📚 **[Manual Completo →](USER_MANUAL.md)**

---

## ✨ Funcionalidades Principais

### 🎬 Gravação Interativa
Grave suas interações no navegador e gere YAML automaticamente.

```bash
playwright-simple record teste.yaml --url https://example.com
```

### ▶️ Execução de Testes
Execute testes YAML com vídeo, legendas e áudio.

```bash
playwright-simple run teste.yaml --video --subtitles --audio
```

### 🔧 Auto-Fix Inteligente
Correção automática de erros usando contexto completo (HTML, estado, histórico).

### 🔌 Extensão Odoo
Ações específicas para Odoo com sintaxe amigável.

```yaml
- action: login
  login: admin
  password: admin
  
- action: go_to
  go_to: "Vendas > Pedidos"
  
- action: fill
  fill: "Cliente = João Silva"
```

### 📸 Comparação Visual
Detecte regressões visuais comparando screenshots.

### 🔄 Hot Reload
Recarregue YAML e Python automaticamente durante execução.

---

## 📚 Documentação

### Para Usuários
- **[Quick Start](QUICK_START.md)** - Comece em 5 minutos
- **[User Manual](USER_MANUAL.md)** - Manual completo do usuário
- **[Validation Guide](VALIDATION_GUIDE.md)** - Guia de validação e testes
- **[What You Can Use Now](WHAT_YOU_CAN_USE_NOW.md)** - O que está pronto
- **[Hybrid Workflow](docs/HYBRID_WORKFLOW.md)** - Fluxo completo: gravar → editar → executar

### Para Desenvolvedores
- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Plano de implementação completo
- **[Implementation Status](IMPLEMENTATION_STATUS.md)** - Status atual das fases
- **[API Reference](docs/API_REFERENCE.md)** - Referência completa da API
- **[Performance Guide](docs/PERFORMANCE.md)** - Guia de performance

### Tutoriais
- **[Tutorial 1: Testes Básicos](examples/tutorials/tutorial_01_basic_testing.md)**
- **[Tutorial 2: Testes Odoo](examples/tutorials/tutorial_02_odoo_testing.md)**
- **[Tutorial 3: Gravação Interativa](examples/tutorials/tutorial_03_recording.md)**

### Exemplos
- **[Examples](examples/)** - Exemplos práticos
- **[Odoo Examples](examples/odoo/)** - Exemplos específicos para Odoo

---

## 🎯 Status de Implementação

| Fase | Status | Progresso |
|------|--------|-----------|
| FASE 0 | ✅ Completa | 100% |
| FASE 1 | ✅ Completa | 100% |
| FASE 6 | ✅ Completa | 100% |
| FASE 7 | ✅ Completa | 100% |
| FASE 8 | ✅ Completa | 100% |
| FASE 9 | ✅ Completa | 100% |
| FASE 10 | ✅ Completa | 100% |
| FASE 11 | ✅ Completa | 100% |
| FASE 12 | ✅ Completa | 100% |

**Ver [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) para detalhes completos**

---

## 📖 Exemplos

### Exemplo 1: Teste Simples

```yaml
name: Login Test
steps:
  - action: go_to
    url: http://localhost:8069
    
  - action: click
    text: Entrar
    
  - action: type
    text: admin@example.com
    selector: input[name="login"]
    
  - action: click
    text: Login
```

### Exemplo 2: Teste Odoo

```yaml
name: Criar Pedido Odoo
steps:
  - action: login
    login: admin
    password: admin
    
  - action: go_to
    go_to: "Vendas > Pedidos"
    
  - action: click
    click: "Criar"
    
  - action: fill
    fill: "Cliente = João Silva"
    
  - action: click
    click: "Salvar"
```

---

## 🛠️ Instalação

```bash
# Clonar repositório
git clone <repo-url>
cd playwright-simple

# Instalar dependências
pip install -e ".[dev]"

# Instalar browsers
playwright install chromium
```

---

## 📝 Comandos Disponíveis

### Gravar Interações
```bash
playwright-simple record <output.yaml> [--url URL] [--headless] [--debug]
```

### Executar Testes
```bash
playwright-simple run <test.yaml> [--video] [--subtitles] [--audio] [--debug]
```

---

## 🧪 Validação

Quer testar e validar? Consulte o **[Validation Guide](VALIDATION_GUIDE.md)** e use o **[Validation Checklist](VALIDATION_CHECKLIST.md)**.

---

## 🤝 Contribuindo

1. Leia o [Implementation Plan](IMPLEMENTATION_PLAN.md)
2. Veja o [Implementation Status](IMPLEMENTATION_STATUS.md)
3. Siga os padrões de código
4. Adicione testes

---

## 📄 Licença

[Adicione sua licença aqui]

---

## 🔗 Links Úteis

- [Playwright Documentation](https://playwright.dev/python/)
- [YAML Specification](https://yaml.org/spec/)

---

**Última Atualização**: Novembro 2024  
**Status**: ✅ **Todas as fases completas - Pronto para validação**
