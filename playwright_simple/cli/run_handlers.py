#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Command Handlers.

Handles execution of 'run' command.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import argparse

from playwright_simple import TestRunner, TestConfig
from playwright_simple.core.yaml_parser import YAMLParser
from playwright_simple.core.logger import get_logger
from playwright_simple.extensions.debug import DebugExtension, DebugConfig
from playwright_simple.extensions.video import VideoExtension, VideoConfig
from playwright_simple.extensions.audio import AudioExtension, AudioConfig
from playwright_simple.extensions.subtitles import SubtitleExtension, SubtitleConfig


async def run_test(yaml_file: str, config: TestConfig, args: argparse.Namespace) -> None:
    """Run a YAML test file."""
    logger = get_logger()
    
    yaml_path = Path(yaml_file)
    if not yaml_path.exists():
        logger.error(f"Arquivo YAML não encontrado: {yaml_path}")
        print(f"❌ Arquivo não encontrado: {yaml_path}")
        return
    
    logger.info(f"Executando teste: {yaml_path}")
    print(f"🧪 Executando teste: {yaml_path}")
    
    # Parse YAML
    parser = YAMLParser()
    test_definition = parser.parse_file(yaml_path)
    
    if not test_definition:
        logger.error("Falha ao parsear YAML")
        print("❌ Erro ao parsear arquivo YAML")
        return
    
    # Create runner
    runner = TestRunner(config)
    
    # Add extensions based on config
    if config.video.enabled:
        video_config = VideoConfig(
            enabled=True,
            quality=config.video.quality,
            codec=config.video.codec,
            speed=config.video.speed,
            dir=config.video.dir
        )
        runner.add_extension(VideoExtension(video_config))
    
    if config.video.audio or config.video.narration:
        audio_config = AudioConfig(
            enabled=True,
            lang=config.video.audio_lang or 'pt-BR',
            engine=config.video.audio_engine or 'gtts',
            slow=config.video.audio_slow
        )
        runner.add_extension(AudioExtension(audio_config))
    
    if config.video.subtitles:
        subtitle_config = SubtitleConfig(
            enabled=True,
            hard=config.video.hard_subtitles
        )
        runner.add_extension(SubtitleExtension(subtitle_config))
    
    if config.debug.enabled:
        debug_config = DebugConfig(
            enabled=True,
            screenshot_on_failure=config.debug.screenshot_on_failure,
            pause_on_failure=config.debug.pause_on_failure
        )
        runner.add_extension(DebugExtension(debug_config))
    
    # Run test
    try:
        result = await runner.run(test_definition)
        
        if result.get('success'):
            print("✅ Teste passou!")
        else:
            print("❌ Teste falhou!")
            if result.get('error'):
                print(f"   Erro: {result.get('error')}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Erro ao executar teste: {e}", exc_info=True)
        print(f"❌ Erro ao executar teste: {e}")
        sys.exit(1)
    
    if result.get('video_path'):
        print(f"📹 Vídeo salvo: {result['video_path']}")

