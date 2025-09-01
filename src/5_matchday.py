#!/usr/bin/env python3
"""
Script simples para gerar o arquivo football_rodadas_final.csv.

Este script executa os três passos necessários:
1. Gera rodadas por temporada
2. Analisa as rodadas (opcional)
3. Organiza o arquivo final

Uso:
    python src/generate_final_rodadas.py
"""

import os
import sys
from pathlib import Path

def main():
    """Executa os scripts necessários para gerar o arquivo final."""
    
    print("🚀 Gerando arquivo football_rodadas_final.csv...")
    print("=" * 50)
    
    # Mudar para o diretório do projeto
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Scripts a serem executados
    scripts = [
        "src/rodadas/generate_rodadas_v3.py",
        "src/rodadas/analise_rodadas_v3.py", 
        "src/rodadas/organize_final.py"
    ]
    
    # Executar cada script
    for i, script in enumerate(scripts, 1):
        print(f"\n📋 Etapa {i}/3: {Path(script).name}")
        print("-" * 30)
        
        # Executar o script
        exit_code = os.system(f"python {script}")
        
        if exit_code != 0:
            print(f"❌ Erro ao executar {script}")
            sys.exit(1)
        else:
            print(f"✅ {Path(script).name} executado com sucesso")
    
    # Verificar se o arquivo final foi criado
    final_file = Path("data/5_matchdays/football_rodadas_final.csv")
    
    if final_file.exists():
        file_size = final_file.stat().st_size
        print(f"\n🎉 Sucesso! Arquivo criado:")
        print(f"📁 {final_file}")
        print(f"📊 Tamanho: {file_size:,} bytes")
    else:
        print(f"\n❌ Erro: Arquivo final não foi criado")
        sys.exit(1)

if __name__ == '__main__':
    main()