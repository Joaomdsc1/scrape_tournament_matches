import pandas as pd
import numpy as np
from collections import Counter

def analisar_rodadas(csv_file_path):
    """
    Analisa as rodadas geradas e fornece estatísticas detalhadas
    """
    # Carregar os dados
    df = pd.read_csv(csv_file_path)
    
    print(f"=== ANÁLISE DAS RODADAS GERADAS ===")
    print(f"Total de jogos: {len(df)}")
    print(f"Total de rodadas: {df['rodada'].max()}")
    
    # Análise por campeonato/liga
    print("\n=== ANÁLISE POR CAMPEONATO ===")
    df['campeonato'] = df['id'].str.split('@').str[0]
    campeonatos = df['campeonato'].value_counts()
    print(f"Número de campeonatos: {len(campeonatos)}")
    print("\nTop 10 campeonatos por número de jogos:")
    print(campeonatos.head(10))
    
    # Análise das rodadas por campeonato
    print("\n=== RODADAS POR CAMPEONATO ===")
    rodadas_por_campeonato = df.groupby('campeonato')['rodada'].agg(['min', 'max', 'nunique']).reset_index()
    rodadas_por_campeonato.columns = ['campeonato', 'rodada_min', 'rodada_max', 'total_rodadas']
    rodadas_por_campeonato = rodadas_por_campeonato.sort_values('total_rodadas', ascending=False)
    
    print("Top 10 campeonatos por número de rodadas:")
    print(rodadas_por_campeonato.head(10))
    
    # Análise de jogos por rodada
    print("\n=== DISTRIBUIÇÃO DE JOGOS POR RODADA ===")
    jogos_por_rodada = df.groupby('rodada').size()
    
    print(f"Estatísticas de jogos por rodada:")
    print(f"  Média: {jogos_por_rodada.mean():.2f}")
    print(f"  Mediana: {jogos_por_rodada.median():.2f}")
    print(f"  Mínimo: {jogos_por_rodada.min()}")
    print(f"  Máximo: {jogos_por_rodada.max()}")
    
    # Distribuição de frequência
    freq_jogos = Counter(jogos_por_rodada)
    print("\nDistribuição de frequência (jogos por rodada):")
    for jogos, freq in sorted(freq_jogos.items()):
        print(f"  {jogos} jogos: {freq} rodadas ({freq/len(jogos_por_rodada)*100:.1f}%)")
    
    # Verificar consistência dentro de cada campeonato
    print("\n=== VERIFICAÇÃO DE CONSISTÊNCIA POR CAMPEONATO ===")
    problemas_campeonato = []
    
    for campeonato in df['campeonato'].unique():
        df_camp = df[df['campeonato'] == campeonato].copy()
        
        # Verificar se as rodadas são sequenciais dentro do campeonato
        rodadas_camp = sorted(df_camp['rodada'].unique())
        
        # Para cada rodada do campeonato, verificar se cada time aparece apenas uma vez
        for rodada in rodadas_camp:
            jogos_rodada = df_camp[df_camp['rodada'] == rodada]
            times_home = list(jogos_rodada['home'])
            times_away = list(jogos_rodada['away'])
            todos_times = times_home + times_away
            
            # Verificar duplicatas
            times_duplicados = [time for time, count in Counter(todos_times).items() if count > 1]
            if times_duplicados:
                problemas_campeonato.append(f"{campeonato} - Rodada {rodada}: Times duplicados: {times_duplicados}")
    
    if problemas_campeonato:
        print(f"Encontrados {len(problemas_campeonato)} problemas de consistência:")
        for problema in problemas_campeonato[:5]:  # mostrar apenas os primeiros 5
            print(f"  - {problema}")
    else:
        print("✓ Todos os campeonatos estão consistentes")
    
    # Análise temporal
    print("\n=== ANÁLISE TEMPORAL ===")
    df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
    
    # Verificar se as rodadas seguem ordem cronológica dentro de cada campeonato
    problemas_cronologicos = []
    
    for campeonato in df['campeonato'].unique():
        df_camp = df[df['campeonato'] == campeonato].copy()
        df_camp = df_camp.dropna(subset=['date']).sort_values('date')
        
        if len(df_camp) > 1:
            # Verificar se as rodadas aumentam com o tempo
            rodadas_anteriores = df_camp['rodada'].shift(1)
            problemas = df_camp[df_camp['rodada'] < rodadas_anteriores]
            
            if len(problemas) > 0:
                problemas_cronologicos.append(f"{campeonato}: {len(problemas)} jogos fora de ordem cronológica")
    
    if problemas_cronologicos:
        print(f"Encontrados problemas cronológicos em {len(problemas_cronologicos)} campeonatos:")
        for problema in problemas_cronologicos[:5]:
            print(f"  - {problema}")
    else:
        print("✓ Ordem cronológica respeitada em todos os campeonatos")
    
    # Exemplo de rodadas para alguns campeonatos
    print("\n=== EXEMPLOS DE RODADAS ===")
    
    # Pegar alguns campeonatos com mais jogos
    top_campeonatos = campeonatos.head(3).index
    
    for campeonato in top_campeonatos:
        print(f"\n{campeonato.upper()}:")
        df_camp = df[df['campeonato'] == campeonato]
        
        # Mostrar as primeiras 3 rodadas
        for rodada in sorted(df_camp['rodada'].unique())[:3]:
            jogos_rodada = df_camp[df_camp['rodada'] == rodada]
            print(f"  Rodada {rodada} ({len(jogos_rodada)} jogos):")
            for _, jogo in jogos_rodada.head(5).iterrows():
                print(f"    {jogo['home']} vs {jogo['away']} ({jogo['date']})")
            if len(jogos_rodada) > 5:
                print(f"    ... e mais {len(jogos_rodada) - 5} jogos")
    
    return df

if __name__ == "__main__":
    # Analisar o arquivo gerado
    file_path = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/filtered/football_rodadas_corrigidas.csv"
    
    df = analisar_rodadas(file_path)
    
    print("\n=== ANÁLISE CONCLUÍDA ===")