#!/usr/bin/env python3
"""
Script para gerar números de rodada para dados de futebol.
Versão 3: Considera temporadas específicas por campeonato.

Cada temporada de cada campeonato deve ter suas próprias rodadas,
onde cada time joga apenas uma vez por rodada.
"""

import pandas as pd
import re
from collections import defaultdict
from typing import Dict, List, Tuple

def extract_season_from_id(game_id: str) -> str:
    """
    Extrai a temporada do ID do jogo.
    
    Exemplos:
    - 'bundesliga@/football/germany/bundesliga-2015-2016/' -> '2015-2016'
    - 'serie-a-betano@/football/brazil/serie-a-2015/' -> '2015'
    """
    # Procura por padrões de ano no final do path
    patterns = [
        r'-(\d{4}-\d{4})/?$',  # formato 2015-2016
        r'-(\d{4})/?$',        # formato 2015
    ]
    
    for pattern in patterns:
        match = re.search(pattern, game_id)
        if match:
            return match.group(1)
    
    # Se não encontrar padrão, retorna 'unknown'
    return 'unknown'

def extract_championship_from_id(game_id: str) -> str:
    """
    Extrai o nome do campeonato do ID do jogo.
    
    Exemplo:
    - 'bundesliga@/football/germany/bundesliga-2015-2016/' -> 'bundesliga'
    """
    return game_id.split('@')[0]

