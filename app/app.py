import streamlit as st
import pandas as pd

# Carregar dados
data_path = "../data/formatted/football.csv"
try:
    football_data = pd.read_csv(data_path)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Processar ligas e temporadas
if 'id' in football_data.columns:
    campeonatos_disponiveis = football_data['id'].dropna().unique()
    
    campeonatos_info = []
    for campeonato in campeonatos_disponiveis:
        try:
            # Dividir o ID em duas partes
            if '@' in campeonato:
                liga_part, url_part = campeonato.split('@', 1)
            else:
                liga_part = campeonato
                url_part = ''
            
            # Formatar nome da liga (parte antes do @)
            liga_nome = liga_part.replace('-', ' ').title()
            
            # Substituir Serie por Série
            liga_nome = liga_nome.replace('Serie', 'Série')
            
            # Extrair temporada da URL
            if url_part:
                season = url_part.strip('/').split('/')[-1].split('-')[-1]
                # Validar se é um ano (4 dígitos)
                if len(season) == 4 and season.isdigit():
                    temporada = season
                else:
                    temporada = 'N/A'
            else:
                temporada = 'N/A'
            
            campeonatos_info.append({
                'original_id': campeonato,
                'liga': liga_nome,
                'temporada': temporada
            })
            
        except Exception as e:
            st.error(f"Erro ao processar {campeonato}: {e}")

    # Criar DataFrame com ligas e temporadas
    df_ligas = pd.DataFrame(campeonatos_info).drop_duplicates()

    # Selectbox para ligas
    liga_selecionada = st.selectbox(
        'Selecione a Liga',
        sorted(df_ligas['liga'].unique())
    )
    
    # Filtrar temporadas
    temporadas_disponiveis = df_ligas[df_ligas['liga'] == liga_selecionada]['temporada'].unique()
    
    if len(temporadas_disponiveis) == 0:
        st.warning("Nenhuma temporada disponível para esta liga")
        st.stop()
        
    # Selectbox para temporadas
    temporada_selecionada = st.selectbox(
        'Selecione a Temporada',
        sorted(temporadas_disponiveis, reverse=True)
    )
    
    # Obter ID correspondente
    id_selecionado = df_ligas[
        (df_ligas['liga'] == liga_selecionada) &
        (df_ligas['temporada'] == temporada_selecionada)
    ]['original_id'].values[0]

else:
    st.error("Coluna 'id' não encontrada nos dados")
    st.stop()

# Mostrar dados
st.header(f"{liga_selecionada} - {temporada_selecionada}")
dados_filtrados = football_data[football_data['id'] == id_selecionado]

if not dados_filtrados.empty:
    colunas = ['date', 'home', 'away', 'result', 'odds home', 'odds tie', 'odds away']
    st.dataframe(dados_filtrados[colunas], hide_index=True)
else:
    st.warning("Nenhum dado encontrado para esta seleção")