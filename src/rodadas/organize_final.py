#!/usr/bin/env python3
"""
Script para organizar o arquivo final por ID e rodada.
Organiza os dados de forma que fique fácil de consultar por campeonato-temporada e rodada.
"""

import pandas as pd

def organize_data(input_file: str, output_file: str):
    """
    Organiza os dados por ID (campeonato-temporada) e rodada.
    
    Args:
        input_file: Arquivo de entrada
        output_file: Arquivo de saída organizado
    """
    print(f"Carregando dados de: {input_file}")
    df = pd.read_csv(input_file)
    
    print(f"Dados carregados: {len(df)} jogos")
    print(f"Colunas: {list(df.columns)}")
    
    # Criar chave de ordenação combinando campeonato, temporada e rodada
    # Isso garante que os dados fiquem organizados por:
    # 1. Campeonato (alfabético)
    # 2. Temporada (cronológica)
    # 3. Rodada (numérica)
    # 4. Date number (cronológica dentro da rodada)
    
    print("\nOrganizando dados por ID e rodada...")
    
    # Ordenar por: campeonato, temporada, rodada, date number
    df_organized = df.sort_values([
        'campeonato',
        'temporada', 
        'rodada',
        'date number'
    ]).reset_index(drop=True)
    
    # Salvar arquivo organizado
    df_organized.to_csv(output_file, index=False)
    
    print(f"\nArquivo organizado salvo: {output_file}")
    print(f"Total de jogos: {len(df_organized)}")
    
    # Mostrar estatísticas da organização
    print("\n=== ESTATÍSTICAS DA ORGANIZAÇÃO ===")
    
    print(f"Campeonatos: {df_organized['campeonato'].nunique()}")
    print(f"Temporadas: {df_organized['temporada'].nunique()}")
    print(f"Combinações campeonato-temporada: {(df_organized['campeonato'] + '_' + df_organized['temporada']).nunique()}")
    print(f"Rodada máxima: {df_organized['rodada'].max()}")
    
    print("\nPrimeiras 10 linhas do arquivo organizado:")
    print(df_organized[['id', 'campeonato', 'temporada', 'rodada', 'home', 'away', 'date']].head(10).to_string(index=False))
    
    print("\nDistribuição por campeonato-temporada:")
    distribution = df_organized.groupby(['campeonato', 'temporada']).agg({
        'rodada': ['count', 'max'],
        'date': ['min', 'max']
    }).round(2)
    
    # Simplificar nomes das colunas
    distribution.columns = ['jogos', 'rodadas', 'data_inicio', 'data_fim']
    
    for (campeonato, temporada), row in distribution.iterrows():
        print(f"  {campeonato}_{temporada}: {int(row['jogos'])} jogos, {int(row['rodadas'])} rodadas ({row['data_inicio']} a {row['data_fim']})")
    
    return df_organized

def verify_organization(df: pd.DataFrame):
    """
    Verifica se a organização está correta.
    
    Args:
        df: DataFrame organizado
    """
    print("\n=== VERIFICAÇÃO DA ORGANIZAÇÃO ===")
    
    # Verificar se está ordenado corretamente
    is_sorted = True
    prev_camp = ""
    prev_temp = ""
    prev_round = 0
    prev_date_num = -1
    
    for _, row in df.iterrows():
        curr_camp = row['campeonato']
        curr_temp = row['temporada']
        curr_round = row['rodada']
        curr_date_num = row['date number']
        
        # Verificar ordem dos campeonatos
        if curr_camp < prev_camp:
            is_sorted = False
            break
        
        # Se mesmo campeonato, verificar temporada
        if curr_camp == prev_camp and curr_temp < prev_temp:
            is_sorted = False
            break
        
        # Se mesma temporada, verificar rodada
        if curr_camp == prev_camp and curr_temp == prev_temp:
            if curr_round < prev_round:
                is_sorted = False
                break
            
            # Se mesma rodada, verificar date number
            if curr_round == prev_round and curr_date_num < prev_date_num:
                is_sorted = False
                break
        
        prev_camp = curr_camp
        prev_temp = curr_temp
        prev_round = curr_round
        prev_date_num = curr_date_num
    
    if is_sorted:
        print("✓ Dados estão corretamente organizados por campeonato → temporada → rodada → date number")
    else:
        print("✗ ERRO: Dados não estão corretamente organizados")
    
    # Verificar consistência das rodadas
    print("\nVerificando consistência das rodadas por temporada...")
    
    inconsistencies = 0
    
    for camp_temp in df.groupby(['campeonato', 'temporada']):
        (campeonato, temporada), season_data = camp_temp
        
        for round_num in season_data['rodada'].unique():
            round_games = season_data[season_data['rodada'] == round_num]
            
            # Verificar times duplicados na rodada
            home_teams = set(round_games['home'])
            away_teams = set(round_games['away'])
            all_teams = list(round_games['home']) + list(round_games['away'])
            
            if len(all_teams) != len(set(all_teams)):
                inconsistencies += 1
                if inconsistencies <= 3:  # Mostrar apenas os primeiros 3
                    print(f"  ✗ {campeonato}_{temporada} rodada {round_num}: times duplicados")
    
    if inconsistencies == 0:
        print("✓ Todas as rodadas são consistentes (nenhum time joga mais de uma vez por rodada)")
    else:
        print(f"✗ Encontradas {inconsistencies} rodadas com inconsistências")

def main():
    """
    Função principal do script.
    """
    # Caminhos dos arquivos
    input_file = '/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_v4.csv'
    output_file = '/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_final.csv'
    
    print("=== ORGANIZAÇÃO FINAL DOS DADOS ===")
    print("Organizando por ID (campeonato-temporada) e rodada\n")
    
    try:
        # Organizar dados
        df_organized = organize_data(input_file, output_file)
        
        # Verificar organização
        verify_organization(df_organized)
        
        print("\n=== ORGANIZAÇÃO CONCLUÍDA ===")
        print(f"Arquivo final disponível em: {output_file}")
        
    except Exception as e:
        print(f"Erro durante a organização: {e}")
        raise

if __name__ == "__main__":
    main()