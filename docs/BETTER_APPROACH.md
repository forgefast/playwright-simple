# Abordagem Melhor: Execução Direta com Auto-Correção

## Problema com Abordagem Atual

**Abordagem atual:**
- ❌ Processo separado em background
- ❌ Comunicação via arquivos/stdout
- ❌ Polling ou leitura de eventos
- ❌ Overhead de IPC
- ❌ Complexidade desnecessária

## Abordagem Melhor: Execução Direta

**Nova abordagem:**
- ✅ Executar teste diretamente no contexto Python
- ✅ Capturar exceções quando ocorrem
- ✅ Corrigir código/YAML imediatamente
- ✅ Usar hot reload para re-aplicar
- ✅ Continuar de onde parou (rollback + retry)

### Vantagens

1. **Zero overhead de comunicação**
   - Não precisa de arquivos, sockets, ou pipes
   - Erro já está na exceção capturada

2. **Acesso direto ao estado**
   - Tenho acesso a `page`, `test`, `context`
   - Posso inspecionar HTML diretamente
   - Não preciso ler arquivos

3. **Correção imediata**
   - Erro ocorre → capturo → corrijo → continuo
   - Sem latência de comunicação

4. **Mais simples**
   - Um único script Python
   - Sem gerenciamento de processos
   - Sem threads ou polling

## Implementação

```python
async def run_test_with_auto_fix(yaml_file, base_url):
    """Executa teste com auto-correção integrada."""
    
    # Configurar hot reload
    python_reloader = PythonReloader(['playwright_simple'])
    yaml_file_path = Path(yaml_file)
    
    # Executar teste
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        test = SimpleTestBase(page, base_url=base_url)
        
        # Carregar YAML
        yaml_data = YAMLParser.parse_file(yaml_file_path)
        steps = yaml_data.get('steps', [])
        
        current_step_index = 0
        max_retries = 5
        
        while current_step_index < len(steps):
            # Hot reload Python antes de cada passo
            python_reloader.check_and_reload_all()
            
            # Hot reload YAML se modificado
            if yaml_file_path.stat().st_mtime > last_yaml_mtime:
                yaml_data = YAMLParser.parse_file(yaml_file_path)
                steps = yaml_data.get('steps', [])
                last_yaml_mtime = yaml_file_path.stat().st_mtime
            
            step = steps[current_step_index]
            state_before = await capture_state(page)
            
            # Tentar executar passo
            retry_count = 0
            step_success = False
            
            while retry_count < max_retries and not step_success:
                try:
                    await execute_step(step, test, page)
                    step_success = True
                    current_step_index += 1
                    
                except Exception as e:
                    retry_count += 1
                    
                    # EU (IA) analiso e corrijo aqui
                    error_info = {
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'step': step,
                        'step_number': current_step_index + 1,
                        'html': await page.content(),  # Tenho acesso direto!
                        'url': page.url
                    }
                    
                    # Analisar erro e corrigir
                    fix_result = await analyze_and_fix(error_info, yaml_file_path)
                    
                    if fix_result['fixed']:
                        # Rollback para estado antes do passo
                        await restore_state(page, state_before)
                        
                        # Recarregar YAML corrigido
                        yaml_data = YAMLParser.parse_file(yaml_file_path)
                        steps = yaml_data.get('steps', [])
                        
                        # Tentar novamente
                        continue
                    else:
                        # Não consegui corrigir, relançar
                        raise
            
            if not step_success:
                break  # Falhou após todas tentativas
```

## Comparação

| Aspecto | Abordagem Atual | Abordagem Melhor |
|---------|----------------|------------------|
| **Comunicação** | Arquivos/stdout | Direto (exceções) |
| **Latência** | ~100-500ms | Imediato |
| **Complexidade** | Alta (processos, IPC) | Baixa (um script) |
| **Acesso ao estado** | Via arquivos | Direto (variáveis) |
| **Debug** | Difícil | Fácil (pdb, etc) |
| **Overhead** | Alto | Zero |

## Migração

Posso criar um novo script `auto_fix_direct.py` que:
1. Executa teste diretamente
2. Captura exceções
3. Chama funções de correção
4. Usa hot reload para aplicar
5. Continua automaticamente

**Você prefere que eu implemente essa abordagem?**

