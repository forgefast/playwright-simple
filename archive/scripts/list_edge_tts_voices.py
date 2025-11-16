#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para listar vozes disponíveis no edge-tts.
"""

import asyncio
import sys

try:
    import edge_tts
except ImportError:
    print("❌ edge-tts não está instalado. Instale com: pip install edge-tts")
    sys.exit(1)


async def list_voices():
    """Lista todas as vozes disponíveis no edge-tts."""
    print("🔍 Buscando vozes disponíveis no edge-tts...\n")
    
    try:
        voices = await edge_tts.list_voices()
        
        # Filtrar vozes brasileiras (verificar Locale e ShortName)
        pt_br_voices = []
        for v in voices:
            locale = v.get('Locale', '').upper()
            short_name = v.get('ShortName', '').upper()
            if 'PT-BR' in locale or 'PT-BR' in short_name:
                pt_br_voices.append(v)
        
        print("=" * 80)
        print("🇧🇷 VOZES BRASILEIRAS (pt-BR)")
        print("=" * 80)
        
        for voice in sorted(pt_br_voices, key=lambda v: (v.get('Gender', ''), v.get('ShortName', ''))):
            short_name = voice.get('ShortName', 'N/A')
            name = voice.get('Name', 'N/A')
            gender = voice.get('Gender', 'N/A')
            locale = voice.get('Locale', 'N/A')
            
            print(f"\n📢 {short_name}")
            print(f"   Nome completo: {name}")
            print(f"   Gênero: {gender}")
            print(f"   Locale: {locale}")
        
        print("\n" + "=" * 80)
        print(f"Total de vozes brasileiras: {len(pt_br_voices)}")
        print("=" * 80)
        
        # Mostrar outras vozes também (limitado)
        print("\n\n🌍 OUTRAS VOZES (amostra - primeiras 10)")
        print("=" * 80)
        
        other_voices = [v for v in voices if 'pt-BR' not in v.get('Locale', '').upper()][:10]
        for voice in sorted(other_voices, key=lambda v: v.get('Locale', '')):
            short_name = voice.get('ShortName', 'N/A')
            name = voice.get('Name', 'N/A')
            gender = voice.get('Gender', 'N/A')
            locale = voice.get('Locale', 'N/A')
            
            print(f"\n📢 {short_name}")
            print(f"   Nome completo: {name}")
            print(f"   Gênero: {gender}")
            print(f"   Locale: {locale}")
        
        print("\n" + "=" * 80)
        print(f"Total de vozes disponíveis: {len(voices)}")
        print("=" * 80)
        
        # Recomendações
        print("\n\n💡 RECOMENDAÇÕES PARA PORTUGUÊS BRASILEIRO:")
        print("=" * 80)
        female_voices = [v for v in pt_br_voices if v.get('Gender') == 'Female']
        male_voices = [v for v in pt_br_voices if v.get('Gender') == 'Male']
        
        if female_voices:
            print("\n👩 Vozes Femininas:")
            for voice in female_voices:
                print(f"   - {voice.get('ShortName')} ({voice.get('Name')})")
        
        if male_voices:
            print("\n👨 Vozes Masculinas:")
            for voice in male_voices:
                print(f"   - {voice.get('ShortName')} ({voice.get('Name')})")
        
        print("\n" + "=" * 80)
        print("Para usar uma voz, configure no YAML:")
        print('  audio_voice: "pt-BR-FranciscaNeural"  # ou outra voz da lista acima')
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erro ao listar vozes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(list_voices())

