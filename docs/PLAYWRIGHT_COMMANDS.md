# Playwright Direct Commands Interface

## Visão Geral

A interface de comandos diretos do Playwright permite que IAs mais limitadas e usuários humanos controlem o browser diretamente durante a gravação de testes. Isso é especialmente útil para:

- **IAs com capacidades limitadas**: Comandos simples e diretos que não requerem conhecimento profundo do Playwright
- **Testes manuais**: Facilita debugging e testes interativos
- **Automação assistida**: Permite que IAs ajudem usuários a interagir com páginas web

## Comandos Disponíveis

### Encontrar Elementos

#### `find "texto"`
Encontra um elemento pelo texto visível.

```bash
find "Entrar"
find "Login"
find "E-mail"
```

#### `find selector "#id"`
Encontra um elemento por seletor CSS.

```bash
find selector "#login-button"
find selector ".btn-primary"
find selector "input[name='email']"
```

#### `find role button`
Encontra um elemento por role ARIA.

```bash
find role button
find role link
find role textbox
```

#### `find-all "texto"`
Encontra todos os elementos que correspondem ao critério.

```bash
find-all "Entrar"
find-all selector ".button"
find-all role button
```

### Clicar em Elementos

#### `pw-click "texto"`
Clica em um elemento pelo texto.

```bash
pw-click "Entrar"
pw-click "Login"
pw-click "Submit"
```

#### `pw-click selector "#id"`
Clica em um elemento por seletor.

```bash
pw-click selector "#login-button"
pw-click selector ".btn-primary"
```

#### `pw-click role button [index]`
Clica em um elemento por role, com índice opcional se houver múltiplos.

```bash
pw-click role button
pw-click role button [0]  # Primeiro botão
pw-click role button [1]  # Segundo botão
```

### Digitar Texto

#### `pw-type "texto" into "campo"`
Digita texto em um campo de entrada.

```bash
pw-type "admin@example.com" into "E-mail"
pw-type "senha123" into "Senha"
pw-type "admin@example.com" into selector "#email"
```

### Esperar Elementos

#### `pw-wait "texto" [timeout]`
Espera um elemento aparecer na página.

```bash
pw-wait "Login"        # Espera 5 segundos (padrão)
pw-wait "Login" 10    # Espera 10 segundos
pw-wait selector "#login-form" 5
```

### Informações da Página

#### `pw-info`
Mostra informações sobre a página atual.

```bash
pw-info
```

Retorna:
- URL atual
- Título da página
- Estado de carregamento

### Obter HTML

#### `pw-html [selector] [--pretty] [--max-length N]`
Obtém HTML da página ou de um elemento específico.

```bash
# HTML da página inteira
pw-html

# HTML de elemento específico
pw-html selector "#login-form"

# HTML formatado (com indentação)
pw-html --pretty

# HTML com limite de tamanho
pw-html --max-length 5000

# Combinar opções
pw-html selector "#login-form" --pretty --max-length 10000
```

**Útil para:**
- Debugging: entender por que elementos não são encontrados
- Validação: verificar estrutura HTML atual
- Desenvolvimento: analisar DOM da página

## Exemplos de Uso

### Exemplo 1: Login Simples

```bash
# Encontrar botão de login na página inicial
find "Entrar"

# Clicar no botão
pw-click "Entrar"

# Esperar formulário aparecer
pw-wait "E-mail" 5

# Preencher campos
pw-type "admin@example.com" into "E-mail"
pw-type "senha123" into "Senha"

# Clicar no botão de submit
pw-click "Entrar"
```

### Exemplo 2: Usando Seletores

```bash
# Encontrar elemento por ID
find selector "#login-button"

# Clicar usando seletor
pw-click selector "#login-button"

# Digitar em campo por seletor
pw-type "texto" into selector "#email-field"
```

### Exemplo 3: Múltiplos Elementos

```bash
# Encontrar todos os botões
find-all role button

# Clicar no segundo botão
pw-click role button [1]
```

## Integração com Gravação

Os comandos do Playwright podem ser usados durante a gravação de testes. Eles são executados diretamente no browser, mas **não são automaticamente gravados** no YAML. Para gravar ações, use os comandos normais de gravação ou interaja diretamente com o browser.

### Quando Usar

- **Durante gravação**: Para ajudar a navegar até o ponto onde você quer começar a gravar
- **Debugging**: Para testar se elementos estão visíveis e clicáveis
- **Assistência de IA**: Para permitir que IAs controlem o browser e ajudem o usuário

### Quando NÃO Usar

- **Para gravar ações**: Use interação direta com o browser ou comandos de gravação normais
- **Em testes automatizados**: Use o executor YAML normal

## Diferença entre Comandos

### Comandos de Gravação (gravam no YAML)
- `click "texto"` - Clica e grava a ação
- `type "texto" into "campo"` - Digita e grava a ação

### Comandos Diretos do Playwright (não gravam)
- `pw-click "texto"` - Clica diretamente, não grava
- `pw-type "texto" into "campo"` - Digita diretamente, não grava

## Dicas para IAs

1. **Sempre verifique se o elemento existe antes de clicar**:
   ```bash
   find "Entrar"
   pw-click "Entrar"
   ```

2. **Use `pw-wait` para aguardar elementos dinâmicos**:
   ```bash
   pw-wait "Formulário" 10
   ```

3. **Use `find-all` para ver quantos elementos existem**:
   ```bash
   find-all "Entrar"
   # Se houver múltiplos, use índice
   pw-click role button [0]
   ```

4. **Verifique informações da página quando necessário**:
   ```bash
   pw-info
   ```

5. **Use `pw-html` para debugar elementos não encontrados**:
   ```bash
   # Ver HTML da página
   pw-html > page.html
   
   # Ver HTML de elemento específico formatado
   pw-html selector "#element-id" --pretty
   ```

## Troubleshooting

### Elemento não encontrado
- Verifique se o texto está exatamente correto (case-sensitive)
- Use `find-all` para ver todos os elementos disponíveis
- Tente usar `selector` ou `role` em vez de texto

### Clique não funciona
- Verifique se o elemento está visível usando `find`
- Use `pw-wait` para aguardar o elemento aparecer
- Tente usar seletor CSS mais específico

### Timeout em `pw-wait`
- Aumente o timeout: `pw-wait "texto" 30`
- Verifique se o elemento realmente aparece na página
- Use `pw-info` para verificar o estado da página

### Elemento não encontrado - como debugar
1. **Obter HTML da página**:
   ```bash
   pw-html > page.html
   # Abra page.html em um editor para ver estrutura
   ```

2. **Ver HTML de área específica**:
   ```bash
   pw-html selector "body" --pretty
   ```

3. **Verificar seletor**:
   ```bash
   # Teste seletor
   find selector "#element-id"
   ```

4. **Ver HTML formatado de elemento**:
   ```bash
   pw-html selector "#element-id" --pretty
   ```

