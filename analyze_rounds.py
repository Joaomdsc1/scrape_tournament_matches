#!/usr/bin/env python3
import pandas as pd

# Carregar dados
df = pd.read_csv('/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_final.csv')

print('=== ANÁLISE DETALHADA DE CAMPEONATOS COM MUITAS RODADAS ===')

# Analisar campeonatos com mais de 40 rodadas
problematic = df[df['rodada'] > 40]

for (camp, temp), group in problematic.groupby(['campeonato', 'temporada']):
    print(f'\n{camp} {temp}:')
    print(f'  - Total de jogos: {len(group)}')
    print(f'  - Rodadas: {group["rodada"].min()} a {group["rodada"].max()}')
    print(f'  - Times únicos: {group["home"].nunique()}')
    
    jogos_por_rodada = group.groupby('rodada').size()
    print(f'  - Jogos por rodada: min={jogos_por_rodada.min()}, max={jogos_por_rodada.max()}, média={jogos_por_rodada.mean():.1f}')
    
    # Verificar se há rodadas com apenas 1 jogo (possível problema)
    rodadas_com_1_jogo = (jogos_por_rodada == 1).sum()
    print(f'  - Rodadas com apenas 1 jogo: {rodadas_com_1_jogo}')
    
    # Mostrar algumas rodadas problemáticas
    if rodadas_com_1_jogo > 0:
        rodadas_problema = jogos_por_rodada[jogos_por_rodada == 1].head(5)
        print(f'  - Exemplos de rodadas com 1 jogo: {list(rodadas_problema.index)}')

print('\n=== COMPARAÇÃO COM NÚMEROS ESPERADOS DE RODADAS ===')
print('Números típicos de rodadas por campeonato:')
print('- Bundesliga (18 times): 34 rodadas (2 turnos)')
print('- Premier League (20 times): 38 rodadas (2 turnos)')
print('- Serie A (20 times): 38 rodadas (2 turnos)')
print('- Ligue 1 (20 times): 38 rodadas (2 turnos)')
print('- Brasileirão Serie A (20 times): 38 rodadas (2 turnos)')
print('- Brasileirão Serie B (20 times): 38 rodadas (2 turnos)')

print('\n=== ANÁLISE DE POSSÍVEIS PROBLEMAS ===')
for (camp, temp), group in df.groupby(['campeonato', 'temporada']):
    max_rodada = group['rodada'].max()
    times_unicos = group['home'].nunique()
    rodadas_esperadas = (times_unicos - 1) * 2  # Para campeonato de pontos corridos
    
    if max_rodada > rodadas_esperadas + 5:  # Margem de 5 rodadas
        print(f'{camp} {temp}: {max_rodada} rodadas (esperado ~{rodadas_esperadas}) - POSSÍVEL PROBLEMA')