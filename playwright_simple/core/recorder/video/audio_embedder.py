#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio embedding module.

Provides functionality for generating and embedding audio narration in videos.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Any

logger = logging.getLogger(__name__)


class AudioEmbedder:
    """Generates and embeds audio narration in videos."""
    
    def __init__(self, steps: List[Any], video_config):
        """
        Initialize audio embedder.
        
        Args:
            steps: List of TestStep objects or dicts with timing information
            video_config: VideoConfig object with audio settings
        """
        self.steps = steps
        self.video_config = video_config
    
    async def generate_and_add_audio(self, video_path: Path, test_name: str) -> Optional[Path]:
        """
        Generate audio narration from step timestamps and add to video.
        
        Args:
            video_path: Path to video file
            test_name: Name of test (for audio filename)
            
        Returns:
            Path to video with audio, or original path if processing failed
        """
        logger.info(f"🎤 DEBUG: generate_and_add_audio called")
        logger.info(f"🎤 DEBUG: hasattr steps: {hasattr(self, 'steps')}")
        if hasattr(self, 'steps'):
            logger.info(f"🎤 DEBUG: steps is not None: {self.steps is not None}")
            if self.steps:
                logger.info(f"🎤 DEBUG: steps length: {len(self.steps)}")
            else:
                logger.warning(f"🎤 DEBUG: steps is EMPTY list!")
        else:
            logger.warning(f"🎤 DEBUG: steps attribute does NOT exist!")
        
        if not self.steps:
            logger.warning("No steps available for audio generation")
            print(f"⚠️  DEBUG: Não há steps para gerar áudio")
            return video_path
        
        # Check if TTS is available
        try:
            from ...tts import TTSManager
        except ImportError:
            logger.warning("TTSManager not available, skipping audio generation")
            print(f"⚠️  TTSManager não disponível. Instale: pip install edge-tts")
            return video_path
        
        # Determine which config to use (audio or narration)
        use_audio_config = self.video_config.audio
        if use_audio_config:
            lang = self.video_config.audio_lang
            engine = self.video_config.audio_engine
            voice = getattr(self.video_config, 'audio_voice', None)
            rate = getattr(self.video_config, 'audio_rate', None)
            pitch = getattr(self.video_config, 'audio_pitch', None)
            volume = getattr(self.video_config, 'audio_volume', None)
        else:
            lang = self.video_config.narration_lang
            engine = self.video_config.narration_engine
            voice = getattr(self.video_config, 'narration_voice', None)
            rate = None
            pitch = None
            volume = None
        
        # Default to edge-tts if not specified (better voices)
        if not engine or engine == 'gtts':
            engine = 'edge-tts'
            logger.info("Using edge-tts for better voice quality")
        
        try:
            # Create TTSManager
            # Check if edge-tts is available before creating TTSManager
            # Try importing edge_tts directly first
            try:
                import edge_tts
                # Test if it actually works
                edge_tts_available = True
                logger.info(f"🎤 DEBUG: edge_tts importado com sucesso")
                logger.info(f"🎤 DEBUG: edge_tts module path: {edge_tts.__file__ if hasattr(edge_tts, '__file__') else 'unknown'}")
            except ImportError as e:
                edge_tts_available = False
                logger.warning(f"edge-tts not available, cannot generate audio: {e}")
                logger.warning(f"🎤 DEBUG: ImportError ao importar edge_tts: {e}")
                logger.warning(f"🎤 DEBUG: Python path: {__import__('sys').path}")
                print(f"⚠️  edge-tts não está disponível. Instale: pip install edge-tts")
                print(f"⚠️  DEBUG: Erro de importação: {e}")
                print(f"⚠️  DEBUG: Tente executar: python3 -m pip install edge-tts")
                return video_path
            except Exception as e:
                edge_tts_available = False
                logger.error(f"🎤 DEBUG: Erro inesperado ao importar edge_tts: {e}", exc_info=True)
                print(f"⚠️  Erro ao importar edge-tts: {e}")
                return video_path
            
            logger.info(f"🎤 DEBUG: Criando TTSManager com engine={engine}, lang={lang}, voice={voice}")
            try:
                tts_manager = TTSManager(
                    lang=lang,
                    engine=engine,
                    slow=False,
                    voice=voice,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
                logger.info(f"🎤 DEBUG: TTSManager criado com sucesso")
            except ImportError as e:
                logger.error(f"🎤 DEBUG: ImportError ao criar TTSManager: {e}", exc_info=True)
                print(f"⚠️  Erro ao criar TTSManager: {e}")
                return video_path
            except Exception as e:
                logger.error(f"🎤 DEBUG: Erro inesperado ao criar TTSManager: {e}", exc_info=True)
                print(f"⚠️  Erro inesperado ao criar TTSManager: {e}")
                return video_path
            
            # Pass steps directly to TTSManager - it now handles TestStep objects
            # TTSManager will generate audio and store it in the steps themselves
            from ...step import TestStep
            
            logger.info(f"🎤 DEBUG: Processing {len(self.steps)} steps for audio generation")
            steps_with_audio = sum(1 for s in self.steps if isinstance(s, TestStep) and s.audio)
            steps_without_audio = len(self.steps) - steps_with_audio
            
            logger.info(f"🎤 DEBUG: Steps with audio: {steps_with_audio}, without audio: {steps_without_audio}")
            
            if not self.steps:
                logger.warning("No steps prepared for audio generation")
                print(f"⚠️  Nenhum step preparado para geração de áudio")
                return video_path
            
            # Check if we have any audio text at all
            steps_with_audio_text = sum(1 for s in self.steps if isinstance(s, TestStep) and s.audio and s.audio.strip())
            if steps_with_audio_text == 0:
                logger.warning("No steps with audio text found (all steps have None or empty audio)")
                print(f"⚠️  Nenhum step com texto de áudio encontrado (todos têm audio=None ou vazio)")
                print(f"⚠️  DEBUG: Verifique se os steps no YAML têm o campo 'audio' preenchido")
                return video_path
            
            # Generate narration - TTSManager will store audio data in steps
            logger.info(f"Generating audio narration for {len(self.steps)} steps...")
            logger.info(f"🎤 DEBUG: Steps with audio text: {steps_with_audio_text}/{len(self.steps)}")
            print(f"🔊 Gerando narração para {len(self.steps)} steps...")
            print(f"🔊 DEBUG: {steps_with_audio_text} steps têm texto de áudio")
            
            try:
                narration_audio = await tts_manager.generate_narration(
                    self.steps,
                    video_path.parent,
                    test_name,
                    return_timed_audio=True  # Returns single file with all audio + silence, synchronized with video
                )
                
                logger.info(f"🎤 DEBUG: generate_narration returned: {narration_audio}")
                if narration_audio:
                    logger.info(f"🎤 DEBUG: narration_audio path exists: {narration_audio.exists()}")
                    if narration_audio.exists():
                        logger.info(f"🎤 DEBUG: narration_audio size: {narration_audio.stat().st_size} bytes")
                
                if not narration_audio or not narration_audio.exists():
                    logger.warning("Audio narration generation failed")
                    logger.warning(f"🎤 DEBUG: narration_audio is None or doesn't exist: {narration_audio}")
                    print(f"⚠️  Falha ao gerar narração de áudio")
                    print(f"⚠️  DEBUG: TTSManager.generate_narration retornou: {narration_audio}")
                    return video_path
            except Exception as e:
                logger.error(f"🎤 DEBUG: Exception during generate_narration: {e}", exc_info=True)
                print(f"⚠️  Erro ao gerar narração: {e}")
                import traceback
                print(f"⚠️  DEBUG: Traceback: {traceback.format_exc()}")
                return video_path
            
            logger.info(f"Audio narration generated: {narration_audio.name} ({narration_audio.stat().st_size / 1024:.1f} KB)")
            print(f"✅ Narração de áudio gerada: {narration_audio.name}")
            
            # Verify audio file is valid
            audio_duration = tts_manager._get_audio_duration(narration_audio)
            logger.info(f"Audio duration: {audio_duration:.2f}s")
            print(f"📊 Duração do áudio: {audio_duration:.2f}s")
            
            # Embed audio into video MP4
            logger.info("Embedding audio into video MP4...")
            print(f"🎬 Embutindo áudio no vídeo MP4...")
            
            try:
                # Check if ffmpeg is available
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("ffmpeg not found, cannot embed audio")
                print(f"⚠️  ffmpeg não encontrado. Áudio não será embutido no vídeo.")
                return video_path
            
            # Output will be MP4 (even if input is webm, we convert)
            # Use same name as input but ensure .mp4 extension
            # If input is already MP4, use temporary suffix to avoid overwriting
            if video_path.suffix == '.mp4':
                output_path = video_path.parent / f"{video_path.stem}_with_audio.mp4"
            else:
                output_path = video_path.parent / f"{video_path.stem}.mp4"
            
            # Ensure output_path is absolute
            output_path = output_path.resolve()
            
            # Build ffmpeg command to embed audio
            # Video input may already have subtitles embedded, so we preserve them
            # For MP4, we use AAC codec for audio
            # IMPORTANT: Use absolute paths for all inputs
            video_input_absolute = str(video_path.resolve())
            audio_input_absolute = str(narration_audio.resolve())
            
            # Verify files exist before processing
            if not video_path.exists():
                logger.error(f"Video file does not exist: {video_path}")
                print(f"❌ Erro: Arquivo de vídeo não encontrado: {video_path}")
                return video_path
            
            if not narration_audio.exists():
                logger.error(f"Audio file does not exist: {narration_audio}")
                print(f"❌ Erro: Arquivo de áudio não encontrado: {narration_audio}")
                return video_path
            
            logger.info(f"🎤 DEBUG: Video file exists: {video_path.exists()}, size: {video_path.stat().st_size} bytes")
            logger.info(f"🎤 DEBUG: Audio file exists: {narration_audio.exists()}, size: {narration_audio.stat().st_size} bytes")
            
            cmd = [
                'ffmpeg',
                '-i', video_input_absolute,  # Video input (may already have subtitles) - absolute path
                '-i', audio_input_absolute,  # Audio input (MP3 with all segments + silence) - absolute path
                '-c:v', 'libx264',  # Re-encode video to ensure compatibility (preserves subtitles)
                '-preset', 'ultrafast',  # Otimização: codificação mais rápida
                '-crf', '23',  # Qualidade razoável
                '-c:a', 'aac',  # AAC codec for MP4
                '-b:a', '128k',  # Otimização: bitrate de áudio reduzido (era 192k)
                '-map', '0:v:0',  # Use video from first input (with subtitles if embedded)
                '-map', '1:a:0',  # Use audio from second input
                '-shortest',  # End when shortest stream ends (sync with audio)
                '-movflags', '+faststart',  # Fast start for web playback
                '-y',  # Overwrite output
                str(output_path)  # Output path is already absolute
            ]
            
            logger.info(f"Running ffmpeg to embed audio: {' '.join(cmd)}")
            logger.info(f"🎤 DEBUG: Video input (relative): {video_path}")
            logger.info(f"🎤 DEBUG: Video input (absolute): {video_input_absolute}")
            logger.info(f"🎤 DEBUG: Audio input (relative): {narration_audio}")
            logger.info(f"🎤 DEBUG: Audio input (absolute): {audio_input_absolute}")
            logger.info(f"🎤 DEBUG: Video output (absolute): {output_path}")
            print(f"🔄 Processando vídeo com áudio...")
            print(f"🎤 DEBUG: Embutindo áudio do arquivo: {narration_audio.name}")
            print(f"🎤 DEBUG: Vídeo de entrada: {video_path.name}")
            print(f"🎤 DEBUG: Vídeo de saída: {output_path.name}")
            
            result = subprocess.run(
                cmd,
                cwd=str(video_path.parent),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout (video processing can take time)
            )
            
            # Log ffmpeg output for debugging
            if result.returncode != 0:
                # Get full error message
                error_output = result.stderr if result.stderr else result.stdout
                logger.warning(f"🎤 DEBUG: FFmpeg return code: {result.returncode}")
                logger.warning(f"🎤 DEBUG: FFmpeg stderr (full): {error_output}")
                logger.warning(f"🎤 DEBUG: FFmpeg stdout: {result.stdout}")
                print(f"⚠️  DEBUG: FFmpeg retornou código {result.returncode}")
                if error_output:
                    # Try to extract the actual error message (usually after version info)
                    error_lines = error_output.split('\n')
                    # Skip version info and find actual error
                    actual_error = '\n'.join([line for line in error_lines if line and not line.startswith('ffmpeg version') and not line.startswith('built with') and not line.startswith('configuration:')])
                    if actual_error:
                        print(f"⚠️  DEBUG: Erro FFmpeg: {actual_error[:500]}")
                    else:
                        print(f"⚠️  DEBUG: Erro FFmpeg completo: {error_output[:500]}")
            
            if result.returncode == 0 and output_path.exists():
                # Verify output file
                output_size = output_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"Video with audio created: {output_path.name} ({output_size:.1f} MB)")
                print(f"✅ Vídeo com áudio criado: {output_path.name} ({output_size:.1f} MB)")
                
                # Replace original video with audio version
                if video_path.exists() and video_path != output_path:
                    video_path.unlink()
                if output_path != video_path:
                    output_path.rename(video_path)
                
                logger.info(f"Video processed with embedded audio: {video_path.name}")
                print(f"✅ Vídeo processado com áudio embutido: {video_path.name}")
                
                # Clean up temporary audio file (audio is now embedded)
                if narration_audio.exists():
                    try:
                        narration_audio.unlink()
                        logger.info(f"Cleaned up temporary audio file: {narration_audio.name}")
                    except Exception as e:
                        logger.warning(f"Could not delete temporary audio file: {e}")
                
                return video_path
            else:
                error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
                logger.warning(f"ffmpeg failed to embed audio: {error_msg}")
                print(f"⚠️  Erro ao embutir áudio no vídeo")
                print(f"   Detalhes: {error_msg[:200]}")
                if output_path.exists():
                    output_path.unlink()
                return video_path
                
        except ImportError as e:
            logger.warning(f"TTS library not available: {e}")
            print(f"⚠️  Biblioteca TTS não disponível: {e}")
            print(f"💡 Instale: pip install edge-tts")
            return video_path
        except Exception as e:
            logger.error(f"Error generating audio: {e}", exc_info=True)
            print(f"⚠️  Erro ao gerar áudio: {e}")
            return video_path

