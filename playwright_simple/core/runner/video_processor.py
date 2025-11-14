#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video processing module.

Handles video speed adjustment, format conversion, and processing.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, List, Any, Union, Tuple, TYPE_CHECKING
from datetime import datetime

from ..config import TestConfig
from ..exceptions import VideoProcessingError
from ..constants import FFMPEG_TIMEOUT

if TYPE_CHECKING:
    from .subtitle_generator import SubtitleGenerator
    from .audio_processor import AudioProcessor

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Handles video processing operations."""
    
    def __init__(self, config: TestConfig):
        """
        Initialize video processor.
        
        Args:
            config: Test configuration
        """
        self.config = config
    
    async def process_speed(self, video_path: Path, speed: float) -> Optional[Path]:
        """
        Process video to change playback speed using ffmpeg.
        
        Args:
            video_path: Path to original video
            speed: Playback speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = 2x slower)
            
        Returns:
            Path to processed video, or None if processing failed
        """
        if speed == 1.0:
            return video_path
        
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffmpeg não encontrado. Vídeo não será processado.")
            return video_path
        
        # Create temporary output path
        output_path = video_path.parent / f"{video_path.stem}_processed{video_path.suffix}"
        
        try:
            # Calculate PTS (presentation timestamp) scale
            # For speed > 1.0: video plays faster (pts scale < 1.0)
            # For speed < 1.0: video plays slower (pts scale > 1.0)
            pts_scale = 1.0 / speed
            
            # Use ffmpeg to change video speed
            # -filter:v "setpts=PTS*{pts_scale}" changes video speed
            # -filter:a "atempo={speed}" changes audio speed (if audio exists)
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-filter:v', f'setpts=PTS*{pts_scale}',
                '-c:v', 'libvpx-vp9' if video_path.suffix == '.webm' else 'libx264',
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            # Handle audio speed (atempo range is 0.5 to 2.0, so we may need multiple filters)
            if speed != 1.0:
                if speed > 2.0:
                    # Speed > 2.0: need multiple atempo filters (each max 2.0)
                    num_filters = int(speed / 2.0) + (1 if speed % 2.0 > 0 else 0)
                    atempo_chain = []
                    remaining_speed = speed
                    for _ in range(num_filters):
                        if remaining_speed >= 2.0:
                            atempo_chain.append('atempo=2.0')
                            remaining_speed /= 2.0
                        else:
                            atempo_chain.append(f'atempo={remaining_speed}')
                            break
                    audio_filter = ','.join(atempo_chain)
                elif speed < 0.5:
                    # Speed < 0.5: need multiple atempo filters (each min 0.5)
                    num_filters = int(0.5 / speed) + (1 if 0.5 % speed > 0 else 0)
                    atempo_chain = []
                    remaining_speed = speed
                    for _ in range(num_filters):
                        if remaining_speed <= 0.5:
                            atempo_chain.append('atempo=0.5')
                            remaining_speed *= 2.0
                        else:
                            atempo_chain.append(f'atempo={remaining_speed}')
                            break
                    audio_filter = ','.join(atempo_chain)
                else:
                    # Single atempo filter (0.5 <= speed <= 2.0)
                    audio_filter = f'atempo={speed}'
                
                cmd.insert(5, '-filter:a')
                cmd.insert(6, audio_filter)
                cmd.insert(7, '-c:a')
                cmd.insert(8, 'libopus' if video_path.suffix == '.webm' else 'aac')
            else:
                # No audio processing needed
                cmd.insert(5, '-an')  # Remove audio
            
            # Run ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=FFMPEG_TIMEOUT
            )
            
            if result.returncode == 0 and output_path.exists():
                # Replace original with processed video
                video_path.unlink()
                output_path.rename(video_path)
                return video_path
            else:
                logger.warning(f"Erro ao processar vídeo: {result.stderr[:200]}")
                if output_path.exists():
                    output_path.unlink()
                return video_path
                
        except subprocess.TimeoutExpired as e:
            logger.error(f"Timeout processing video: {e}")
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Video processing timeout: {e}") from e
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Failed to process video: {e}") from e
    
    def _format_video_name(self, test_name: str) -> str:
        """
        Format test name for video title screen.
        
        Converts technical names to readable format:
        - test_colaborador_portal -> "Colaborador Portal"
        - test_video_simple -> "Video Simple"
        - 01_login -> "Login"
        
        Args:
            test_name: Technical test name
            
        Returns:
            Formatted name for display
        """
        # Remove common prefixes
        name = test_name
        for prefix in ['test_', 'test', 'Test_', 'Test']:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        
        # Remove numeric prefixes (01_, 02_, etc.)
        import re
        name = re.sub(r'^\d+_', '', name)
        
        # Convert snake_case to Title Case
        name = name.replace('_', ' ').replace('-', ' ')
        # Capitalize each word
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name if name else test_name
    
    def _create_intro_screen(
        self,
        video_name: str,
        duration: float = 3.0,
        width: int = 1920,
        height: int = 1080
    ) -> Optional[Path]:
        """
        Create intro screen video using ffmpeg.
        
        Args:
            video_name: Formatted video name to display
            duration: Duration of intro screen in seconds
            width: Video width
            height: Video height
            
        Returns:
            Path to intro screen video, or None if creation failed
        """
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ffmpeg não encontrado. Tela inicial não será criada.")
            return None
        
        # Create temporary intro video path
        intro_path = Path("/tmp") / f"intro_{video_name.replace(' ', '_')}.mp4"
        
        try:
            # Create intro screen with solid color background (faster than gradient)
            # Using simple solid color with text overlay - much faster!
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c=0x667eea:size={width}x{height}:duration={duration}:rate=30',
                '-vf', (
                    f"drawtext=text='{video_name}':"
                    f"fontsize=72:"
                    f"fontcolor=white:"
                    f"x=(w-text_w)/2:"
                    f"y=(h-text_h)/2-50,"
                    f"drawtext=text='Gravando vídeo de teste...':"
                    f"fontsize=36:"
                    f"fontcolor=white:"
                    f"x=(w-text_w)/2:"
                    f"y=(h-text_h)/2+50"
                ),
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # Use fastest preset for intro screen
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                '-y',
                str(intro_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10  # Reduced timeout since we're using simpler method
            )
            
            if result.returncode == 0 and intro_path.exists():
                size_kb = intro_path.stat().st_size / 1024
                logger.info(f"Tela inicial criada: {intro_path} ({size_kb:.1f}KB)")
                return intro_path
            else:
                # Log full error, but skip version info at the start
                stderr_lines = result.stderr.split('\n')
                # Skip FFmpeg version info (first few lines)
                error_lines = [line for line in stderr_lines if line.strip() and 
                              not line.startswith('ffmpeg version') and
                              not line.startswith('built with') and
                              not line.startswith('configuration:') and
                              not line.startswith('libav') and
                              ('error' in line.lower() or 'failed' in line.lower() or 'invalid' in line.lower() or 'No such file' in line)]
                if error_lines:
                    logger.error(f"Erro ao criar tela inicial: {error_lines[0]}")
                elif result.returncode != 0:
                    # Show last few non-empty lines if no error found
                    last_lines = [line for line in stderr_lines[-5:] if line.strip() and not line.startswith('ffmpeg version')]
                    if last_lines:
                        logger.error(f"Erro ao criar tela inicial (código {result.returncode}): {last_lines[-1]}")
                    else:
                        logger.error(f"Erro ao criar tela inicial (código {result.returncode})")
                else:
                    logger.warning(f"Tela inicial não foi criada (código {result.returncode}, arquivo existe: {intro_path.exists()})")
                return None
                    
        except Exception as e:
            logger.error(f"Erro ao criar tela inicial: {e}")
            return None
    
    async def process_all_in_one(
        self,
        video_path: Path,
        test_steps: List[Any],  # Can be TestStep objects or dicts
        start_time: datetime,
        subtitle_generator: 'SubtitleGenerator',
        audio_processor: Optional['AudioProcessor'] = None,
        narration_audio: Optional[Path] = None,
        test_name: Optional[str] = None
    ) -> Optional[Path]:
        """
        Process video with speed, subtitles, and audio in ONE ffmpeg pass (much faster!).
        
        Args:
            video_path: Path to original video
            test_steps: List of test steps for subtitles
            start_time: Test start time
            subtitle_generator: SubtitleGenerator instance
            audio_processor: AudioProcessor instance
            narration_audio: Optional narration audio file
            test_name: Test name for intro screen (optional)
            
        Returns:
            Path to processed video, or None if processing failed
        """
        process_start_time = time.time()
        logger.info(f"process_all_in_one chamado: video={video_path.name}, test_name={test_name}, subtitles={self.config.video.subtitles}, steps={len(test_steps) if test_steps else 0}")
        print(f"  🔍 DEBUG: process_all_in_one chamado: video={video_path.name}, test_name={test_name}")
        print(f"  ⏱️  Performance: Iniciando process_all_in_one às {time.strftime('%H:%M:%S')}")
        try:
            # Check if ffmpeg is available
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            logger.debug("FFmpeg disponível")
            print(f"  🔍 DEBUG: FFmpeg disponível")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            process_duration = time.time() - process_start_time
            logger.warning(f"ffmpeg não encontrado após {process_duration:.2f}s. Vídeo não será processado.")
            print(f"  🔍 DEBUG: FFmpeg NÃO encontrado: {e}")
            print(f"  ⏱️  Performance: process_all_in_one abortado após {process_duration:.2f}s (FFmpeg não encontrado)")
            return video_path
        
        # Determine output extension based on config
        output_ext = ".mp4" if self.config.video.codec == "mp4" else video_path.suffix
        output_path = video_path.parent / f"{video_path.stem}_processed{output_ext}"
        print(f"  🔍 DEBUG: output_path={output_path.name}")
        
        try:
            print(f"  🔍 DEBUG: Entrando no try de process_all_in_one")
            # Create intro screen if test_name is provided
            # TEMPORARILY DISABLED - focus on fixing library first
            intro_video = None
            formatted_name = None
            if False and test_name:  # DISABLED: test_name
                intro_start = time.time()
                formatted_name = self._format_video_name(test_name)
                logger.info(f"Criando tela inicial para: {formatted_name}")
                print(f"  🔍 DEBUG: Criando tela inicial para: {formatted_name}")
                print(f"  ⏱️  Performance: Iniciando criação de tela inicial às {time.strftime('%H:%M:%S')}")
                intro_video = self._create_intro_screen(formatted_name, duration=3.0)
                intro_duration = time.time() - intro_start
                print(f"  ⏱️  Performance: Criação de tela inicial concluída em {intro_duration:.2f}s")
                if intro_video and intro_video.exists():
                    size_kb = intro_video.stat().st_size / 1024
                    logger.info(f"Tela inicial criada com sucesso: {intro_video.name} ({size_kb:.1f}KB)")
                    print(f"  🔍 DEBUG: Tela inicial criada: {intro_video.name}")
                else:
                    logger.warning(f"Tela inicial não foi criada para: {formatted_name}")
                    print(f"  🔍 DEBUG: Tela inicial NÃO foi criada")
            else:
                print(f"  🔍 DEBUG: Tela inicial DESABILITADA para teste de performance")
            
            # Build complex filter combining speed, subtitles, and audio
            filter_build_start = time.time()
            print(f"  🔍 DEBUG: Construindo filtros...")
            print(f"  ⏱️  Performance: Iniciando construção de filtros às {time.strftime('%H:%M:%S')}")
            video_filters = []
            audio_filters = []
            input_files = []
            
            # Add intro video first if created (use relative path if in same directory)
            if intro_video and intro_video.exists():
                if intro_video.parent == video_path.parent:
                    input_files.extend(['-i', intro_video.name])
                else:
                    input_files.extend(['-i', str(intro_video)])
                logger.info(f"Tela inicial será adicionada ao vídeo: {formatted_name}")
            elif test_name:
                logger.warning(f"Tela inicial não disponível apesar de test_name={test_name}")
            
            # Add main video (will use relative path when FFmpeg runs in video directory)
            input_files.extend(['-i', video_path.name])
            
            # 1. Speed adjustment
            if self.config.video.speed != 1.0:
                pts_scale = 1.0 / self.config.video.speed
                video_filters.append(f'setpts=PTS*{pts_scale}')
                
                # Audio speed adjustment
                if self.config.video.speed > 2.0:
                    num_filters = int(self.config.video.speed / 2.0) + (1 if self.config.video.speed % 2.0 > 0 else 0)
                    atempo_chain = []
                    remaining_speed = self.config.video.speed
                    for _ in range(num_filters):
                        if remaining_speed >= 2.0:
                            atempo_chain.append('atempo=2.0')
                            remaining_speed /= 2.0
                        else:
                            atempo_chain.append(f'atempo={remaining_speed}')
                            break
                    audio_filters.append(','.join(atempo_chain))
                elif self.config.video.speed < 0.5:
                    num_filters = int(0.5 / self.config.video.speed) + (1 if 0.5 % self.config.video.speed > 0 else 0)
                    atempo_chain = []
                    remaining_speed = self.config.video.speed
                    for _ in range(num_filters):
                        if remaining_speed <= 0.5:
                            atempo_chain.append('atempo=0.5')
                            remaining_speed *= 2.0
                        else:
                            atempo_chain.append(f'atempo={remaining_speed}')
                            break
                    audio_filters.append(','.join(atempo_chain))
                else:
                    audio_filters.append(f'atempo={self.config.video.speed}')
            
            # 2. Subtitles (if enabled and steps available)
            # Can use hard subtitles (burned into video) or soft subtitles (separate track)
            srt_path = None
            use_hard_subtitles = self.config.video.hard_subtitles
            print(f"  🔍 DEBUG: hard_subtitles config: {use_hard_subtitles}")
            if self.config.video.subtitles and test_steps:
                subtitle_gen_start = time.time()
                print(f"  🔍 DEBUG: Gerando legendas...")
                print(f"  ⏱️  Performance: Iniciando geração de legendas às {time.strftime('%H:%M:%S')}")
                # test_steps can be TestStep objects or dicts - _generate_srt_file handles both
                srt_path = await subtitle_generator.generate(video_path, test_steps, start_time)
                subtitle_gen_duration = time.time() - subtitle_gen_start
                print(f"  ⏱️  Performance: Geração de legendas concluída em {subtitle_gen_duration:.2f}s")
                if srt_path and srt_path.exists():
                    if use_hard_subtitles:
                        # Use hard subtitles (burned into video) - requires re-encode
                        # Use filename only (SRT is in same directory as video)
                        # FFmpeg will look for it relative to video file location
                        srt_filename = srt_path.name
                        # Escape for filter: colon, brackets, single quotes
                        srt_path_escaped = (srt_filename
                                          .replace(':', '\\:')
                                          .replace('[', '\\[')
                                          .replace(']', '\\]')
                                          .replace("'", "\\'"))
                        # Use single quotes for the path
                        subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20'"
                        video_filters.append(subtitle_filter)
                        logger.info(f"Legendas serão queimadas no vídeo (hard subtitles): {srt_path.name}")
                        print(f"  🔍 DEBUG: Legendas geradas: {srt_path.name}, serão queimadas no vídeo (hard subtitles)")
                    else:
                        # Use soft subtitles (separate track) - MUCH faster, no re-encode needed
                        logger.info(f"Legendas serão adicionadas como faixa separada (soft subtitles): {srt_path.name}")
                        print(f"  🔍 DEBUG: Legendas geradas: {srt_path.name}, serão adicionadas como faixa separada (soft subtitles - rápido)")
                else:
                    print(f"  🔍 DEBUG: Legendas NÃO foram geradas")
            else:
                print(f"  🔍 DEBUG: Legendas desabilitadas ou sem steps (subtitles={self.config.video.subtitles}, test_steps={bool(test_steps)})")
            
            # 3. Build ffmpeg command
            cmd = ['ffmpeg'] + input_files
            
            # Add subtitle file as input (for soft subtitles - no re-encode needed!)
            if srt_path and srt_path.exists() and not use_hard_subtitles:
                cmd.extend(['-i', str(srt_path)])
            
            # Add audio inputs (narration takes priority, then background audio)
            # Use relative paths from video directory for FFmpeg execution
            audio_inputs = []
            audio_input_paths = []
            
            # Add narration audio (now always a single concatenated file with silence)
            if narration_audio and narration_audio.exists():
                audio_inputs.append(narration_audio)
                # Use relative path if in same directory, otherwise absolute
                if narration_audio.parent == video_path.parent:
                    audio_input_paths.append(narration_audio.name)
                else:
                    audio_input_paths.append(str(narration_audio))
            if self.config.video.audio_file:
                audio_path = Path(self.config.video.audio_file)
                if audio_path.exists():
                    audio_inputs.append(audio_path)
                    if audio_path.parent == video_path.parent:
                        audio_input_paths.append(audio_path.name)
                    else:
                        audio_input_paths.append(str(audio_path))
            
            for i, audio_input_path in enumerate(audio_input_paths):
                # Loop background audio if mixing with narration
                if len(audio_input_paths) > 1 and i == len(audio_input_paths) - 1:
                    cmd.extend(['-stream_loop', '-1'])
                cmd.extend(['-i', audio_input_path])
            
            # Clean up intro video after processing
            intro_cleanup = intro_video if intro_video and intro_video.exists() else None
            
            # Build filter_complex for video and audio
            filter_complex_parts = []
            video_output_label = '[v]'
            audio_output_label = '[a]'
            
            # Determine input indices
            # Input order: [0] intro (if exists), [1] main video, [2] subtitles (if soft subtitles), [3+] audio inputs
            main_video_idx = 1 if intro_video and intro_video.exists() else 0
            intro_video_idx = 0 if intro_video and intro_video.exists() else None
            subtitle_input_idx = None
            if srt_path and srt_path.exists() and not use_hard_subtitles:
                # Subtitle input index: after intro (if exists) + main video
                # Input order: [0] intro (if exists), [1] main video, [2] subtitles (if intro exists), [1] subtitles (if no intro)
                subtitle_input_idx = (1 if intro_video and intro_video.exists() else 0) + 1
            
            # Check conditions for fast path
            # IMPORTANT: Soft subtitles don't count as video_filters - they don't require re-encode!
            # Hard subtitles DO count as video_filters because they require re-encode
            has_video_filters = bool(video_filters)  # Speed/setpts filters + hard subtitles (if enabled)
            needs_conversion = self.config.video.codec == "mp4" and video_path.suffix == ".webm"
            has_intro = intro_video and intro_video.exists()
            has_audio_input = len(audio_inputs) > 0
            has_soft_subtitles = srt_path and srt_path.exists() and not use_hard_subtitles
            # Audio input offset: intro(1) + main(1) + subtitles(1 if soft subtitles) = base offset
            audio_input_offset = (1 if intro_video and intro_video.exists() else 0) + 1 + (1 if has_soft_subtitles else 0)
            
            # Fast path: intro + conversion + soft subtitles (all without re-encode except conversion)
            # Soft subtitles can be added with -c copy, so they don't block fast path!
            # Hard subtitles block fast path because they require re-encode
            use_fast_path = (has_intro and not audio_filters and 
                           self.config.video.speed == 1.0 and not has_audio_input and
                           not has_video_filters)  # NO VIDEO FILTERS (but soft subtitles are OK!)
            
            if use_fast_path:
                print(f"  🔍 DEBUG: use_fast_path=True, has_video_filters={has_video_filters}, needs_conversion={needs_conversion}")
                if not has_video_filters:
                    # No filters at all - fastest path
                    logger.info("Usando caminho rápido: concatenação em webm + conversão para mp4")
                    print(f"  🔍 DEBUG: Caminho rápido sem filtros")
                    if needs_conversion and has_intro:
                        # OPTIMIZED: Concat in webm first (can use copy = fast!), then convert to mp4
                        # Step 1: Convert intro.mp4 to webm (quick)
                        intro_webm = None
                        if intro_video and intro_video.exists():
                            intro_webm_start = time.time()
                            intro_webm = video_path.parent / f"intro_{video_path.stem}.webm"
                            print(f"  🔍 DEBUG: Convertendo intro para webm: {intro_webm.name}")
                            convert_intro_cmd = [
                                'ffmpeg', '-i', str(intro_video),
                                '-c:v', 'libvpx-vp9', '-preset', 'ultrafast', '-crf', '30',
                                '-c:a', 'libopus', '-y', str(intro_webm)
                            ]
                            convert_result = subprocess.run(convert_intro_cmd, capture_output=True, text=True, timeout=30)
                            intro_webm_duration = time.time() - intro_webm_start
                            print(f"  ⏱️  Performance: Intro convertido para webm em {intro_webm_duration:.2f}s")
                            if convert_result.returncode != 0 or not intro_webm.exists():
                                logger.warning("Falha ao converter intro para webm, usando método direto")
                                intro_webm = None
                        
                        # Step 2: Concat intro.webm + main.webm → temp.webm (using copy = FAST!)
                        if intro_webm and intro_webm.exists():
                            concat_start = time.time()
                            temp_webm = video_path.parent / f"{video_path.stem}_concat.webm"
                            # Create concat file for demuxer (fastest method)
                            concat_file = video_path.parent / f"{video_path.stem}_concat.txt"
                            with open(concat_file, 'w') as f:
                                f.write(f"file '{intro_webm.absolute()}'\n")
                                f.write(f"file '{video_path.absolute()}'\n")
                            
                            concat_cmd = [
                                'ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(concat_file),
                                '-c', 'copy', '-y', str(temp_webm)
                            ]
                            print(f"  🔍 DEBUG: Concatenando em webm (copy - rápido!)")
                            concat_result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=60)
                            concat_duration = time.time() - concat_start
                            print(f"  ⏱️  Performance: Concatenação webm concluída em {concat_duration:.2f}s")
                            
                            # Clean up concat file and intro webm
                            if concat_file.exists():
                                concat_file.unlink()
                            if intro_webm.exists():
                                intro_webm.unlink()
                            
                            if concat_result.returncode == 0 and temp_webm.exists():
                                # Step 3: Convert temp.webm → final.mp4 with soft subtitles
                                convert_start = time.time()
                                print(f"  🔍 DEBUG: Convertendo webm concatenado para mp4 com legendas")
                                final_cmd = ['ffmpeg', '-i', str(temp_webm)]
                                if srt_path and srt_path.exists():
                                    final_cmd.extend(['-i', str(srt_path)])
                                    final_cmd.extend(['-map', '0:v', '-map', '0:a?', '-map', '1:s?'])
                                    final_cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-threads', '0'])
                                    final_cmd.extend(['-c:a', 'aac'])
                                    final_cmd.extend(['-c:s', 'mov_text'])
                                else:
                                    final_cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-threads', '0'])
                                    final_cmd.extend(['-c:a', 'aac'])
                                final_cmd.extend(['-y', str(output_path)])
                                
                                ffmpeg_start_time = time.time()
                                print(f"  ⏱️  Performance: Iniciando conversão final webm→mp4 às {time.strftime('%H:%M:%S')}")
                                result = subprocess.run(final_cmd, capture_output=True, text=True, timeout=600)
                                convert_duration = time.time() - convert_start
                                ffmpeg_duration = time.time() - ffmpeg_start_time
                                print(f"  ⏱️  Performance: Conversão webm→mp4 concluída em {ffmpeg_duration:.2f}s")
                                
                                # Clean up temp webm
                                if temp_webm.exists():
                                    temp_webm.unlink()
                                
                                if result.returncode == 0 and output_path.exists():
                                    if video_path.exists():
                                        video_path.unlink()
                                    process_duration = time.time() - process_start_time
                                    logger.info(f"process_all_in_one concluído (fast path - webm concat) em {process_duration:.2f}s")
                                    print(f"  ⏱️  Performance: process_all_in_one concluído (fast path - webm concat) em {process_duration:.2f}s")
                                    if intro_cleanup and intro_cleanup.exists():
                                        try:
                                            intro_cleanup.unlink()
                                        except Exception as e:
                                            logger.warning(f"Erro ao remover tela inicial temporária: {e}")
                                    return output_path
                                else:
                                    error_output = result.stderr if result.stderr else result.stdout or 'Erro desconhecido'
                                    logger.error(f"FFmpeg error (conversão final): {error_output[:500]}")
                                    if output_path.exists():
                                        output_path.unlink()
                                    raise VideoProcessingError(f"Falha ao converter para MP4: {error_output[:500]}")
                            else:
                                logger.warning("Falha na concatenação webm, usando método direto")
                                # Fall through to direct method
                        else:
                            logger.warning("Intro webm não disponível, usando método direto")
                            # Fall through to direct method
                    
                    # Direct method: concat + convert in one pass (if webm concat failed or no intro)
                    if needs_conversion:
                        # Concat intro + main, then convert to mp4
                        print(f"  🔍 DEBUG: Precisa conversão, criando filter_complex para concat + conversão")
                        filter_complex_parts = [f'[{intro_video_idx}:v][{main_video_idx}:v]concat=n=2:v=1:a=0[v]']
                        cmd.extend(['-filter_complex', ';'.join(filter_complex_parts)])
                        cmd.extend(['-map', '[v]'])
                        # Copy audio from main video if exists
                        cmd.extend(['-map', f'{main_video_idx}:a?'])
                        # Add soft subtitles if available (no re-encode needed!)
                        if has_soft_subtitles and subtitle_input_idx is not None:
                            cmd.extend(['-map', f'{subtitle_input_idx}:s?'])
                            cmd.extend(['-c:s', 'mov_text'])  # MP4 subtitle codec
                        cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-threads', '0'])
                        cmd.extend(['-c:a', 'aac'])
                        cmd.extend(['-y', str(output_path)])
                        print(f"  🔍 DEBUG: Comando FFmpeg montado, executando...")
                        # Execute FFmpeg immediately for fast path
                        ffmpeg_start_time = time.time()
                        logger.info("Iniciando processamento FFmpeg (fast path)...")
                        print(f"  ⏱️  Performance: Iniciando FFmpeg (fast path) às {time.strftime('%H:%M:%S')}")
                        try:
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                            ffmpeg_duration = time.time() - ffmpeg_start_time
                            logger.info(f"FFmpeg processou (fast path) em {ffmpeg_duration:.2f}s")
                            print(f"  ⏱️  Performance: FFmpeg (fast path) concluído em {ffmpeg_duration:.2f}s")
                        except subprocess.TimeoutExpired as e:
                            logger.error(f"Timeout no processamento FFmpeg (fast path) após 600s")
                            raise VideoProcessingError(f"Video processing timeout: {e}") from e
                        
                        if result.returncode == 0 and output_path.exists():
                            if video_path.exists():
                                video_path.unlink()
                            process_duration = time.time() - process_start_time
                            logger.info(f"process_all_in_one concluído (fast path) em {process_duration:.2f}s")
                            print(f"  ⏱️  Performance: process_all_in_one concluído (fast path) em {process_duration:.2f}s")
                            # Clean up intro video
                            if intro_cleanup and intro_cleanup.exists():
                                try:
                                    intro_cleanup.unlink()
                                except Exception as e:
                                    logger.warning(f"Erro ao remover tela inicial temporária: {e}")
                            return output_path
                        else:
                            error_output = result.stderr if result.stderr else result.stdout or 'Erro desconhecido'
                            logger.error(f"FFmpeg error (fast path): {error_output[:500]}")
                            if output_path.exists():
                                output_path.unlink()
                            raise VideoProcessingError(f"Falha ao processar vídeo (fast path): {error_output[:500]}")
                    else:
                        # Just concat, no conversion needed
                        print(f"  🔍 DEBUG: Sem conversão, apenas concat")
                        filter_complex_parts = [f'[{intro_video_idx}:v][{main_video_idx}:v]concat=n=2:v=1:a=0[v]']
                        cmd.extend(['-filter_complex', ';'.join(filter_complex_parts)])
                        cmd.extend(['-map', '[v]'])
                        cmd.extend(['-map', f'{main_video_idx}:a?'])
                        # Add soft subtitles if available (no re-encode needed!)
                        if has_soft_subtitles and subtitle_input_idx is not None:
                            cmd.extend(['-map', f'{subtitle_input_idx}:s?'])
                            cmd.extend(['-c:s', 'mov_text'])  # MP4 subtitle codec
                        cmd.extend(['-c:v', 'copy'])
                        cmd.extend(['-c:a', 'copy'])
                        cmd.extend(['-y', str(output_path)])
                        print(f"  🔍 DEBUG: Comando FFmpeg montado (copy), executando...")
                        # Execute FFmpeg immediately for fast path
                        ffmpeg_start_time = time.time()
                        logger.info("Iniciando processamento FFmpeg (fast path - copy)...")
                        print(f"  ⏱️  Performance: Iniciando FFmpeg (fast path - copy) às {time.strftime('%H:%M:%S')}")
                        try:
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                            ffmpeg_duration = time.time() - ffmpeg_start_time
                            logger.info(f"FFmpeg processou (fast path - copy) em {ffmpeg_duration:.2f}s")
                            print(f"  ⏱️  Performance: FFmpeg (fast path - copy) concluído em {ffmpeg_duration:.2f}s")
                        except subprocess.TimeoutExpired as e:
                            logger.error(f"Timeout no processamento FFmpeg (fast path - copy) após 600s")
                            raise VideoProcessingError(f"Video processing timeout: {e}") from e
                        
                        if result.returncode == 0 and output_path.exists():
                            if video_path.exists():
                                video_path.unlink()
                            process_duration = time.time() - process_start_time
                            logger.info(f"process_all_in_one concluído (fast path - copy) em {process_duration:.2f}s")
                            print(f"  ⏱️  Performance: process_all_in_one concluído (fast path - copy) em {process_duration:.2f}s")
                            # Clean up intro video
                            if intro_cleanup and intro_cleanup.exists():
                                try:
                                    intro_cleanup.unlink()
                                except Exception as e:
                                    logger.warning(f"Erro ao remover tela inicial temporária: {e}")
                            return output_path
                        else:
                            error_output = result.stderr if result.stderr else result.stdout or 'Erro desconhecido'
                            logger.error(f"FFmpeg error (fast path - copy): {error_output[:500]}")
                            if output_path.exists():
                                output_path.unlink()
                            raise VideoProcessingError(f"Falha ao processar vídeo (fast path - copy): {error_output[:500]}")
                else:
                    # Has video filters (subtitles) but can still optimize
                    # NOTE: This should not happen if use_fast_path logic is correct
                    logger.warning("use_fast_path=True mas has_video_filters=True - isso não deveria acontecer!")
                    print(f"  🔍 DEBUG: ERRO: use_fast_path=True mas tem filtros de vídeo!")
                    # This case shouldn't happen, but if it does, fall through to full path processing
                    # Don't execute here, let it fall through to the full path handler below
            else:
                # Not using fast path - build filters normally
                if intro_video and intro_video.exists():
                    # Concatenate intro + main video
                    if video_filters:
                        video_filter_chain = ','.join(video_filters)
                        filter_complex_parts.append(f'[{main_video_idx}:v]{video_filter_chain}[main_v]')
                        filter_complex_parts.append(f'[{intro_video_idx}:v][main_v]concat=n=2:v=1:a=0[v]')
                    else:
                        filter_complex_parts.append(f'[{intro_video_idx}:v][{main_video_idx}:v]concat=n=2:v=1:a=0[v]')
                elif video_filters:
                    video_filter_chain = ','.join(video_filters)
                    filter_complex_parts.append(f'[{main_video_idx}:v]{video_filter_chain}{video_output_label}')
                else:
                    video_output_label = f'[{main_video_idx}:v]'  # Use input directly
                
                # Audio handling
                if has_audio_input:
                    # Use only external audio inputs (narration/background) if video doesn't have audio
                    # This avoids the "Output with label '1:a' does not exist" error
                    # Audio is now always a single concatenated file (with silence already included)
                    num_audio_inputs = len(audio_inputs)
                    
                    if audio_filters:
                        # Only apply filters to external audio (video audio might not exist)
                        if num_audio_inputs == 1:
                            filter_complex_parts.append(f'[{audio_input_offset}:a]{",".join(audio_filters)}{audio_output_label}')
                        else:
                            # Multiple audio inputs (narration + background)
                            filter_complex_parts.append(f'[{audio_input_offset}:a]{",".join(audio_filters)}[a0];[a0][{audio_input_offset + 1}:a]amix=inputs=2{audio_output_label}')
                    else:
                        # Just use external audio (no mixing with video audio to avoid errors)
                        if num_audio_inputs == 1:
                            # No filters needed, just map directly - don't add to filter_complex
                            audio_output_label = f'[{audio_input_offset}:a]'
                        else:
                            # Multiple audio inputs (narration + background) - need to mix
                            filter_complex_parts.append(f'[{audio_input_offset}:a][{audio_input_offset + 1}:a]amix=inputs=2{audio_output_label}')
                elif audio_filters:
                    # Only speed adjustment - but video might not have audio
                    # Use optional stream selector to avoid errors
                    filter_complex_parts.append(f'[{main_video_idx}:a?]{",".join(audio_filters)}{audio_output_label}')
                else:
                    audio_output_label = f'[{main_video_idx}:a]?'  # Use input directly (optional)
            
            filter_build_duration = time.time() - filter_build_start
            print(f"  ⏱️  Performance: Construção de filtros concluída em {filter_build_duration:.3f}s")
            print(f"  🔍 DEBUG: filter_complex_parts={len(filter_complex_parts)}, use_fast_path={use_fast_path}")
            if filter_complex_parts and not use_fast_path:
                # Full processing path (with filters)
                print(f"  🔍 DEBUG: Entrando no caminho completo de processamento")
                # If we only have video filters (no audio mixing needed), use -vf instead of -filter_complex
                # This is simpler and more reliable for subtitles filter
                # Check if audio_output_label is a direct input reference (not from filter_complex)
                use_vf = (video_filters and 
                         audio_output_label and 
                         audio_output_label.startswith('[') and 
                         not audio_output_label == '[a]' and
                         ';' not in ';'.join(filter_complex_parts) or len([p for p in filter_complex_parts if ':a' in p]) == 0)
                
                # If we have video filters and external audio (no complex audio mixing), use -vf
                # This is simpler and more reliable for subtitles filter
                if video_filters and has_audio_input and len(audio_inputs) == 1 and not audio_filters:
                    # Simple case: video filters + single external audio, use -vf for video
                    video_filter_chain = ','.join(video_filters)
                    cmd.extend(['-vf', video_filter_chain])
                    # Map video and audio directly
                    cmd.extend(['-map', f'{main_video_idx}:v'])
                    cmd.extend(['-map', f'{audio_input_offset}:a'])
                else:
                    # Complex case: need filter_complex for audio mixing or multiple filters
                    cmd.extend(['-filter_complex', ';'.join(filter_complex_parts)])
                    # Map video stream
                    if video_output_label == '[v]':
                        cmd.extend(['-map', '[v]'])
                    else:
                        cmd.extend(['-map', '0:v'])
                    # Map audio stream (only if audio output label was created)
                    if audio_output_label == '[a]':
                        # Audio was processed through filter_complex
                        cmd.extend(['-map', '[a]'])
                    elif audio_output_label and audio_output_label.startswith('[') and audio_output_label.endswith(']'):
                        # Audio label from filter (e.g., [0:a]?)
                        # Extract the label without '?' if present
                        audio_label = audio_output_label.rstrip('?')
                        cmd.extend(['-map', audio_label])
                    # If audio_output_label is None or empty, don't map audio
                
                # Add soft subtitles if available (no re-encode needed!)
                if has_soft_subtitles and subtitle_input_idx is not None:
                    cmd.extend(['-map', f'{subtitle_input_idx}:s?'])
                    cmd.extend(['-c:s', 'mov_text'])  # MP4 subtitle codec
                
                # Video codec (re-encode if we have video filters or need to convert format)
                # If output should be mp4 but input is webm, always re-encode
                # NOTE: Soft subtitles don't require re-encode, so they don't affect needs_reencode
                needs_reencode = bool(video_filters) or (self.config.video.codec == "mp4" and video_path.suffix == ".webm")
                if needs_reencode:
                    # Use ultrafast preset for maximum performance (especially important with subtitles filter)
                    # Use multiple threads for faster encoding
                    cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-threads', '0'])
                else:
                    cmd.extend(['-c:v', 'copy'])  # No video filters, just copy
            else:
                # No filters, but may need format conversion
                print(f"  🔍 DEBUG: Sem filtros, verificando se precisa conversão...")
                needs_conversion = self.config.video.codec == "mp4" and video_path.suffix == ".webm"
                # Map video and audio
                cmd.extend(['-map', f'{main_video_idx}:v'])
                cmd.extend(['-map', f'{main_video_idx}:a?'])
                # Add soft subtitles if available (no re-encode needed!)
                if has_soft_subtitles and subtitle_input_idx is not None:
                    cmd.extend(['-map', f'{subtitle_input_idx}:s?'])
                    cmd.extend(['-c:s', 'mov_text'])  # MP4 subtitle codec
                if needs_conversion:
                    # Need to convert format, can't just copy
                    print(f"  🔍 DEBUG: Precisa conversão webm->mp4, usando codec libx264")
                    cmd.extend(['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-threads', '0'])
                    cmd.extend(['-c:a', 'aac'])
                else:
                    # No conversion needed, just copy
                    print(f"  🔍 DEBUG: Sem conversão, apenas copiando streams")
                    cmd.extend(['-c:v', 'copy'])
                    cmd.extend(['-c:a', 'copy'])
                cmd.extend(['-y', str(output_path)])
                # Run command
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0 and output_path.exists():
                    if video_path.exists():
                        video_path.unlink()
                    process_duration = time.time() - process_start_time
                    logger.info(f"process_all_in_one concluído (caminho simples) em {process_duration:.2f}s")
                    print(f"  ⏱️  Performance: process_all_in_one concluído (caminho simples) em {process_duration:.2f}s")
                    # Return processed video (caller will rename)
                    return output_path
                process_duration = time.time() - process_start_time
                print(f"  🔍 DEBUG: Processamento falhou após {process_duration:.2f}s, retornando vídeo original")
                print(f"  ⏱️  Performance: process_all_in_one falhou após {process_duration:.2f}s")
                return video_path
            
            # Audio codec
            if has_audio_input or audio_filters:
                cmd.extend(['-c:a', 'libopus' if video_path.suffix == '.webm' else 'aac'])
                # DON'T use -shortest - let video determine duration
                # If audio is shorter, it will loop or pad with silence
                # If audio is longer, video duration takes precedence
            else:
                cmd.extend(['-c:a', 'copy'])
            
            # Output path - use relative path when running in video directory
            if output_path.parent == video_path.parent:
                cmd.extend(['-y', output_path.name])
            else:
                cmd.extend(['-y', str(output_path)])
            
            # IMPORTANT: Don't limit duration - preserve full video length
            # Remove any -t or -to flags that might limit duration
            
            # Log command for debugging
            cmd_build_duration = time.time() - filter_build_start
            logger.info(f"Processando vídeo: {video_path.name} -> {output_path.name}")
            print(f"  🔍 DEBUG: Processando vídeo: {video_path.name} -> {output_path.name}")
            print(f"  ⏱️  Performance: Comando FFmpeg montado em {cmd_build_duration:.3f}s")
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            # Print command for debugging when there are errors
            if video_filters or filter_complex_parts:
                print(f"  🔍 DEBUG: Comando FFmpeg completo: {' '.join(cmd[:20])}...")
                if filter_complex_parts:
                    print(f"  🔍 DEBUG: filter_complex: {';'.join(filter_complex_parts)[:200]}...")
            if intro_video and intro_video.exists():
                logger.info(f"Tela inicial incluída: {intro_video.name} ({intro_video.stat().st_size / 1024:.1f}KB)")
                print(f"  🔍 DEBUG: Tela inicial incluída: {intro_video.name}")
            
            # Run ffmpeg (single pass - much faster!)
            # Increased timeout for large videos with subtitles and intro screen
            ffmpeg_start_time = time.time()
            logger.info("Iniciando processamento FFmpeg...")
            print(f"  🔍 DEBUG: Iniciando processamento FFmpeg...")
            print(f"  ⏱️  Performance: Iniciando FFmpeg às {time.strftime('%H:%M:%S')}")
            try:
                # Change to video directory so SRT paths work correctly with relative paths
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minutes for complex processing
                    cwd=str(video_path.parent)
                )
                ffmpeg_duration = time.time() - ffmpeg_start_time
                logger.info(f"FFmpeg processou em {ffmpeg_duration:.2f}s")
                print(f"  ⏱️  Performance: FFmpeg concluído em {ffmpeg_duration:.2f}s")
            except subprocess.TimeoutExpired as e:
                logger.error(f"Timeout no processamento FFmpeg após 600s")
                logger.error(f"Comando que causou timeout: {' '.join(cmd[:10])}...")
                raise VideoProcessingError(f"Video processing timeout: {e}") from e
            
            # Log ffmpeg output for debugging
            if result.returncode != 0:
                logger.error(f"FFmpeg falhou com código {result.returncode}")
                # Extract actual error (skip version info)
                stderr_lines = result.stderr.split('\n') if result.stderr else []
                error_lines = [line for line in stderr_lines if line.strip() and 
                              not line.startswith('ffmpeg version') and
                              not line.startswith('built with') and
                              not line.startswith('configuration:') and
                              not line.startswith('libav') and
                              ('error' in line.lower() or 'failed' in line.lower() or 'invalid' in line.lower())]
                if error_lines:
                    logger.error(f"FFmpeg error: {error_lines[0]}")
                    # Show more context if available
                    if len(error_lines) > 1:
                        logger.error(f"FFmpeg errors: {error_lines[:3]}")
                else:
                    # Show last few non-empty lines
                    last_lines = [line for line in stderr_lines[-10:] if line.strip() and not line.startswith('ffmpeg version')]
                    if last_lines:
                        logger.error(f"FFmpeg stderr (últimas linhas): {last_lines[-3:]}")
                    else:
                        logger.error(f"FFmpeg stderr (primeiros 500 chars): {result.stderr[:500] if result.stderr else 'N/A'}")
            else:
                logger.info("FFmpeg processou com sucesso")
                if result.stderr:
                    # FFmpeg sempre escreve em stderr, mesmo em sucesso
                    stderr_lines = result.stderr.strip().split('\n')
                    # Procurar por warnings ou erros no stderr
                    warnings = [line for line in stderr_lines if 'warning' in line.lower() or 'error' in line.lower()]
                    if warnings:
                        logger.warning(f"FFmpeg warnings: {warnings[:5]}")
            
            if result.returncode == 0 and output_path.exists():
                # Always delete original video and return processed video
                # The caller (test_executor) will handle renaming to expected name
                if video_path.exists():
                    video_path.unlink()  # Delete original video
                # Return the processed output file (keeps _processed suffix for caller to rename)
                final_video = output_path
                
                # Clean up SRT file if created (but keep it for debugging for now)
                # TODO: Remove this after verifying subtitle timing
                if self.config.video.subtitles and test_steps:
                    srt_path = final_video.parent / f"{final_video.stem}.srt"
                    if srt_path.exists():
                        # Log SRT content for debugging
                        logger.debug(f"SRT file generated: {srt_path}")
                        # Keep SRT for now to verify timing
                        # srt_path.unlink()
                
                logger.info("Vídeo processado (velocidade, legendas, áudio, tela inicial) em uma única passada")
                
                # Clean up intro video
                if intro_cleanup and intro_cleanup.exists():
                    try:
                        intro_cleanup.unlink()
                        logger.debug(f"Tela inicial temporária removida: {intro_cleanup}")
                    except Exception as e:
                        logger.warning(f"Erro ao remover tela inicial temporária: {e}")
                
                # Verify output file exists and is valid
                if not final_video.exists():
                    error_msg = f"Vídeo processado não encontrado após processamento: {final_video}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                # Verify format if MP4 was requested
                if self.config.video.codec == "mp4" and final_video.suffix != ".mp4":
                    error_msg = f"Vídeo deveria ser MP4 mas é {final_video.suffix}: {final_video}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                process_duration = time.time() - process_start_time
                logger.info(f"process_all_in_one concluído em {process_duration:.2f}s total")
                print(f"  ⏱️  Performance: process_all_in_one concluído em {process_duration:.2f}s total")
                return final_video
            else:
                # Get full error message
                error_output = result.stderr if result.stderr else result.stdout or 'Erro desconhecido'
                error_msg = f"Erro ao processar vídeo com ffmpeg: {error_output[:1000]}"
                logger.error(f"FFmpeg error (full): {error_output}")
                # Also print last few lines for debugging
                if result.stderr:
                    stderr_lines = result.stderr.strip().split('\n')
                    logger.debug("Últimas linhas do erro:")
                    for line in stderr_lines[-5:]:
                        if line.strip():
                            logger.debug(f"     {line}")
                if output_path.exists():
                    output_path.unlink()
                # If MP4 was requested, this is a critical failure
                if self.config.video.codec == "mp4":
                    raise VideoProcessingError(f"Falha ao processar vídeo para MP4: {error_msg}")
                # Return original video if processing failed but MP4 not required
                process_duration = time.time() - process_start_time
                logger.warning(f"Processamento falhou após {process_duration:.2f}s, retornando vídeo original: {video_path}")
                print(f"  ⏱️  Performance: process_all_in_one falhou após {process_duration:.2f}s")
                return video_path
                
        except subprocess.TimeoutExpired as e:
            logger.error(f"Timeout processing video: {e}")
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Video processing timeout: {e}") from e
        except VideoProcessingError:
            raise
        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            if output_path.exists():
                output_path.unlink()
            raise VideoProcessingError(f"Failed to process video: {e}") from e

