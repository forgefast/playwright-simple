# Tutorial 1: Testes Básicos

**Nível**: Iniciante  
**Tempo**: 10 minutos

---

## Objetivo

Criar e executar seu primeiro teste automatizado.

---

## Passo 1: Criar Teste YAML

Crie um arquivo `meu_primeiro_teste.yaml`:

```yaml
name: Meu Primeiro Teste
description: Teste básico de exemplo

steps:
  - action: go_to
    url: https://example.com
    description: Navegar para example.com
    
  - action: wait
    seconds: 2
    description: Aguardar página carregar
    
  - action: assert_visible
    selector: body
    description: Verificar que página carregou
```

---

## Passo 2: Executar Teste

```bash
playwright-simple run meu_primeiro_teste.yaml
```

---

## Passo 3: Adicionar Interações

Edite o YAML para adicionar interações:

```yaml
name: Meu Primeiro Teste
steps:
  - action: go_to
    url: https://example.com
    
  - action: click
    text: "More information"
    description: Clicar em link
    
  - action: wait_for
    selector: h1
    timeout: 5000
    description: Aguardar título aparecer
```

---

## Passo 4: Executar com Vídeo

```bash
playwright-simple run meu_primeiro_teste.yaml --video
```

O vídeo será salvo em `videos/meu_primeiro_teste.mp4`.

---

## Próximos Passos

- [Tutorial 2: Testes Odoo](tutorial_02_odoo_testing.md)
- [Tutorial 3: Gravação Interativa](tutorial_03_recording.md)

---

**Concluído!** 🎉

