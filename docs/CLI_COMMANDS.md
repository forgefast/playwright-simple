# Comandos CLI para Gravação Ativa

## Visão Geral

Durante uma gravação ativa (com `playwright-simple record`), você pode usar comandos CLI separados para controlar o browser. Isso é especialmente útil para:

- **IAs com capacidades limitadas**: Comandos simples que não requerem conhecimento profundo
- **Automação de scripts**: Controlar a gravação programaticamente
- **Debugging**: Testar elementos antes de interagir manualmente

## Pré-requisitos

1. Uma gravação deve estar ativa:
   ```bash
   playwright-simple record test.yaml --url localhost:18069
   ```

2. Em outro terminal, você pode executar os comandos CLI

## Comandos Disponíveis

### `playwright-simple find`

Encontrar um elemento na página.

```bash
# Por texto
playwright-simple find "Entrar"

# Por seletor CSS
playwright-simple find --selector "#login-button"

# Por role ARIA
playwright-simple find --role button
```

**Exemplo de saída:**
```
✅ Elemento encontrado:
   Tag: A
   Texto: Entrar
   ID: 
   Classe: nav-link o_nav_link_btn
   Visível: True
```

### `playwright-simple click`

Clicar em um elemento.

```bash
# Por texto
playwright-simple click "Entrar"

# Por seletor CSS
playwright-simple click --selector "#login-button"

# Por role ARIA (com índice se houver múltiplos)
playwright-simple click --role button --index 0
```

**Exemplo de saída:**
```
✅ Clicado com sucesso
```

### `playwright-simple type`

Digitar texto em um campo.

```bash
# Por label/placeholder
playwright-simple type "admin@example.com" --into "E-mail"

# Por seletor CSS
playwright-simple type "admin@example.com" --selector "#email-field"
```

**Exemplo de saída:**
```
✅ Texto 'admin@example.com' digitado com sucesso
```

### `playwright-simple wait`

Esperar um elemento aparecer na página.

```bash
# Por texto (timeout padrão: 5 segundos)
playwright-simple wait "Login"

# Por texto com timeout customizado
playwright-simple wait "Login" --timeout 10

# Por seletor CSS
playwright-simple wait --selector "#login-form" --timeout 5

# Por role ARIA
playwright-simple wait --role textbox --timeout 3
```

**Exemplo de saída:**
```
✅ Elemento apareceu
```

### `playwright-simple info`

Mostrar informações sobre a página atual.

```bash
playwright-simple info
```

**Exemplo de saída:**
```
📄 Informações da página:
   URL: http://localhost:18069/web/login
   Título: Login | My Website
   Estado: complete
```

### `playwright-simple html`

Obter HTML da página ou de um elemento específico.

```bash
# HTML da página inteira
playwright-simple html

# HTML de um elemento específico
playwright-simple html --selector "#login-form"

# HTML formatado (com indentação)
playwright-simple html --pretty

# HTML com limite de tamanho
playwright-simple html --max-length 5000

# Combinar opções
playwright-simple html --selector "#login-form" --pretty --max-length 10000
```

**Exemplo de saída:**
```
📄 HTML (15234 caracteres):
------------------------------------------------------------
<!DOCTYPE html>
<html>
  <head>
    <title>Login | My Website</title>
  </head>
  <body>
    <form id="login-form">
      ...
    </form>
  </body>
</html>
------------------------------------------------------------

💡 Dica: HTML é grande (15234 caracteres). Considere salvar em arquivo:
   playwright-simple html > page.html
```

**Opções:**
- `--selector` ou `-s`: Seletor CSS do elemento (opcional)
- `--pretty` ou `-p`: Formatar HTML com indentação
- `--max-length` ou `--max`: Limitar tamanho do HTML retornado

## Exemplos Práticos

### Exemplo 1: Login no Odoo

