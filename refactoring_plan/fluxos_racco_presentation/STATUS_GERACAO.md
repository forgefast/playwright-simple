# Status da Geração de Vídeos

## Script em Execução

O script `generate_all_videos.py` está rodando em background e gerando todos os 10 vídeos dos fluxos Racco.

## Progresso

Para verificar o progresso:

```bash
# Ver log em tempo real
tail -f /home/gabriel/softhill/playwright-simple/generate_videos.log

# Ver quantos YAMLs foram gerados
ls -lh /home/gabriel/softhill/playwright-simple/yaml_fluxos_racco/*.yaml | wc -l

# Ver quantos vídeos foram gerados
ls -lh /home/gabriel/softhill/playwright-simple/videos_fluxos_racco/*.mp4 | wc -l

# Ver processos em execução
ps aux | grep generate_all_videos
```

## Fluxos a Gerar

1. ✅ fluxo_01_consumidor - YAML gerado, vídeo gerado
2. ⏳ fluxo_02_revendedor - Em processamento
3. ⏳ fluxo_03_escalonamento - Aguardando
4. ⏳ fluxo_04_treinamento - Aguardando
5. ⏳ fluxo_05_gamificacao - Aguardando
6. ⏳ fluxo_06_venda - Aguardando
7. ⏳ fluxo_07_comissoes - Aguardando
8. ⏳ fluxo_08_portal_consumidor - Aguardando
9. ⏳ fluxo_09_portal_revendedor - Aguardando
10. ⏳ fluxo_10_gestao_parceiros - Aguardando

## Executar Fluxo Individual

Se precisar gerar um fluxo específico:

```bash
cd /home/gabriel/softhill/playwright-simple
python3 refactoring_plan/fluxos_racco_presentation/generate_single_flow.py fluxo_01_consumidor
```

## Localização dos Arquivos

- **YAMLs**: `/home/gabriel/softhill/playwright-simple/yaml_fluxos_racco/`
- **Vídeos**: `/home/gabriel/softhill/playwright-simple/videos_fluxos_racco/`
- **Log**: `/home/gabriel/softhill/playwright-simple/generate_videos.log`

## Notas

- Cada fluxo pode levar 5-15 minutos para ser gerado completamente
- O script executa em modo não-headless (browser visível) por padrão
- Todos os vídeos terão legendas e áudio conforme documentado nos MDs
- O processo completo pode levar 1-2 horas para todos os 10 fluxos

