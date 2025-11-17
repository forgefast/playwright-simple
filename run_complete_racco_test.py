#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de execução para o teste completo dos fluxos Racco.

Facilita a execução do teste com opções de configuração.
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar e executar o teste
from test_complete_racco_flows import main

if __name__ == "__main__":
    # Permitir configurar headless via variável de ambiente
    if "HEADLESS" in os.environ:
        # O teste já usa a variável HEADLESS do módulo
        pass
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


