# Tutorial 2: Testes Odoo

**Nível**: Intermediário  
**Tempo**: 15 minutos

---

## Objetivo

Criar e executar testes para Odoo.

---

## Passo 1: Criar Teste Odoo

Crie um arquivo `teste_odoo.yaml`:

```yaml
name: Teste Odoo Básico
description: Login e navegação no Odoo

steps:
  - action: login
    login: admin
    password: admin
    database: devel
    description: Fazer login
    
  - action: go_to
    go_to: "Vendas > Pedidos"
    description: Navegar para Pedidos
    
  - action: wait
    seconds: 2
    description: Aguardar página carregar
```

---

## Passo 2: Executar Teste

```bash
playwright-simple run teste_odoo.yaml --video
```

---

## Passo 3: Adicionar CRUD

Edite o YAML para criar um registro:

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
    
  - action: fill
    fill: "Data = 01/01/2024"
    
  - action: click
    click: "Salvar"
```

---

## Passo 4: Executar com Legendas

```bash
playwright-simple run teste_odoo.yaml --video --subtitles
```

---

## Próximos Passos

- [Tutorial 3: Gravação Interativa](tutorial_03_recording.md)
- [Tutorial 4: Auto-Fix](tutorial_04_auto_fix.md)

---

**Concluído!** 🎉

