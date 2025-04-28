import streamlit as st
import pandas as pd
import numpy as np

# Load data from CSV file
data_path = "../data/formatted/football.csv"
try:
    football_data = pd.read_csv(data_path)
    # st.write("Dados do arquivo CSV carregados com sucesso:")
    # st.write(football_data)
except FileNotFoundError:
    st.error(f"Arquivo não encontrado: {data_path}")
except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")

# # # # Design da página

# Add a selectbox to the sidebar:
if 'id' in football_data.columns:
    campeonatos_disponiveis = football_data['id'].dropna().unique()
    campeonatos_formatados = [
        ' '.join(word.capitalize() for word in str(campeonato).split('/')[-2].replace('-', ' ').split())
        for campeonato in campeonatos_disponiveis
    ]
    campeonato_escolhido = st.selectbox(
        'Qual campeonato você quer analisar?',
        campeonatos_formatados
    )
else:
    st.error("A coluna 'campeonato' não foi encontrada nos dados.")
    campeonato_escolhido = None

st.write(f"O campeonato escolhido foi: {campeonato_escolhido}!")

if campeonato_escolhido:
    # Map the formatted name back to the original ID
    campeonato_id_map = {
        ' '.join(word.capitalize() for word in str(campeonato).split('/')[-2].replace('-', ' ').split()): campeonato
        for campeonato in campeonatos_disponiveis
    }
    campeonato_id_escolhido = campeonato_id_map.get(campeonato_escolhido)

    # Filter the data for the selected championship
    partidas_filtradas = football_data[football_data['id'] == campeonato_id_escolhido]

    if not partidas_filtradas.empty:
        st.write("Partidas relacionadas ao campeonato escolhido:")
        colunas_ordem = ['home','away','result','date','odds home','odds tie','odds away'] + [col for col in partidas_filtradas.columns if col not in ['home','away','result','date','odds home','odds tie','odds away']]
        partidas_filtradas = partidas_filtradas[colunas_ordem]
        st.dataframe(partidas_filtradas)
    else:
        st.warning("Nenhuma partida encontrada para o campeonato selecionado.")