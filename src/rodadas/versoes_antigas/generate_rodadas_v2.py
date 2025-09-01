import pandas as pd
import numpy as np
from collections import defaultdict

def generate_rodadas_por_campeonato(csv_file_path):
    """
    Gera números de rodada baseado no agrupamento de jogos onde cada time
    aparece apenas uma vez por rodada, processando cada campeonato separadamente
    e respeitando a ordem cronológica.
    """
    # Carregar os dados
    df = pd.read_csv(csv_file_path)
    
    # Extrair o campeonato do ID
    df['campeonato'] = df['id'].str.split('@').str[0]
    
    # Converter datas
    df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
    
    print(f"Processando {len(df)} jogos de {df['campeonato'].nunique()} campeonatos...")
    
    # Lista para armazenar os resultados
    resultados = []
    
    # Processar cada campeonato separadamente
    for campeonato in sorted(df['campeonato'].unique()):
        print(f"\nProcessando campeonato: {campeonato}")
        
        df_camp = df[df['campeonato'] == campeonato].copy()
        
        # Ordenar por date number e depois por data (se disponível)
        df_camp = df_camp.sort_values(['date number', 'date'], na_position='last').reset_index(drop=True)
        
        # Gerar rodadas para este campeonato
        rodadas_camp = gerar_rodadas_campeonato(df_camp, campeonato)
        
        # Adicionar aos resultados
        resultados.extend(rodadas_camp)
    
    # Criar DataFrame final
    df_final = pd.DataFrame(resultados)
    
    # Ordenar pelo índice original para manter a ordem
    df_final = df_final.sort_values('indice_original').reset_index(drop=True)
    
    # Remover coluna auxiliar
    df_final = df_final.drop('indice_original', axis=1)
    
    return df_final

def gerar_rodadas_campeonato(df_camp, nome_campeonato):
    """
    Gera rodadas para um campeonato específico
    """
    rodada_atual = 1
    times_usados_na_rodada = set()
    resultados = []
    
    print(f"  {len(df_camp)} jogos encontrados")
    
    for idx, (original_idx, row) in enumerate(df_camp.iterrows()):
        home_team = row['home']
        away_team = row['away']
        
        # Verificar se algum dos times já jogou na rodada atual
        if home_team in times_usados_na_rodada or away_team in times_usados_na_rodada:
            # Iniciar nova rodada
            rodada_atual += 1
            times_usados_na_rodada = set()
        
        # Adicionar os times à rodada atual
        times_usados_na_rodada.add(home_team)
        times_usados_na_rodada.add(away_team)
        
        # Criar registro com a rodada
        registro = row.to_dict()
        registro['rodada'] = rodada_atual
        registro['indice_original'] = original_idx  # Para manter ordem original
        
        resultados.append(registro)
    
    print(f"  Geradas {rodada_atual} rodadas")
    
    # Verificar consistência das rodadas geradas
    verificar_consistencia_campeonato(resultados, nome_campeonato)
    
    return resultados

def verificar_consistencia_campeonato(resultados, nome_campeonato):
    """
    Verifica se as rodadas de um campeonato estão consistentes
    """
    df_temp = pd.DataFrame(resultados)
    
    problemas = []
    
    for rodada in df_temp['rodada'].unique():
        jogos_rodada = df_temp[df_temp['rodada'] == rodada]
        
        # Coletar todos os times da rodada
        times_home = set(jogos_rodada['home'])
        times_away = set(jogos_rodada['away'])
        
        # Verificar se algum time joga em casa e fora na mesma rodada
        times_duplicados = times_home.intersection(times_away)
        if times_duplicados:
            problemas.append(f"Rodada {rodada}: Times jogando em casa e fora: {times_duplicados}")
        
        # Verificar se algum time aparece mais de uma vez
        todos_times = list(jogos_rodada['home']) + list(jogos_rodada['away'])
        from collections import Counter
        contagem_times = Counter(todos_times)
        
        for time, count in contagem_times.items():
            if count > 1:
                problemas.append(f"Rodada {rodada}: Time {time} aparece {count} vezes")
    
    if problemas:
        print(f"  ⚠️  {len(problemas)} problemas encontrados:")
        for problema in problemas[:3]:  # mostrar apenas os primeiros 3
            print(f"    - {problema}")
    else:
        print(f"  ✓ Rodadas consistentes")

def salvar_arquivo_corrigido(df, output_path):
    """
    Salva o DataFrame com as rodadas corrigidas
    """
    df.to_csv(output_path, index=False)
    print(f"\nArquivo salvo em: {output_path}")
    
    # Estatísticas finais
    print(f"\nEstatísticas finais:")
    print(f"Total de jogos: {len(df)}")
    print(f"Total de campeonatos: {df['campeonato'].nunique()}")
    print(f"Rodada máxima: {df['rodada'].max()}")
    
    # Estatísticas por campeonato
    stats_campeonato = df.groupby('campeonato').agg({
        'rodada': ['min', 'max', 'nunique'],
        'home': 'count'
    }).round(2)
    
    stats_campeonato.columns = ['rodada_min', 'rodada_max', 'total_rodadas', 'total_jogos']
    stats_campeonato = stats_campeonato.sort_values('total_jogos', ascending=False)
    
    print("\nTop 10 campeonatos:")
    print(stats_campeonato.head(10))

if __name__ == "__main__":
    # Caminhos dos arquivos
    input_file = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/filtered/football.csv"
    output_file = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/filtered/football_rodadas_v2.csv"
    
    # Processar
    print("=== GERAÇÃO DE RODADAS V2 ===")
    print("Processando cada campeonato separadamente...")
    
    df_updated = generate_rodadas_por_campeonato(input_file)
    
    # Salvar resultado
    salvar_arquivo_corrigido(df_updated, output_file)
    
    print("\n=== PROCESSAMENTO CONCLUÍDO ===")