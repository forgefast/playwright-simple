#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script rápido para verificar o YAML gerado."""

from pathlib import Path

yaml_file = Path("test_user_click_entrar.yaml")

if yaml_file.exists():
    print("=" * 60)
    print("📄 Conteúdo do YAML gerado:")
    print("=" * 60)
    with open(yaml_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    print("=" * 60)
    
    # Verificar se "Entrar" está no YAML
    if "Entrar" in content or "entrar" in content.lower():
        print("\n✅ SUCESSO: 'Entrar' encontrado no YAML!")
        print("   O clique do usuário foi capturado corretamente.")
    else:
        print("\n❌ PROBLEMA: 'Entrar' NÃO encontrado no YAML!")
        print("   O clique do usuário pode não ter sido capturado.")
    
    # Contar steps
    import yaml
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            steps = data.get('steps', [])
            print(f"\n📊 Total de steps: {len(steps)}")
            for i, step in enumerate(steps, 1):
                print(f"   {i}. {step.get('action')}: {step.get('description', '')}")
    except Exception as e:
        print(f"\n⚠️  Erro ao analisar YAML: {e}")
else:
    print(f"❌ Arquivo YAML não encontrado: {yaml_file}")

