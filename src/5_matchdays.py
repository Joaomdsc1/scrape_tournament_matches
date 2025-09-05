import pandas as pd
<<<<<<< HEAD
import os

def gerar_dicionarios_por_id_rodada(caminho_csv):
    """
    Lê um CSV de futebol e gera dicionários para cada ID único,
    com nomes baseados no número de rodadas do campeonato.
    
    Args:
        caminho_csv (str): Caminho para o arquivo CSV
    
    Returns:
        dict: Dicionário contendo todos os dicionários gerados
    """
    
    # Verifica se o arquivo existe
    if not os.path.exists(caminho_csv):
        print(f"Erro: Arquivo {caminho_csv} não encontrado!")
        return {}
    
    try:
        # Lê o CSV
        df = pd.read_csv(caminho_csv)
        print(f"CSV carregado com sucesso! {len(df)} linhas encontradas.")
        
        # Verifica se as colunas necessárias existem
        colunas_necessarias = ['home', 'away']
        if 'id' not in df.columns:
            print("Aviso: Coluna 'id' não encontrada. Usando índice como ID.")
            df['id'] = df.index
        
        for col in colunas_necessarias:
            if col not in df.columns:
                print(f"Erro: Coluna '{col}' não encontrada no CSV!")
                return {}
        
        # Obtém IDs únicos
        ids_unicos = df['id'].unique()
        print(f"IDs únicos encontrados: {len(ids_unicos)}")

        for id_unico in ids_unicos:
            # Filtra o DataFrame para o ID atual
            df_id = df[df['id'] == id_unico]
        # Calcula o número de times únicos
            times_home = set(df_id['home'].dropna())
            times_away = set(df_id['away'].dropna())
            times_unicos = times_home.union(times_away)
            num_times = len(times_unicos)
            
            # Calcula o número de rodadas: (num_times - 1) * 2
            num_rodadas = (num_times - 1) * 2
            
            print(f'Para o id {id_unico}:')
            print(f"Times únicos encontrados: {num_times}")
            print(f"Times: {sorted(list(times_unicos))}")
            print(f"Número de rodadas calculado: {num_rodadas}")
        
        # Gera os dicionários
        dicionarios_gerados = {}
        
        for id_unico in ids_unicos:
            # Filtra dados para este ID
            dados_id = df[df['id'] == id_unico]
            
            # Cria dicionários para cada rodada
            for rodada in range(1, num_rodadas + 1):
                nome_dict = f"{id_unico}_{rodada}"
                
                # Cria o dicionário com os dados filtrados para este ID
                dicionarios_gerados[nome_dict] = {
                    'id': id_unico,
                    'rodada': rodada,
                    'num_jogos': len(dados_id)
                }
        
        print(f"\n{len(dicionarios_gerados)} dicionários gerados com sucesso!")
        
        # Mostra alguns exemplos
        print("\nExemplos de dicionários gerados:")
        contador = 0
        for nome, conteudo in dicionarios_gerados.items():
            if contador < 3:  # Mostra apenas os primeiros 3
                print(f"\n{nome}:")
                print(f"  - ID: {conteudo['id']}")
                print(f"  - Rodada: {conteudo['rodada']}")
                print(f"  - Número de jogos: {conteudo['num_jogos']}")
                contador += 1
        
        return dicionarios_gerados
        
    except Exception as e:
        print(f"Erro ao processar o arquivo: {str(e)}")
        return {}

