import streamlit as st
import pandas as pd
import re
from datetime import datetime
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Análise de Partidas e Classificações",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("⚽ Análise de Partidas e Classificações")

# Função para calcular classificação
def calcular_classificacao(dados_partidas):
    """Calcula a classificação baseada nos dados das partidas"""
    if dados_partidas.empty or 'winner' not in dados_partidas.columns:
        return pd.DataFrame()
    
    # Obter todos os times únicos
    times = sorted(set(
        list(dados_partidas['home'].unique()) + 
        list(dados_partidas['away'].unique())
    ))
    
    classificacao = []
    
    for time in times:
        # Partidas como mandante
        partidas_casa = dados_partidas[dados_partidas['home'] == time]
        vitorias_casa = len(partidas_casa[partidas_casa['winner'] == 'h'])
        empates_casa = len(partidas_casa[partidas_casa['winner'] == 'd'])
        derrotas_casa = len(partidas_casa[partidas_casa['winner'] == 'a'])
        
        # Partidas como visitante
        partidas_fora = dados_partidas[dados_partidas['away'] == time]
        vitorias_fora = len(partidas_fora[partidas_fora['winner'] == 'a'])
        empates_fora = len(partidas_fora[partidas_fora['winner'] == 'd'])
        derrotas_fora = len(partidas_fora[partidas_fora['winner'] == 'h'])
        
        # Totais
        total_jogos = vitorias_casa + empates_casa + derrotas_casa + vitorias_fora + empates_fora + derrotas_fora
        total_vitorias = vitorias_casa + vitorias_fora
        total_empates = empates_casa + empates_fora
        total_derrotas = derrotas_casa + derrotas_fora
        
        # Calcular pontos (3 por vitória, 1 por empate)
        pontos = (total_vitorias * 3) + total_empates
        
        # Calcular gols marcados e sofridos
        gols_marcados = 0
        gols_sofridos = 0
        
        # Gols como mandante
        for _, partida in partidas_casa.iterrows():
            if pd.notna(partida['result']):
                try:
                    gols_casa, gols_fora = map(int, partida['result'].split(':'))
                    gols_marcados += gols_casa
                    gols_sofridos += gols_fora
                except:
                    pass
        
        # Gols como visitante
        for _, partida in partidas_fora.iterrows():
            if pd.notna(partida['result']):
                try:
                    gols_casa, gols_fora = map(int, partida['result'].split(':'))
                    gols_marcados += gols_fora
                    gols_sofridos += gols_casa
                except:
                    pass
        
        saldo_gols = gols_marcados - gols_sofridos
        
        classificacao.append({
            'Time': time,
            'Jogos': total_jogos,
            'Vitórias': total_vitorias,
            'Empates': total_empates,
            'Derrotas': total_derrotas,
            'Gols Marcados': gols_marcados,
            'Gols Sofridos': gols_sofridos,
            'Saldo de Gols': saldo_gols,
            'Pontos': pontos
        })
    
    # Criar DataFrame e ordenar por pontos (decrescente) e saldo de gols (decrescente)
    df_classificacao = pd.DataFrame(classificacao)
    df_classificacao = df_classificacao.sort_values(
        ['Pontos', 'Saldo de Gols', 'Gols Marcados'], 
        ascending=[False, False, False]
    ).reset_index(drop=True)
    
    # Adicionar posição
    df_classificacao.insert(0, 'Pos', range(1, len(df_classificacao) + 1))
    
    return df_classificacao

# Função para calcular estatísticas gerais
def calcular_estatisticas_gerais(dados_partidas):
    """Calcula estatísticas gerais de vitórias da casa, empates e vitórias fora"""
    if dados_partidas.empty or 'winner' not in dados_partidas.columns:
        return None
    
    # Calcular totais
    vitorias_casa = len(dados_partidas[dados_partidas['winner'] == 'h'])
    vitorias_fora = len(dados_partidas[dados_partidas['winner'] == 'a'])
    empates = len(dados_partidas[dados_partidas['winner'] == 'd'])
    
    total_partidas = len(dados_partidas)
    
    return {
        'Vitórias Casa': vitorias_casa,
        'Empates': empates,
        'Vitórias Fora': vitorias_fora,
        'Total': total_partidas
    }

