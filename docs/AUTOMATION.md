# Automação Web com playwright-simple

## Não é só para testes!

O `playwright-simple` foi projetado para **automação web em geral**, não apenas testes. Você pode usar para:

- ✅ **Testes automatizados** (QA, E2E)
- ✅ **Automação de tarefas** (scripts, bots, workflows)
- ✅ **Monitoramento** (verificar status, coletar dados)
- ✅ **Integração** (conectar sistemas, sincronizar dados)
- ✅ **Web scraping** (coletar informações de sites)
- ✅ **Relatórios automatizados** (gerar e enviar relatórios)

---

## Casos de Uso Reais

### 1. Monitoramento e Alertas

**Exemplo: Verificar Odoo e enviar email se algo estiver fora do normal**

```yaml
name: Monitoramento Odoo - Pedidos Pendentes
description: Verifica pedidos pendentes e envia alerta por email

steps:
  - action: login
    login: monitor@empresa.com
    password: senha123
    database: producao
  
  - action: navigate_menu
    menu_path: ["Vendas", "Pedidos"]
  
  - action: filter_by
    filter_text: "Pendente"
  
  # Contar pedidos pendentes
  - action: evaluate
    code: |
      () => {
        const rows = document.querySelectorAll('.o_list_table tbody tr');
        return rows.length;
      }
    store_result: pedidos_pendentes
  
  # Verificar se há muitos pedidos pendentes
  - if: "{{ pedidos_pendentes > 10 }}"
    then:
      - action: evaluate
        code: |
          () => {
            // Coletar informações dos pedidos
            const rows = document.querySelectorAll('.o_list_table tbody tr');
            const pedidos = [];
            rows.forEach(row => {
              const cells = row.querySelectorAll('td');
              pedidos.push({
                numero: cells[0]?.textContent?.trim(),
                cliente: cells[1]?.textContent?.trim(),
                valor: cells[2]?.textContent?.trim(),
                data: cells[3]?.textContent?.trim()
              });
            });
            return JSON.stringify(pedidos);
          }
        store_result: dados_pedidos
      
      # Enviar email (usando Python ou webhook)
      - action: request
        method: POST
        url: "https://api.email-service.com/send"
        data:
          to: "gerente@empresa.com"
          subject: "⚠️ Alerta: {{ pedidos_pendentes }} pedidos pendentes"
          body: |
            Há {{ pedidos_pendentes }} pedidos pendentes no Odoo.
            
            Dados:
            {{ dados_pedidos }}
```

### 2. Coleta de Dados e Relatórios

**Exemplo: Coletar dados de vendas e gerar relatório**

```yaml
name: Coleta de Dados de Vendas
description: Coleta dados de vendas do mês e gera relatório

steps:
  - action: login
    login: relatorios@empresa.com
    password: senha123
  
  - action: navigate_menu
    menu_path: ["Vendas", "Relatórios", "Vendas do Mês"]
  
  # Filtrar por mês atual
  - action: click
    text: "Filtros"
  
  - action: fill_field
    field_label: "Data"
    field_value: "{{ datetime.now().strftime('%Y-%m') }}"
  
  - action: click
    text: "Aplicar"
  
  # Coletar dados da tabela
  - action: evaluate
    code: |
      () => {
        const table = document.querySelector('.o_list_table');
        const rows = table.querySelectorAll('tbody tr');
        const dados = [];
        rows.forEach(row => {
          const cells = row.querySelectorAll('td');
          dados.push({
            produto: cells[0]?.textContent?.trim(),
            quantidade: cells[1]?.textContent?.trim(),
            valor: cells[2]?.textContent?.trim(),
            vendedor: cells[3]?.textContent?.trim()
          });
        });
        return JSON.stringify(dados);
      }
    store_result: dados_vendas
  
  # Salvar em arquivo (via Python)
  - action: evaluate
    code: |
      () => {
        // Preparar dados para salvar
        return window.dados_vendas;
      }
    store_result: dados_finais
```

### 3. Sincronização de Dados

**Exemplo: Sincronizar dados entre sistemas**

```yaml
name: Sincronizar Clientes Odoo -> CRM
description: Busca novos clientes no Odoo e sincroniza com CRM

steps:
  - action: login
    login: sync@empresa.com
    password: senha123
  
  - action: navigate_menu
    menu_path: ["Vendas", "Clientes"]
  
  # Filtrar clientes criados hoje
  - action: filter_by
    filter_text: "Hoje"
  
  # Coletar novos clientes
  - action: evaluate
    code: |
      () => {
        const rows = document.querySelectorAll('.o_list_table tbody tr');
        const clientes = [];
        rows.forEach(row => {
          const cells = row.querySelectorAll('td');
          clientes.push({
            nome: cells[0]?.textContent?.trim(),
            email: cells[1]?.textContent?.trim(),
            telefone: cells[2]?.textContent?.trim(),
            cidade: cells[3]?.textContent?.trim()
          });
        });
        return JSON.stringify(clientes);
      }
    store_result: novos_clientes
  
  # Enviar para API do CRM
  - for: cliente in novos_clientes
    steps:
      - action: request
        method: POST
        url: "https://api.crm.com/clientes"
        data:
          nome: "{{ cliente.nome }}"
          email: "{{ cliente.email }}"
          telefone: "{{ cliente.telefone }}"
          cidade: "{{ cliente.cidade }}"
```

### 4. Automação de Tarefas Repetitivas

**Exemplo: Processar pedidos em lote**

