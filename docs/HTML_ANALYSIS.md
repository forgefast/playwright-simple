# Análise de HTML para Auto-Fix

## Visão Geral

O sistema agora pode capturar e analisar o HTML da página durante o debug, permitindo que a IA "veja" a tela e sugira correções mais precisas.

## Como Usar

### 1. Durante o Debug Interativo

Quando um erro ocorre e o debug interativo é ativado, você pode usar o comando `[g]`:

```
Debug> g
✅ HTML salvo em: /tmp/playwright_html.html
✅ Metadata salvo em: /tmp/playwright_html_metadata.json
✅ Versão simplificada salva em: /tmp/playwright_html_simplified.json
📄 URL: http://localhost:18069/
📄 Título: Home | My Website
📊 Tamanho do HTML: 12345 caracteres
```

### 2. Arquivos Gerados

- **`/tmp/playwright_html.html`**: HTML completo da página
- **`/tmp/playwright_html_metadata.json`**: Metadados (URL, título, timestamp)
- **`/tmp/playwright_html_simplified.json`**: Versão simplificada com apenas elementos clicáveis e inputs

### 3. Versão Simplificada

A versão simplificada contém:
- **Botões**: Texto, tag, id, class, visibilidade
- **Inputs**: Tipo, placeholder, name, id, label
- **Links**: Texto e tipo

Exemplo:
```json
{
  "buttons": [
    {
      "text": "Login",
      "tag": "button",
      "id": "login-btn",
      "class": "btn btn-primary",
      "visible": true
    }
  ],
  "inputs": [
    {
      "type": "text",
      "placeholder": "Email",
      "name": "email",
      "id": "email-input",
      "label": "Email"
    }
  ],
  "url": "http://localhost:18069/",
  "title": "Home | My Website"
}
```

## Integração com Auto-Fix

O `HTMLAnalyzer` pode ser usado para:

1. **Sugerir seletores precisos**:
   ```python
   from playwright_simple.core.html_analyzer import HTMLAnalyzer
   
   analyzer = HTMLAnalyzer()
   selector = analyzer.suggest_selector("Login")
   # Retorna: 'button:has-text("Login")'
   ```

2. **Listar todos os elementos clicáveis**:
   ```python
   elements = analyzer.get_all_clickable_elements()
   # Retorna lista de botões e links com sugestões de seletores
   ```

3. **Analisar página completa**:
   ```python
   data = analyzer.analyze()
   # Retorna dict completo com buttons, inputs, links, suggestions
   ```

## Modo Headless

O `auto_fix_runner` agora suporta modo headless:

```bash
# Modo headless (padrão)
python3 scripts/auto_fix_runner.py test.yaml --base-url http://localhost:18069

# Modo com navegador visível
python3 scripts/auto_fix_runner.py test.yaml --base-url http://localhost:18069 --no-headless
```

## Gerenciamento de Processos

O sistema agora:
- ✅ **Encerra processos antigos** antes de iniciar novo
- ✅ **Usa psutil** (se disponível) para encerrar processos de forma segura
- ✅ **Fallback para pkill** se psutil não estiver disponível
- ✅ **Garante apenas um processo** rodando por vez

## Fluxo Completo

1. **Erro ocorre** → Debug interativo ativado
2. **Usuário digita `g`** → HTML capturado
3. **IA lê HTML** → Analisa elementos disponíveis
4. **IA sugere correção** → Atualiza YAML com seletor correto
5. **Hot reload** → Aplica correção automaticamente
6. **Teste continua** → Com correção aplicada

## Exemplo Prático

```
Erro: ElementNotFoundError - Não encontrou "Login"
→ Debug> g (captura HTML)
→ IA lê /tmp/playwright_html_simplified.json
→ IA encontra: {"text": "Entrar", "tag": "button"}
→ IA corrige YAML: text: "Login" → text: "Entrar"
→ Hot reload aplica
→ Teste continua com sucesso
```

