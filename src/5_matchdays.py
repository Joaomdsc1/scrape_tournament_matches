import pandas as pd
from datetime import datetime
import os
import re # Importado do segundo script

def importar_e_processar_dados(caminho_arquivo):
    """
    Carrega o arquivo CSV inicial e processa a coluna 'result' para criar
    as colunas 'goal_home' e 'goal_away'.
    """
    df = pd.read_csv(caminho_arquivo)
    
    # --- Início da lógica do segundo script ---
    # Divide a coluna 'result' em 'goal_home' e 'goal_away'
    # 'expand=True' expande o resultado em novas colunas
    df[['goal_home', 'goal_away']] = df['result'].str.split(':', expand=True)

    # Extrai apenas os dígitos, preenche com '0' se não houver e converte para inteiro
    df['goal_home'] = df['goal_home'].str.extract('(\d+)').fillna('0').astype(int)
    df['goal_away'] = df['goal_away'].str.extract('(\d+)').fillna('0').astype(int)
    # --- Fim da lógica do segundo script ---
    
    return df

def criar_dicionarios(df):
    """
    Cria uma estrutura de dicionários para armazenar as rodadas de cada ID.
    """
    dicionarios = {}
    ids_unicos = df['id'].unique()
    
    for id_unico in ids_unicos:
        df_id = df[df['id'] == id_unico]
        times = df_id['home'].unique().tolist()
        rodadas_max = (len(times) - 1) * 2
        
        for rodada in range(1, rodadas_max + 1):
            chave = f"{id_unico}_{rodada}"
            dicionarios[chave] = {'jogos': []}
            
    return dicionarios

def preencher_rodadas(df, dicionarios):
    """
    Distribui os jogos do DataFrame nas estruturas de rodadas criadas.
    """
    ids_unicos = df['id'].unique()
    
    for id_unico in ids_unicos:
        print(f"Processando ID: {id_unico}")
        df_id = df[df['id'] == id_unico]
        registros_id = df_id.to_dict('records')
        
        rodadas_do_id = sorted([k for k in dicionarios.keys() if k.startswith(f"{id_unico}_")])
        
        for registro in registros_id:
            home_team = registro['home']
            away_team = registro['away']
            
            for rodada_nome in rodadas_do_id:
                times_na_rodada = set()
                for jogo in dicionarios[rodada_nome]['jogos']:
                    times_na_rodada.add(jogo['home'])
                    times_na_rodada.add(jogo['away'])
                    
                if home_team not in times_na_rodada and away_team not in times_na_rodada:
                    dicionarios[rodada_nome]['jogos'].append(registro)
                    break
                    
    return dicionarios

def salvar_csv_final(dicionarios, nome_arquivo):
    """
    Salva todos os jogos, agora com suas rodadas e gols processados, em um
    único arquivo CSV no local especificado.
    """
    output_dir = os.path.dirname(nome_arquivo)
    os.makedirs(output_dir, exist_ok=True)

    lista_de_todos_os_jogos = []
    
    for chave, rodada_data in dicionarios.items():
        id_val, rodada_num = chave.split('_')
        
        for jogo in rodada_data['jogos']:
            linha_jogo = {
                'id': id_val,
                'rodada': int(rodada_num)
            }
            linha_jogo.update(jogo)
            lista_de_todos_os_jogos.append(linha_jogo)
            
    if not lista_de_todos_os_jogos:
        print("Nenhum jogo para salvar.")
        return
        
    df_completo = pd.DataFrame(lista_de_todos_os_jogos)
    
    # Salva no arquivo CSV final
    df_completo.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
    
    print(f"\nArquivo final salvo com sucesso em: {nome_arquivo}")
    print(f"Total de jogos: {len(df_completo)}")
    print(f"Total de IDs: {df_completo['id'].nunique()}")

# --- Execução Principal ---
if __name__ == "__main__":
    # Define os caminhos dos arquivos de entrada e saída
    arquivo_entrada = '../data/3_filtered/football.csv'
    arquivo_saida = '../data/5_matchdays/football.csv'

    # 1. Carrega os dados e processa os gols
    df_processado = importar_e_processar_dados(arquivo_entrada)
    print("Dados importados e gols processados:")
    print(f"Total de registros: {len(df_processado)}")
    
    # 2. Cria a estrutura de dicionários para as rodadas
    dicionarios_vazios = criar_dicionarios(df_processado)
    print(f"\nEstrutura de rodadas criada para {len(dicionarios_vazios)} ID/rodada combinações.")
    
    # 3. Preenche as rodadas com os jogos do dataframe processado
    dicionarios_preenchidos = preencher_rodadas(df_processado, dicionarios_vazios)
    
    # 4. Salva o resultado final no arquivo CSV único
    print("\n" + "="*50)
    print("SALVANDO ARQUIVO CSV FINAL:")
    print("="*50)
    salvar_csv_final(dicionarios_preenchidos, arquivo_saida)

    # Opcional: Imprime as primeiras linhas do DataFrame final para verificação
    df_final = pd.read_csv(arquivo_saida)
    print("\n--- Amostra do arquivo final gerado ---")
    print(df_final.head())