```yaml
name: Processar Pedidos em Lote
description: Processa múltiplos pedidos automaticamente

steps:
  - action: login
    login: automação@empresa.com
    password: senha123
  
  - action: navigate_menu
    menu_path: ["Vendas", "Pedidos"]
  
  # Filtrar pedidos para processar
  - action: filter_by
    filter_text: "Aguardando Processamento"
  
  # Processar cada pedido
  - action: evaluate
    code: |
      () => {
        const rows = document.querySelectorAll('.o_list_table tbody tr');
        return Array.from(rows).map((row, idx) => ({
          index: idx,
          numero: row.querySelector('td')?.textContent?.trim()
        }));
      }
    store_result: pedidos
  
  - for: pedido in pedidos
    steps:
      - action: open_record
        record_text: "{{ pedido.numero }}"
      
      - action: click
        text: "Processar"
      
      - action: wait
        seconds: 2
      
      - action: screenshot
        name: "pedido_{{ pedido.numero }}_processado"
```

### 5. Validação e Verificação

**Exemplo: Verificar integridade de dados**

```yaml
name: Validação de Dados
description: Verifica integridade de dados no sistema

steps:
  - action: login
    login: validacao@empresa.com
    password: senha123
  
  - set: erros_encontrados = []
  
  # Verificar produtos sem preço
  - action: navigate_menu
    menu_path: ["Vendas", "Produtos"]
  
  - action: evaluate
    code: |
      () => {
        const rows = document.querySelectorAll('.o_list_table tbody tr');
        const sem_preco = [];
        rows.forEach(row => {
          const preco = row.querySelector('td:nth-child(3)')?.textContent?.trim();
          if (!preco || preco === '0,00') {
            const nome = row.querySelector('td')?.textContent?.trim();
            sem_preco.push(nome);
          }
        });
        return sem_preco;
      }
    store_result: produtos_sem_preco
  
  - if: "{{ len(produtos_sem_preco) > 0 }}"
    then:
      - set: erros_encontrados = "{{ erros_encontrados + ['Produtos sem preço: ' + str(produtos_sem_preco)] }}"
  
  # Verificar clientes sem email
  - action: navigate_menu
    menu_path: ["Vendas", "Clientes"]
  
  - action: evaluate
    code: |
      () => {
        const rows = document.querySelectorAll('.o_list_table tbody tr');
        const sem_email = [];
        rows.forEach(row => {
          const email = row.querySelector('td:nth-child(2)')?.textContent?.trim();
          if (!email || !email.includes('@')) {
            const nome = row.querySelector('td')?.textContent?.trim();
            sem_email.push(nome);
          }
        });
        return sem_email;
      }
    store_result: clientes_sem_email
  
  - if: "{{ len(clientes_sem_email) > 0 }}"
    then:
      - set: erros_encontrados = "{{ erros_encontrados + ['Clientes sem email: ' + str(clientes_sem_email)] }}"
  
  # Enviar relatório de erros
  - if: "{{ len(erros_encontrados) > 0 }}"
    then:
      - action: request
        method: POST
        url: "https://api.notificacao.com/alert"
        data:
          tipo: "Validação de Dados"
          erros: "{{ erros_encontrados }}"
```

---

## Integração com Python

Para casos mais complexos, você pode combinar YAML com Python:

```python
import asyncio
from playwright_simple import TestRunner, TestConfig
from playwright_simple.core.yaml_parser import YAMLParser

async def automação_completa():
    # Carregar script YAML
    yaml_path = Path("automatizacoes/monitoramento_odoo.yaml")
    test_name, test_func = YAMLParser.load_test(yaml_path)
    
    # Configurar
    config = TestConfig(base_url="https://odoo.empresa.com")
    runner = TestRunner(config=config)
    
    # Executar automação
    result = await runner.run_test(test_name, test_func)
    
    # Processar resultados
    if result['status'] == 'passed':
        # Fazer algo com os dados coletados
        dados = result.get('dados_coletados')
        enviar_email(dados)
    
    return result

# Agendar execução (usando cron, schedule, etc.)
if __name__ == "__main__":
    asyncio.run(automação_completa())
```

---

## Agendamento e Execução

### Cron (Linux/Mac)
```bash
# Executar a cada hora
0 * * * * cd /path/to/project && python -m playwright_simple.run automatizacoes/monitoramento.yaml
```

### Windows Task Scheduler
```xml
<!-- Agendar execução diária -->
<Task>
  <Actions>
    <Exec>
      <Command>python</Command>
      <Arguments>-m playwright_simple.run automatizacoes/monitoramento.yaml</Arguments>
    </Exec>
  </Actions>
</Task>
```

### Python Schedule
```python
import schedule
import time
from playwright_simple.core.yaml_parser import YAMLParser

def executar_automação():
    yaml_path = Path("automatizacoes/monitoramento.yaml")
    test_name, test_func = YAMLParser.load_test(yaml_path)
    # ... executar

# Agendar
schedule.every().hour.do(executar_automação)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Boas Práticas para Automação

1. **Tratamento de Erros**: Use `try/catch` para lidar com falhas
2. **Logging**: Registre todas as ações importantes
3. **Notificações**: Envie alertas quando necessário
4. **Idempotência**: Scripts devem poder rodar múltiplas vezes
5. **Dados Sensíveis**: Use variáveis de ambiente para senhas
6. **Timeout**: Configure timeouts apropriados
7. **Retry**: Implemente retry para operações críticas

---

## Diferença: Testes vs Automação

| Testes | Automação |
|--------|-----------|
| Verifica se algo funciona | Executa tarefas |
| Falha se algo está errado | Continua mesmo com erros |
| Foco em validação | Foco em execução |
| Relatórios de teste | Notificações e ações |
| Ambiente controlado | Ambiente de produção |

**playwright-simple funciona para ambos!** 🎯

