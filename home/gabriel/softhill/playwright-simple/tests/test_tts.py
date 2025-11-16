#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for TTS module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from playwright_simple.core.tts import TTSManager


def test_tts_manager_init_gtts():
    """Test TTSManager initialization with gTTS."""
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', True):
        manager = TTSManager(lang='pt-br', engine='gtts')
        assert manager.lang == 'pt-br'
        assert manager.engine == 'gtts'
        assert manager.slow is False


def test_tts_manager_init_edge_tts():
    """Test TTSManager initialization with edge-tts."""
    with patch('playwright_simple.core.tts.EDGE_TTS_AVAILABLE', True):
        manager = TTSManager(lang='en', engine='edge-tts')
        assert manager.lang == 'en'
        assert manager.engine == 'edge-tts'


def test_tts_manager_init_pyttsx3():
    """Test TTSManager initialization with pyttsx3."""
    with patch('playwright_simple.core.tts.PYTTSX3_AVAILABLE', True):
        manager = TTSManager(lang='es', engine='pyttsx3')
        assert manager.lang == 'es'
        assert manager.engine == 'pyttsx3'


def test_tts_manager_init_engine_not_available():
    """Test TTSManager initialization with unavailable engine."""
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', False):
        with pytest.raises(ImportError, match="gTTS is required"):
            TTSManager(engine='gtts')
    
    with patch('playwright_simple.core.tts.EDGE_TTS_AVAILABLE', False):
        with pytest.raises(ImportError, match="edge-tts is required"):
            TTSManager(engine='edge-tts')
    
    with patch('playwright_simple.core.tts.PYTTSX3_AVAILABLE', False):
        with pytest.raises(ImportError, match="pyttsx3 is required"):
            TTSManager(engine='pyttsx3')


@pytest.mark.asyncio
async def test_tts_generate_audio_empty_text():
    """Test generating audio with empty text."""
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', True):
        manager = TTSManager(engine='gtts')
        output_path = Path("test.mp3")
        
        result = await manager.generate_audio("", output_path)
        assert result is False
        
        result = await manager.generate_audio("   ", output_path)
        assert result is False


@pytest.mark.asyncio
async def test_tts_generate_audio_gtts():
    """Test generating audio with gTTS."""
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', True):
        # Mock the _gtts_sync method directly
        with patch.object(TTSManager, '_gtts_sync', new_callable=MagicMock) as mock_sync:
            # Create the file to simulate successful save
            output_path = Path("test.mp3")
            output_path.touch()
            
            manager = TTSManager(engine='gtts', lang='pt-br')
            
            try:
                result = await manager.generate_audio("Test text", output_path)
                assert result is True
                mock_sync.assert_called_once()
            finally:
                if output_path.exists():
                    output_path.unlink()


@pytest.mark.asyncio
async def test_tts_generate_audio_edge_tts():
    """Test generating audio with edge-tts."""
    with patch('playwright_simple.core.tts.EDGE_TTS_AVAILABLE', True):
        # Mock the _generate_edge_tts method directly
        with patch.object(TTSManager, '_generate_edge_tts', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = True
            
            manager = TTSManager(engine='edge-tts', lang='pt-br')
            output_path = Path("test.mp3")
            output_path.touch()
            
            try:
                result = await manager.generate_audio("Test text", output_path)
                assert result is True
                mock_generate.assert_called_once()
            finally:
                if output_path.exists():
                    output_path.unlink()


@pytest.mark.asyncio
async def test_tts_generate_audio_pyttsx3():
    """Test generating audio with pyttsx3."""
    with patch('playwright_simple.core.tts.PYTTSX3_AVAILABLE', True):
        # Mock the _generate_pyttsx3 method directly
        with patch.object(TTSManager, '_generate_pyttsx3', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = True
            
            manager = TTSManager(engine='pyttsx3')
            output_path = Path("test.wav")
            output_path.touch()
            
            try:
                result = await manager.generate_audio("Test text", output_path)
                assert result is True
                mock_generate.assert_called_once()
            finally:
                if output_path.exists():
                    output_path.unlink()


@pytest.mark.asyncio
async def test_tts_generate_audio_unknown_engine():
    """Test generating audio with unknown engine."""
    manager = TTSManager(engine='unknown')
    output_path = Path("test.mp3")
    
    result = await manager.generate_audio("Test text", output_path)
    assert result is False


@pytest.mark.asyncio
async def test_tts_generate_narration():
    """Test generating narration from test steps."""
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', True):
        manager = TTSManager(engine='gtts')
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        test_steps = [
            {"text": "Step 1"},
            {"description": "Step 2"},
            {"text": "Step 3"},
        ]
        
        try:
            # Mock generate_audio and _concatenate_audio
            with patch.object(manager, 'generate_audio', new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = True
                with patch.object(manager, '_concatenate_audio', new_callable=AsyncMock) as mock_concat:
                    mock_concat.return_value = True
                    # Mock Path operations to avoid file system issues
                    with patch('pathlib.Path.exists') as mock_exists:
                        mock_exists.return_value = True
                        with patch('pathlib.Path.mkdir'):
                            with patch('pathlib.Path.unlink'):
                                with patch('pathlib.Path.rmdir'):
                                    result = await manager.generate_narration(
                                        test_steps, output_dir, "test"
                                    )
                                    
                                    # Should attempt to generate narration
                                    assert mock_gen.called
                                    assert mock_concat.called or result is None
        finally:
            # Cleanup
            if output_dir.exists():
                for f in output_dir.glob("*"):
                    if f.is_file():
                        f.unlink()
                    elif f.is_dir():
                        for subf in f.glob("*"):
                            subf.unlink()
                        f.rmdir()
                output_dir.rmdir()


@pytest.mark.asyncio
async def test_tts_generate_narration_empty_steps():
    """Test generating narration with empty steps."""
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', True):
        manager = TTSManager(engine='gtts')
        output_dir = Path("test_output")
        
        result = await manager.generate_narration([], output_dir, "test")
        assert result is None


@pytest.mark.asyncio
async def test_tts_concatenate_audio():
    """Test concatenating audio files."""
    import subprocess
    
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', True):
        manager = TTSManager(engine='gtts')
        audio_files = [Path("test1.mp3"), Path("test2.mp3")]
        output_path = Path("output.mp3")
        
        with patch('subprocess.run') as mock_run:
            # subprocess.run returns a CompletedProcess-like object
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            with patch('pathlib.Path.exists', return_value=True):
                result = await manager._concatenate_audio(audio_files, output_path)
                assert result is True
                # subprocess.run is called with kwargs, so just check it was called
                assert mock_run.called


@pytest.mark.asyncio
async def test_tts_concatenate_audio_no_ffmpeg():
    """Test concatenating audio when ffmpeg is not available."""
    import subprocess
    
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', True):
        manager = TTSManager(engine='gtts')
        audio_files = [Path("test1.mp3")]
        output_path = Path("output.mp3")
        
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            # Should catch the exception and return False or raise TTSGenerationError
            try:
                result = await manager._concatenate_audio(audio_files, output_path)
                assert result is False
            except Exception as e:
                # If it raises an exception, that's also acceptable
                assert "ffmpeg" in str(e).lower() or "not found" in str(e).lower()


@pytest.mark.asyncio
async def test_tts_concatenate_audio_empty_list():
    """Test concatenating empty audio file list."""
    with patch('playwright_simple.core.tts.GTTS_AVAILABLE', True):
        manager = TTSManager(engine='gtts')
        output_path = Path("output.mp3")
        
        result = await manager._concatenate_audio([], output_path)
        assert result is False

