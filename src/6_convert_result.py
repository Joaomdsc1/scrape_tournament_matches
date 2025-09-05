import pandas as pd
import re
import os

# Carrega o arquivo CSV para um DataFrame do pandas
# 'rodadas.csv' é o nome do arquivo que você enviou
df = pd.read_csv('../data/3_filtered/football.csv')

# Usa a função .str.split() na coluna 'result'
# O ':' é o caractere usado para dividir a string
# 'expand=True' garante que o resultado seja expandido em novas colunas
df[['goal_home', 'goal_away']] = df['result'].str.split(':', expand=True)

# Remove caracteres não numéricos e converte para inteiro
# Usa regex para extrair apenas números, se não houver números, usa 0
df['goal_home'] = df['goal_home'].str.extract('(\d+)').fillna('0').astype(int)
df['goal_away'] = df['goal_away'].str.extract('(\d+)').fillna('0').astype(int)

# Criar diretório caso ele não exista
output_dir = '../data/5_converted'
os.makedirs(output_dir, exist_ok=True)

# Salva o DataFrame modificado em um novo arquivo CSV
# 'index=False' evita que o pandas adicione uma nova coluna de índice ao arquivo
df.to_csv(os.path.join(output_dir, 'football.csv'), index=False)

# Imprime as 5 primeiras linhas do DataFrame para verificação
print(df.head())