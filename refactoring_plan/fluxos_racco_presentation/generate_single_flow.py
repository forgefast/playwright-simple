#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar YAML e vídeo de um único fluxo Racco.

Uso:
    python3 generate_single_flow.py fluxo_01_consumidor
"""

import asyncio
import sys
import subprocess
import yaml
from pathlib import Path
from typing import List

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Importar funções do script principal
from generate_all_videos import (
    generate_yaml_for_flow,
    generate_video_for_flow,
    parse_commands_from_md,
    print_step,
    YAMLS_DIR,
    VIDEOS_DIR,
    FLUXOS_DIR
)

# Mapeamento de nomes de fluxo para arquivos MD
FLOW_MAP = {
    "fluxo_01_consumidor": ("fluxo_01_criterios_ingresso_consumidor.md", 1),
    "fluxo_02_revendedor": ("fluxo_02_criterios_ingresso_revendedor.md", 2),
    "fluxo_03_escalonamento": ("fluxo_03_escalonamento_niveis.md", 3),
    "fluxo_04_treinamento": ("fluxo_04_jornada_treinamento.md", 4),
    "fluxo_05_gamificacao": ("fluxo_05_gamificacao.md", 5),
    "fluxo_06_venda": ("fluxo_06_venda_revendedor.md", 6),
    "fluxo_07_comissoes": ("fluxo_07_sistema_comissoes.md", 7),
    "fluxo_08_portal_consumidor": ("fluxo_08_portal_consumidor.md", 8),
    "fluxo_09_portal_revendedor": ("fluxo_09_portal_revendedor.md", 9),
    "fluxo_10_gestao_parceiros": ("fluxo_10_gestao_parceiros.md", 10),
}


async def main():
    """Gera YAML e vídeo para um fluxo específico."""
    if len(sys.argv) < 2:
        print("Uso: python3 generate_single_flow.py <nome_do_fluxo>")
        print("\nFluxos disponíveis:")
        for flow_name, (md_file, num) in FLOW_MAP.items():
            print(f"  {flow_name} - {md_file}")
        sys.exit(1)
    
    flow_name = sys.argv[1]
    
    if flow_name not in FLOW_MAP:
        print(f"❌ Fluxo não encontrado: {flow_name}")
        print("\nFluxos disponíveis:")
        for name in FLOW_MAP.keys():
            print(f"  {name}")
        sys.exit(1)
    
    md_filename, flow_num = FLOW_MAP[flow_name]
    md_file = FLUXOS_DIR / md_filename
    
    if not md_file.exists():
        print(f"❌ MD não encontrado: {md_file}")
        sys.exit(1)
    
    print_step(flow_num, flow_name)
    
    # Extrair comandos
    commands = parse_commands_from_md(md_file)
    
    if not commands:
        print(f"❌ Nenhum comando encontrado no MD")
        sys.exit(1)
    
    print(f"📋 Comandos encontrados: {len(commands)}")
    
    # Gerar YAML
    print("\n📝 Gerando YAML...")
    yaml_success = await generate_yaml_for_flow(flow_name, commands)
    
    if not yaml_success:
        print(f"❌ Falha ao gerar YAML")
        sys.exit(1)
    
    # Gerar vídeo
    print("\n📹 Gerando vídeo...")
    video_success = await generate_video_for_flow(flow_name)
    
    if not video_success:
        print(f"❌ Falha ao gerar vídeo")
        sys.exit(1)
    
    print(f"\n✅ Fluxo {flow_name} concluído com sucesso!")
    print(f"📁 YAML: {YAMLS_DIR / f'{flow_name}.yaml'}")
    print(f"📹 Vídeo: {VIDEOS_DIR}")


if __name__ == '__main__':
    asyncio.run(main())

