# Fluxo Híbrido: Gravar → Editar → Executar

Este documento descreve o fluxo completo de trabalho com o playwright-simple usando a abordagem híbrida: gravar interações, editar o YAML gerado e executar o teste.

## Visão Geral

O fluxo híbrido combina:
1. **Gravação automática** de interações do usuário
2. **Edição manual** do YAML gerado para refinar e adicionar lógica
3. **Execução automatizada** do teste YAML

Esta abordagem oferece o melhor dos dois mundos: a velocidade da gravação automática e a flexibilidade da edição manual.

## 1. Gravação

### Iniciando a Gravação

Para gravar interações, use o comando `record`:

```bash
playwright-simple record test_login.yaml --url http://localhost:18069
```

Ou use o modo interativo:

```bash
playwright-simple record test_login.yaml
```

### Durante a Gravação

O recorder captura automaticamente:
- Cliques em elementos
- Digitação em campos
- Navegação entre páginas
- Scrolls
- Submissão de formulários

### Comandos Disponíveis Durante a Gravação

- `start` - Inicia gravação
- `save` - Salva YAML atual
- `exit` - Sai e salva YAML
- `pause` - Pausa gravação
- `resume` - Retoma gravação
- `caption "texto"` - Adiciona legenda ao passo atual
- `audio "texto"` - Adiciona narração ao passo atual
- `screenshot` - Tira screenshot

### Exemplo de Uso

```bash
# Iniciar gravação
playwright-simple record test_login.yaml --url http://localhost:18069

# No navegador:
# 1. Clicar em "Entrar"
# 2. Preencher email: admin
# 3. Preencher senha: admin
# 4. Clicar em "Entrar"

# No console:
save
exit
```

## 2. Edição

### Estrutura do YAML Gerado

O YAML gerado tem a seguinte estrutura:

```yaml
name: Test Login
base_url: http://localhost:18069
steps:
  - action: go_to
    url: http://localhost:18069
    description: Navegar para http://localhost:18069
  - action: click
    text: Entrar
    description: Clicar em 'Entrar'
  - action: type
    text: admin
    field_text: E-mail
    description: Digitar 'admin' no campo 'E-mail'
  - action: type
    text: admin
    field_text: Senha
    description: Digitar 'admin' no campo 'Senha'
  - action: click
    text: Entrar
    description: Clicar em 'Entrar'
```

### Editando o YAML

Você pode editar o YAML para:
- Adicionar waits explícitos
- Adicionar assertions
- Modificar seletores
- Adicionar lógica condicional
- Adicionar loops
- Comentar passos

### Exemplo de Edição

```yaml
name: Test Login
base_url: http://localhost:18069
steps:
  - action: go_to
    url: http://localhost:18069
    description: Navegar para página inicial
  
  # Aguardar página carregar
  - action: wait
    seconds: 2
    description: Aguardar página carregar
  
  - action: click
    text: Entrar
    description: Clicar em 'Entrar'
  
  # Aguardar formulário aparecer
  - action: wait_for
    selector: input[name="login"]
    state: visible
    description: Aguardar campo de email aparecer
  
  - action: type
    text: admin
    field_text: E-mail
    description: Digitar email
  
  - action: type
    text: admin
    field_text: Senha
    description: Digitar senha
  
  - action: click
    text: Entrar
    description: Submeter formulário
  
  # Verificar login bem-sucedido
  - action: assert_visible
    selector: .dashboard
    description: Verificar que dashboard está visível
```

## 3. Execução

### Executando o YAML

Para executar o YAML editado:

```bash
playwright-simple run test_login.yaml
```

Ou usando o modo read do recorder diretamente:

```python
from playwright_simple.core.recorder.recorder import Recorder
from pathlib import Path

async def run_test():
    yaml_path = Path('test_login.yaml')
    recorder = Recorder(
        output_path=yaml_path,
        initial_url=None,  # Lido do YAML
        headless=False,
        fast_mode=True,
        mode='read'
    )
    await recorder.start()

asyncio.run(run_test())
```

### Opções de Execução

- `--headless`: Executar em modo headless
- `--debug`: Habilitar modo debug
- `--fast-mode`: Acelerar execução (reduz delays)

### Exemplo de Execução

```bash
# Executar em modo normal
playwright-simple run test_login.yaml

# Executar em modo headless (mais rápido)
playwright-simple run test_login.yaml --headless

# Executar com debug
playwright-simple run test_login.yaml --debug
```

## Boas Práticas

### 1. Gravação
- Aguarde a mensagem "✅ Recording started!" antes de interagir
- Use comandos `caption` e `audio` para documentar passos importantes
- Salve frequentemente com `save` durante gravações longas

### 2. Edição
- Adicione waits explícitos após navegações
- Use `wait_for` para aguardar elementos aparecerem
- Adicione assertions para validar resultados
- Comente passos complexos

### 3. Execução
- Teste em modo não-headless primeiro para ver o que acontece
- Use `--fast-mode` apenas quando o teste estiver estável
- Verifique logs para identificar problemas

## Troubleshooting

### Problema: Cliques não são capturados
**Solução**: Aguarde a mensagem "✅ Recording started!" antes de clicar. O script de captura precisa ser injetado primeiro.

### Problema: Elemento não encontrado na execução
**Solução**: 
- Adicione `wait_for` antes do passo
- Verifique se o seletor está correto
- Use `assert_visible` para validar que elemento existe

### Problema: Teste muito lento
**Solução**: 
- Use `--fast-mode` para acelerar
- Remova waits desnecessários
- Use `wait_for` em vez de `wait` quando possível

### Problema: YAML não executa
**Solução**:
- Verifique sintaxe YAML (indentação, etc.)
- Verifique se `base_url` está correto
- Verifique se todos os seletores estão corretos

## Exemplos Completos

### Exemplo 1: Login Simples

**Gravação**:
```bash
playwright-simple record login.yaml --url http://localhost:18069
```

**YAML Gerado** (editado):
```yaml
name: Login Test
base_url: http://localhost:18069
steps:
  - action: go_to
    url: http://localhost:18069
  - action: click
    text: Entrar
  - action: type
    text: admin
    field_text: E-mail
  - action: type
    text: admin
    field_text: Senha
  - action: click
    text: Entrar
  - action: assert_visible
    selector: .dashboard
```

**Execução**:
```bash
playwright-simple run login.yaml
```

### Exemplo 2: Formulário Completo

**YAML Editado**:
```yaml
name: Create User
base_url: http://localhost:18069
steps:
  - action: go_to
    url: http://localhost:18069/users
  - action: click
    text: Criar
  - action: wait_for
    selector: input[name="name"]
    state: visible
  - action: type
    text: João Silva
    field_text: Nome
  - action: type
    text: joao@example.com
    field_text: E-mail
  - action: click
    text: Salvar
  - action: wait_for
    selector: .success-message
    state: visible
  - action: assert_text
    selector: .success-message
    expected: Usuário criado com sucesso
```

## Conclusão

O fluxo híbrido oferece uma abordagem poderosa para criar testes:
1. **Grave** interações rapidamente
2. **Edite** o YAML para refinar e adicionar lógica
3. **Execute** o teste de forma automatizada

Esta combinação permite criar testes robustos e manuteníveis de forma eficiente.
