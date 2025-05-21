import streamlit as st
import pandas as pd
import numpy as np

# Título
st.sidebar.title('TCC APP')

# Introdução
st.sidebar.write("Bem vindo ao aplicativo")

# Escolher Esporte
sport = st.sidebar.selectbox("Escolha o esporte a ser analisado", ["Football", "Basketball"])

data_path = f"../data/formatted/{sport.lower()}.csv"
try:
    sports_data = pd.read_csv(data_path)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Escolher o País
country = st.sidebar.selectbox("Escolha o país", ["Brazil", "Alemanha"])

# Escolher Liga
league = st.sidebar.selectbox('Escolha a liga que deseja analisar', ['bundesliga', 'premier league'])

# Escolher Temporada
season = st.sidebar.selectbox('Escolha a temporada que deseja analisar', ['2021', '2020'])

standings_path = "../data/standings/csv/standings_2011_2021.csv"
try:
    standings = pd.read_csv(standings_path)
except Exception as e:
    st.error(f"Erro ao carregar tabela de classificação: {e}")
    standings = pd.DataFrame()  # vazio, mas o app continua


left_column, right_column = st.columns(2)

# Plotar a classificação do campeonato escolhido
left_column.title("Classificação da liga selecionada:")

# Plotar os dados sobre as partidas deste campeonato
right_column.title("Dados sobre as partidas da liga selecionada:")