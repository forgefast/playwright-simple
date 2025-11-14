# Exemplos de Automação

Estes exemplos mostram como usar `playwright-simple` para **automação de tarefas**, não apenas testes.

## Casos de Uso

### 1. Monitoramento
- `monitoramento_odoo.yaml` - Monitora pedidos pendentes e envia alertas

### 2. Coleta de Dados
- `coleta_dados.yaml` - Coleta dados de vendas para relatórios

## Como Executar

```bash
# Executar automação
python -m playwright_simple.run examples/automation/monitoramento_odoo.yaml

# Ou usando o runner Python
from playwright_simple.core.yaml_parser import YAMLParser
from playwright_simple import TestRunner, TestConfig

yaml_path = Path("examples/automation/monitoramento_odoo.yaml")
test_name, test_func = YAMLParser.load_test(yaml_path)

config = TestConfig(base_url="https://odoo.empresa.com")
runner = TestRunner(config=config)
await runner.run_test(test_name, test_func)
```

## Agendamento

### Cron (Linux/Mac)
```bash
# Executar a cada hora
0 * * * * cd /path/to/project && python -m playwright_simple.run examples/automation/monitoramento_odoo.yaml
```

### Windows Task Scheduler
Agende a execução do script Python que carrega e executa o YAML.

### Python Schedule
```python
import schedule
import time
from playwright_simple.core.yaml_parser import YAMLParser
from playwright_simple import TestRunner, TestConfig

async def executar_automação():
    yaml_path = Path("examples/automation/monitoramento_odoo.yaml")
    test_name, test_func = YAMLParser.load_test(yaml_path)
    config = TestConfig(base_url="https://odoo.empresa.com")
    runner = TestRunner(config=config)
    await runner.run_test(test_name, test_func)

# Agendar
schedule.every().hour.do(lambda: asyncio.run(executar_automação()))
```

## Variáveis de Ambiente

Configure variáveis de ambiente para dados sensíveis:

```bash
export ODOO_PASSWORD=senha123
export WEBHOOK_URL=https://api.notificacao.com/webhook
```

Acesse no YAML usando `{{ env.VAR_NAME }}`.

## Mais Exemplos

Veja [docs/AUTOMATION.md](../../docs/AUTOMATION.md) para mais exemplos e casos de uso.

