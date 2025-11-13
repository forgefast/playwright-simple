#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analisar e validar vídeos gerados pelos testes.

Extrai informações como duração, tamanho, codec, resolução, etc.
Valida integridade, duração mínima, resolução esperada e gera relatórios JSON.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List


def validate_video_integrity(video_path: Path) -> Dict[str, Any]:
    """
    Valida integridade do vídeo tentando reproduzi-lo.
    
    Args:
        video_path: Caminho para o arquivo de vídeo
        
    Returns:
        Dicionário com resultados da validação
    """
    result = {
        'valid': False,
        'playable': False,
        'corrupted': False,
        'error': None
    }
    
    if not video_path.exists():
        result['error'] = 'Arquivo não existe'
        return result
    
    try:
        # Tenta obter informações básicas do vídeo (se conseguir, não está corrompido)
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            str(video_path)
        ]
        
        probe_result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if probe_result.returncode == 0:
            result['playable'] = True
            result['valid'] = True
        else:
            result['corrupted'] = True
            result['error'] = probe_result.stderr[:200]
            
    except subprocess.TimeoutExpired:
        result['error'] = 'Timeout ao validar vídeo'
    except Exception as e:
        result['error'] = str(e)
        result['corrupted'] = True
    
    return result


def validate_video_requirements(
    info: Dict[str, Any],
    min_duration: Optional[float] = None,
    expected_resolution: Optional[Dict[str, int]] = None,
    expected_codec: Optional[str] = None,
    min_size_bytes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Valida se o vídeo atende aos requisitos especificados.
    
    Args:
        info: Informações do vídeo (de get_video_info)
        min_duration: Duração mínima esperada em segundos
        expected_resolution: Resolução esperada {'width': X, 'height': Y}
        expected_codec: Codec esperado (ex: 'vp9', 'vp8', 'h264')
        min_size_bytes: Tamanho mínimo em bytes
        
    Returns:
        Dicionário com resultados da validação
    """
    validation = {
        'passed': True,
        'errors': [],
        'warnings': []
    }
    
    if not info:
        validation['passed'] = False
        validation['errors'].append('Informações do vídeo não disponíveis')
        return validation
    
    # Validar duração mínima
    if min_duration is not None:
        actual_duration = info.get('duration_seconds', 0)
        if actual_duration < min_duration:
            validation['passed'] = False
            validation['errors'].append(
                f'Duração {actual_duration:.2f}s é menor que o mínimo esperado {min_duration:.2f}s'
            )
    
    # Validar resolução
    if expected_resolution:
        actual_width = info.get('width', 0)
        actual_height = info.get('height', 0)
        expected_width = expected_resolution.get('width', 0)
        expected_height = expected_resolution.get('height', 0)
        
        if actual_width != expected_width or actual_height != expected_height:
            validation['warnings'].append(
                f'Resolução {actual_width}x{actual_height} difere da esperada {expected_width}x{expected_height}'
            )
    
    # Validar codec
    if expected_codec:
        actual_codec = info.get('codec', '').lower()
        if actual_codec != expected_codec.lower():
            validation['warnings'].append(
                f'Codec {actual_codec} difere do esperado {expected_codec}'
            )
    
    # Validar tamanho mínimo
    if min_size_bytes is not None:
        actual_size = info.get('size_bytes', 0)
        if actual_size < min_size_bytes:
            validation['passed'] = False
            validation['errors'].append(
                f'Tamanho {actual_size} bytes é menor que o mínimo esperado {min_size_bytes} bytes'
            )
    
    return validation


def get_video_info(video_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extrai informações de um vídeo usando ffprobe.
    
    Args:
        video_path: Caminho para o arquivo de vídeo
        
    Returns:
        Dicionário com informações do vídeo ou None se houver erro
    """
    if not video_path.exists():
        return None
    
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration,size,bit_rate',
            '-show_entries', 'stream=width,height,codec_name,r_frame_rate',
            '-of', 'json',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ Erro ao analisar vídeo: {result.stderr}")
            return None
        
        data = json.loads(result.stdout)
        
        # Extrair informações
        format_info = data.get('format', {})
        streams = data.get('streams', [])
        
        video_stream = None
        for stream in streams:
            # Video streams may not have codec_type, check for video codec names
            codec_name = stream.get('codec_name', '')
            if codec_name in ['vp8', 'vp9', 'h264', 'av1', 'hevc'] or stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        # If no video stream found, use first stream (usually video)
        if not video_stream and streams:
            video_stream = streams[0]
        
        info = {
            'path': str(video_path),
            'size_bytes': int(format_info.get('size', 0)),
            'size_mb': round(int(format_info.get('size', 0)) / (1024 * 1024), 2),
            'duration_seconds': float(format_info.get('duration', 0)),
            'duration_formatted': format_duration(float(format_info.get('duration', 0))),
            'bit_rate': int(format_info.get('bit_rate', 0)),
            'bit_rate_mbps': round(int(format_info.get('bit_rate', 0)) / 1000000, 2),
        }
        
        if video_stream:
            info.update({
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'codec': video_stream.get('codec_name', 'unknown'),
                'fps': calculate_fps(video_stream.get('r_frame_rate', '0/1')),
            })
        
        return info
        
    except subprocess.TimeoutExpired:
        print(f"⏱️  Timeout ao analisar vídeo: {video_path}")
        return None
    except Exception as e:
        print(f"❌ Erro ao analisar vídeo {video_path}: {e}")
        return None


def format_duration(seconds: float) -> str:
    """Formata duração em segundos para formato legível."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def calculate_fps(fps_str: str) -> float:
    """Calcula FPS a partir de string 'num/den'."""
    try:
        if '/' in fps_str:
            num, den = map(int, fps_str.split('/'))
            return round(num / den, 2) if den > 0 else 0.0
        return float(fps_str)
    except:
        return 0.0


def print_video_info(info: Dict[str, Any]) -> None:
    """Imprime informações do vídeo de forma formatada."""
    print(f"\n📹 Vídeo: {Path(info['path']).name}")
    print(f"   📁 Caminho: {info['path']}")
    print(f"   ⏱️  Duração: {info['duration_formatted']} ({info['duration_seconds']:.2f}s)")
    print(f"   📊 Resolução: {info.get('width', '?')}x{info.get('height', '?')}")
    print(f"   🎬 Codec: {info.get('codec', 'unknown')}")
    print(f"   🎞️  FPS: {info.get('fps', 0)}")
    print(f"   💾 Tamanho: {info['size_mb']} MB ({info['size_bytes']:,} bytes)")
    print(f"   📡 Bitrate: {info['bit_rate_mbps']} Mbps")


def validate_videos(
    video_paths: List[Path],
    min_duration: Optional[float] = None,
    expected_resolution: Optional[Dict[str, int]] = None,
    expected_codec: Optional[str] = None,
    min_size_bytes: Optional[int] = None,
    output_json: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Valida múltiplos vídeos e gera relatório.
    
    Args:
        video_paths: Lista de caminhos para vídeos
        min_duration: Duração mínima esperada
        expected_resolution: Resolução esperada
        expected_codec: Codec esperado
        min_size_bytes: Tamanho mínimo
        output_json: Caminho para salvar relatório JSON
        
    Returns:
        Dicionário com resultados da validação
    """
    results = {
        'total': len(video_paths),
        'valid': 0,
        'invalid': 0,
        'videos': []
    }
    
    for video_path in video_paths:
        video_result = {
            'path': str(video_path),
            'name': video_path.name,
            'exists': video_path.exists(),
            'info': None,
            'integrity': None,
            'validation': None
        }
        
        if not video_path.exists():
            video_result['integrity'] = {'valid': False, 'error': 'Arquivo não existe'}
            results['invalid'] += 1
            results['videos'].append(video_result)
            continue
        
        # Obter informações
        info = get_video_info(video_path)
        video_result['info'] = info
        
        # Validar integridade
        integrity = validate_video_integrity(video_path)
        video_result['integrity'] = integrity
        
        # Validar requisitos
        if info:
            validation = validate_video_requirements(
                info,
                min_duration=min_duration,
                expected_resolution=expected_resolution,
                expected_codec=expected_codec,
                min_size_bytes=min_size_bytes
            )
            video_result['validation'] = validation
            
            if integrity['valid'] and validation['passed']:
                results['valid'] += 1
            else:
                results['invalid'] += 1
        else:
            results['invalid'] += 1
        
        results['videos'].append(video_result)
    
    # Salvar relatório JSON se solicitado
    if output_json:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analisa e valida vídeos gerados pelos testes'
    )
    parser.add_argument(
        'videos',
        nargs='+',
        help='Caminhos para os arquivos de vídeo'
    )
    parser.add_argument(
        '--min-duration',
        type=float,
        help='Duração mínima esperada em segundos'
    )
    parser.add_argument(
        '--expected-resolution',
        help='Resolução esperada no formato WIDTHxHEIGHT (ex: 1920x1080)'
    )
    parser.add_argument(
        '--expected-codec',
        help='Codec esperado (ex: vp9, vp8, h264)'
    )
    parser.add_argument(
        '--min-size',
        type=int,
        help='Tamanho mínimo em bytes'
    )
    parser.add_argument(
        '--json',
        type=str,
        help='Caminho para salvar relatório JSON'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Executar validação completa (integridade + requisitos)'
    )
    
    args = parser.parse_args()
    
    video_paths = [Path(p) for p in args.videos]
    
    # Parse expected resolution
    expected_resolution = None
    if args.expected_resolution:
        try:
            width, height = map(int, args.expected_resolution.split('x'))
            expected_resolution = {'width': width, 'height': height}
        except ValueError:
            print(f"❌ Formato de resolução inválido: {args.expected_resolution}")
            print("   Use o formato WIDTHxHEIGHT (ex: 1920x1080)")
            sys.exit(1)
    
    if args.validate:
        print("🔍 Validando vídeos...\n")
        results = validate_videos(
            video_paths,
            min_duration=args.min_duration,
            expected_resolution=expected_resolution,
            expected_codec=args.expected_codec,
            min_size_bytes=args.min_size,
            output_json=Path(args.json) if args.json else None
        )
        
        print(f"\n📊 Resultados da Validação")
        print(f"   Total: {results['total']}")
        print(f"   ✅ Válidos: {results['valid']}")
        print(f"   ❌ Inválidos: {results['invalid']}\n")
        
        for video_result in results['videos']:
            print(f"📹 {video_result['name']}")
            if not video_result['exists']:
                print(f"   ❌ Arquivo não existe")
            elif not video_result['integrity']['valid']:
                print(f"   ❌ Vídeo corrompido ou inválido")
                if video_result['integrity']['error']:
                    print(f"      Erro: {video_result['integrity']['error']}")
            elif video_result['validation']:
                if video_result['validation']['passed']:
                    print(f"   ✅ Validação passou")
                else:
                    print(f"   ❌ Validação falhou:")
                    for error in video_result['validation']['errors']:
                        print(f"      - {error}")
                if video_result['validation']['warnings']:
                    for warning in video_result['validation']['warnings']:
                        print(f"      ⚠️  {warning}")
            print()
        
        if args.json:
            print(f"📄 Relatório JSON salvo em: {args.json}")
    else:
        print("🔍 Analisando vídeos...\n")
        
        for video_path in video_paths:
            info = get_video_info(video_path)
            if info:
                print_video_info(info)
                
                # Validação básica de integridade
                integrity = validate_video_integrity(video_path)
                if integrity['valid']:
                    print(f"   ✅ Vídeo válido e reproduzível")
                else:
                    print(f"   ❌ Vídeo inválido ou corrompido")
                    if integrity['error']:
                        print(f"      Erro: {integrity['error']}")
            else:
                print(f"❌ Não foi possível analisar: {video_path}")
            print()


if __name__ == "__main__":
    main()

