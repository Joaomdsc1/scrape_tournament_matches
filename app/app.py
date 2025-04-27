import streamlit as st
import pandas as pd
import numpy as np

# Tabela dinâmica
dataframe = pd.DataFrame(
    np.random.randn(10, 20),
    columns=('col %d' % i for i in range(20)))

st.dataframe(dataframe.style.highlight_max(axis=0))

# Gráfico de Linha 
chart_data = pd.DataFrame(
     np.random.randn(20, 3),
     columns=['a', 'b', 'c'])

st.line_chart(chart_data)

# Plotar um mapa
map_data = pd.DataFrame(
    np.random.randn(1000, 2) / [50, 50] + [-19.912998, -43.940933],
    columns=['lat', 'lon'])

st.map(map_data)

# Widgets
x = st.slider('x')  # 👈 this is a widget
st.write(x, 'squared is', x * x)

# Layout
# Add a selectbox to the sidebar:
add_selectbox = st.sidebar.selectbox(
    'How would you like to be contacted?',
    ('Email', 'Home phone', 'Mobile phone')
)

# Add a slider to the sidebar:
add_slider = st.sidebar.slider(
    'Select a range of values',
    0.0, 100.0, (25.0, 75.0)
)

left_column, right_column = st.columns(2)
# You can use a column just like st.sidebar:
left_column.button('Press me!')

# Or even better, call Streamlit functions inside a "with" block:
with right_column:
    chosen = st.radio(
        'Sorting hat',
        ("Gryffindor", "Ravenclaw", "Hufflepuff", "Slytherin"))
    st.write(f"You are in {chosen} house!")

import time

'Starting a long computation...'

# Add a placeholder
latest_iteration = st.empty()
bar = st.progress(0)

for i in range(100):
  # Update the progress bar with each iteration.
  latest_iteration.text(f'Iteration {i+1}')
  bar.progress(i + 1)
  time.sleep(0.1)

'...and now we\'re done!'

# # # # Criação de tabelas, gráficos e imagens

# df = pd.DataFrame({
#     'first column': ["Galo", "América", "Athletic", "Itabirito"],
#     'second column': ["1º", "2º", "3º", "4º"],
# })

# # # # Design da página

# Add a selectbox to the sidebar:
# add_selectbox = st.sidebar.selectbox(
#     'Qual campeonato você quer analisar?',
#     ('Brasileirão Betano', 'Brasileirão Serie B', 'Bundesliga')
# )

# st.write("Escolha um campeonato para análise")
# st.write(df)