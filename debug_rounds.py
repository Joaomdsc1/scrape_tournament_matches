#!/usr/bin/env python3
import pandas as pd

# Carregar dados
df = pd.read_csv('/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_final.csv')

print('=== ANÁLISE DETALHADA DE UM CASO PROBLEMÁTICO ===')

# Analisar Serie A Betano 2020 (51 rodadas)
problematic_case = df[(df['campeonato'] == 'serie-a-betano') & (df['temporada'] == '2020')].copy()
problematic_case = problematic_case.sort_values(['rodada', 'date number'])

print(f'Serie A Betano 2020:')
print(f'Total de jogos: {len(problematic_case)}')
print(f'Rodadas: {problematic_case["rodada"].min()} a {problematic_case["rodada"].max()}')
print(f'Times únicos: {problematic_case["home"].nunique()}')

# Analisar as últimas rodadas (onde provavelmente está o problema)
print('\n=== ÚLTIMAS 15 RODADAS ===')
last_rounds = problematic_case[problematic_case['rodada'] >= 37]

for rodada in sorted(last_rounds['rodada'].unique()):
    round_games = last_rounds[last_rounds['rodada'] == rodada]
    teams_in_round = set(round_games['home'].tolist() + round_games['away'].tolist())
    
    print(f'\nRodada {rodada}: {len(round_games)} jogos, {len(teams_in_round)} times')
    
    if len(round_games) <= 5:  # Mostrar detalhes para rodadas pequenas
        for _, game in round_games.iterrows():
            print(f'  {game["home"]} vs {game["away"]} (date: {game["date"]}, date_number: {game["date number"]})')

print('\n=== ANÁLISE DE TIMES POR RODADA ===')
for rodada in sorted(last_rounds['rodada'].unique())[-10:]:
    round_games = last_rounds[last_rounds['rodada'] == rodada]
    home_teams = set(round_games['home'])
    away_teams = set(round_games['away'])
    all_teams = home_teams.union(away_teams)
    
    print(f'Rodada {rodada}: {len(all_teams)} times únicos - {sorted(all_teams)}')

print('\n=== VERIFICAÇÃO DE SOBREPOSIÇÃO DE TIMES ===')
# Verificar se há times jogando mais de uma vez na mesma rodada
for rodada in sorted(last_rounds['rodada'].unique())[-5:]:
    round_games = last_rounds[last_rounds['rodada'] == rodada]
    all_teams_list = round_games['home'].tolist() + round_games['away'].tolist()
    
    duplicates = [team for team in set(all_teams_list) if all_teams_list.count(team) > 1]
    
    if duplicates:
        print(f'Rodada {rodada}: Times duplicados: {duplicates}')
    else:
        print(f'Rodada {rodada}: Sem duplicatas (OK)')