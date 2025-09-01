#!/usr/bin/env python3

import pandas as pd

df = pd.read_csv('data/5_matchdays/football_rodadas_final.csv')

print('=== VERIFICAÇÃO FINAL ===')
print(f'Total de jogos: {len(df):,}')
print(f'Rodada máxima: {df["rodada"].max()}')
print(f'Campeonatos: {df["campeonato"].nunique()}')
print(f'Temporadas: {df["temporada"].nunique()}')
print()
print('Rodadas por campeonato-temporada:')
for ct in sorted(df["campeonato_temporada"].unique()):
    season_data = df[df["campeonato_temporada"] == ct]
    print(f'  {ct}: {season_data["rodada"].max()} rodadas')