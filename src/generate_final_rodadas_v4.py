#!/usr/bin/env python3
"""
Script principal para gerar o arquivo football_rodadas_final.csv usando a versão 4 otimizada.

Este script executa o pipeline completo:
1. Geração de rodadas otimizada (generate_rodadas_v4.py)
2. Análise de consistência (analise_rodadas_v3.py)
3. Organização final (organize_final.py)

Resultado: data/5_matchdays/football_rodadas_final.csv
"""

import subprocess
import sys
import os
from pathlib import Path

def run_script(script_path, description):
    """
    Executa um script Python e verifica o sucesso.
    
    Args:
        script_path: Caminho para o script
        description: Descrição do que o script faz
        
    Returns:
        bool: True se executou com sucesso, False caso contrário
    """
    print(f"\n=== {description} ===")
    print(f"Executando: {script_path}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✅ Executado com sucesso!")
        if result.stdout:
            print("Saída:")
            print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na execução (código {e.returncode})")
        if e.stdout:
            print("Saída:")
            print(e.stdout)
        if e.stderr:
            print("Erro:")
            print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def check_file_exists(file_path, description):
    """
    Verifica se um arquivo existe e mostra informações sobre ele.
    
    Args:
        file_path: Caminho do arquivo
        description: Descrição do arquivo
        
    Returns:
        bool: True se o arquivo existe, False caso contrário
    """
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {description}: {file_path} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description} não encontrado: {file_path}")
        return False

def main():
    """
    Função principal que executa o pipeline completo.
    """
    print("=== PIPELINE DE GERAÇÃO DE RODADAS V4 (OTIMIZADA) ===")
    print("Este script executa o pipeline completo para gerar football_rodadas_final.csv")
    print("usando o algoritmo otimizado da versão 4.")
    
    # Definir caminhos
    base_dir = Path(__file__).parent
    rodadas_dir = base_dir / "rodadas"
    
    # Scripts do pipeline
    scripts = [
        {
            "path": rodadas_dir / "generate_rodadas_v4.py",
            "description": "ETAPA 1: Geração de Rodadas Otimizada",
            "output_file": "data/5_matchdays/football_rodadas_v4.csv"
        },
        {
            "path": rodadas_dir / "analise_rodadas_v3.py",
            "description": "ETAPA 2: Análise de Consistência",
            "output_file": None  # Este script não gera arquivo específico
        },
        {
            "path": rodadas_dir / "organize_final.py",
            "description": "ETAPA 3: Organização Final",
            "output_file": "data/5_matchdays/football_rodadas_final.csv"
        }
    ]
    
    # Verificar arquivo de entrada
    input_file = "data/3_filtered/football.csv"
    if not check_file_exists(input_file, "Arquivo de entrada"):
        print("\n❌ ERRO: Arquivo de entrada não encontrado!")
        print("Execute primeiro os scripts de filtragem de dados.")
        return False
    
    print(f"\nIniciando pipeline com {len(scripts)} etapas...")
    
    # Executar cada script do pipeline
    for i, script_info in enumerate(scripts, 1):
        script_path = script_info["path"]
        description = script_info["description"]
        
        # Verificar se o script existe
        if not script_path.exists():
            print(f"\n❌ ERRO: Script não encontrado: {script_path}")
            return False
        
        # Executar o script
        success = run_script(str(script_path), description)
        
        if not success:
            print(f"\n❌ FALHA na etapa {i}: {description}")
            print("Pipeline interrompido.")
            return False
        
        # Verificar arquivo de saída se especificado
        if script_info["output_file"]:
            if not check_file_exists(script_info["output_file"], f"Saída da etapa {i}"):
                print(f"\n⚠️  AVISO: Arquivo de saída esperado não foi encontrado.")
    
    # Verificar resultado final
    final_output = "data/5_matchdays/football_rodadas_final.csv"
    print(f"\n=== VERIFICAÇÃO FINAL ===")
    
    if check_file_exists(final_output, "Arquivo final"):
        print("\n🎉 SUCESSO! Pipeline executado com sucesso!")
        print(f"Arquivo gerado: {final_output}")
        
        # Mostrar estatísticas básicas
        try:
            import pandas as pd
            df = pd.read_csv(final_output)
            print(f"\nEstatísticas do arquivo final:")
            print(f"- Total de jogos: {len(df):,}")
            print(f"- Campeonatos: {df['campeonato'].nunique()}")
            print(f"- Temporadas: {df['temporada'].nunique()}")
            print(f"- Rodada máxima: {df['rodada'].max()}")
            print(f"- Colunas: {', '.join(df.columns)}")
            
        except Exception as e:
            print(f"⚠️  Não foi possível ler estatísticas: {e}")
        
        return True
    else:
        print("\n❌ FALHA: Arquivo final não foi gerado!")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n=== PIPELINE CONCLUÍDO COM SUCESSO ===")
        print("O arquivo football_rodadas_final.csv foi gerado com o algoritmo otimizado.")
        print("\nPróximos passos:")
        print("1. Verificar a qualidade dos dados gerados")
        print("2. Comparar com a versão anterior se necessário")
        print("3. Usar o arquivo em suas análises")
        sys.exit(0)
    else:
        print("\n=== PIPELINE FALHOU ===")
        print("Verifique os erros acima e tente novamente.")
        sys.exit(1)