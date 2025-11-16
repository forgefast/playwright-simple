#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar áudio de todas as vozes masculinas brasileiras.
"""

import asyncio
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("❌ edge-tts não está instalado. Instale com: pip install edge-tts")
    sys.exit(1)


async def generate_voice_samples():
    """Gera amostras de áudio para todas as vozes masculinas brasileiras."""
    text = "Fazendo login no sistema"
    output_dir = Path("voice_samples")
    output_dir.mkdir(exist_ok=True)
    
    print("🔍 Buscando vozes masculinas brasileiras...\n")
    
    try:
        voices = await edge_tts.list_voices()
        
        # Filtrar vozes masculinas brasileiras
        pt_br_male_voices = []
        for v in voices:
            locale = v.get('Locale', '').upper()
            short_name = v.get('ShortName', '').upper()
            gender = v.get('Gender', '')
            if ('PT-BR' in locale or 'PT-BR' in short_name) and gender == 'Male':
                pt_br_male_voices.append(v)
        
        if not pt_br_male_voices:
            print("❌ Nenhuma voz masculina brasileira encontrada")
            return
        
        print(f"✅ Encontradas {len(pt_br_male_voices)} vozes masculinas brasileiras\n")
        print("=" * 80)
        print(f"🎤 Gerando áudio com o texto: '{text}'")
        print("=" * 80)
        print()
        
        for i, voice in enumerate(sorted(pt_br_male_voices, key=lambda v: v.get('ShortName', '')), 1):
            short_name = voice.get('ShortName', 'N/A')
            name = voice.get('Name', 'N/A')
            
            # Nome do arquivo seguro (sem caracteres especiais)
            safe_name = short_name.replace(':', '_').replace('/', '_')
            output_file = output_dir / f"{i:02d}_{safe_name}.mp3"
            
            print(f"[{i}/{len(pt_br_male_voices)}] Gerando: {short_name}")
            print(f"   Arquivo: {output_file.name}")
            
            try:
                communicate = edge_tts.Communicate(text, short_name)
                await communicate.save(str(output_file))
                
                if output_file.exists():
                    file_size = output_file.stat().st_size / 1024  # KB
                    print(f"   ✅ Gerado ({file_size:.1f} KB)")
                else:
                    print(f"   ❌ Erro: arquivo não foi criado")
            except Exception as e:
                print(f"   ❌ Erro ao gerar: {e}")
            
            print()
        
        print("=" * 80)
        print("✅ Geração concluída!")
        print("=" * 80)
        print(f"\n📁 Arquivos salvos em: {output_dir.absolute()}")
        print("\n💡 Para ouvir os arquivos:")
        print(f"   cd {output_dir}")
        print("   # Use seu player de áudio favorito ou:")
        print("   mpv *.mp3  # ou vlc *.mp3, ou qualquer outro player")
        print("\n📋 Lista de vozes geradas:")
        for i, voice in enumerate(sorted(pt_br_male_voices, key=lambda v: v.get('ShortName', '')), 1):
            short_name = voice.get('ShortName', 'N/A')
            safe_name = short_name.replace(':', '_').replace('/', '_')
            print(f"   {i:02d}_{safe_name}.mp3 - {short_name}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(generate_voice_samples())

