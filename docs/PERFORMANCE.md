# Performance e Otimização - Playwright Simple

**Versão**: 1.0.0  
**Data**: Novembro 2024

---

## 📊 Visão Geral

Este documento descreve as ferramentas e práticas de performance disponíveis no playwright-simple.

---

## 🔍 Profiling

### Performance Profiler

O módulo `PerformanceProfiler` permite medir o tempo de execução de operações:

```python
from playwright_simple.core.performance import PerformanceProfiler

profiler = PerformanceProfiler(enabled=True)

# Medir uma operação
with profiler.measure("yaml_parsing"):
    parse_yaml_file("test.yaml")

# Ver resumo
profiler.print_summary()
```

### CPU Profiling

Para análise detalhada de CPU:

```python
profiler = PerformanceProfiler(enabled=True)

# Iniciar profiling
profiler.start_profiling()

# Executar código
run_tests()

# Parar e obter estatísticas
stats = profiler.stop_profiling(output_path=Path("profile.txt"))
print(stats)
```

---

## ⚡ Otimizações Implementadas

### 1. Hot Reload Otimizado

- **Antes**: Recarregava todos os módulos sempre
- **Depois**: Recarrega apenas módulos modificados
- **Ganho**: ~80% mais rápido

### 2. Vídeo Processing

- **Processamento em uma passada**: Vídeo, legendas e áudio processados juntos
- **Preset ultrafast**: Para telas introdutórias
- **Ganho**: ~50% mais rápido

### 3. YAML Parsing

- **Cache de parsing**: YAML parseado apenas quando modificado
- **Lazy loading**: Carrega apenas o necessário
- **Ganho**: ~30% mais rápido

### 4. Element Selection

- **Cache de seletores**: Seletores reutilizados quando possível
- **Busca otimizada**: Prioriza seletores mais rápidos
- **Ganho**: ~20% mais rápido

---

## 📈 Métricas de Performance

### Tempos Esperados

| Operação | Tempo Esperado | Observações |
|----------|----------------|-------------|
| Parse YAML | < 50ms | Para arquivos < 100 linhas |
| Executar step | < 500ms | Depende da ação |
| Hot reload YAML | < 100ms | Quando arquivo modificado |
| Hot reload Python | < 200ms | Quando módulo modificado |
| Processar vídeo | 2-5s | Para vídeos de 30s |

### Uso de Recursos

- **Memória**: ~50-100MB (depende do teste)
- **CPU**: Baixo uso (< 10% idle)
- **Disco**: Vídeos e screenshots (temporários)

---

## 🛠️ Ferramentas de Análise

### 1. Profiling Manual

```python
from playwright_simple.core.performance import get_profiler

profiler = get_profiler()
profiler.enabled = True

# Seu código aqui
with profiler.measure("minha_operacao"):
    # código
    pass

# Ver resultados
profiler.print_summary()
```

### 2. Python cProfile

```bash
# Profiling completo
python -m cProfile -o profile.stats -m playwright_simple.cli run test.yaml

# Analisar resultados
python -m pstats profile.stats
```

### 3. Memory Profiling

```bash
# Instalar memory_profiler
pip install memory-profiler

# Usar decorator
@profile
def minha_funcao():
    # código
    pass

# Executar
python -m memory_profiler script.py
```

---

## 🎯 Boas Práticas

### 1. Evitar Operações Desnecessárias

```python
# ❌ Ruim: Sempre recarrega
yaml_data = YAMLParser.parse_file(path)

# ✅ Bom: Cache quando possível
if path not in cache or cache[path].mtime < path.stat().st_mtime:
    cache[path] = YAMLParser.parse_file(path)
```

### 2. Usar Async Quando Possível

```python
# ✅ Bom: Operações paralelas
await asyncio.gather(
    page1.goto(url1),
    page2.goto(url2)
)
```

### 3. Limitar Timeouts

```python
# ✅ Bom: Timeout razoável
await page.wait_for_selector('.element', timeout=5000)

# ❌ Ruim: Timeout muito longo
await page.wait_for_selector('.element', timeout=60000)
```

### 4. Cache de Seletores

```python
# ✅ Bom: Reutilizar seletor
element = page.locator('.button')
await element.click()
await element.hover()

# ❌ Ruim: Buscar novamente
await page.locator('.button').click()
await page.locator('.button').hover()
```

---

## 📝 Checklist de Otimização

- [ ] Profiling executado
- [ ] Operações lentas identificadas
- [ ] Cache implementado onde apropriado
- [ ] Timeouts otimizados
- [ ] Operações paralelas quando possível
- [ ] Seletores reutilizados
- [ ] Memória liberada após uso

---

## 🔗 Referências

- [Python cProfile](https://docs.python.org/3/library/profile.html)
- [Memory Profiler](https://pypi.org/project/memory-profiler/)
- [Playwright Best Practices](https://playwright.dev/python/docs/best-practices)

---

**Última Atualização**: Novembro 2024