```bash
# Terminal 1: Iniciar gravação
playwright-simple record login_test.yaml --url localhost:18069

# Terminal 2: Encontrar e clicar no botão "Entrar" da página inicial
playwright-simple find "Entrar"
playwright-simple click "Entrar"

# Esperar formulário aparecer
playwright-simple wait "E-mail" --timeout 10

# Preencher campos
playwright-simple type "admin@example.com" --into "E-mail"
playwright-simple type "senha123" --into "Senha"

# Clicar no botão de submit
playwright-simple click "Entrar"
```

### Exemplo 2: Usando Seletores CSS

```bash
# Encontrar elemento por ID
playwright-simple find --selector "#login-button"

# Clicar usando seletor
playwright-simple click --selector "#login-button"

# Digitar em campo por seletor
playwright-simple type "texto" --selector "#email-field"
```

### Exemplo 3: Múltiplos Elementos

```bash
# Se houver múltiplos botões com mesmo texto/role
playwright-simple click --role button --index 0  # Primeiro botão
playwright-simple click --role button --index 1  # Segundo botão
```

### Exemplo 4: Debugging com HTML

```bash
# Obter HTML da página para entender estrutura
playwright-simple html > page.html

# Obter HTML de elemento específico
playwright-simple html --selector "#login-form" --pretty

# Ver HTML formatado de elemento que não está sendo encontrado
playwright-simple html --selector "button" --pretty --max-length 2000
```

## Integração com IAs

Para IAs mais limitadas, os comandos são simples e diretos:

1. **Sempre verifique se o elemento existe antes de clicar**:
   ```bash
   playwright-simple find "Entrar"
   # Se encontrar, então:
   playwright-simple click "Entrar"
   ```

2. **Use `wait` para elementos dinâmicos**:
   ```bash
   playwright-simple wait "Formulário" 10
   ```

3. **Use `info` para verificar estado da página**:
   ```bash
   playwright-simple info
   ```

4. **Use `html` para debugar elementos não encontrados**:
   ```bash
   # Ver HTML da página
   playwright-simple html > page.html
   
   # Ver HTML de elemento específico
   playwright-simple html --selector "#element-id" --pretty
   ```

## Troubleshooting

### Erro: "No active recording session found"

- Certifique-se de que uma gravação está rodando
- Verifique se o processo não foi encerrado

### Erro: "Elemento não encontrado"

- Verifique se o texto está correto (case-sensitive)
- Tente usar `--selector` ou `--role` em vez de texto
- Use `playwright-simple info` para verificar a URL atual

### Erro: "Timeout"

- Aumente o timeout: `--timeout 30`
- Verifique se o elemento realmente aparece na página
- Use `playwright-simple info` para verificar o estado da página

### Comandos não funcionam

- Certifique-se de que a gravação está ativa e não pausada
- Verifique os logs da gravação para erros
- Tente reiniciar a gravação

### Elemento não encontrado - como debugar

1. **Obter HTML da página**:
   ```bash
   playwright-simple html > page.html
   # Abra page.html em um editor para ver estrutura
   ```

2. **Ver HTML de área específica**:
   ```bash
   playwright-simple html --selector "body" --pretty
   ```

3. **Verificar seletor**:
   ```bash
   # Teste seletor
   playwright-simple find --selector "#element-id"
   ```

4. **Ver HTML formatado de elemento**:
   ```bash
   playwright-simple html --selector "#element-id" --pretty
   ```

## Notas Importantes

1. **Os comandos CLI não gravam no YAML**: Eles executam diretamente no browser, mas não são automaticamente gravados. Para gravar ações, interaja diretamente com o browser ou use os comandos do console durante a gravação.

2. **Comandos são síncronos**: Cada comando espera a conclusão antes de retornar.

3. **Timeout padrão**: 5 segundos para comandos `wait`.

4. **Case-sensitive**: Busca por texto é case-sensitive.

5. **Múltiplas sessões**: Se houver múltiplas gravações ativas, o comando usa a primeira encontrada.

