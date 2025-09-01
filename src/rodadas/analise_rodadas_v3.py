#!/usr/bin/env python3
"""
Script para analisar as rodadas geradas na versão 3.
Verifica a qualidade e consistência das rodadas por temporada.
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime

def load_and_analyze_data(file_path: str) -> pd.DataFrame:
    """
    Carrega e faz análise inicial dos dados.
    
    Args:
        file_path: Caminho do arquivo CSV
        
    Returns:
        DataFrame carregado
    """
    print(f"Carregando dados de: {file_path}")
    df = pd.read_csv(file_path)
    
    print(f"\n=== ANÁLISE INICIAL ===")
    print(f"Total de jogos: {len(df)}")
    print(f"Colunas disponíveis: {list(df.columns)}")
    
    # Verificar se as colunas necessárias existem
    required_cols = ['campeonato', 'temporada', 'rodada', 'home', 'away']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"AVISO: Colunas ausentes: {missing_cols}")
    
    return df

def analyze_by_season(df: pd.DataFrame):
    """
    Analisa os dados por temporada de cada campeonato.
    
    Args:
        df: DataFrame com os dados
    """
    print(f"\n=== ANÁLISE POR TEMPORADA ===")
    
    # Criar coluna combinada se não existir
    if 'campeonato_temporada' not in df.columns:
        df['campeonato_temporada'] = df['campeonato'] + '_' + df['temporada']
    
    print(f"Total de campeonatos: {df['campeonato'].nunique()}")
    print(f"Total de temporadas: {df['temporada'].nunique()}")
    print(f"Total de combinações campeonato-temporada: {df['campeonato_temporada'].nunique()}")
    
    print("\nDetalhes por campeonato-temporada:")
    
    for camp_temp in sorted(df['campeonato_temporada'].unique()):
        season_data = df[df['campeonato_temporada'] == camp_temp]
        
        # Estatísticas básicas
        total_games = len(season_data)
        total_rounds = season_data['rodada'].max()
        unique_teams = set(season_data['home'].unique()) | set(season_data['away'].unique())
        
        # Período dos jogos
        if 'date' in season_data.columns:
            dates = pd.to_datetime(season_data['date'], errors='coerce')
            valid_dates = dates.dropna()
            if len(valid_dates) > 0:
                date_range = f"{valid_dates.min().strftime('%Y-%m-%d')} a {valid_dates.max().strftime('%Y-%m-%d')}"
            else:
                date_range = "N/A"
        else:
            date_range = "N/A"
        
        print(f"\n  {camp_temp}:")
        print(f"    - Jogos: {total_games}")
        print(f"    - Rodadas: {total_rounds}")
        print(f"    - Times únicos: {len(unique_teams)}")
        print(f"    - Período: {date_range}")
        
        # Análise de jogos por rodada
        games_per_round = season_data.groupby('rodada').size()
        print(f"    - Jogos por rodada: min={games_per_round.min()}, max={games_per_round.max()}, média={games_per_round.mean():.1f}")
        
        # Verificar consistência das rodadas
        check_round_consistency(season_data, camp_temp)

def check_round_consistency(season_data: pd.DataFrame, season_name: str):
    """
    Verifica a consistência das rodadas para uma temporada.
    
    Args:
        season_data: DataFrame com dados de uma temporada
        season_name: Nome da temporada
    """
    problems = []
    
    for round_num in sorted(season_data['rodada'].unique()):
        round_games = season_data[season_data['rodada'] == round_num]
        
        # Verificar times duplicados
        home_teams = list(round_games['home'])
        away_teams = list(round_games['away'])
        all_teams = home_teams + away_teams
        
        # Contar ocorrências de cada time
        team_counts = Counter(all_teams)
        duplicated_teams = [team for team, count in team_counts.items() if count > 1]
        
        if duplicated_teams:
            problems.append(f"Rodada {round_num}: times duplicados {duplicated_teams}")
    
    if problems:
        print(f"    - PROBLEMAS ENCONTRADOS:")
        for problem in problems[:5]:  # Mostrar apenas os primeiros 5
            print(f"      * {problem}")
        if len(problems) > 5:
            print(f"      * ... e mais {len(problems) - 5} problemas")
    else:
        print(f"    - ✓ Todas as rodadas consistentes")

def analyze_chronological_order(df: pd.DataFrame):
    """
    Analisa a ordem cronológica dos jogos dentro de cada temporada.
    
    Args:
        df: DataFrame com os dados
    """
    print(f"\n=== ANÁLISE CRONOLÓGICA ===")
    
    if 'date' not in df.columns:
        print("Coluna 'date' não encontrada. Pulando análise cronológica.")
        return
    
    # Criar coluna combinada se não existir
    if 'campeonato_temporada' not in df.columns:
        df['campeonato_temporada'] = df['campeonato'] + '_' + df['temporada']
    
    for camp_temp in sorted(df['campeonato_temporada'].unique()):
        season_data = df[df['campeonato_temporada'] == camp_temp].copy()
        
        # Converter datas
        season_data['date_parsed'] = pd.to_datetime(season_data['date'], errors='coerce')
        valid_data = season_data.dropna(subset=['date_parsed'])
        
        if len(valid_data) == 0:
            print(f"\n  {camp_temp}: Sem datas válidas")
            continue
        
        # Verificar ordem cronológica por rodada
        chronological_problems = 0
        
        for round_num in sorted(valid_data['rodada'].unique()):
            round_games = valid_data[valid_data['rodada'] == round_num]
            
            if len(round_games) > 1:
                dates = round_games['date_parsed'].sort_values()
                date_range_days = (dates.max() - dates.min()).days
                
                # Considerar problemático se jogos da mesma rodada estão muito espalhados
                if date_range_days > 7:  # Mais de 7 dias entre jogos da mesma rodada
                    chronological_problems += 1
        
        total_rounds = valid_data['rodada'].nunique()
        problem_percentage = (chronological_problems / total_rounds * 100) if total_rounds > 0 else 0
        
        print(f"\n  {camp_temp}:")
        print(f"    - Rodadas com problemas cronológicos: {chronological_problems}/{total_rounds} ({problem_percentage:.1f}%)")
        
        if chronological_problems > 0:
            print(f"    - ⚠️  Algumas rodadas têm jogos muito espalhados no tempo")
        else:
            print(f"    - ✓ Ordem cronológica adequada")

def show_examples(df: pd.DataFrame, num_examples: int = 3):
    """
    Mostra exemplos das primeiras rodadas de cada temporada.
    
    Args:
        df: DataFrame com os dados
        num_examples: Número de exemplos por temporada
    """
    print(f"\n=== EXEMPLOS DAS PRIMEIRAS RODADAS ===")
    
    # Criar coluna combinada se não existir
    if 'campeonato_temporada' not in df.columns:
        df['campeonato_temporada'] = df['campeonato'] + '_' + df['temporada']
    
    for camp_temp in sorted(df['campeonato_temporada'].unique())[:3]:  # Mostrar apenas 3 temporadas
        season_data = df[df['campeonato_temporada'] == camp_temp]
        
        print(f"\n  {camp_temp}:")
        
        for round_num in sorted(season_data['rodada'].unique())[:num_examples]:
            round_games = season_data[season_data['rodada'] == round_num]
            
            print(f"    Rodada {round_num} ({len(round_games)} jogos):")
            
            for _, game in round_games.head(5).iterrows():  # Mostrar até 5 jogos por rodada
                date_str = game.get('date', 'N/A')
                print(f"      {game['home']} vs {game['away']} ({date_str})")
            
            if len(round_games) > 5:
                print(f"      ... e mais {len(round_games) - 5} jogos")

def generate_summary_statistics(df: pd.DataFrame):
    """
    Gera estatísticas resumidas dos dados.
    
    Args:
        df: DataFrame com os dados
    """
    print(f"\n=== ESTATÍSTICAS RESUMIDAS ===")
    
    # Criar coluna combinada se não existir
    if 'campeonato_temporada' not in df.columns:
        df['campeonato_temporada'] = df['campeonato'] + '_' + df['temporada']
    
    # Estatísticas gerais
    total_games = len(df)
    total_seasons = df['campeonato_temporada'].nunique()
    total_rounds = df['rodada'].max()
    
    print(f"Total de jogos: {total_games}")
    print(f"Total de temporadas: {total_seasons}")
    print(f"Rodada máxima: {total_rounds}")
    
    # Distribuição de jogos por rodada
    games_per_round = df.groupby(['campeonato_temporada', 'rodada']).size()
    
    print(f"\nDistribuição de jogos por rodada:")
    print(f"  Mínimo: {games_per_round.min()}")
    print(f"  Máximo: {games_per_round.max()}")
    print(f"  Média: {games_per_round.mean():.2f}")
    print(f"  Mediana: {games_per_round.median():.2f}")
    
    # Frequência de jogos por rodada
    freq_dist = games_per_round.value_counts().sort_index()
    print(f"\nFrequência de jogos por rodada:")
    for games, freq in freq_dist.head(10).items():
        print(f"  {games} jogos: {freq} rodadas")

def main():
    """
    Função principal do script.
    """
    # Caminho do arquivo
    file_path = '/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_v3.csv'
    
    print("=== ANÁLISE DE RODADAS V3 ===")
    print("Análise por temporada de cada campeonato\n")
    
    try:
        # Carregar dados
        df = load_and_analyze_data(file_path)
        
        # Análises
        analyze_by_season(df)
        analyze_chronological_order(df)
        show_examples(df)
        generate_summary_statistics(df)
        
        print("\n=== ANÁLISE CONCLUÍDA ===")
        
    except Exception as e:
        print(f"Erro durante a análise: {e}")
        raise

if __name__ == "__main__":
    main()