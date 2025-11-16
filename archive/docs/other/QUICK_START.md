# Quick Start - Playwright Simple

Guia rápido para começar a usar o playwright-simple em 5 minutos.

---

## 🚀 Instalação Rápida

```bash
cd playwright-simple
pip install -e ".[dev]"
playwright install chromium
```

---

## 📝 Exemplo 1: Gravar um Teste

```bash
# 1. Iniciar gravação
playwright-simple record meu_teste.yaml --url https://example.com

# 2. Interagir no navegador (clique, digite, navegue)

# 3. No console, digite: exit
```

**Resultado**: Arquivo `meu_teste.yaml` criado automaticamente!

---

## ▶️ Exemplo 2: Executar um Teste

```bash
# Executar teste básico
playwright-simple run meu_teste.yaml

# Com vídeo e legendas
playwright-simple run meu_teste.yaml --video --subtitles
```

---

## 🎯 Exemplo 3: Teste YAML Simples

Crie `teste_login.yaml`:

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
    
  - action: type
    text: senha123
    selector: input[name="password"]
    
  - action: click
    text: Login
```

Execute:
```bash
playwright-simple run teste_login.yaml --video
```

---

## 🔌 Exemplo 4: Teste Odoo

Crie `teste_odoo.yaml`:

```yaml
name: Teste Odoo
steps:
  - action: login
    login: admin
    password: admin
    database: devel
    
  - action: go_to
    go_to: "Vendas > Pedidos"
    
  - action: click
    click: "Criar"
    
  - action: fill
    fill: "Cliente = João Silva"
    
  - action: click
    click: "Salvar"
```

Execute:
```bash
playwright-simple run teste_odoo.yaml --video --subtitles
```

---

## 📚 Próximos Passos

- Leia `USER_MANUAL.md` para documentação completa
- Veja `examples/` para mais exemplos
- Consulte `HYBRID_WORKFLOW.md` para fluxo completo

---

**Dúvidas?** Consulte `USER_MANUAL.md` para documentação completa!

