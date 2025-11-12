import pandas as pd
import os
from typing import Dict, List, Tuple

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

def _preparar_dataframe_para_id(df_id: pd.DataFrame) -> pd.DataFrame:
    """
    Cria colunas auxiliares para garantir a ordenação cronológica
    respeitando datas e um eventual índice numérico já existente.
    """
    df_trabalho = df_id.copy()

    if 'date' in df_trabalho.columns:
        df_trabalho['__date_parsed'] = pd.to_datetime(
            df_trabalho['date'],
            format='%d.%m.%Y',
            errors='coerce'
        )
    else:
        df_trabalho['__date_parsed'] = pd.NaT

    if 'date number' in df_trabalho.columns:
        df_trabalho['__date_number'] = pd.to_numeric(
            df_trabalho['date number'],
            errors='coerce'
        )
    else:
        df_trabalho['__date_number'] = pd.Series(range(len(df_trabalho)), index=df_trabalho.index)

    df_trabalho = df_trabalho.sort_values(
        by=['__date_parsed', '__date_number', 'home', 'away'],
        kind='mergesort'
    ).reset_index(drop=True)

    return df_trabalho

def _calcular_capacidade_rodada(times: List[str]) -> int:
    """
    Determina quantos jogos cabem em uma rodada respeitando a regra
    de que cada time joga no máximo uma vez.
    """
    if not times:
        return 0

    capacidade = len(times) // 2
    return max(1, capacidade)

def _existe_rodada_incompleta(rodadas: List[Dict], capacidade_maxima: int) -> bool:
    """
    Verifica se há alguma rodada ainda com espaço disponível.
    """
    if capacidade_maxima == 0:
        return False

    return any(len(rodada['jogos']) < capacidade_maxima for rodada in rodadas)

def _tentar_inserir_jogo(
    rodadas: List[Dict],
    jogo: Dict,
    capacidade_maxima: int,
    pode_criar_nova: bool
) -> bool:
    """
    Tenta inserir o jogo na primeira rodada possível respeitando
    o limite de jogos e evitando times repetidos.
    """
    for rodada in rodadas:
        if capacidade_maxima and len(rodada['jogos']) >= capacidade_maxima:
            continue

        times_na_rodada = rodada['times']
        if jogo['home'] in times_na_rodada or jogo['away'] in times_na_rodada:
            continue

        rodada['jogos'].append(jogo)
        rodada['times'].update([jogo['home'], jogo['away']])
        return True

    if pode_criar_nova or not rodadas:
        rodadas.append({
            'jogos': [jogo],
            'times': {jogo['home'], jogo['away']}
        })
        return True

    return False