# ===== SIDEBAR =====
st.sidebar.header("🎯 Configurações")

# Seleção de esporte
esporte = st.sidebar.selectbox(
    "Selecione o Esporte",
    ["Football", "Basketball"],
    help="Escolha o esporte para visualizar os dados"
)

# Carregar dados do esporte selecionado
@st.cache_data
def carregar_dados_esporte(esporte):
    """Carrega os dados do esporte selecionado"""
    try:
        caminho = f"data/5_matchdays/{esporte.lower()}.csv"
        dados = pd.read_csv(caminho)
        return dados
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado para {esporte} no caminho esperado: {caminho}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados do {esporte}: {e}")
        return None

# Informações de competitividade
@st.cache_data
def carregar_dados_sumario():
    """Carrega os dados do relatório de análise de competitividade."""
    try:
        caminho = "data/6_analysis/summary_report_enhanced.csv"
        dados = pd.read_csv(caminho)
        return dados
    except FileNotFoundError:
        st.warning(f"Arquivo de sumário não encontrado: {caminho}. As métricas de competitividade não serão exibidas.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados do sumário: {e}")
        return None

@st.cache_data
def calcular_medias_competitividade(dados_sumario):
    """Calcula as médias dos valores de competitividade para comparação."""
    if dados_sumario is None or dados_sumario.empty:
        return None
    
    try:
        medias = {
            'variancia_forcas_media': dados_sumario['Variância Forças'].mean(),
            'desequilibrio_final_media': dados_sumario['Desequilíbrio Final'].mean(),
            'p_casa_media': dados_sumario['P(Casa)'].mean(),
            'p_empate_media': dados_sumario['P(Empate)'].mean(),
            'p_fora_media': dados_sumario['P(Fora)'].mean(),
            'total_campeonatos': len(dados_sumario)
        }
        return medias
    except Exception as e:
        st.error(f"Erro ao calcular médias de competitividade: {e}")
        return None

def obter_caminho_imagem_simulacao(id_campeonato):
    """Mapeia o ID do campeonato para o caminho da imagem de simulação correspondente."""
    try:
        # Extrair informações do ID do campeonato
        if '@' in id_campeonato:
            liga_part, url_part = id_campeonato.split('@', 1)
        else:
            liga_part = id_campeonato
            url_part = ''
        
        # Construir o nome do arquivo baseado no padrão observado
        # Exemplo: bundesliga@/football/germany/bundesliga-2010-2011/ -> bundesliga__football_germany_bundesliga-2010-2011_.png
        if url_part:
            # Remover barras iniciais e finais, substituir barras internas por underscores
            url_clean = url_part.strip('/').replace('/', '_')
            nome_arquivo = f"{liga_part}__{url_clean}_.png"
        else:
            nome_arquivo = f"{liga_part}_.png"
        
        caminho_imagem = f"data/6_analysis/{nome_arquivo}"
        return caminho_imagem
    except Exception as e:
        st.error(f"Erro ao gerar caminho da imagem para {id_campeonato}: {e}")
        return None

dados_esporte = carregar_dados_esporte(esporte)
dados_sumario = carregar_dados_sumario()
medias_competitividade = calcular_medias_competitividade(dados_sumario) 

if dados_esporte is None:
    st.stop()

# Processar ligas e temporadas disponíveis
def extrair_info_campeonato(id_campeonato):
    """Extrai informações de liga e temporada do ID do campeonato"""
    try:
        if '@' in id_campeonato:
            liga_part, url_part = id_campeonato.split('@', 1)
        else:
            liga_part = id_campeonato
            url_part = ''
        
        liga_nome = liga_part.replace('-', ' ').title()
        
        if url_part:
            anos = re.findall(r'\d{4}', url_part)
            if anos:
                if len(anos) >= 2:
                    temporada = f"{anos[0]}/{anos[1]}"
                else:
                    temporada = anos[0]
            else:
                temporada = 'N/A'
        else:
            temporada = 'N/A'
        
        return {
            'original_id': id_campeonato,
            'liga': liga_nome,
            'temporada': temporada
        }
    except Exception as e:
        st.error(f"Erro ao processar {id_campeonato}: {e}")
        return None

