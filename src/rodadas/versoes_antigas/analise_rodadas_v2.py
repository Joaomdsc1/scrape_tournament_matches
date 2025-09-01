import pandas as pd
import numpy as np
from collections import Counter

def analisar_rodadas_v2(csv_file_path):
    """
    Analisa as rodadas geradas na versão 2 (por campeonato)
    """
    # Carregar os dados
    df = pd.read_csv(csv_file_path)
    
    print(f"=== ANÁLISE DAS RODADAS V2 ===")
    print(f"Total de jogos: {len(df)}")
    print(f"Total de campeonatos: {df['campeonato'].nunique()}")
    
    # Análise por campeonato
    print("\n=== ANÁLISE POR CAMPEONATO ===")
    
    for campeonato in sorted(df['campeonato'].unique()):
        print(f"\n{campeonato.upper()}:")
        df_camp = df[df['campeonato'] == campeonato].copy()
        
        print(f"  Total de jogos: {len(df_camp)}")
        print(f"  Total de rodadas: {df_camp['rodada'].nunique()}")
        print(f"  Rodadas: {df_camp['rodada'].min()} a {df_camp['rodada'].max()}")
        
        # Converter datas
        df_camp['date'] = pd.to_datetime(df_camp['date'], errors='coerce')
        df_camp_com_data = df_camp.dropna(subset=['date'])
        
        if len(df_camp_com_data) > 0:
            print(f"  Período: {df_camp_com_data['date'].min().strftime('%Y-%m-%d')} a {df_camp_com_data['date'].max().strftime('%Y-%m-%d')}")
        
        # Estatísticas de jogos por rodada
        jogos_por_rodada = df_camp.groupby('rodada').size()
        print(f"  Jogos por rodada - Média: {jogos_por_rodada.mean():.1f}, Min: {jogos_por_rodada.min()}, Max: {jogos_por_rodada.max()}")
        
        # Verificar consistência das rodadas
        verificar_consistencia_detalhada(df_camp, campeonato)
        
        # Verificar ordem cronológica
        verificar_ordem_cronologica(df_camp_com_data, campeonato)
        
        # Mostrar exemplo de algumas rodadas
        print(f"  Exemplo das primeiras 3 rodadas:")
        for rodada in sorted(df_camp['rodada'].unique())[:3]:
            jogos_rodada = df_camp[df_camp['rodada'] == rodada]
            print(f"    Rodada {rodada}: {len(jogos_rodada)} jogos")
            
            # Mostrar alguns jogos da rodada
            for _, jogo in jogos_rodada.head(3).iterrows():
                data_str = jogo['date'].strftime('%Y-%m-%d') if pd.notna(jogo['date']) else 'N/A'
                print(f"      {jogo['home']} vs {jogo['away']} ({data_str})")
            
            if len(jogos_rodada) > 3:
                print(f"      ... e mais {len(jogos_rodada) - 3} jogos")

def verificar_consistencia_detalhada(df_camp, nome_campeonato):
    """
    Verifica consistência detalhada das rodadas de um campeonato
    """
    problemas = []
    
    for rodada in df_camp['rodada'].unique():
        jogos_rodada = df_camp[df_camp['rodada'] == rodada]
        
        # Coletar todos os times
        times_home = list(jogos_rodada['home'])
        times_away = list(jogos_rodada['away'])
        todos_times = times_home + times_away
        
        # Verificar duplicatas
        contagem_times = Counter(todos_times)
        times_duplicados = [time for time, count in contagem_times.items() if count > 1]
        
        if times_duplicados:
            problemas.append(f"Rodada {rodada}: Times duplicados: {times_duplicados}")
    
    if problemas:
        print(f"  ⚠️  {len(problemas)} problemas de consistência encontrados")
        for problema in problemas[:2]:
            print(f"    - {problema}")
    else:
        print(f"  ✓ Todas as rodadas são consistentes")

def verificar_ordem_cronologica(df_camp_com_data, nome_campeonato):
    """
    Verifica se as rodadas seguem ordem cronológica
    """
    if len(df_camp_com_data) == 0:
        print(f"  ⚠️  Sem dados de data para verificar ordem cronológica")
        return
    
    # Ordenar por data
    df_ordenado = df_camp_com_data.sort_values('date')
    
    # Verificar se as rodadas aumentam com o tempo
    problemas_cronologicos = 0
    rodada_anterior = 0
    
    for _, row in df_ordenado.iterrows():
        if row['rodada'] < rodada_anterior:
            problemas_cronologicos += 1
        rodada_anterior = max(rodada_anterior, row['rodada'])
    
    if problemas_cronologicos > 0:
        print(f"  ⚠️  {problemas_cronologicos} jogos fora de ordem cronológica")
    else:
        print(f"  ✓ Ordem cronológica respeitada")

def estatisticas_gerais(df):
    """
    Mostra estatísticas gerais do dataset
    """
    print("\n=== ESTATÍSTICAS GERAIS ===")
    
    # Distribuição de jogos por rodada (geral)
    jogos_por_rodada = df.groupby(['campeonato', 'rodada']).size()
    
    print(f"Estatísticas de jogos por rodada (todas as rodadas):")
    print(f"  Média: {jogos_por_rodada.mean():.2f}")
    print(f"  Mediana: {jogos_por_rodada.median():.2f}")
    print(f"  Mínimo: {jogos_por_rodada.min()}")
    print(f"  Máximo: {jogos_por_rodada.max()}")
    
    # Distribuição de frequência
    freq_jogos = Counter(jogos_por_rodada)
    print("\nDistribuição de frequência (jogos por rodada):")
    for jogos, freq in sorted(freq_jogos.items()):
        if freq >= 5:  # Mostrar apenas frequências significativas
            print(f"  {jogos} jogos: {freq} rodadas ({freq/len(jogos_por_rodada)*100:.1f}%)")
    
    # Resumo por campeonato
    print("\nResumo por campeonato:")
    resumo = df.groupby('campeonato').agg({
        'rodada': ['min', 'max', 'nunique'],
        'home': 'count'
    })
    
    resumo.columns = ['rodada_min', 'rodada_max', 'total_rodadas', 'total_jogos']
    print(resumo)

if __name__ == "__main__":
    # Analisar o arquivo v2
    file_path = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/filtered/football_rodadas_v2.csv"
    
    df = pd.read_csv(file_path)
    
    analisar_rodadas_v2(file_path)
    estatisticas_gerais(df)
    
    print("\n=== ANÁLISE V2 CONCLUÍDA ===")