def salvar_dicionarios_como_arquivos(dicionarios, pasta_destino="../data/output"):
    """
    Salva cada dicionário como um arquivo JSON separado.
    
    Args:
        dicionarios (dict): Dicionários gerados
        pasta_destino (str): Pasta onde salvar os arquivos
    """
    import json
    import re
    
    def limpar_nome_arquivo(nome):
        """Remove caracteres inválidos do nome do arquivo"""
        # Remove ou substitui caracteres especiais
        nome_limpo = re.sub(r'[<>:"/\\|?*@]', '_', nome)
        # Remove espaços extras e caracteres repetidos
        nome_limpo = re.sub(r'_+', '_', nome_limpo)
        # Remove underscores no início e fim
        nome_limpo = nome_limpo.strip('_')
        return nome_limpo
    
    # Cria a pasta se não existir
    os.makedirs(pasta_destino, exist_ok=True)
    
    print(f"Salvando {len(dicionarios)} dicionários...")
    
    for nome, conteudo in dicionarios.items():
        nome_arquivo_limpo = limpar_nome_arquivo(nome)
        caminho_arquivo = os.path.join(pasta_destino, f"{nome_arquivo_limpo}.json")
        
        print(f"Salvando: {nome} -> {nome_arquivo_limpo}.json")
        
        try:
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(conteudo, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar {nome}: {e}")
    
    print(f"\nTodos os dicionários foram salvos em: {pasta_destino}")

# Função principal
if __name__ == "__main__":
    # Caminho do arquivo CSV
    caminho_csv = "../data/3_filtered/football.csv"
    
    # Gera os dicionários
    dicionarios = gerar_dicionarios_por_id_rodada(caminho_csv)
    
    if dicionarios:
        # Opcional: salvar como arquivos JSON
        resposta = input("\nDeseja salvar os dicionários como arquivos JSON? (s/n): ")
        if resposta.lower() in ['s', 'sim', 'y', 'yes']:
            salvar_dicionarios_como_arquivos(dicionarios)
        
        # Os dicionários estão disponíveis na variável 'dicionarios'
        print(f"\nTodos os dicionários estão disponíveis na variável 'dicionarios'")
        print(f"Nomes dos dicionários: {list(dicionarios.keys())[:10]}{'...' if len(dicionarios) > 10 else ''}")
    else:
        print("Nenhum dicionário foi gerado devido a erros.")
=======
import json
from datetime import datetime
import os

def importar_dados():
    return pd.read_csv('../data/3_filtered/football.csv')

def criar_dicionarios(df):
    dicionarios = {}
    ids_unicos = df['id'].unique()
    
    # Para cada ID único, cria suas rodadas
    for id_unico in ids_unicos:
        # Filtra dados apenas para este ID
        df_id = df[df['id'] == id_unico]
        times = df_id['home'].unique().tolist()
        rodadas_max = (len(times) - 1) * 2
        
        # Cria rodadas para este ID específico
        for rodada in range(1, rodadas_max + 1):
            chave = f"{id_unico}_{rodada}"
            dicionarios[chave] = {'jogos': []}
    
    return dicionarios

def preencher_rodadas(df, dicionarios):
    """
    Preenche as rodadas considerando cada ID separadamente
    """
    ids_unicos = df['id'].unique()
    
    # Processa cada ID separadamente
    for id_unico in ids_unicos:
        print(f"Processando ID: {id_unico}")
        
        # Filtra jogos apenas deste ID
        df_id = df[df['id'] == id_unico]
        registros_id = df_id.to_dict('records')
        
        # Filtra rodadas apenas deste ID
        rodadas_do_id = [k for k in dicionarios.keys() if k.startswith(f"{id_unico}_")]
        rodadas_do_id.sort()  # Ordena para processar na ordem correta
        
        # Para cada jogo deste ID
        for registro in registros_id:
            home_team = registro['home']
            away_team = registro['away']
            
            # Procura a primeira rodada DESTE ID onde ambos os times ainda não estão presentes
            for rodada_nome in rodadas_do_id:
                # Obtém os times já presentes nesta rodada
                times_na_rodada = set()
                for jogo in dicionarios[rodada_nome]['jogos']:
                    times_na_rodada.add(jogo['home'])
                    times_na_rodada.add(jogo['away'])
                
                # Verifica se ambos os times podem ser adicionados nesta rodada
                if home_team not in times_na_rodada and away_team not in times_na_rodada:
                    dicionarios[rodada_nome]['jogos'].append(registro)
                    break  # Sai do loop das rodadas e vai para o próximo jogo
        
        # Mostra estatísticas para este ID
        total_jogos_id = sum(len(dicionarios[r]['jogos']) for r in rodadas_do_id)
        print(f"  - {len(rodadas_do_id)} rodadas criadas")
        print(f"  - {total_jogos_id} jogos distribuídos")
    
    return dicionarios

def verificar_distribuicao(dicionarios):
    """
    Função para verificar como ficou a distribuição dos jogos
    """
    ids_unicos = set()
    for chave in dicionarios.keys():
        id_val = chave.split('_')[0]
        ids_unicos.add(id_val)
    
    for id_val in sorted(ids_unicos):
        print(f"\n=== ID {id_val} ===")
        rodadas_id = [k for k in dicionarios.keys() if k.startswith(f"{id_val}_")]
        rodadas_id.sort()
        
        for rodada_nome in rodadas_id:
            rodada_dados = dicionarios[rodada_nome]
            times_na_rodada = set()
            print(f"\n{rodada_nome}:")
            
            for jogo in rodada_dados.get('jogos', []):
                home = jogo['home']
                away = jogo['away']
                times_na_rodada.add(home)
                times_na_rodada.add(away)
                print(f"  {home} vs {away}")
            
            print(f"  Total de times: {len(times_na_rodada)}")
            print(f"  Total de jogos: {len(rodada_dados.get('jogos', []))}")

def salvar_rodadas_csv_unico(dicionarios, nome_arquivo=None):
    """
    Salva todos os jogos de todos os IDs em um único arquivo CSV.
    
    Args:
        dicionarios (dict): Dicionário com todas as rodadas preenchidas.
        nome_arquivo (str): Nome do arquivo de saída.
    """
    if nome_arquivo is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"../data/5_matchdays/rodadas_completo.csv"
        
    if not nome_arquivo.endswith('.csv'):
        nome_arquivo += '.csv'
        
    lista_de_todos_os_jogos = []
    
    # Itera sobre todas as rodadas de todos os IDs
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
        print("Nenhum jogo para salvar no arquivo CSV único.")
        return None
        
    try:
        # Cria um único DataFrame com todos os jogos
        df_completo = pd.DataFrame(lista_de_todos_os_jogos)
        
        # Salva em um arquivo CSV
        df_completo.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
        
        print(f"\nTodos os jogos foram salvos com sucesso em: {nome_arquivo}")
        print(f"Total de jogos: {len(df_completo)}")
        print(f"Total de IDs: {df_completo['id'].nunique()}")
        
        return nome_arquivo
        
    except Exception as e:
        print(f"Erro ao salvar arquivo CSV único: {e}")
        return None

# Execução principal
if __name__ == "__main__":
    df = importar_dados()
    print("Dados importados:")
    print(f"Total de registros: {len(df)}")
    print(f"IDs únicos: {sorted(df['id'].unique())}")
    
    dicionarios = criar_dicionarios(df)
    print(f"\nDicionários criados: {len(dicionarios)} rodadas")
    
    dicionarios_preenchidos = preencher_rodadas(df, dicionarios)
    
    print("\n" + "="*50)
    print("SALVANDO ARQUIVO CSV ÚNICO:")
    print("="*50)
    
    # Opcional: também salva um arquivo CSV único com todos os IDs
    salvar_rodadas_csv_unico(dicionarios_preenchidos)
>>>>>>> f5a8e8577dab0b97a6bacee45c1ceb999a005671
