# Fluxo Híbrido: Gravar → Editar → Executar

Este documento descreve o fluxo completo de trabalho híbrido do playwright-simple, combinando gravação interativa com edição manual e execução automatizada.

## Visão Geral

O playwright-simple oferece um fluxo híbrido que combina:

1. **Gravação Interativa**: Grave interações do usuário e gere YAML automaticamente
2. **Edição Manual**: Edite o YAML gerado para refinar e adicionar lógica
3. **Execução Automatizada**: Execute os testes YAML com recursos avançados (vídeo, áudio, legendas)

## Fluxo Completo

```
┌─────────────────┐
│ 1. GRAVAR       │
│ playwright-simple│
│ record test.yaml│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. INTERAGIR    │
│ - Clicar        │
│ - Digitar       │
│ - Navegar       │
│ - Adicionar     │
│   legendas/áudio│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. SALVAR       │
│ YAML gerado     │
│ automaticamente │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. EDITAR       │
│ - Adicionar     │
│   lógica        │
│ - Loops         │
│ - Condicionais  │
│ - Variáveis     │
│ - Expressões    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. EXECUTAR     │
│ playwright-simple│
│ run test.yaml   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. RESULTADOS   │
│ - Vídeo         │
│ - Legendas      │
│ - Áudio         │
│ - Screenshots   │
└─────────────────┘
```

## Passo a Passo

### 1. Gravar Interações

Inicie a gravação interativa:

```bash
playwright-simple record meu_teste.yaml --url https://example.com
```

O navegador abrirá e você pode interagir normalmente. Todas as interações serão capturadas e convertidas em YAML.

**Comandos disponíveis durante a gravação:**

- `save` - Salvar YAML sem parar (continua gravando)
- `exit` - Sair e salvar
- `pause` - Pausar gravação
- `resume` - Retomar gravação
- `caption "texto"` - Adicionar legenda
- `audio "texto"` - Adicionar narração
- `screenshot` - Tirar screenshot

### 2. YAML Gerado

O YAML gerado será algo como:

```yaml
name: Gravação Automática
description: Gravação interativa do usuário - 2024-11-14 10:30:00
steps:
  - action: go_to
    url: https://example.com
    description: Navegar para https://example.com
  
  - action: click
    text: Entrar
    description: Clicar em 'Entrar'
  
  - action: type
    text: admin@example.com
    description: Campo 'E-mail'
  
  - caption: Preenchendo formulário de login
  
  - action: type
    text: senha123
    description: Campo 'Senha'
  
  - action: click
    text: Login
    description: Clicar em 'Login'
```

### 3. Editar YAML

Edite o YAML para adicionar lógica e refinar:

```yaml
name: Teste de Login Completo
description: Teste automatizado de login com validações

variables:
  email: admin@example.com
  password: senha123

steps:
  - action: go_to
    url: https://example.com
    description: Navegar para página inicial
  
  - caption: Iniciando processo de login
  
  - action: click
    text: Entrar
    description: Clicar em botão Entrar
  
  # Preencher formulário
  - action: type
    text: "{{ email }}"
    description: Campo 'E-mail'
  
  - action: type
    text: "{{ password }}"
    description: Campo 'Senha'
  
  - action: click
    text: Login
    description: Clicar em Login
  
  # Validar login
  - action: wait_for
    selector: .dashboard
    timeout: 5000
    description: Aguardar dashboard aparecer
  
  - action: assert_text
    selector: .welcome-message
    text: "Bem-vindo"
    description: Verificar mensagem de boas-vindas
  
  # Loop para testar múltiplos usuários
  - for:
      var: user
      in: ["admin@example.com", "user@example.com"]
    steps:
      - action: click
        text: Logout
        description: Fazer logout
      
      - action: click
        text: Entrar
        description: Clicar em Entrar novamente
      
      - action: type
        text: "{{ user }}"
        description: Campo 'E-mail'
      
      - action: type
        text: "{{ password }}"
        description: Campo 'Senha'
      
      - action: click
        text: Login
        description: Clicar em Login
```

### 4. Executar Teste

Execute o teste editado:

```bash
playwright-simple run meu_teste.yaml \
  --video \
  --audio \
  --subtitles \
  --screenshots
```

### 5. Resultados

Após a execução, você terá:

- **Vídeo**: Gravação completa da execução
- **Legendas**: Sincronizadas com o vídeo
- **Áudio**: Narração automática (se habilitado)
- **Screenshots**: Capturas em pontos importantes
- **Relatório**: Log detalhado da execução

## Recursos Avançados

### Hot Reload

Durante a execução, você pode editar o YAML e o teste será recarregado automaticamente:

```bash
playwright-simple run meu_teste.yaml --hot-reload
```

### Auto-Fix

O sistema tenta corrigir erros automaticamente:

- Elemento não encontrado → Adiciona wait ou sugere elemento similar
- Timeout → Aumenta timeout
- Ação desconhecida → Mapeia para ação conhecida

### Debug Interativo

Pause em erros para inspecionar:

```bash
playwright-simple run meu_teste.yaml --debug --pause-on-error
```

## Vantagens do Fluxo Híbrido

1. **Rápido**: Gravação elimina digitação manual
2. **Flexível**: Edição permite adicionar lógica complexa
3. **Manutenível**: YAML é legível e fácil de editar
4. **Completo**: Recursos avançados (vídeo, áudio, legendas)
5. **Inteligente**: Auto-fix e hot reload facilitam desenvolvimento

## Exemplos de Uso

### Exemplo 1: Teste Simples

```bash
# 1. Gravar
playwright-simple record login.yaml --url https://app.com

# 2. Editar (adicionar validações)
# Editar login.yaml manualmente

# 3. Executar
playwright-simple run login.yaml --video
```

### Exemplo 2: Teste com Lógica

```bash
# 1. Gravar fluxo básico
playwright-simple record crud.yaml --url https://app.com

# 2. Editar (adicionar loops, condicionais)
# Editar crud.yaml para adicionar:
# - Loop para criar múltiplos itens
# - Condicionais para validações
# - Variáveis para dados dinâmicos

# 3. Executar
playwright-simple run crud.yaml --video --audio
```

### Exemplo 3: Teste com Extensões

```bash
# 1. Gravar teste Odoo
playwright-simple record odoo_test.yaml --url http://localhost:8069

# 2. Editar (adicionar ações Odoo específicas)
# Usar ações como:
# - odoo_login
# - odoo_navigate
# - odoo_create_record

# 3. Executar com extensão Odoo
playwright-simple run odoo_test.yaml --extensions odoo --video
```

## Dicas e Boas Práticas

1. **Grave primeiro, edite depois**: Comece gravando o fluxo básico, depois adicione lógica
2. **Use variáveis**: Evite valores hardcoded, use variáveis para facilitar manutenção
3. **Adicione legendas**: Legendas ajudam a entender o que está acontecendo no vídeo
4. **Valide resultados**: Sempre adicione assertions para validar o comportamento esperado
5. **Use hot reload**: Durante desenvolvimento, use hot reload para iterar rapidamente
6. **Organize steps**: Use descrições claras e organize steps logicamente

## Conclusão

O fluxo híbrido do playwright-simple combina o melhor dos dois mundos:

- **Gravação interativa** para velocidade
- **Edição manual** para flexibilidade
- **Execução automatizada** para confiabilidade

Isso permite criar testes complexos de forma rápida e eficiente, mantendo a flexibilidade de edição manual quando necessário.

