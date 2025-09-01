#!/usr/bin/env python3
"""
Script principal para executar o pipeline completo de geração de rodadas.

Este script executa todos os passos necessários para gerar o arquivo final
football_rodadas_final.csv a partir dos dados de futebol filtrados.

Pipeline:
1. generate_rodadas_v3.py - Gera rodadas por temporada
2. analise_rodadas_v3.py - Analisa qualidade das rodadas (opcional)
3. organize_final.py - Organiza dados finais por ID e rodada

Uso:
    python src/run_rodadas_pipeline.py [--skip-analysis]
    
Opções:
    --skip-analysis    Pula a etapa de análise (mais rápido)
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_path: Path, description: str) -> bool:
    """
    Executa um script Python e retorna True se bem-sucedido.
    
    Args:
        script_path: Caminho para o script
        description: Descrição do script para logging
        
    Returns:
        bool: True se o script executou com sucesso
    """
    logger.info(f"Iniciando: {description}")
    logger.info(f"Executando: {script_path}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"✅ Concluído: {description}")
        if result.stdout:
            logger.info(f"Saída: {result.stdout.strip()}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro em {description}")
        logger.error(f"Código de saída: {e.returncode}")
        if e.stdout:
            logger.error(f"Saída: {e.stdout}")
        if e.stderr:
            logger.error(f"Erro: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Erro inesperado em {description}: {e}")
        return False

def check_input_file() -> bool:
    """
    Verifica se o arquivo de entrada existe.
    
    Returns:
        bool: True se o arquivo existe
    """
    input_file = Path('/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/3_filtered/football.csv')
    
    if input_file.exists():
        logger.info(f"✅ Arquivo de entrada encontrado: {input_file}")
        return True
    else:
        logger.error(f"❌ Arquivo de entrada não encontrado: {input_file}")
        logger.error("Execute primeiro os scripts de scraping, formatação e filtragem.")
        return False

def check_output_file() -> bool:
    """
    Verifica se o arquivo final foi criado com sucesso.
    
    Returns:
        bool: True se o arquivo existe
    """
    output_file = Path('/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_final.csv')
    
    if output_file.exists():
        file_size = output_file.stat().st_size
        logger.info(f"✅ Arquivo final criado: {output_file}")
        logger.info(f"Tamanho do arquivo: {file_size:,} bytes")
        return True
    else:
        logger.error(f"❌ Arquivo final não foi criado: {output_file}")
        return False

def main():
    """
    Função principal que executa o pipeline completo.
    """
    parser = argparse.ArgumentParser(
        description='Executa o pipeline completo de geração de rodadas'
    )
    parser.add_argument(
        '--skip-analysis', 
        action='store_true',
        help='Pula a etapa de análise das rodadas'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Iniciando pipeline de geração de rodadas")
    logger.info("=" * 50)
    
    # Definir caminhos dos scripts
    src_dir = Path(__file__).parent
    rodadas_dir = src_dir / 'rodadas'
    
    scripts = [
        (rodadas_dir / 'generate_rodadas_v4.py', 'Geração de rodadas por temporada (Otimizada)'),
    ]
    
    if not args.skip_analysis:
        scripts.append(
            (rodadas_dir / 'analise_rodadas_v3.py', 'Análise da qualidade das rodadas')
        )
    
    scripts.append(
        (rodadas_dir / 'organize_final.py', 'Organização final dos dados')
    )
    
    # Verificar arquivo de entrada
    if not check_input_file():
        sys.exit(1)
    
    # Executar scripts sequencialmente
    success_count = 0
    total_scripts = len(scripts)
    
    for i, (script_path, description) in enumerate(scripts, 1):
        logger.info(f"\n📋 Etapa {i}/{total_scripts}: {description}")
        logger.info("-" * 40)
        
        if not script_path.exists():
            logger.error(f"❌ Script não encontrado: {script_path}")
            sys.exit(1)
        
        if run_script(script_path, description):
            success_count += 1
        else:
            logger.error(f"❌ Pipeline interrompido na etapa {i}")
            sys.exit(1)
    
    # Verificar resultado final
    logger.info("\n🔍 Verificando resultado final...")
    logger.info("-" * 40)
    
    if check_output_file():
        logger.info("\n🎉 Pipeline executado com sucesso!")
        logger.info("=" * 50)
        logger.info(f"✅ {success_count}/{total_scripts} etapas concluídas")
        logger.info("📁 Arquivo final disponível em:")
        logger.info("   data/5_matchdays/football_rodadas_final.csv")
        
        if args.skip_analysis:
            logger.info("\n💡 Dica: Execute sem --skip-analysis para ver análises detalhadas")
    else:
        logger.error("\n❌ Pipeline falhou - arquivo final não foi criado")
        sys.exit(1)

if __name__ == '__main__':
    main()