def generate_rounds_by_season(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gera números de rodada para cada temporada de cada campeonato.
    
    Args:
        df: DataFrame com os dados dos jogos
        
    Returns:
        DataFrame com coluna 'rodada' atualizada
    """
    # Criar cópias das colunas necessárias
    df = df.copy()
    
    # Extrair campeonato e temporada
    df['campeonato'] = df['id'].apply(extract_championship_from_id)
    df['temporada'] = df['id'].apply(extract_season_from_id)
    df['campeonato_temporada'] = df['campeonato'] + '_' + df['temporada']
    
    print(f"Total de jogos: {len(df)}")
    print(f"Campeonatos únicos: {df['campeonato'].nunique()}")
    print(f"Temporadas únicas: {df['temporada'].nunique()}")
    print(f"Combinações campeonato-temporada: {df['campeonato_temporada'].nunique()}")
    print()
    
    # Processar cada combinação campeonato-temporada separadamente
    all_results = []
    
    for camp_temp in sorted(df['campeonato_temporada'].unique()):
        season_df = df[df['campeonato_temporada'] == camp_temp].copy()
        
        # Ordenar por date number e date
        season_df = season_df.sort_values(['date number', 'date']).reset_index(drop=True)
        
        print(f"Processando {camp_temp}: {len(season_df)} jogos")
        
        # Gerar rodadas para esta temporada
        season_df['rodada'] = generate_rounds_for_season(season_df)
        
        # Verificar consistência
        max_round = season_df['rodada'].max()
        teams_per_round = check_season_consistency(season_df, camp_temp)
        
        print(f"  - Rodadas geradas: {max_round}")
        print(f"  - Times por rodada: {teams_per_round}")
        print()
        
        all_results.append(season_df)
    
    # Combinar todos os resultados
    result_df = pd.concat(all_results, ignore_index=True)
    
    # Ordenar por campeonato_temporada e rodada
    result_df = result_df.sort_values(['campeonato_temporada', 'rodada', 'date number']).reset_index(drop=True)
    
    return result_df

def generate_rounds_for_season(season_df: pd.DataFrame) -> List[int]:
    """
    Gera números de rodada para uma temporada específica.
    
    Args:
        season_df: DataFrame com jogos de uma temporada
        
    Returns:
        Lista com números de rodada para cada jogo
    """
    rounds = []
    current_round = 1
    teams_in_current_round = set()
    
    for _, game in season_df.iterrows():
        home_team = game['home']
        away_team = game['away']
        
        # Verificar se algum dos times já jogou nesta rodada
        if home_team in teams_in_current_round or away_team in teams_in_current_round:
            # Iniciar nova rodada
            current_round += 1
            teams_in_current_round = set()
        
        # Adicionar times à rodada atual
        teams_in_current_round.add(home_team)
        teams_in_current_round.add(away_team)
        rounds.append(current_round)
    
    return rounds

def check_season_consistency(season_df: pd.DataFrame, season_name: str) -> str:
    """
    Verifica a consistência das rodadas para uma temporada.
    
    Args:
        season_df: DataFrame com jogos de uma temporada
        season_name: Nome da temporada
        
    Returns:
        String com estatísticas dos times por rodada
    """
    round_stats = []
    
    for round_num in sorted(season_df['rodada'].unique()):
        round_games = season_df[season_df['rodada'] == round_num]
        
        # Coletar todos os times da rodada
        teams_in_round = set()
        for _, game in round_games.iterrows():
            teams_in_round.add(game['home'])
            teams_in_round.add(game['away'])
        
        round_stats.append(len(teams_in_round))
        
        # Verificar duplicatas
        home_teams = list(round_games['home'])
        away_teams = list(round_games['away'])
        all_teams = home_teams + away_teams
        
        if len(all_teams) != len(set(all_teams)):
            print(f"  AVISO: Times duplicados na rodada {round_num} de {season_name}")
    
    if round_stats:
        return f"min={min(round_stats)}, max={max(round_stats)}, média={sum(round_stats)/len(round_stats):.1f}"
    return "N/A"

def save_results(df: pd.DataFrame, output_file: str):
    """
    Salva os resultados em arquivo CSV.
    
    Args:
        df: DataFrame com rodadas geradas
        output_file: Caminho do arquivo de saída
    """
    # Remover colunas auxiliares antes de salvar
    columns_to_save = [col for col in df.columns if col not in ['campeonato_temporada']]
    df_to_save = df[columns_to_save].copy()
    
    df_to_save.to_csv(output_file, index=False)
    print(f"Arquivo salvo: {output_file}")
    print(f"Total de jogos salvos: {len(df_to_save)}")

def print_final_statistics(df: pd.DataFrame):
    """
    Imprime estatísticas finais dos dados processados.
    
    Args:
        df: DataFrame com rodadas geradas
    """
    print("\n=== ESTATÍSTICAS FINAIS ===")
    print(f"Total de jogos: {len(df)}")
    print(f"Total de campeonatos: {df['campeonato'].nunique()}")
    print(f"Total de temporadas: {df['temporada'].nunique()}")
    print(f"Total de combinações campeonato-temporada: {df['campeonato_temporada'].nunique()}")
    print(f"Rodada máxima geral: {df['rodada'].max()}")
    
    print("\nDistribuição por campeonato-temporada:")
    for camp_temp in sorted(df['campeonato_temporada'].unique()):
        season_data = df[df['campeonato_temporada'] == camp_temp]
        print(f"  {camp_temp}: {len(season_data)} jogos, {season_data['rodada'].max()} rodadas")

def main():
    """
    Função principal do script.
    """
    # Caminhos dos arquivos
    input_file = '/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/3_filtered/football.csv'
    output_file = '/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_v3.csv'
    
    print("=== GERAÇÃO DE RODADAS V3 ===")
    print("Considerando temporadas específicas por campeonato\n")
    
    try:
        # Carregar dados
        print(f"Carregando dados de: {input_file}")
        df = pd.read_csv(input_file)
        print(f"Dados carregados: {len(df)} jogos\n")
        
        # Gerar rodadas
        print("Gerando rodadas por temporada...")
        df_with_rounds = generate_rounds_by_season(df)
        
        # Salvar resultados
        save_results(df_with_rounds, output_file)
        
        # Estatísticas finais
        print_final_statistics(df_with_rounds)
        
        print("\n=== PROCESSAMENTO CONCLUÍDO ===")
        
    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        raise

if __name__ == "__main__":
    main()