import pandas as pd
import numpy as np
from collections import defaultdict

def generate_rodadas(csv_file_path):
    """
    Gera números de rodada baseado no agrupamento de jogos onde cada time
    aparece apenas uma vez por rodada.
    """
    # Carregar os dados
    df = pd.read_csv(csv_file_path)
    
    # Ordenar por date number para processar em ordem cronológica
    df = df.sort_values('date number').reset_index(drop=True)
    
    # Inicializar variáveis
    rodada_atual = 1
    times_usados_na_rodada = set()
    rodadas = []
    
    print(f"Processando {len(df)} jogos...")
    
    for idx, row in df.iterrows():
        home_team = row['home']
        away_team = row['away']
        
        # Verificar se algum dos times já jogou na rodada atual
        if home_team in times_usados_na_rodada or away_team in times_usados_na_rodada:
            # Iniciar nova rodada
            rodada_atual += 1
            times_usados_na_rodada = set()
            print(f"Nova rodada iniciada: {rodada_atual} (jogo {idx + 1})")
        
        # Adicionar os times à rodada atual
        times_usados_na_rodada.add(home_team)
        times_usados_na_rodada.add(away_team)
        
        # Registrar a rodada para este jogo
        rodadas.append(rodada_atual)
        
        # Debug: mostrar progresso a cada 100 jogos
        if (idx + 1) % 100 == 0:
            print(f"Processado jogo {idx + 1}, rodada atual: {rodada_atual}")
    
    # Adicionar a coluna de rodadas ao DataFrame
    df['rodada_gerada'] = rodadas
    
    # Comparar com a rodada original se existir
    if 'rodada' in df.columns:
        print("\nComparação entre rodada original e gerada:")
        comparison = df.groupby(['rodada', 'rodada_gerada']).size().reset_index(name='count')
        print(comparison.head(20))
        
        # Verificar diferenças
        diferentes = df[df['rodada'] != df['rodada_gerada']]
        if len(diferentes) > 0:
            print(f"\nEncontradas {len(diferentes)} diferenças entre rodada original e gerada")
            print(diferentes[['date number', 'date', 'home', 'away', 'rodada', 'rodada_gerada']].head(10))
    
    # Estatísticas das rodadas geradas
    print(f"\nEstatísticas das rodadas geradas:")
    print(f"Total de rodadas: {rodada_atual}")
    
    rodada_stats = df.groupby('rodada_gerada').agg({
        'home': 'count',  # número de jogos por rodada
        'date number': ['min', 'max']  # range de date numbers por rodada
    }).round(2)
    
    rodada_stats.columns = ['jogos_por_rodada', 'date_number_min', 'date_number_max']
    print("\nJogos por rodada (primeiras 10):")
    print(rodada_stats.head(10))
    
    # Verificar se cada time aparece apenas uma vez por rodada
    print("\nVerificando se cada time aparece apenas uma vez por rodada...")
    problemas = []
    
    for rodada in range(1, rodada_atual + 1):
        jogos_rodada = df[df['rodada_gerada'] == rodada]
        times_home = set(jogos_rodada['home'])
        times_away = set(jogos_rodada['away'])
        todos_times = times_home.union(times_away)
        
        # Verificar duplicatas
        times_duplicados = times_home.intersection(times_away)
        if times_duplicados:
            problemas.append(f"Rodada {rodada}: Times jogando em casa e fora: {times_duplicados}")
        
        # Contar aparições de cada time
        for time in todos_times:
            aparicoes = len(jogos_rodada[(jogos_rodada['home'] == time) | (jogos_rodada['away'] == time)])
            if aparicoes > 1:
                problemas.append(f"Rodada {rodada}: Time {time} aparece {aparicoes} vezes")
    
    if problemas:
        print(f"Encontrados {len(problemas)} problemas:")
        for problema in problemas[:10]:  # mostrar apenas os primeiros 10
            print(f"  - {problema}")
    else:
        print("✓ Todas as rodadas estão corretas - cada time aparece apenas uma vez por rodada")
    
    return df

def save_updated_csv(df, output_path):
    """
    Salva o DataFrame atualizado com as rodadas geradas
    """
    # Substituir a coluna rodada original pela gerada
    df['rodada'] = df['rodada_gerada']
    df = df.drop('rodada_gerada', axis=1)
    
    # Salvar
    df.to_csv(output_path, index=False)
    print(f"\nArquivo salvo em: {output_path}")

if __name__ == "__main__":
    # Caminho do arquivo
    input_file = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/filtered/football.csv"
    output_file = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/filtered/football_rodadas_corrigidas.csv"
    
    # Processar
    df_updated = generate_rodadas(input_file)
    
    # Salvar resultado
    save_updated_csv(df_updated, output_file)
    
    print("\nProcessamento concluído!")