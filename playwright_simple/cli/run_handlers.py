#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Command Handlers.

Handles execution of 'run' command.
"""

import sys
from pathlib import Path

import argparse

from playwright_simple.core.recorder.recorder import Recorder
from playwright_simple.core.logger import get_logger


async def run_test(yaml_file: str, config, args: argparse.Namespace) -> None:
    """Run a YAML test file using Recorder directly (SAME as test_odoo_interactive.py)."""
    logger = get_logger()
    
    yaml_path = Path(yaml_file)
    if not yaml_path.exists():
        logger.error(f"Arquivo YAML não encontrado: {yaml_path}")
        print(f"❌ Arquivo não encontrado: {yaml_path}")
        return
    
    logger.info(f"Executando teste: {yaml_path}")
    print(f"🧪 Executando teste: {yaml_path}")
    
    # Use Recorder in read mode (SAME class as recording, just different mode)
    recorder = Recorder(
        output_path=yaml_path,  # Input YAML file
        initial_url=None,  # Will be read from YAML
        headless=config.browser.headless if hasattr(config, 'browser') else False,
        debug=args.debug if hasattr(args, 'debug') else False,
        fast_mode=getattr(config.step, 'fast_mode', False) if hasattr(config, 'step') else False,
        mode='read'  # Read mode: import YAML instead of export
    )
    
    # Start recorder (SAME method as recording, but executes YAML steps)
    try:
        await recorder.start()
        print("✅ Teste passou!")
    except Exception as e:
        logger.error(f"Erro ao executar teste: {e}", exc_info=True)
        print(f"❌ Erro ao executar teste: {e}")
        sys.exit(1)

