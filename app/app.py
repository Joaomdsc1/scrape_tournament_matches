import streamlit as st
import pandas as pd

st.set_page_config(page_title="Classificações e Partidas", layout="wide")

# Selecionar esporte
esporte = st.selectbox("Selecione o Esporte", ["Football", "Basketball"])

# Carregar dados
data_path = f"../data/formatted/{esporte.lower()}.csv"
try:
    dados_esporte = pd.read_csv(data_path)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Carregar classificação
standings_path = "../data/standings/csv/standings_2011_2021.csv"
try:
    standings = pd.read_csv(standings_path)
except Exception as e:
    st.error(f"Erro ao carregar tabela de classificação: {e}")
    standings = pd.DataFrame()  # vazio, mas o app continua


# Processar ligas e temporadas
if 'id' in dados_esporte.columns:
    campeonatos_disponiveis = dados_esporte['id'].dropna().unique()
    
    campeonatos_info = []
    for campeonato in campeonatos_disponiveis:
        try:
            if '@' in campeonato:
                liga_part, url_part = campeonato.split('@', 1)
            else:
                liga_part = campeonato
                url_part = ''
            
            liga_nome = liga_part.replace('-', ' ').title()
            
            if url_part:
                season = url_part.strip('/').split('/')[-1].split('-')[-1]
                temporada = season if len(season) == 4 and season.isdigit() else 'N/A'
            else:
                temporada = 'N/A'
            
            campeonatos_info.append({
                'original_id': campeonato,
                'liga': liga_nome,
                'temporada': temporada
            })
            
        except Exception as e:
            st.error(f"Erro ao processar {campeonato}: {e}")

    df_ligas = pd.DataFrame(campeonatos_info).drop_duplicates()

    # Seleção de liga
    liga_selecionada = st.selectbox(
        'Selecione a Liga',
        sorted(df_ligas['liga'].unique())
    )  # Fechamento correto do selectbox
    
    # Filtro de temporada
    temporadas_disponiveis = df_ligas[df_ligas['liga'] == liga_selecionada]['temporada'].unique()
    
    if temporadas_disponiveis.size == 0:  # Verificação correta para arrays NumPy
        st.warning("Nenhuma temporada disponível para esta liga")
        st.stop()
        
    temporada_selecionada = st.selectbox(
        'Selecione a Temporada',
        sorted(temporadas_disponiveis, reverse=True)
    )  # Fechamento correto do selectbox

    # Obter ID correspondente
    id_selecionado = df_ligas[
        (df_ligas['liga'] == liga_selecionada) &
        (df_ligas['temporada'] == temporada_selecionada)
    ]['original_id'].values[0]

else:
    st.error("Coluna 'id' não encontrada nos dados")
    st.stop()

# Exibir dados
st.header(f"{liga_selecionada} - {temporada_selecionada}")
dados_filtrados = dados_esporte[dados_esporte['id'] == id_selecionado]

if not dados_filtrados.empty:
    # Definir colunas dinamicamente conforme o esporte
    colunas_base = ['date', 'home', 'away', 'result']
    
    # Verificar quais colunas de odds existem
    colunas_odds = []
    if 'odds home' in dados_esporte.columns:
        colunas_odds.append('odds home')
    if 'odds tie' in dados_esporte.columns:  # Só existirá no football
        colunas_odds.append('odds tie')
    if 'odds away' in dados_esporte.columns:
        colunas_odds.append('odds away')
    
    # Combinar colunas
    colunas = colunas_base + colunas_odds
    
    st.dataframe(dados_filtrados[colunas], hide_index=True)
else:
    st.warning("Nenhum dado encontrado para esta seleção")

# === PROCESSAR NOMES PARA SELEÇÃO ===
standings['liga'] = standings['tournament'].apply(lambda x: x.rsplit('-', 1)[0].replace('-', ' ').title())
standings['temporada'] = standings['tournament'].apply(lambda x: x.rsplit('-', 1)[1])

ligas_disponiveis = standings['liga'].unique()
liga_selecionada = st.selectbox('Selecione a Liga', sorted(ligas_disponiveis))

temporadas_disponiveis = standings[standings['liga'] == liga_selecionada]['temporada'].unique()
temporada_selecionada = st.selectbox('Selecione a Temporada', sorted(temporadas_disponiveis, reverse=True))

# === IDENTIFICADOR DE TORNEIO ===
tournament_id = f"{liga_selecionada.lower().replace(' ', '-')}-{temporada_selecionada}"
st.markdown(f"**Tournament ID buscado:** `{tournament_id}`")

# === EXIBIR CLASSIFICAÇÃO ===
st.subheader(f"Classificação: {liga_selecionada} - {temporada_selecionada}")
standings_filtrada = standings[standings['tournament'] == tournament_id]

if not standings_filtrada.empty:
    st.dataframe(standings_filtrada.drop(columns=['liga', 'temporada']), hide_index=True)
else:
    st.warning("Classificação não encontrada para esta liga/temporada.")


