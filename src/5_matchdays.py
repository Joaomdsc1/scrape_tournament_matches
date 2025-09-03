import pandas as pd
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