def _organizar_rodadas_para_id(df_id: pd.DataFrame, id_val: str) -> Tuple[List[Dict], int]:
    """
    Monta as rodadas de um ID específico considerando a cronologia
    e marcando jogos adiados quando necessário.
    Respeita o limite máximo de rodadas para campeonatos concluídos.
    """
    df_trabalho = _preparar_dataframe_para_id(df_id)
    registros = df_trabalho.drop(columns=[c for c in df_trabalho.columns if c.startswith('__')]).to_dict('records')

    times = pd.unique(pd.concat([df_trabalho['home'], df_trabalho['away']], ignore_index=True)).tolist()
    capacidade_maxima = _calcular_capacidade_rodada(times)

    # Calcula o limite máximo de rodadas para campeonatos concluídos
    # Campeonatos de 2025 e 2025-2026 estão em andamento e não seguem a regra
    eh_campeonato_andamento = '2025' in str(id_val)
    if eh_campeonato_andamento:
        limite_max_rodadas = None  # Sem limite
    else:
        num_times = len(times)
        limite_max_rodadas = (num_times - 1) * 2

    rodadas: List[Dict] = []
    adiados: List[Dict] = []

    # Primeiro, organiza todos os jogos normalmente
    for jogo in registros:
        jogo.setdefault('adiado', False)
        pode_criar_nova = not _existe_rodada_incompleta(rodadas, capacidade_maxima)
        inserido = _tentar_inserir_jogo(rodadas, jogo, capacidade_maxima, pode_criar_nova=pode_criar_nova)

        if not inserido:
            jogo['adiado'] = True
            adiados.append(jogo)

    if adiados:
        adiados_restantes: List[Dict] = []
        for jogo in adiados:
            inserido = _tentar_inserir_jogo(rodadas, jogo, capacidade_maxima, pode_criar_nova=False)
            if not inserido:
                adiados_restantes.append(jogo)

        for jogo in adiados_restantes:
            _tentar_inserir_jogo(rodadas, jogo, capacidade_maxima, pode_criar_nova=True)

    # Aplica o limite de rodadas para campeonatos concluídos
    if limite_max_rodadas is not None and len(rodadas) > limite_max_rodadas:
        # Jogos das rodadas excedentes devem ser marcados como adiados
        jogos_excedentes = []
        for i in range(limite_max_rodadas, len(rodadas)):
            jogos_excedentes.extend(rodadas[i]['jogos'])

        # Remove as rodadas excedentes
        rodadas = rodadas[:limite_max_rodadas]

        # Marca os jogos excedentes como adiados
        for jogo in jogos_excedentes:
            jogo['adiado'] = True
            adiados.append(jogo)

    # Remove o conjunto de times antes de retornar
    for rodada in rodadas:
        rodada.pop('times', None)

    jogos_adiados = sum(
        1 for rodada in rodadas for jogo in rodada['jogos'] if jogo.get('adiado', False)
    )

    return rodadas, jogos_adiados

def criar_dicionarios(df):
    """
    Cria uma estrutura de dicionários para armazenar as rodadas de cada ID,
    respeitando temporadas em andamento e tratando partidas adiadas.
    """
    dicionarios: Dict[str, Dict[str, List[Dict]]] = {}
    resumo_processamento: Dict[str, Dict[str, int]] = {}

    ids_unicos = df['id'].unique()
    
    for id_unico in ids_unicos:
        df_id = df[df['id'] == id_unico]
        rodadas, total_adiados = _organizar_rodadas_para_id(df_id, id_unico)

        resumo_processamento[id_unico] = {
            'rodadas': len(rodadas),
            'adiados': total_adiados
        }

        for indice, rodada in enumerate(rodadas, start=1):
            chave = f"{id_unico}_{indice}"
            dicionarios[chave] = {'jogos': rodada['jogos']}

        print(
            f"Processando ID: {id_unico} -> Rodadas geradas: {len(rodadas)} | "
            f"Jogos adiados: {total_adiados}"
        )
            
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
    import os
    # Define os caminhos dos arquivos de entrada e saída de forma robusta
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    diretorio_projeto = os.path.dirname(diretorio_atual)  # Vai para o diretório pai (raiz do projeto)

    arquivo_entrada = os.path.join(diretorio_projeto, 'data', '3_filtered', 'football.csv')
    arquivo_saida = os.path.join(diretorio_projeto, 'data', '5_matchdays', 'football.csv')

    # 1. Carrega os dados e processa os gols
    df_processado = importar_e_processar_dados(arquivo_entrada)
    print("Dados importados e gols processados:")
    print(f"Total de registros: {len(df_processado)}")
    
    # 2. Cria e preenche a estrutura de dicionários para as rodadas
    dicionarios_preenchidos = criar_dicionarios(df_processado)
    print(f"\nTotal de chaves ID/rodada geradas: {len(dicionarios_preenchidos)}")
    
    # 3. Salva o resultado final no arquivo CSV único
    print("\n" + "="*50)
    print("SALVANDO ARQUIVO CSV FINAL:")
    print("="*50)
    salvar_csv_final(dicionarios_preenchidos, arquivo_saida)

    # Opcional: Imprime as primeiras linhas do DataFrame final para verificação
    df_final = pd.read_csv(arquivo_saida)
    print("\n--- Amostra do arquivo final gerado ---")
    print(df_final.head())