if 'id' in dados_esporte.columns:
    campeonatos_disponiveis = dados_esporte['id'].dropna().unique()
    
    campeonatos_info = []
    for campeonato in campeonatos_disponiveis:
        info = extrair_info_campeonato(campeonato)
        if info:
            campeonatos_info.append(info)
    
    df_ligas = pd.DataFrame(campeonatos_info).drop_duplicates()
    
    if not df_ligas.empty:
        ligas_disponiveis = sorted(df_ligas['liga'].unique())
        liga_selecionada = st.sidebar.selectbox('🏆 Selecione a Liga', ligas_disponiveis)
        
        temporadas_disponiveis = df_ligas[df_ligas['liga'] == liga_selecionada]['temporada'].unique()
        
        if len(temporadas_disponiveis) > 0:
            temporada_selecionada = st.sidebar.selectbox('📅 Selecione a Temporada', sorted(temporadas_disponiveis, reverse=True))
            
            id_selecionado = df_ligas[
                (df_ligas['liga'] == liga_selecionada) &
                (df_ligas['temporada'] == temporada_selecionada)
            ]['original_id'].values[0]
            
            st.header(f"🏆 {liga_selecionada} - {temporada_selecionada}")

            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 Filtros")
            
            dados_filtrados = dados_esporte[dados_esporte['id'] == id_selecionado].copy()
            
            if not dados_filtrados.empty:
                dados_filtrados['date'] = pd.to_datetime(dados_filtrados['date'], format='%d.%m.%Y', errors='coerce')
                
                if 'date' in dados_filtrados.columns and not dados_filtrados['date'].isna().all():
                    min_date = dados_filtrados['date'].min()
                    max_date = dados_filtrados['date'].max()
                    
                    periodo = st.sidebar.date_input("📅 Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                    
                    if len(periodo) == 2:
                        start_date, end_date = periodo
                        dados_filtrados = dados_filtrados[
                            (dados_filtrados['date'] >= pd.Timestamp(start_date)) &
                            (dados_filtrados['date'] <= pd.Timestamp(end_date))
                        ]
                
                times_disponiveis = sorted(set(list(dados_filtrados['home'].unique()) + list(dados_filtrados['away'].unique())))
                time_filtro = st.sidebar.selectbox("🏃‍♂️ Filtrar por Time", ["Todos"] + times_disponiveis)
                
                if time_filtro != "Todos":
                    dados_filtrados = dados_filtrados[(dados_filtrados['home'] == time_filtro) | (dados_filtrados['away'] == time_filtro)]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Total de Partidas", len(dados_filtrados))
                with col2:
                    st.metric("🏟️ Número de Times", len(times_disponiveis))
                
                classificacao = calcular_classificacao(dados_filtrados)
                with col3:
                    if not classificacao.empty:
                        campeao = classificacao.iloc[0]['Time']
                        st.metric("🏆 Campeão", campeao)
                    else:
                        st.metric("🏆 Campeão", "Não disponível")
                
                if 'winner' in dados_filtrados.columns:
                    st.markdown("---")
                    st.subheader("📊 Distribuição de Resultados")
                    
                    estatisticas = calcular_estatisticas_gerais(dados_filtrados)
                    
                    if estatisticas and estatisticas['Total'] > 0:
                        dados_pizza = {
                            'Resultado': ['Vitórias Casa', 'Empates', 'Vitórias Fora'],
                            'Quantidade': [estatisticas['Vitórias Casa'], estatisticas['Empates'], estatisticas['Vitórias Fora']]
                        }
                        df_pizza = pd.DataFrame(dados_pizza)
                        
                        fig = px.pie(
                            df_pizza, values='Quantidade', names='Resultado',
                            title='Distribuição de Resultados: Vitórias Casa, Empates e Vitórias Fora',
                            color_discrete_map={'Vitórias Casa': '#2E8B57', 'Empates': '#FFD700', 'Vitórias Fora': '#4169E1'}
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label', hole=0.3)
                        fig.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=400)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            percentual_vitorias_casa = (estatisticas['Vitórias Casa'] / estatisticas['Total']) * 100
                            st.metric("🏠 Vitórias Casa", f"{estatisticas['Vitórias Casa']} ({percentual_vitorias_casa:.1f}%)")
                        with col2:
                            percentual_empates = (estatisticas['Empates'] / estatisticas['Total']) * 100
                            st.metric("🤝 Empates", f"{estatisticas['Empates']} ({percentual_empates:.1f}%)")
                        with col3:
                            percentual_vitorias_fora = (estatisticas['Vitórias Fora'] / estatisticas['Total']) * 100
                            st.metric("✈️ Vitórias Fora", f"{estatisticas['Vitórias Fora']} ({percentual_vitorias_fora:.1f}%)")
                    else:
                        st.warning("⚠️ Não há dados suficientes para gerar o gráfico de distribuição.")
                
                st.markdown("---")
                st.subheader("🏆 Classificação")
                
                if not classificacao.empty:
                    colunas_renomeadas = {
                        'Pos': '🏆 Pos', 'Time': '🏃‍♂️ Time', 'Jogos': '⚽ Jogos', 'Vitórias': '✅ Vitórias',
                        'Empates': '🤝 Empates', 'Derrotas': '❌ Derrotas', 'Gols Marcados': '⚽ GM',
                        'Gols Sofridos': '🥅 GS', 'Saldo de Gols': '📊 SG', 'Pontos': '🏅 Pontos'
                    }
                    classificacao_exibicao = classificacao.rename(columns=colunas_renomeadas)
                    st.dataframe(classificacao_exibicao, hide_index=True, use_container_width=True)
                    
                    csv_classificacao = classificacao_exibicao.to_csv(index=False)
                    st.download_button(
                        label="📥 Download da Classificação (CSV)", data=csv_classificacao,
                        file_name=f"classificacao_{liga_selecionada.lower().replace(' ', '_')}_{temporada_selecionada.replace('/', '_')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ Não foi possível calcular a classificação com os dados disponíveis.")
                
                st.markdown("---")
                st.subheader("Partidas")

                # Adicionada a coluna 'rodada'
                colunas_exibicao = ['rodada', 'date', 'home', 'away', 'result']
                if 'odds home' in dados_filtrados.columns: colunas_exibicao.append('odds home')
                if 'odds tie' in dados_filtrados.columns: colunas_exibicao.append('odds tie')
                if 'odds away' in dados_filtrados.columns: colunas_exibicao.append('odds away')

                dados_exibicao = dados_filtrados[colunas_exibicao].copy()
                dados_exibicao['date'] = dados_exibicao['date'].dt.strftime('%d/%m/%Y')

                colunas_renomeadas = {
                    'rodada': '🗓️ Rodada',  
                    'date': '📅 Data', 
                    'home': '🏠 Casa', 
                    'away': '✈️ Fora', 
                    'result': '⚽ Resultado',
                    'odds home': '💰 Odds Casa', 
                    'odds tie': '💰 Odds Empate', 
                    'odds away': '💰 Odds Fora'
                }
                dados_exibicao = dados_exibicao.rename(columns=colunas_renomeadas)
                st.dataframe(dados_exibicao, hide_index=True, use_container_width=True)
                
                csv_partidas = dados_exibicao.to_csv(index=False)
                st.download_button(
                    label="📥 Download das Partidas (CSV)", data=csv_partidas,
                    file_name=f"partidas_{liga_selecionada.lower().replace(' ', '_')}_{temporada_selecionada.replace('/', '_')}.csv",
                    mime="text/csv"
                )

                # ===== INDICADORES DE COMPETITIVIDADE =====
                if dados_sumario is not None and medias_competitividade is not None:
                    info_campeonato = dados_sumario[dados_sumario['ID Campeonato'] == id_selecionado]
                    
                    if not info_campeonato.empty:
                        st.markdown("---")
                        st.subheader("📈 Análise de Competitividade")
                        
                        competitivo_status = info_campeonato.iloc[0]['É Competitivo']
                        variancia = info_campeonato.iloc[0]['Variância Forças']
                        desequilibrio = info_campeonato.iloc[0]['Desequilíbrio Final']
                        p_casa = info_campeonato.iloc[0]['P(Casa)']
                        p_empate = info_campeonato.iloc[0]['P(Empate)']
                        p_fora = info_campeonato.iloc[0]['P(Fora)']
                        
                        # Calcular diferenças em relação à média
                        diff_variancia = variancia - medias_competitividade['variancia_forcas_media']
                        diff_desequilibrio = desequilibrio - medias_competitividade['desequilibrio_final_media']
                        diff_p_casa = p_casa - medias_competitividade['p_casa_media']
                        diff_p_empate = p_empate - medias_competitividade['p_empate_media']
                        diff_p_fora = p_fora - medias_competitividade['p_fora_media']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Campeonato Competitivo",
                                f"{competitivo_status}",
                                help="Indica se o campeonato foi considerado competitivo com base na análise."
                            )
                        with col2:
                            st.metric(
                                "Variância de Forças",
                                f"{variancia:.4f}",
                                delta=f"{diff_variancia:+.4f} vs média ({medias_competitividade['variancia_forcas_media']:.4f})",
                                help="Mede a dispersão da 'força' dos times. Valores mais baixos indicam maior equilíbrio."
                            )
                        with col3:
                            st.metric(
                                "Desequilíbrio Final",
                                f"{desequilibrio:.4f}",
                                delta=f"{diff_desequilibrio:+.4f} vs média ({medias_competitividade['desequilibrio_final_media']:.4f})",
                                help="Mede o quão desequilibrada foi a classificação final. Valores mais baixos são mais equilibrados."
                            )
                        
                        # Adicionar métricas de probabilidades com comparação
                        st.markdown("#### 📊 Probabilidades de Resultado")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Probabilidade Vitória Casa",
                                f"{p_casa:.3f}",
                                delta=f"{diff_p_casa:+.3f} vs média ({medias_competitividade['p_casa_media']:.3f})",
                                help="Probabilidade de vitória do time da casa"
                            )
                        with col2:
                            st.metric(
                                "Probabilidade Empate",
                                f"{p_empate:.3f}",
                                delta=f"{diff_p_empate:+.3f} vs média ({medias_competitividade['p_empate_media']:.3f})",
                                help="Probabilidade de empate"
                            )
                        with col3:
                            st.metric(
                                "Probabilidade Vitória Fora",
                                f"{p_fora:.3f}",
                                delta=f"{diff_p_fora:+.3f} vs média ({medias_competitividade['p_fora_media']:.3f})",
                                help="Probabilidade de vitória do time visitante"
                            )
                        
                        # Informação sobre o total de campeonatos analisados
                        st.info(f"📈 Comparação baseada em {medias_competitividade['total_campeonatos']} campeonatos analisados")
                        
                        # ===== DEFINIÇÃO DE POSIÇÕES =====
                        st.markdown("#### 🏆 Definição de Posições")
                        
                        # Verificar se há dados de definição de posições
                        has_position_data = any(col in info_campeonato.columns for col in ['Campeão (Rodada)', 'Vice (Rodada)', '3º Lugar (Rodada)', '4º Lugar (Rodada)'])
                        
                        if has_position_data:
                            # Seção das 4 primeiras posições
                            st.markdown("##### 🥇 Primeiras 4 Posições")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                champion_round = info_campeonato.iloc[0].get('Campeão (Rodada)', 'N/A')
                                if champion_round != 'N/A':
                                    champion_percent = (champion_round / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                                    st.metric(
                                        "🏆 Campeão",
                                        f"Rodada {champion_round}",
                                        delta=f"{champion_percent:.1f}% da temporada",
                                        help="Rodada em que o campeão foi matematicamente definido"
                                    )
                                else:
                                    st.metric("🏆 Campeão", "N/A")
                            
                            with col2:
                                vice_round = info_campeonato.iloc[0].get('Vice (Rodada)', 'N/A')
                                if vice_round != 'N/A':
                                    vice_percent = (vice_round / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                                    st.metric(
                                        "🥈 Vice-Campeão",
                                        f"Rodada {vice_round}",
                                        delta=f"{vice_percent:.1f}% da temporada",
                                        help="Rodada em que o vice-campeão foi matematicamente definido"
                                    )
                                else:
                                    st.metric("🥈 Vice-Campeão", "N/A")
                            
                            with col3:
                                third_round = info_campeonato.iloc[0].get('3º Lugar (Rodada)', 'N/A')
                                if third_round != 'N/A':
                                    third_percent = (third_round / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                                    st.metric(
                                        "🥉 3º Lugar",
                                        f"Rodada {third_round}",
                                        delta=f"{third_percent:.1f}% da temporada",
                                        help="Rodada em que o 3º lugar foi matematicamente definido"
                                    )
                                else:
                                    st.metric("🥉 3º Lugar", "N/A")
                            
                            with col4:
                                fourth_round = info_campeonato.iloc[0].get('4º Lugar (Rodada)', 'N/A')
                                if fourth_round != 'N/A':
                                    fourth_percent = (fourth_round / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                                    st.metric(
                                        "🏅 4º Lugar",
                                        f"Rodada {fourth_round}",
                                        delta=f"{fourth_percent:.1f}% da temporada",
                                        help="Rodada em que o 4º lugar foi matematicamente definido"
                                    )
                                else:
                                    st.metric("🏅 4º Lugar", "N/A")
                            
                            # Seção das últimas posições (rebaixamento)
                            st.markdown("##### ⬇️ Últimas Posições (Rebaixamento)")
                            
                            # Encontrar colunas de rebaixamento
                            relegation_cols = [col for col in info_campeonato.columns if col.startswith('Posição ') and col.endswith(' (Rodada)')]
                            
                            if relegation_cols:
                                # Ordenar por posição
                                relegation_data = []
                                for col in relegation_cols:
                                    pos_num = int(col.split(' ')[1])
                                    round_val = info_campeonato.iloc[0].get(col, 'N/A')
                                    if round_val != 'N/A':
                                        relegation_data.append((pos_num, round_val))
                                
                                relegation_data.sort(key=lambda x: x[0])
                                
                                # Exibir em colunas
                                num_cols = min(4, len(relegation_data))
                                if num_cols > 0:
                                    cols = st.columns(num_cols)
                                    
                                    for i, (pos, round_val) in enumerate(relegation_data[:4]):
                                        with cols[i]:
                                            if round_val != 'N/A':
                                                round_percent = (round_val / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                                                st.metric(
                                                    f"Posição {pos}",
                                                    f"Rodada {round_val}",
                                                    delta=f"{round_percent:.1f}% da temporada",
                                                    help=f"Rodada em que a posição {pos} foi matematicamente definida"
                                                )
                                            else:
                                                st.metric(f"Posição {pos}", "N/A")
                        
                        # Exibir imagem de simulação se disponível
                        caminho_imagem = obter_caminho_imagem_simulacao(id_selecionado)
                        if caminho_imagem:
                            try:
                                st.subheader("📊 Simulação de Rankings")
                                st.image(caminho_imagem, caption=f"Simulação de Rankings - {liga_selecionada} {temporada_selecionada}", use_container_width=True)
                            except FileNotFoundError:
                                st.warning(f"⚠️ Imagem de simulação não encontrada: {caminho_imagem}")
                            except Exception as e:
                                st.error(f"❌ Erro ao carregar imagem de simulação: {e}")
                        else:
                            st.warning("⚠️ Não foi possível determinar o caminho da imagem de simulação.")
                        
                        st.markdown("---")

            else:
                st.warning("⚠️ Nenhuma partida encontrada para esta seleção.")
        else:
            st.sidebar.warning("⚠️ Nenhuma temporada disponível para esta liga.")
    else:
        st.error("❌ Nenhuma liga encontrada nos dados.")
else:
    st.error("❌ Coluna 'id' não encontrada nos dados.")
    st.stop()
