#!/usr/bin/env python3
"""
Script para gerar números de rodada para dados de futebol.
Versão 4: Algoritmo otimizado para minimizar o número de rodadas.

Este algoritmo tenta agrupar o máximo de jogos possível em cada rodada,
respeitando a regra de que cada time joga apenas uma vez por rodada.
"""

import pandas as pd
import re
from collections import defaultdict
from typing import Dict, List, Tuple, Set

def extract_season_from_id(game_id: str) -> str:
    """
    Extrai a temporada do ID do jogo.
    
    Exemplos:
    - 'bundesliga@/football/germany/bundesliga-2015-2016/' -> '2015-2016'
    - 'serie-a-betano@/football/brazil/serie-a-betano-2020/' -> '2020'
    """
    # Extrair a parte após o último '-' antes da barra final
    match = re.search(r'-(\d{4}(?:-\d{4})?)/?$', game_id)
    if match:
        return match.group(1)
    
    # Fallback: tentar extrair apenas o ano
    match = re.search(r'-(\d{4})/?$', game_id)
    if match:
        return match.group(1)
    
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
        
        # Gerar rodadas para esta temporada usando algoritmo otimizado
        season_df['rodada'] = generate_optimized_rounds_for_season(season_df)
        
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

def generate_optimized_rounds_for_season(season_df: pd.DataFrame) -> List[int]:
    """
    Gera números de rodada otimizados para uma temporada específica.
    
    Este algoritmo tenta agrupar o máximo de jogos possível em cada rodada,
    minimizando o número total de rodadas.
    
    Args:
        season_df: DataFrame com jogos de uma temporada
        
    Returns:
        Lista com números de rodada para cada jogo
    """
    games = []
    for idx, game in season_df.iterrows():
        games.append({
            'index': idx,
            'home': game['home'],
            'away': game['away'],
            'date_number': game['date number'],
            'date': game['date']
        })
    
    # Ordenar jogos por date_number e date para manter ordem cronológica
    games.sort(key=lambda x: (x['date_number'], x['date']))
    
    rounds = [0] * len(games)  # Inicializar com zeros
    current_round = 1
    
    # Processar jogos em grupos cronológicos
    i = 0
    while i < len(games):
        if rounds[i] != 0:  # Jogo já foi atribuído a uma rodada
            i += 1
            continue
            
        # Iniciar nova rodada
        teams_in_round = set()
        games_in_round = []
        
        # Tentar adicionar o máximo de jogos possível nesta rodada
        j = i
        while j < len(games):
            if rounds[j] != 0:  # Jogo já foi atribuído
                j += 1
                continue
                
            game = games[j]
            home_team = game['home']
            away_team = game['away']
            
            # Verificar se os times já estão na rodada atual
            if home_team not in teams_in_round and away_team not in teams_in_round:
                # Adicionar jogo à rodada atual
                rounds[game['index']] = current_round
                teams_in_round.add(home_team)
                teams_in_round.add(away_team)
                games_in_round.append(j)
                
            j += 1
        
        # Se nenhum jogo foi adicionado, forçar o próximo jogo disponível
        if not games_in_round:
            while i < len(games) and rounds[i] != 0:
                i += 1
            if i < len(games):
                game = games[i]
                rounds[game['index']] = current_round
                i += 1
        
        current_round += 1
        i = 0  # Reiniciar busca do início para próxima rodada
    
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
    inconsistencies = []
    games_per_round = []
    
    for round_num in sorted(season_df['rodada'].unique()):
        round_games = season_df[season_df['rodada'] == round_num]
        
        # Contar times únicos na rodada
        home_teams = set(round_games['home'])
        away_teams = set(round_games['away'])
        all_teams_list = list(round_games['home']) + list(round_games['away'])
        unique_teams = len(set(all_teams_list))
        
        games_per_round.append(len(round_games))
        
        # Verificar se há times duplicados
        if len(all_teams_list) != unique_teams:
            duplicates = [team for team in set(all_teams_list) if all_teams_list.count(team) > 1]
            inconsistencies.append(f"Rodada {round_num}: times duplicados {duplicates}")
    
    if inconsistencies:
        print(f"  ⚠️  Inconsistências encontradas em {season_name}:")
        for inc in inconsistencies[:3]:  # Mostrar apenas as primeiras 3
            print(f"    {inc}")
    
    if games_per_round:
        min_games = min(games_per_round)
        max_games = max(games_per_round)
        avg_games = sum(games_per_round) / len(games_per_round)
        return f"min={min_games}, max={max_games}, média={avg_games:.1f}"
    
    return "N/A"

def save_results(df: pd.DataFrame, output_file: str):
    """
    Salva os resultados em arquivo CSV.
    
    Args:
        df: DataFrame com rodadas geradas
        output_file: Caminho do arquivo de saída
    """
    df.to_csv(output_file, index=False)
    print(f"\nResultados salvos em: {output_file}")
    print(f"Total de linhas: {len(df)}")

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
    Função principal.
    """
    print("=== GERAÇÃO DE RODADAS V4 (OTIMIZADA) ===")
    print("Algoritmo otimizado para minimizar número de rodadas\n")
    
    # Caminhos dos arquivos
    input_file = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/3_filtered/football.csv"
    output_file = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_v4.csv"
    
    # Carregar dados
    print(f"Carregando dados de: {input_file}")
    df = pd.read_csv(input_file)
    print(f"Dados carregados: {len(df)} jogos")
    
    # Gerar rodadas
    df_with_rounds = generate_rounds_by_season(df)
    
    # Salvar resultados
    save_results(df_with_rounds, output_file)
    
    # Imprimir estatísticas finais
    print_final_statistics(df_with_rounds)
    
    print("\n=== PROCESSAMENTO CONCLUÍDO ===")

if __name__ == "__main__":
    main()