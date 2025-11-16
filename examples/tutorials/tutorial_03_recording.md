# Tutorial 3: Gravação Interativa

**Nível**: Intermediário  
**Tempo**: 10 minutos

---

## Objetivo

Gravar interações e gerar YAML automaticamente.

---

## Passo 1: Iniciar Gravação

```bash
playwright-simple record meu_teste.yaml --url https://example.com
```

---

## Passo 2: Interagir no Navegador

1. O navegador abre automaticamente
2. Clique, digite, navegue normalmente
3. Todas as interações são gravadas

---

## Passo 3: Adicionar Legendas

No console, digite:

```
caption "Realizando login"
```

---

## Passo 4: Adicionar Áudio

No console, digite:

```
audio "Agora vou fazer login no sistema"
```

---

## Passo 5: Salvar e Sair

No console, digite:

```
exit
```

O arquivo YAML será gerado automaticamente!

---

## Passo 6: Editar YAML Gerado

Edite o YAML gerado para ajustar:

```yaml
name: Gravação Automática
steps:
  - action: go_to
    url: https://example.com
    
  - caption: Realizando login
  
  - action: click
    text: Entrar
```

---

## Passo 7: Executar Teste Gravado

```bash
playwright-simple run meu_teste.yaml --video --subtitles --audio
```

---

## Próximos Passos

- [Tutorial 4: Auto-Fix](tutorial_04_auto_fix.md)
- [Tutorial 5: YAML Avançado](tutorial_05_advanced_yaml.md)

---

**Concluído!** 🎉

