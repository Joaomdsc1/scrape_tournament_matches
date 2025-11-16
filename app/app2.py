import streamlit as st
import pandas as pd
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import logging

# ===== CONFIGURAÇÃO DO LOGGER =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Análise de Competitividade em Ligas de Futebol",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("⚽ Análise de Competitividade em Ligas de Futebol")

# ===== NOVAS FUNÇÕES PARA CARREGAR DADOS DE COMPETITIVIDADE =====

@st.cache_data
def carregar_dados_competitividade():
    """Carrega os dados do relatório de análise de competitividade otimizado."""
    try:
        caminho = "data/6_analysis_optimized/optimized_summary_report.csv"
        dados = pd.read_csv(caminho)
        
        # Converter colunas numéricas
        colunas_numericas = ['Variância Forças', 'Desequilíbrio Final', 'P(Casa)', 'P(Empate)', 'P(Fora)']
        for coluna in colunas_numericas:
            if coluna in dados.columns:
                # Remover 'N/A' e converter para float
                dados[coluna] = pd.to_numeric(dados[coluna].replace('N/A', None), errors='coerce')
        
        # Converter colunas de rodadas para numérico
        colunas_rodadas = ['Campeão (Rodada)', 'Vice (Rodada)', '3º Lugar (Rodada)', '4º Lugar (Rodada)']
        for coluna in colunas_rodadas:
            if coluna in dados.columns:
                dados[coluna] = pd.to_numeric(dados[coluna].replace('N/A', None), errors='coerce')
        
        # Processar colunas de rebaixamento
        relegation_cols = [col for col in dados.columns if col.startswith('Posição ') and col.endswith(' (Rodada)')]
        for col in relegation_cols:
            dados[col] = pd.to_numeric(dados[col].replace('N/A', None), errors='coerce')
        
        logger.info(f"Dados de competitividade carregados: {len(dados)} campeonatos")
        return dados
    except FileNotFoundError:
        st.error(f"❌ Arquivo de análise de competitividade não encontrado: {caminho}")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de competitividade: {e}")
        return None

@st.cache_data
def carregar_dados_rodadas():
    """Carrega os dados de competitividade consolidados rodada a rodada."""
    try:
        # Caminho para o arquivo consolidado que seu script principal gera
        caminho = "data/6_analysis_optimized/round_by_round_competitiveness.csv"
        dados = pd.read_csv(caminho)
        logger.info(f"Dados de competitividade por rodada carregados: {len(dados)} registros")
        return dados
    except FileNotFoundError:
        st.error(f"❌ Arquivo de competitividade por rodada não encontrado: {caminho}")
        st.warning("Execute o script de análise principal para gerar este arquivo.")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de competitividade por rodada: {e}")
        return None

@st.cache_data
def calcular_estatisticas_gerais_competitividade(dados_competitividade):
    """Calcula estatísticas gerais de competitividade baseadas nos dados carregados."""
    if dados_competitividade is None or dados_competitividade.empty:
        return None
    
    try:
        total_campeonatos = len(dados_competitividade)
        competitivos = len(dados_competitividade[dados_competitividade['É Competitivo'] == 'Sim'])
        nao_competitivos = total_campeonatos - competitivos
        
        # Calcular médias das métricas numéricas
        medias = {
            'total_campeonatos': total_campeonatos,
            'percentual_competitivos': (competitivos / total_campeonatos) * 100,
            'percentual_nao_competitivos': (nao_competitivos / total_campeonatos) * 100,
            'variancia_forcas_media': dados_competitividade['Variância Forças'].mean(),
            'desequilibrio_final_media': dados_competitividade['Desequilíbrio Final'].mean(),
            'p_casa_media': dados_competitividade['P(Casa)'].mean(),
            'p_empate_media': dados_competitividade['P(Empate)'].mean(),
            'p_fora_media': dados_competitividade['P(Fora)'].mean(),
        }
        
        # Calcular ponto de virada médio apenas para ligas não competitivas
        ligas_nao_competitivas = dados_competitividade[dados_competitividade['É Competitivo'] == 'Não']
        if not ligas_nao_competitivas.empty and 'Ponto Virada (%)' in ligas_nao_competitivas.columns:
            # Extrair valores percentuais (remover o símbolo % e converter para float)
            percentuais = ligas_nao_competitivas['Ponto Virada (%)'].str.rstrip('%').astype(float)
            medias['ponto_virada_medio'] = percentuais.mean()
        else:
            medias['ponto_virada_medio'] = None
            
        return medias
    except Exception as e:
        st.error(f"❌ Erro ao calcular estatísticas de competitividade: {e}")
        return None

def obter_caminho_imagem_simulacao(id_campeonato):
    """Mapeia o ID do campeonato para o caminho da imagem de simulação correspondente."""
    try:
        # Limpar o ID para criar nome de arquivo válido
        id_limpo = id_campeonato.replace('/', '_').replace('@', '_').replace(':', '_')
        nome_arquivo = f"{id_limpo}.png"
        
        # Tentar primeiro o diretório otimizado
        caminho_otimizado = f"data/6_analysis_optimized/{nome_arquivo}"
        if Path(caminho_otimizado).exists():
            return caminho_otimizado
        
        # Tentar o diretório original
        caminho_original = f"data/6_analysis/{nome_arquivo}"
        if Path(caminho_original).exists():
            return caminho_original
        
        return None
    except Exception as e:
        st.error(f"Erro ao gerar caminho da imagem para {id_campeonato}: {e}")
        return None

# ===== FUNÇÕES EXISTENTES (MANTIDAS) =====

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

# ===== NOVA FUNÇÃO PARA PÁGINA DE VISÃO GERAL (COM CORREÇÃO) =====

def exibir_pagina_visao_geral(dados_competitividade, estatisticas_gerais):
    """Exibe a página de visão geral com estatísticas de todos os campeonatos."""
    st.header("📊 Visão Geral da Competitividade")
    
    if dados_competitividade is None or estatisticas_gerais is None:
        st.warning("⚠️ Não há dados de competitividade disponíveis.")
        return
    
    # Função para extrair país do ID Campeonato
    def extrair_pais_do_id(id_campeonato):
        try:
            if '@' in id_campeonato:
                # Exemplo: "albania@/football/albania/superliga-2015-2016/"
                partes = id_campeonato.split('@')[0]  # Pega a parte antes do @
                return partes.title()  # Converte para título (Albania, Austria, etc.)
        except:
            pass
        return 'N/A'
    
    # Adicionar coluna de país aos dados
    if 'ID Campeonato' in dados_competitividade.columns:
        dados_competitividade['País'] = dados_competitividade['ID Campeonato'].apply(extrair_pais_do_id)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Campeonatos Analisados",
            f"{estatisticas_gerais['total_campeonatos']}",
            help="Número total de ligas/campeonatos analisados"
        )
    
    with col2:
        st.metric(
            "Campeonatos Competitivos",
            f"{estatisticas_gerais['percentual_competitivos']:.1f}%",
            f"{estatisticas_gerais['total_campeonatos'] - (estatisticas_gerais['total_campeonatos'] * estatisticas_gerais['percentual_competitivos'] / 100):.0f} campeonatos",
            delta_color="off",
            help="Percentual de ligas consideradas competitivas"
        )
    
    with col3:
        st.metric(
            "Campeonatos Não Competitivos", 
            f"{estatisticas_gerais['percentual_nao_competitivos']:.1f}%",
            help="Percentual de ligas com dominância precoce"
        )
    
    with col4:
        if estatisticas_gerais['ponto_virada_medio']:
            st.metric(
                "Ponto de Virada Médio",
                f"{estatisticas_gerais['ponto_virada_medio']:.1f}%",
                help="Em média, quando as ligas não competitivas se tornaram previsíveis"
            )
        else:
            st.metric("Ponto de Virada Médio", "N/A")
    
    st.markdown("---")
    
    # Gráficos de distribuição
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza - Competitividade
        dados_pizza = {
            'Categoria': ['Competitivas', 'Não Competitivas'],
            'Quantidade': [
                estatisticas_gerais['total_campeonatos'] * estatisticas_gerais['percentual_competitivos'] / 100,
                estatisticas_gerais['total_campeonatos'] * estatisticas_gerais['percentual_nao_competitivos'] / 100
            ]
        }
        df_pizza = pd.DataFrame(dados_pizza)
        
        fig_pizza = px.pie(
            df_pizza, values='Quantidade', names='Categoria',
            title='Distribuição de Competitividade',
            color_discrete_map={'Competitivas': '#2E8B57', 'Não Competitivas': '#DC143C'}
        )
        fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pizza, use_container_width=True)
    
    with col2:
        # Gráfico de barras - Probabilidades médias
        probabilidades = {
            'Resultado': ['Vitória Casa', 'Empate', 'Vitória Fora'],
            'Probabilidade': [
                estatisticas_gerais['p_casa_media'],
                estatisticas_gerais['p_empate_media'], 
                estatisticas_gerais['p_fora_media']
            ]
        }
        df_prob = pd.DataFrame(probabilidades)
        
        fig_barras = px.bar(
            df_prob, x='Resultado', y='Probabilidade',
            title='Probabilidades Médias de Resultado',
            color='Resultado',
            color_discrete_map={
                'Vitória Casa': '#2E8B57',
                'Empate': '#FFD700', 
                'Vitória Fora': '#4169E1'
            }
        )
        fig_barras.update_layout(showlegend=False)
        fig_barras.update_yaxes(range=[0, 0.6])  # Para melhor visualização
        st.plotly_chart(fig_barras, use_container_width=True)
    
    # Métricas detalhadas
    st.subheader("📈 Métricas Detalhadas de Competitividade")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Variância de Forças Média",
            f"{estatisticas_gerais['variancia_forcas_media']:.4f}",
            help="Mede a dispersão média da 'força' dos times entre todas as ligas"
        )
    
    with col2:
        st.metric(
            "Desequilíbrio Final Médio", 
            f"{estatisticas_gerais['desequilibrio_final_media']:.4f}",
            help="Mede o desequilíbrio médio na classificação final"
        )
    
    with col3:
        st.metric(
            "Probabilidade Média - Vitória Casa",
            f"{estatisticas_gerais['p_casa_media']:.3f}",
            help="Chance média de vitória do time da casa"
        )
    
    with col4:
        st.metric(
            "Probabilidade Média - Empate",
            f"{estatisticas_gerais['p_empate_media']:.3f}",
            help="Chance média de empate"
        )
    
    # Tabelas de campeonatos mais e menos competitivos
    st.markdown("---")
    
    # Função auxiliar para calcular porcentagem do ponto de virada
    def calcular_porcentagem_ponto_virada(row):
        """Calcula a porcentagem da temporada em que ocorreu o ponto de virada"""
        try:
            ponto_virada = row.get('Ponto Virada (%)', None)
            if pd.notna(ponto_virada) and ponto_virada != 'N/A':
                # Se já está em formato de porcentagem (string com %)
                if isinstance(ponto_virada, str) and '%' in str(ponto_virada):
                    return float(str(ponto_virada).rstrip('%'))
                # Se é numérico, assumir que já é porcentagem
                return float(ponto_virada)
            return None
        except:
            return None
    
    # Função auxiliar para extrair liga base do ID
    def extrair_liga_base_do_id(id_campeonato):
        """Extrai o nome base da liga (sem temporada) do ID"""
        try:
            # Usar a coluna 'Liga' diretamente se disponível, ou extrair do ID
            if 'Liga' in dados_competitividade.columns:
                match = dados_competitividade[dados_competitividade['ID Campeonato'] == id_campeonato]
                if not match.empty:
                    liga_completa = match.iloc[0].get('Liga', 'N/A')
                    # Remover temporada se presente (formato: "Nome Liga - 2015/2016")
                    if ' - ' in str(liga_completa):
                        return liga_completa.split(' - ')[0]
                    return liga_completa
            # Fallback: extrair do ID usando regex
            if '@' in str(id_campeonato):
                url_part = str(id_campeonato).split('@')[1] if '@' in str(id_campeonato) else ''
                partes_url = url_part.split('/')
                if len(partes_url) >= 4 and partes_url[3]:
                    liga_completa = partes_url[3]
                    # Remover anos no final (formato: -2015-2016 ou -2015)
                    liga_base = re.sub(r'(-\d{4})+$', '', liga_completa)
                    return liga_base.replace('-', ' ').title()
            return 'N/A'
        except Exception as e:
            logger.error(f"Erro ao extrair liga base de {id_campeonato}: {e}")
            return 'N/A'
    
    # Organizar em duas colunas
    col1, col2 = st.columns(2)
    
    # TABELA 1: 5 Campeonatos Mais Competitivos (individuais)
    with col1:
        st.subheader("🏆 Top 5 Campeonatos Mais Competitivos")
        ligas_competitivas = dados_competitividade[dados_competitividade['É Competitivo'] == 'Sim'].copy()
        
        if not ligas_competitivas.empty:
            # Ordenar por menor desequilíbrio (mais competitivas)
            top_competitivas = ligas_competitivas.nsmallest(5, 'Desequilíbrio Final')
            
            # Preparar dados para a tabela
            dados_tabela_mais_comp_ind = []
            for _, liga in top_competitivas.iterrows():
                pais = liga.get('País', 'N/A')
                
                dados_tabela_mais_comp_ind.append({
                    'Liga': liga.get('Liga', 'N/A'),
                    'Temporada': liga.get('Temporada', 'N/A'),
                    'País': pais,
                    'Desequilíbrio Final': f"{liga['Desequilíbrio Final']:.4f}" if pd.notna(liga['Desequilíbrio Final']) else 'N/A'
                })
            
            df_mais_comp_ind = pd.DataFrame(dados_tabela_mais_comp_ind)
            st.dataframe(df_mais_comp_ind, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum campeonato competitivo encontrado")
    
    # TABELA 2: 5 Campeonatos Menos Competitivos (individuais)
    with col2:
        st.subheader("📉 Top 5 Campeonatos Menos Competitivos")
        ligas_nao_competitivas = dados_competitividade[dados_competitividade['É Competitivo'] == 'Não'].copy()
        
        if not ligas_nao_competitivas.empty:
            # Ordenar por maior desequilíbrio (menos competitivas)
            top_nao_competitivas = ligas_nao_competitivas.nlargest(5, 'Desequilíbrio Final')
            
            # Preparar dados para a tabela
            dados_tabela_menos_comp_ind = []
            for _, liga in top_nao_competitivas.iterrows():
                pais = liga.get('País', 'N/A')
                ponto_virada_pct = calcular_porcentagem_ponto_virada(liga)
                
                dados_tabela_menos_comp_ind.append({
                    'Liga': liga.get('Liga', 'N/A'),
                    'Temporada': liga.get('Temporada', 'N/A'),
                    'País': pais,
                    'Desequilíbrio Final': f"{liga['Desequilíbrio Final']:.4f}" if pd.notna(liga['Desequilíbrio Final']) else 'N/A',
                    'Ponto de Virada (%)': f"{ponto_virada_pct:.1f}%" if ponto_virada_pct is not None else 'N/A'
                })
            
            df_menos_comp_ind = pd.DataFrame(dados_tabela_menos_comp_ind)
            st.dataframe(df_menos_comp_ind, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum campeonato não competitivo encontrado")
    
    st.markdown("---")
    
    # TABELA ÚNICA: Todas as Ligas Agrupadas (da mais competitiva para a menos competitiva)
    st.subheader("📊 Ranking de Ligas por Competitividade")
    st.info("Ligas agrupadas e ordenadas da mais competitiva (menor desequilíbrio) para a menos competitiva (maior desequilíbrio)")
    
    # Combinar todas as ligas (competitivas e não competitivas)
    todas_ligas_agrup = dados_competitividade.copy()
    
    if not todas_ligas_agrup.empty:
        # Adicionar coluna de liga base para agrupamento
        todas_ligas_agrup['Liga Base'] = todas_ligas_agrup['ID Campeonato'].apply(extrair_liga_base_do_id)
        
        # Agrupar por liga base e país
        todas_ligas_agrup['Chave Agrupamento'] = todas_ligas_agrup.apply(
            lambda row: f"{row.get('País', 'N/A')}|||{row['Liga Base']}", axis=1
        )
        
        # Calcular médias por liga
        dados_tabela_todas_ligas = []
        for chave, grupo in todas_ligas_agrup.groupby('Chave Agrupamento'):
            pais = grupo.iloc[0].get('País', 'N/A')
            liga_nome = grupo.iloc[0]['Liga Base']
            
            # Calcular médias
            media_desequilibrio = grupo['Desequilíbrio Final'].mean()
            
            # Calcular porcentagem média do ponto de virada
            pontos_virada = []
            for _, row in grupo.iterrows():
                pct = calcular_porcentagem_ponto_virada(row)
                if pct is not None:
                    pontos_virada.append(pct)
            
            media_ponto_virada = sum(pontos_virada) / len(pontos_virada) if pontos_virada else None
            
            # Calcular estatísticas de competitividade
            total_temporadas = len(grupo)
            temporadas_competitivas = len(grupo[grupo['É Competitivo'] == 'Sim'])
            porcentagem_competitivas = (temporadas_competitivas / total_temporadas * 100) if total_temporadas > 0 else 0
            
            dados_tabela_todas_ligas.append({
                'Liga': liga_nome,
                'País': pais,
                'Média Desequilíbrio Final': media_desequilibrio,
                'Média Ponto de Virada (%)': media_ponto_virada,
                'Total Temporadas': total_temporadas,
                'Temporadas Competitivas': temporadas_competitivas,
                '% Competitivas': porcentagem_competitivas,
                '_desequilibrio_num': media_desequilibrio
            })
        
        # Ordenar por menor desequilíbrio (mais competitivas primeiro)
        if dados_tabela_todas_ligas:
            dados_tabela_ordenados = sorted(
                dados_tabela_todas_ligas, 
                key=lambda x: x['_desequilibrio_num']
            )
            
            # Formatar para exibição com ranking
            dados_formatados = []
            for idx, item in enumerate(dados_tabela_ordenados, 1):
                dados_formatados.append({
                    'Ranking': idx,
                    'Liga': item['Liga'],
                    'País': item['País'],
                    'Total Temporadas': item['Total Temporadas'],
                    'Temporadas Competitivas': item['Temporadas Competitivas'],
                    '% Competitivas': f"{item['% Competitivas']:.1f}%",
                    'Média Desequilíbrio Final': f"{item['Média Desequilíbrio Final']:.4f}",
                    'Média Ponto de Virada (%)': f"{item['Média Ponto de Virada (%)']:.1f}%" if item['Média Ponto de Virada (%)'] is not None else 'N/A'
                })
            
            df_todas_ligas = pd.DataFrame(dados_formatados)
            st.dataframe(df_todas_ligas, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma liga encontrada para agrupamento")
    else:
        st.info("Nenhuma liga encontrada")

# ===== FUNÇÃO DE COMPARAÇÃO CORRIGIDA =====

def comparar_ligas(liga1_info, liga1_dados, liga2_info, liga2_dados, dados_competitividade, estatisticas_gerais):
    """Compara duas ligas e retorna visualizações comparativas"""
    
    # Calcular estatísticas básicas
    stats_liga1 = calcular_estatisticas_gerais(liga1_dados)
    stats_liga2 = calcular_estatisticas_gerais(liga2_dados)
    
    # Obter dados de competitividade
    info_liga1 = dados_competitividade[dados_competitividade['ID Campeonato'] == liga1_info['id']]
    info_liga2 = dados_competitividade[dados_competitividade['ID Campeonato'] == liga2_info['id']]
    
    # Criar abas para diferentes tipos de comparação
    tab1, tab2, tab3 = st.tabs(["📊 Estatísticas Gerais", "📈 Competitividade", "🏆 Classificação"])
    
    with tab1:
        st.subheader("📊 Comparação de Estatísticas Gerais")
        
        if stats_liga1 and stats_liga2:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Gráfico de pizza comparativo
                fig = make_subplots(rows=1, cols=2, 
                                    specs=[[{'type':'domain'}, {'type':'domain'}]],
                                    subplot_titles=[f"{liga1_info['nome']}", f"{liga2_info['nome']}"])
                
                fig.add_trace(go.Pie(labels=['Vitórias Casa', 'Empates', 'Vitórias Fora'],
                                      values=[stats_liga1['Vitórias Casa'], stats_liga1['Empates'], stats_liga1['Vitórias Fora']],
                                      name=liga1_info['nome']), 1, 1)
                
                fig.add_trace(go.Pie(labels=['Vitórias Casa', 'Empates', 'Vitórias Fora'],
                                      values=[stats_liga2['Vitórias Casa'], stats_liga2['Empates'], stats_liga2['Vitórias Fora']],
                                      name=liga2_info['nome']), 1, 2)
                
                fig.update_traces(hole=0.4, hoverinfo="label+percent+name")
                fig.update_layout(title_text="Distribuição de Resultados", height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Métricas comparativas
                st.metric(
                    f"Total de Partidas - {liga1_info['nome']}",
                    stats_liga1['Total'],
                    delta=f"{stats_liga1['Total'] - stats_liga2['Total']}"
                )
                st.metric(
                    f"Total de Partidas - {liga2_info['nome']}",
                    stats_liga2['Total']
                )
                
                st.metric(
                    f"Vitórias Casa - {liga1_info['nome']}",
                    f"{stats_liga1['Vitórias Casa']} ({stats_liga1['Vitórias Casa']/stats_liga1['Total']*100:.1f}%)",
                    delta=f"{(stats_liga1['Vitórias Casa']/stats_liga1['Total']*100) - (stats_liga2['Vitórias Casa']/stats_liga2['Total']*100):.1f}%"
                )
                st.metric(
                    f"Vitórias Casa - {liga2_info['nome']}",
                    f"{stats_liga2['Vitórias Casa']} ({stats_liga2['Vitórias Casa']/stats_liga2['Total']*100:.1f}%)"
                )
            
            with col3:
                st.metric(
                    f"Empates - {liga1_info['nome']}",
                    f"{stats_liga1['Empates']} ({stats_liga1['Empates']/stats_liga1['Total']*100:.1f}%)",
                    delta=f"{(stats_liga1['Empates']/stats_liga1['Total']*100) - (stats_liga2['Empates']/stats_liga2['Total']*100):.1f}%"
                )
                st.metric(
                    f"Empates - {liga2_info['nome']}",
                    f"{stats_liga2['Empates']} ({stats_liga2['Empates']/stats_liga2['Total']*100:.1f}%)"
                )
                
                st.metric(
                    f"Vitórias Fora - {liga1_info['nome']}",
                    f"{stats_liga1['Vitórias Fora']} ({stats_liga1['Vitórias Fora']/stats_liga1['Total']*100:.1f}%)",
                    delta=f"{(stats_liga1['Vitórias Fora']/stats_liga1['Total']*100) - (stats_liga2['Vitórias Fora']/stats_liga2['Total']*100):.1f}%"
                )
                st.metric(
                    f"Vitórias Fora - {liga2_info['nome']}",
                    f"{stats_liga2['Vitórias Fora']} ({stats_liga2['Vitórias Fora']/stats_liga2['Total']*100:.1f}%)"
                )

    with tab2:
        st.subheader("📈 Comparação de Competitividade")
        
        if not info_liga1.empty and not info_liga2.empty:
            medias_outras_temporadas1 = calcular_medias_outras_temporadas(dados_competitividade, liga1_info['id'])
            medias_outras_temporadas2 = calcular_medias_outras_temporadas(dados_competitividade, liga2_info['id'])
            # Dados para gráfico de radar
            categorias = ['Variância Forças', 'Desequilíbrio Final', 'P(Casa)', 'P(Empate)', 'P(Fora)']
            
            valores_liga1 = [
                info_liga1.iloc[0]['Variância Forças'],
                info_liga1.iloc[0]['Desequilíbrio Final'],
                info_liga1.iloc[0]['P(Casa)'],
                info_liga1.iloc[0]['P(Empate)'],
                info_liga1.iloc[0]['P(Fora)']
            ]
            
            valores_liga2 = [
                info_liga2.iloc[0]['Variância Forças'],
                info_liga2.iloc[0]['Desequilíbrio Final'],
                info_liga2.iloc[0]['P(Casa)'],
                info_liga2.iloc[0]['P(Empate)'],
                info_liga2.iloc[0]['P(Fora)']
            ]
            
            # Gráfico de radar
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=valores_liga1,
                theta=categorias,
                fill='toself',
                name=liga1_info['nome'],
                line_color='blue'
            ))
            
            fig.add_trace(go.Scatterpolar(
                r=valores_liga2,
                theta=categorias,
                fill='toself',
                name=liga2_info['nome'],
                line_color='red'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(max(valores_liga1), max(valores_liga2)) * 1.1]
                    )),
                showlegend=True,
                title="Perfil de Competitividade - Gráfico de Radar"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Comparação da evolução de desequilíbrio ao longo da temporada
            dados_rodadas_liga1 = carregar_dados_rodadas_liga(liga1_info['id'])
            dados_rodadas_liga2 = carregar_dados_rodadas_liga(liga2_info['id'])

            if dados_rodadas_liga1 is None and dados_rodadas_liga2 is None:
                st.warning("⚠️ Dados por rodada não disponíveis para nenhuma das ligas selecionadas.")
            else:
                try:
                    fig = go.Figure()

                    # Traços para Liga 1
                    if dados_rodadas_liga1 is not None:
                        fig.add_trace(go.Scatter(
                            x=dados_rodadas_liga1['rodada'],
                            y=dados_rodadas_liga1['observed_imbalance'],
                            mode='lines+markers',
                            name=f"{liga1_info['nome']} - Desequilíbrio Observado",
                            line=dict(color='crimson', width=3),
                            marker=dict(size=5)
                        ))
                        fig.add_trace(go.Scatter(
                            x=dados_rodadas_liga1['rodada'],
                            y=dados_rodadas_liga1['envelope_upper'],
                            mode='lines',
                            name=f"{liga1_info['nome']} - Limite (95%)",
                            line=dict(color='crimson', dash='dash')
                        ))

                    # Traços para Liga 2
                    if dados_rodadas_liga2 is not None:
                        fig.add_trace(go.Scatter(
                            x=dados_rodadas_liga2['rodada'],
                            y=dados_rodadas_liga2['observed_imbalance'],
                            mode='lines+markers',
                            name=f"{liga2_info['nome']} - Desequilíbrio Observado",
                            line=dict(color='royalblue', width=3),
                            marker=dict(size=5)
                        ))
                        fig.add_trace(go.Scatter(
                            x=dados_rodadas_liga2['rodada'],
                            y=dados_rodadas_liga2['envelope_upper'],
                            mode='lines',
                            name=f"{liga2_info['nome']} - Limite (95%)",
                            line=dict(color='royalblue', dash='dash')
                        ))

                    # Zona competitiva esperada (linha y=0) usando união das rodadas disponíveis
                    rodadas_union = []
                    if dados_rodadas_liga1 is not None:
                        rodadas_union.extend(list(dados_rodadas_liga1['rodada'].astype(float)))
                    if dados_rodadas_liga2 is not None:
                        rodadas_union.extend(list(dados_rodadas_liga2['rodada'].astype(float)))
                    rodadas_union = sorted(set(rodadas_union))
                    if rodadas_union:
                        fig.add_trace(go.Scatter(
                            x=rodadas_union,
                            y=[0] * len(rodadas_union),
                            fill='tonexty',
                            mode='none',
                            name='Zona Competitiva Esperada',
                            fillcolor='rgba(173, 216, 230, 0.25)'
                        ))

                    # Pontos de virada e rodadas atuais (uma linha por liga, se existir)
                    if dados_rodadas_liga1 is not None:
                        tp1 = dados_rodadas_liga1[dados_rodadas_liga1.get('is_turning_point', False) == True]
                        if not tp1.empty:
                            rp = int(tp1.iloc[0]['rodada'])
                            fig.add_vline(x=rp, line_width=2, line_dash="dot", line_color="crimson",
                                          annotation_text=f"Ponto de Virada - {liga1_info['nome']} (R{rp})",
                                          annotation_position="top left")
                        rodada_atual_1 = int(liga1_dados['rodada'].max()) if 'rodada' in liga1_dados.columns else None
                        if rodada_atual_1 is not None:
                            fig.add_vline(x=rodada_atual_1, line_width=1, line_dash="solid", line_color="crimson",
                                          annotation_text=f"Rodada Atual {liga1_info['nome']}: R{rodada_atual_1}",
                                          annotation_position="bottom left")

                    if dados_rodadas_liga2 is not None:
                        tp2 = dados_rodadas_liga2[dados_rodadas_liga2.get('is_turning_point', False) == True]
                        if not tp2.empty:
                            rp = int(tp2.iloc[0]['rodada'])
                            fig.add_vline(x=rp, line_width=2, line_dash="dot", line_color="royalblue",
                                          annotation_text=f"Ponto de Virada - {liga2_info['nome']} (R{rp})",
                                          annotation_position="top right")
                        rodada_atual_2 = int(liga2_dados['rodada'].max()) if 'rodada' in liga2_dados.columns else None
                        if rodada_atual_2 is not None:
                            fig.add_vline(x=rodada_atual_2, line_width=1, line_dash="solid", line_color="royalblue",
                                          annotation_text=f"Rodada Atual {liga2_info['nome']}: R{rodada_atual_2}",
                                          annotation_position="bottom right")

                    fig.update_layout(
                        title_text='Evolução do Desequilíbrio vs. Modelo Nulo (Comparação)',
                        xaxis_title='Rodada',
                        yaxis_title='Desequilíbrio Normalizado',
                        legend_title='Métricas',
                        hovermode="x unified",
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico comparativo de desequilíbrio: {e}")

            # =========================================================
            # INÍCIO DA CORREÇÃO: Adicionando delta às métricas
            # =========================================================
            st.markdown("---")
            st.subheader("Métricas Finais da Temporada")

            # Métricas lado a lado
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"🏆 {liga1_info['nome']}")
                liga1_final = info_liga1.iloc[0]
                
                st.metric("Competitivo", liga1_final['É Competitivo'])
                
                st.metric(
                    "Desequilíbrio Final", 
                    f"{liga1_final['Desequilíbrio Final']:.4f}",
                    help=f"Média de todas as ligas: {estatisticas_gerais['desequilibrio_final_media']:.4f}. Valores menores indicam maior competitividade."
                )
                delta_geral = liga1_final['Desequilíbrio Final'] - estatisticas_gerais['desequilibrio_final_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['desequilibrio_final_media'],
                    delta_geral,
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas1 and pd.notna(medias_outras_temporadas1.get('desequilibrio_final_media')):
                    delta_liga = liga1_final['Desequilíbrio Final'] - medias_outras_temporadas1['desequilibrio_final_media']
                    bloco_liga = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas1['desequilibrio_final_media'],
                        delta_liga,
                        melhor_quando="menor"
                    )
                    if bloco_liga:
                        st.markdown(bloco_liga, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")

                st.metric(
                    "P(Casa)", 
                    f"{liga1_final['P(Casa)']:.3f}",
                    help=f"Média de todas as ligas: {estatisticas_gerais['p_casa_media']:.3f}"
                )
                delta_geral = liga1_final['P(Casa)'] - estatisticas_gerais['p_casa_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_casa_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas1 and pd.notna(medias_outras_temporadas1.get('p_casa_media')):
                    delta_liga = liga1_final['P(Casa)'] - medias_outras_temporadas1['p_casa_media']
                    bloco_liga = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas1['p_casa_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_liga:
                        st.markdown(bloco_liga, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")

                st.metric(
                    "P(Empate)", 
                    f"{liga1_final['P(Empate)']:.3f}",
                    help=f"Média de todas as ligas: {estatisticas_gerais['p_empate_media']:.3f}"
                )
                delta_geral = liga1_final['P(Empate)'] - estatisticas_gerais['p_empate_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_empate_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas1 and pd.notna(medias_outras_temporadas1.get('p_empate_media')):
                    delta_liga = liga1_final['P(Empate)'] - medias_outras_temporadas1['p_empate_media']
                    bloco_liga = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas1['p_empate_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_liga:
                        st.markdown(bloco_liga, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")

                st.metric(
                    "P(Fora)", 
                    f"{liga1_final['P(Fora)']:.3f}",
                    help=f"Média de todas as ligas: {estatisticas_gerais['p_fora_media']:.3f}"
                )
                delta_geral = liga1_final['P(Fora)'] - estatisticas_gerais['p_fora_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_fora_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas1 and pd.notna(medias_outras_temporadas1.get('p_fora_media')):
                    delta_liga = liga1_final['P(Fora)'] - medias_outras_temporadas1['p_fora_media']
                    bloco_liga = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas1['p_fora_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_liga:
                        st.markdown(bloco_liga, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")
            
            with col2:
                st.subheader(f"🏆 {liga2_info['nome']}")
                liga2_final = info_liga2.iloc[0]

                st.metric("Competitivo", liga2_final['É Competitivo'])
                
                st.metric(
                    "Desequilíbrio Final", 
                    f"{liga2_final['Desequilíbrio Final']:.4f}",
                    help=f"Média de todas as ligas: {estatisticas_gerais['desequilibrio_final_media']:.4f}. Valores menores indicam maior competitividade."
                )
                delta_geral = liga2_final['Desequilíbrio Final'] - estatisticas_gerais['desequilibrio_final_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['desequilibrio_final_media'],
                    delta_geral,
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas2 and pd.notna(medias_outras_temporadas2.get('desequilibrio_final_media')):
                    delta_liga = liga2_final['Desequilíbrio Final'] - medias_outras_temporadas2['desequilibrio_final_media']
                    bloco_liga = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas2['desequilibrio_final_media'],
                        delta_liga,
                        melhor_quando="menor"
                    )
                    if bloco_liga:
                        st.markdown(bloco_liga, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")

                st.metric(
                    "P(Casa)", 
                    f"{liga2_final['P(Casa)']:.3f}",
                    help=f"Média de todas as ligas: {estatisticas_gerais['p_casa_media']:.3f}"
                )
                delta_geral = liga2_final['P(Casa)'] - estatisticas_gerais['p_casa_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_casa_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas2 and pd.notna(medias_outras_temporadas2.get('p_casa_media')):
                    delta_liga = liga2_final['P(Casa)'] - medias_outras_temporadas2['p_casa_media']
                    bloco_liga = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas2['p_casa_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_liga:
                        st.markdown(bloco_liga, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")

                st.metric(
                    "P(Empate)", 
                    f"{liga2_final['P(Empate)']:.3f}",
                    help=f"Média de todas as ligas: {estatisticas_gerais['p_empate_media']:.3f}"
                )
                delta_geral = liga2_final['P(Empate)'] - estatisticas_gerais['p_empate_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_empate_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas2 and pd.notna(medias_outras_temporadas2.get('p_empate_media')):
                    delta_liga = liga2_final['P(Empate)'] - medias_outras_temporadas2['p_empate_media']
                    bloco_liga = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas2['p_empate_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_liga:
                        st.markdown(bloco_liga, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")

                st.metric(
                    "P(Fora)", 
                    f"{liga2_final['P(Fora)']:.3f}",
                    help=f"Média de todas as ligas: {estatisticas_gerais['p_fora_media']:.3f}"
                )
                delta_geral = liga2_final['P(Fora)'] - estatisticas_gerais['p_fora_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_fora_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas2 and pd.notna(medias_outras_temporadas2.get('p_fora_media')):
                    delta_liga = liga2_final['P(Fora)'] - medias_outras_temporadas2['p_fora_media']
                    bloco_liga = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas2['p_fora_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_liga:
                        st.markdown(bloco_liga, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")
            # =========================================================
            # FIM DA CORREÇÃO
            # =========================================================

    with tab3:
        st.subheader("🏆 Comparação de Classificação")
        
        classificacao_liga1 = calcular_classificacao(liga1_dados)
        classificacao_liga2 = calcular_classificacao(liga2_dados)
        
        if not classificacao_liga1.empty and not classificacao_liga2.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"{liga1_info['nome']}")
                classificacao_exibicao1 = classificacao_liga1.rename(columns={
                    'Pos': '🏆 Pos', 'Time': '🏃‍♂️ Time', 'Jogos': '⚽ Jogos', 'Vitórias': '✅ Vitórias',
                    'Empates': '🤝 Empates', 'Derrotas': '❌ Derrotas', 'Gols Marcados': '⚽ GM',
                    'Gols Sofridos': '🥅 GS', 'Saldo de Gols': '📊 SG', 'Pontos': '🏅 Pontos'
                })
                st.dataframe(classificacao_exibicao1, hide_index=True, use_container_width=True)
            
            with col2:
                st.subheader(f"{liga2_info['nome']}")
                classificacao_exibicao2 = classificacao_liga2.rename(columns={
                    'Pos': '🏆 Pos', 'Time': '🏃‍♂️ Time', 'Jogos': '⚽ Jogos', 'Vitórias': '✅ Vitórias',
                    'Empates': '🤝 Empates', 'Derrotas': '❌ Derrotas', 'Gols Marcados': '⚽ GM',
                    'Gols Sofridos': '🥅 GS', 'Saldo de Gols': '📊 SG', 'Pontos': '🏅 Pontos'
                })
                st.dataframe(classificacao_exibicao2, hide_index=True, use_container_width=True)
                
            # Comparação de pontos do campeão
            pontos_campeao_liga1 = classificacao_liga1.iloc[0]['Pontos']
            pontos_campeao_liga2 = classificacao_liga2.iloc[0]['Pontos']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    f"Campeão {liga1_info['nome']}",
                    classificacao_liga1.iloc[0]['Time'],
                    f"{pontos_campeao_liga1} pontos"
                )
            with col2:
                st.metric(
                    f"Campeão {liga2_info['nome']}",
                    classificacao_liga2.iloc[0]['Time'],
                    f"{pontos_campeao_liga2} pontos"
                )
            with col3:
                st.metric(
                    "Diferença de Pontos",
                    f"{abs(pontos_campeao_liga1 - pontos_campeao_liga2)}",
                    "pontos entre campeões"
                )

# ===== FUNÇÃO DE VISÃO INDIVIDUAL CORRIGIDA =====

# ===== FUNÇÃO DE VISÃO INDIVIDUAL CORRIGIDA =====

def exibir_visao_individual(liga_selecionada, temporada_selecionada, id_selecionado, dados_filtrados, dados_competitividade, estatisticas_gerais):
    """
    Exibe a visão individual da liga com abas organizadas, carregando dados de
    competitividade por rodada sob demanda e comparando com a média geral.
    """
    
    # --- Cálculos Iniciais ---
    classificacao = calcular_classificacao(dados_filtrados)
    estatisticas = calcular_estatisticas_gerais(dados_filtrados)
    info_campeonato = dados_competitividade[dados_competitividade['ID Campeonato'] == id_selecionado] if dados_competitividade is not None else pd.DataFrame()
    
    # --- Estrutura das Abas ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Estatísticas Gerais", 
        "📈 Competitividade", 
        "🏆 Classificação", 
        "🗓️ Jogos da Temporada"
    ])

    # ABA 1: ESTATÍSTICAS GERAIS
    with tab1:
        st.subheader("📊 Estatísticas Gerais")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total de Partidas", len(dados_filtrados))
        with col2:
            times_disponiveis = sorted(set(list(dados_filtrados['home'].unique()) + list(dados_filtrados['away'].unique())))
            st.metric("🏟️ Número de Times", len(times_disponiveis))
        with col3:
            if not classificacao.empty:
                campeao = classificacao.iloc[0]['Time']
                st.metric("🏆 Campeão (Parcial)", campeao, help="Campeão considerando apenas as rodadas e times filtrados.")
            else:
                st.metric("🏆 Campeão (Parcial)", "Não disponível")
        with col4:
            if not classificacao.empty:
                pontos_campeao = classificacao.iloc[0]['Pontos']
                st.metric("🏅 Pontos do Campeão (Parcial)", pontos_campeao)
            else:
                st.metric("🏅 Pontos do Campeão (Parcial)", "N/A")
        
        if estatisticas and estatisticas['Total'] > 0:
            st.markdown("---")
            st.subheader("📈 Distribuição de Resultados")
            dados_pizza = {
                'Resultado': ['Vitórias Casa', 'Empates', 'Vitórias Fora'],
                'Quantidade': [estatisticas['Vitórias Casa'], estatisticas['Empates'], estatisticas['Vitórias Fora']]
            }
            df_pizza = pd.DataFrame(dados_pizza)
            fig = px.pie(
                df_pizza, values='Quantidade', names='Resultado',
                title='Distribuição de Resultados (com base nos filtros)',
                color_discrete_map={'Vitórias Casa': '#2E8B57', 'Empates': '#FFD700', 'Vitórias Fora': '#4169E1'}
            )
            fig.update_traces(textposition='inside', textinfo='percent+label', hole=0.3)
            fig.update_layout(showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Não há dados suficientes para gerar o gráfico de distribuição.")

    # ABA 2: COMPETITIVIDADE
    with tab2:
        st.subheader("📈 Análise de Competitividade")
        dados_compet_liga = carregar_dados_rodadas_liga(id_selecionado)

        if dados_compet_liga is None:
            st.warning("⚠️ Dados de competitividade por rodada não foram encontrados. A análise pode não ter sido executada para este campeonato.")
        else:
            rodada_atual = int(dados_filtrados['rodada'].max()) if not dados_filtrados.empty else int(dados_compet_liga['rodada'].max())
            metricas_rodada = dados_compet_liga[dados_compet_liga['rodada'] == rodada_atual]

            st.markdown("##### Métricas da Rodada Atual (Filtro)")
            col1, col2, col3 = st.columns(3)
            with col1:
                if not metricas_rodada.empty:
                    desequilibrio_atual = metricas_rodada.iloc[0]['observed_imbalance']
                    st.metric(f"Desequilíbrio na Rodada {rodada_atual}", f"{desequilibrio_atual:.4f}", help="Variância normalizada dos pontos na classificação até esta rodada.")
                else:
                    st.metric(f"Desequilíbrio na Rodada {rodada_atual}", "N/A")
            
            with col2:
                if not metricas_rodada.empty:
                    limite_confianca = metricas_rodada.iloc[0]['envelope_upper']
                    st.metric(f"Limite de Confiança na Rodada {rodada_atual}", f"{limite_confianca:.4f}", help="Limite superior do envelope de confiança de 95% das simulações.")
                else:
                    st.metric(f"Limite de Confiança na Rodada {rodada_atual}", "N/A")

            with col3:
                if not info_campeonato.empty:
                    status_final = info_campeonato.iloc[0]['É Competitivo']
                    st.metric("Status Final da Liga", "Competitivo" if status_final == 'Sim' else "Não Competitivo", help="Resultado final da análise da temporada completa.")
                else:
                    st.metric("Status Final da Liga", "N/A")

            st.markdown("---")
            st.subheader("Evolução do Desequilíbrio vs. Modelo Nulo")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dados_compet_liga['rodada'], y=dados_compet_liga['observed_imbalance'], mode='lines+markers', name='Desequilíbrio Observado', line=dict(color='red', width=3), marker=dict(size=5)))
            fig.add_trace(go.Scatter(x=dados_compet_liga['rodada'], y=dados_compet_liga['envelope_upper'], mode='lines', name='Limite de Confiança (95%)', line=dict(color='blue', dash='dash')))
            fig.add_trace(go.Scatter(x=dados_compet_liga['rodada'], y=[0] * len(dados_compet_liga), fill='tonexty', mode='none', name='Zona Competitiva Esperada', fillcolor='rgba(173, 216, 230, 0.3)'))
            ponto_virada_info = dados_compet_liga[dados_compet_liga['is_turning_point'] == True]
            if not ponto_virada_info.empty:
                ponto_virada_rodada = ponto_virada_info.iloc[0]['rodada']
                fig.add_vline(x=ponto_virada_rodada, line_width=2, line_dash="dot", line_color="firebrick", annotation_text=f"Ponto de Virada (Rodada {ponto_virada_rodada})", annotation_position="top left")
            fig.add_vline(x=rodada_atual, line_width=2, line_dash="solid", line_color="green", annotation_text=f"Rodada Atual: {rodada_atual}", annotation_position="bottom right")
            fig.update_layout(title_text='Análise de Competitividade Rodada a Rodada', xaxis_title='Rodada', yaxis_title='Desequilíbrio Normalizado', legend_title='Métricas', hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("---")
        
        # =========================================================
        # CORREÇÃO: Adicionando P(Vitória Visitante) com comparativo
        # =========================================================
        st.subheader("Métricas Finais da Temporada (vs. Média Geral)")
        st.info("As métricas abaixo referem-se ao resultado final da temporada e são comparadas com a média geral e com a média das demais temporadas deste campeonato.")
        
        if not info_campeonato.empty and estatisticas_gerais is not None:
            liga_final = info_campeonato.iloc[0]
            medias_outras_temporadas = calcular_medias_outras_temporadas(dados_competitividade, id_selecionado)
            
            # Usar 4 colunas para incluir P(Vitória Visitante)
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Desequilíbrio Final", 
                    f"{liga_final['Desequilíbrio Final']:.4f}",
                    help="Diferença entre a liga e as referências gerais e históricas."
                )
                delta_geral = liga_final['Desequilíbrio Final'] - estatisticas_gerais['desequilibrio_final_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['desequilibrio_final_media'],
                    delta_geral,
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas and pd.notna(medias_outras_temporadas.get('desequilibrio_final_media')):
                    delta_liga = liga_final['Desequilíbrio Final'] - medias_outras_temporadas['desequilibrio_final_media']
                    bloco_outras = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas['desequilibrio_final_media'],
                        delta_liga,
                        melhor_quando="menor"
                    )
                    if bloco_outras:
                        st.markdown(bloco_outras, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")
            with col2:
                st.metric(
                    "P(Vitória Mandante)", 
                    f"{liga_final['P(Casa)']:.3f}"
                )
                delta_geral = liga_final['P(Casa)'] - estatisticas_gerais['p_casa_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_casa_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas and pd.notna(medias_outras_temporadas.get('p_casa_media')):
                    delta_liga = liga_final['P(Casa)'] - medias_outras_temporadas['p_casa_media']
                    bloco_outras = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas['p_casa_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_outras:
                        st.markdown(bloco_outras, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")
            with col3:
                st.metric(
                    "P(Empate)", 
                    f"{liga_final['P(Empate)']:.3f}"
                )
                delta_geral = liga_final['P(Empate)'] - estatisticas_gerais['p_empate_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_empate_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas and pd.notna(medias_outras_temporadas.get('p_empate_media')):
                    delta_liga = liga_final['P(Empate)'] - medias_outras_temporadas['p_empate_media']
                    bloco_outras = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas['p_empate_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_outras:
                        st.markdown(bloco_outras, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")
            with col4:
                st.metric(
                    "P(Vitória Visitante)", 
                    f"{liga_final['P(Fora)']:.3f}"
                )
                delta_geral = liga_final['P(Fora)'] - estatisticas_gerais['p_fora_media']
                bloco_geral = gerar_bloco_comparacao(
                    "Média geral",
                    estatisticas_gerais['p_fora_media'],
                    delta_geral,
                    formato_valor="{:.3f}",
                    formato_delta="{:+.3f}",
                    melhor_quando="menor"
                )
                if bloco_geral:
                    st.markdown(bloco_geral, unsafe_allow_html=True)
                if medias_outras_temporadas and pd.notna(medias_outras_temporadas.get('p_fora_media')):
                    delta_liga = liga_final['P(Fora)'] - medias_outras_temporadas['p_fora_media']
                    bloco_outras = gerar_bloco_comparacao(
                        "Média outras temporadas",
                        medias_outras_temporadas['p_fora_media'],
                        delta_liga,
                        formato_valor="{:.3f}",
                        formato_delta="{:+.3f}",
                        melhor_quando="menor"
                    )
                    if bloco_outras:
                        st.markdown(bloco_outras, unsafe_allow_html=True)
                else:
                    st.caption("Sem histórico suficiente para comparação interna.")
        else:
            st.warning("⚠️ Métricas finais não disponíveis para comparação.")

        # =========================================================
        # FIM DA CORREÇÃO
        # =========================================================

        st.markdown("---")
        st.markdown("#### 🏆 Definição de Posições (Temporada Completa)")
        st.info("As métricas abaixo referem-se ao resultado final da temporada, não ao filtro de rodada.")
        
        if not info_campeonato.empty:
            has_position_data = any(col in info_campeonato.columns for col in ['Campeão (Rodada)', 'Vice (Rodada)', '3º Lugar (Rodada)', '4º Lugar (Rodada)'])
            
            if has_position_data:
                st.markdown("##### 🥇 Primeiras 4 Posições")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    champion_round = info_campeonato.iloc[0].get('Campeão (Rodada)', 'N/A')
                    if champion_round != 'N/A' and not pd.isna(champion_round):
                        champion_percent = (champion_round / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                        st.metric("🏆 Campeão", f"Rodada {int(champion_round)}", delta=f"{champion_percent:.1f}% da temporada", help="Rodada em que o campeão foi matematicamente definido")
                    else:
                        st.metric("🏆 Campeão", "N/A")
                
                with col2:
                    vice_round = info_campeonato.iloc[0].get('Vice (Rodada)', 'N/A')
                    if vice_round != 'N/A' and not pd.isna(vice_round):
                        vice_percent = (vice_round / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                        st.metric("🥈 Vice-Campeão", f"Rodada {int(vice_round)}", delta=f"{vice_percent:.1f}% da temporada", help="Rodada em que o vice-campeão foi matematicamente definido")
                    else:
                        st.metric("🥈 Vice-Campeão", "N/A")
                
                with col3:
                    third_round = info_campeonato.iloc[0].get('3º Lugar (Rodada)', 'N/A')
                    if third_round != 'N/A' and not pd.isna(third_round):
                        third_percent = (third_round / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                        st.metric("🥉 3º Lugar", f"Rodada {int(third_round)}", delta=f"{third_percent:.1f}% da temporada", help="Rodada em que o 3º lugar foi matematicamente definido")
                    else:
                        st.metric("🥉 3º Lugar", "N/A")
                
                with col4:
                    fourth_round = info_campeonato.iloc[0].get('4º Lugar (Rodada)', 'N/A')
                    if fourth_round != 'N/A' and not pd.isna(fourth_round):
                        fourth_percent = (fourth_round / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                        st.metric("🏅 4º Lugar", f"Rodada {int(fourth_round)}", delta=f"{fourth_percent:.1f}% da temporada", help="Rodada em que o 4º lugar foi matematicamente definido")
                    else:
                        st.metric("🏅 4º Lugar", "N/A")

            st.markdown("##### ⬇️ Últimas Posições (Rebaixamento)")
            relegation_cols = [col for col in info_campeonato.columns if col.startswith('Posição ') and col.endswith(' (Rodada)')]
            relegation_map = {}
            for col in relegation_cols:
                parts = col.split()
                if len(parts) < 2: continue
                try: pos_num = int(parts[1])
                except Exception: continue
                round_val = info_campeonato.iloc[0].get(col, 'N/A')
                if pd.isna(round_val) or str(round_val) == 'N/A' or round_val == '': continue
                try: round_val_num = int(float(round_val))
                except Exception: continue
                relegation_map[pos_num] = round_val_num

            if relegation_map:
                sorted_positions = sorted(relegation_map.keys(), reverse=True)
                top_positions = sorted_positions[:4]
                num_cols = min(4, len(top_positions))
                if num_cols > 0:
                    cols = st.columns(num_cols)
                    for i, pos in enumerate(top_positions):
                        round_val = relegation_map.get(pos)
                        with cols[i]:
                            if round_val is not None:
                                round_percent = (round_val / int(info_campeonato.iloc[0]['Rodadas'])) * 100
                                st.metric(f"Posição {pos}", f"Rodada {round_val}", delta=f"{round_percent:.1f}% da temporada", help=f"Rodada em que a posição {pos} foi matematicamente definida")
                            else:
                                st.metric(f"Posição {pos}", "N/A")
            else:
                st.info("ℹ️ Não há dados disponíveis sobre as últimas posições (rebaixamento).")
        else:
            st.warning("⚠️ Não há dados de competitividade disponíveis para esta liga.")

    # ABA 3: CLASSIFICAÇÃO
    with tab3:
        st.subheader("🏆 Classificação")
        if not classificacao.empty:
            colunas_renomeadas = {
                'Pos': '🏆 Pos', 'Time': '🏃‍♂️ Time', 'Jogos': '⚽ Jogos', 'Vitórias': '✅ Vitórias',
                'Empates': '🤝 Empates', 'Derrotas': '❌ Derrotas', 'Gols Marcados': '⚽ GM',
                'Gols Sofridos': '🥅 GS', 'Saldo de Gols': '📊 SG', 'Pontos': '🏅 Pontos'
            }
            classificacao_exibicao = classificacao.rename(columns=colunas_renomeadas)
            st.dataframe(classificacao_exibicao, hide_index=True, use_container_width=True)
            
            csv_classificacao = classificacao_exibicao.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download da Classificação (CSV)", data=csv_classificacao,
                file_name=f"classificacao_{liga_selecionada.lower().replace(' ', '_')}_{temporada_selecionada.replace('/', '_')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Não foi possível calcular a classificação com os dados disponíveis.")
    
    # ABA 4: JOGOS DA TEMPORADA
    with tab4:
        st.subheader("🗓️ Jogos da Temporada")
        colunas_exibicao = ['rodada', 'date', 'home', 'away', 'result']
        dados_exibicao = dados_filtrados[colunas_exibicao].copy()
        
        if pd.api.types.is_datetime64_any_dtype(dados_exibicao['date']):
            dados_exibicao['date'] = dados_exibicao['date'].dt.strftime('%d/%m/%Y')
        
        colunas_renomeadas = {
            'rodada': '🗓️ Rodada', 'date': '📅 Data', 'home': '🏠 Casa', 
            'away': '✈️ Fora', 'result': '⚽ Resultado'
        }
        dados_exibicao = dados_exibicao.rename(columns=colunas_renomeadas)
        
        st.dataframe(dados_exibicao, hide_index=True, use_container_width=True)
        
        csv_partidas = dados_exibicao.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download das Partidas (CSV)", data=csv_partidas,
            file_name=f"partidas_{liga_selecionada.lower().replace(' ', '_')}_{temporada_selecionada.replace('/', '_')}.csv",
            mime="text/csv"
        )

# ===== SIDEBAR E LÓGICA PRINCIPAL =====
st.sidebar.header("🎯 Configurações")

modo_navegacao = st.sidebar.radio(
    "🔍 Modo de Navegação",
    ["📊 Visão Geral", "🏆 Liga Individual", "🔀 Comparar Ligas"],
    help="Escolha entre visão geral, análise individual ou comparação de ligas"
)

dados_competitividade = carregar_dados_competitividade()
estatisticas_gerais = calcular_estatisticas_gerais_competitividade(dados_competitividade)

esporte = st.sidebar.selectbox(
    "Selecione o Esporte",
    ["Football", "Basketball"],
    help="Escolha o esporte para visualizar os dados"
)

@st.cache_data
def carregar_dados_esporte(esporte):
    """Carrega os dados do esporte selecionado"""
    try:
        caminho = f"data/5_matchdays/{esporte.lower()}.csv"
        dados = pd.read_csv(caminho)
        if 'date' in dados.columns:
            dados['date'] = pd.to_datetime(dados['date'], errors='coerce')
        return dados
    except FileNotFoundError:
        st.error(f"Arquivo de dados não encontrado para {esporte} no caminho esperado: {caminho}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar dados do {esporte}: {e}")
        return None

def gerar_nome_arquivo_rodadas(championship_id: str) -> str:
    """Gera o nome do arquivo de dados por rodada a partir do ID do campeonato."""
    id_limpo = championship_id.replace('/', '_').replace('@', '_')
    return f"round_data_{id_limpo}.csv"

@st.cache_data
def carregar_dados_rodadas_liga(championship_id: str):
    """Carrega os dados de competitividade de uma liga específica sob demanda."""
    if not championship_id:
        return None
    try:
        nome_arquivo = gerar_nome_arquivo_rodadas(championship_id)
        caminho = f"data/6_analysis_optimized/{nome_arquivo}"
        dados = pd.read_csv(caminho)
        logger.info(f"Dados de rodada carregados para {championship_id} de {caminho}")
        return dados
    except FileNotFoundError:
        st.warning(f"Arquivo de dados por rodada não encontrado para esta liga. A análise pode não ter sido concluída para ela.")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de rodada para {championship_id}: {e}")
        return None

def calcular_medias_outras_temporadas(dados_competitividade: pd.DataFrame, championship_id: str):
    """
    Calcula a média das métricas de competitividade para outras temporadas do mesmo campeonato.
    Retorna None caso não existam temporadas adicionais para comparação.
    """
    if dados_competitividade is None or dados_competitividade.empty or not championship_id:
        return None
    
    try:
        info_atual = extrair_info_campeonato(championship_id)
        liga_base_atual = info_atual.get('liga_base') if info_atual else None
        
        if not liga_base_atual or liga_base_atual == 'N/A':
            return None
        
        dados_aux = dados_competitividade.copy()
        dados_aux['_liga_base'] = dados_aux['ID Campeonato'].apply(
            lambda x: extrair_info_campeonato(x).get('liga_base', 'N/A')
        )
        
        dados_mesma_liga = dados_aux[
            (dados_aux['_liga_base'] == liga_base_atual) &
            (dados_aux['ID Campeonato'] != championship_id)
        ]
        
        if dados_mesma_liga.empty:
            return None
        
        return {
            'desequilibrio_final_media': dados_mesma_liga['Desequilíbrio Final'].mean(),
            'p_casa_media': dados_mesma_liga['P(Casa)'].mean(),
            'p_empate_media': dados_mesma_liga['P(Empate)'].mean(),
            'p_fora_media': dados_mesma_liga['P(Fora)'].mean(),
        }
    except Exception as e:
        logger.error(f"Erro ao calcular médias de outras temporadas para {championship_id}: {e}")
        return None

def gerar_bloco_comparacao(
    rotulo: str,
    valor_referencia,
    delta,
    formato_valor: str = "{:.4f}",
    formato_delta: str = "{:+.4f}",
    melhor_quando: str = "menor"
):
    """
    Gera um bloco HTML colorido para destacar comparações de métricas.
    
    Parâmetros:
        rotulo: identificação do valor de referência.
        valor_referencia: valor numérico que servirá como comparação.
        delta: diferença entre o valor atual e a referência (valor_atual - valor_referencia).
        formato_valor: formato aplicado ao valor de referência.
        formato_delta: formato aplicado ao delta.
        melhor_quando: define a direção considerada melhor ("menor" ou "maior").
    """
    if (
        valor_referencia is None or pd.isna(valor_referencia) or
        delta is None or pd.isna(delta)
    ):
        return None
    
    if melhor_quando == "maior":
        melhor = delta > 0
    else:
        melhor = delta < 0
    
    cor_fundo = "rgba(46, 204, 113, 0.22)" if melhor else "rgba(231, 76, 60, 0.18)"
    cor_borda = "rgba(39, 174, 96, 0.5)" if melhor else "rgba(192, 57, 43, 0.45)"
    
    valor_fmt = formato_valor.format(valor_referencia)
    delta_fmt = formato_delta.format(delta)
    
    return (
        "<div style='background:{bg}; border-left:4px solid {border}; padding:0.45rem 0.75rem;"
        " border-radius:0.45rem; margin-top:0.45rem; color:#fff;'>"
        "<strong>{rotulo}:</strong> {valor} "
        "<span style=\"color:#fff;\">({delta} vs temporada atual)</span>"
        "</div>"
    ).format(bg=cor_fundo, border=cor_borda, rotulo=rotulo, valor=valor_fmt, delta=delta_fmt)

dados_esporte = carregar_dados_esporte(esporte)

if dados_esporte is None:
    st.stop()

def extrair_info_campeonato(id_campeonato):
    """Extrai informações de liga e temporada do ID do campeonato"""
    try:
        if '@' in id_campeonato:
            liga_part, url_part = id_campeonato.split('@', 1)
        else:
            liga_part = id_campeonato
            url_part = ''
        
        pais = 'N/A'
        liga_nome = 'N/A'
        divisao = 'N/A'
        liga_base = 'N/A'
        
        if url_part:
            partes_url = url_part.split('/')
            if len(partes_url) >= 3 and partes_url[2]:
                pais = partes_url[2].title()
            
            if len(partes_url) >= 4 and partes_url[3]:
                liga_completa = partes_url[3]
                # Remover todos os anos no final (formato: -2015-2016 ou -2015)
                # Remove qualquer sequência de hífen seguido de 4 dígitos no final
                liga_base = re.sub(r'(-\d{4})+$', '', liga_completa)
                liga_nome = liga_base.replace('-', ' ').title()
                
                liga_lower = liga_base.lower()
                if any(x in liga_lower for x in ['serie-a', 'premier', 'primera', 'bundesliga', 'ligue-1', 'eredivisie', 'primeira-liga']):
                    divisao = 'Primeira Divisão'
                elif any(x in liga_lower for x in ['serie-b', 'championship', 'segunda', '2-bundesliga', 'ligue-2']):
                    divisao = 'Segunda Divisão'
                elif any(x in liga_lower for x in ['serie-c', 'league-one', 'tercera']):
                    divisao = 'Terceira Divisão'
                elif any(x in liga_lower for x in ['serie-d', 'league-two']):
                    divisao = 'Quarta Divisão'
                else:
                    divisao = ''
            
            anos = re.findall(r'\d{4}', url_part)
            if anos:
                if len(anos) >= 2:
                    temporada = f"{anos[0]}/{anos[1]}"
                else:
                    temporada = anos[0]
            else:
                anos_liga = re.findall(r'\d{4}', liga_completa)
                if anos_liga:
                    temporada = anos_liga[0]
                else:
                    temporada = 'N/A'
        else:
            temporada = 'N/A'
        
        if pais != 'N/A' and liga_nome != 'N/A':
            if divisao:
                nome_exibicao = f"{pais} - {divisao} ({liga_nome})"
            else:
                nome_exibicao = f"{pais} - {liga_nome}"
        elif liga_nome != 'N/A':
            nome_exibicao = liga_nome
        else:
            nome_exibicao = liga_part.replace('-', ' ').title()
        
        return {
            'original_id': id_campeonato,
            'liga': nome_exibicao,
            'liga_base': liga_base,
            'pais': pais,
            'divisao': divisao,
            'temporada': temporada,
            'url_part': url_part
        }
    except Exception as e:
        st.error(f"Erro ao processar {id_campeonato}: {e}")
        return {
            'original_id': id_campeonato, 'liga': id_campeonato.replace('-', ' ').title(),
            'liga_base': 'N/A', 'pais': 'N/A', 'divisao': 'N/A',
            'temporada': 'N/A', 'url_part': ''
        }

if modo_navegacao == "📊 Visão Geral":
    exibir_pagina_visao_geral(dados_competitividade, estatisticas_gerais)
else:
    if 'id' in dados_esporte.columns:
        campeonatos_disponiveis = dados_esporte['id'].dropna().unique()
        
        campeonatos_info = [info for campeonato in campeonatos_disponiveis if (info := extrair_info_campeonato(campeonato))]
        
        df_ligas = pd.DataFrame(campeonatos_info)
        
        if not df_ligas.empty:
            paises_disponiveis = sorted([p for p in df_ligas['pais'].unique() if p != 'N/A'])
            
            if modo_navegacao == "🏆 Liga Individual":
                if paises_disponiveis:
                    pais_selecionado = st.sidebar.selectbox('🌍 Selecione o País', ['Todos'] + paises_disponiveis)
                else:
                    pais_selecionado = 'Todos'
                    st.sidebar.info("ℹ️ Nenhum país identificado nos dados")
                
                ligas_filtradas = df_ligas if pais_selecionado == 'Todos' else df_ligas[df_ligas['pais'] == pais_selecionado]
                
                # Agrupar ligas por liga_base, divisao e pais para evitar duplicatas de temporadas
                # Criar um grupo único para cada combinação
                ligas_filtradas['grupo_liga'] = ligas_filtradas.apply(
                    lambda row: f"{row['pais']}|||{row['divisao']}|||{row['liga_base']}", axis=1
                )
                
                # Criar um DataFrame com uma entrada única por liga (sem temporada)
                ligas_unicas = ligas_filtradas.groupby('grupo_liga').first().reset_index()
                ligas_unicas = ligas_unicas.sort_values(['divisao', 'liga_base', 'pais'])
                
                # Criar lista de ligas disponíveis usando o campo 'liga' (que não inclui temporada)
                ligas_disponiveis = sorted(ligas_unicas['liga'].unique())
                
                if ligas_disponiveis:
                    liga_selecionada = st.sidebar.selectbox('🏆 Selecione a Liga', ligas_disponiveis)
                    liga_info = ligas_unicas[ligas_unicas['liga'] == liga_selecionada].iloc[0]
                    
                    # Buscar todas as temporadas para esta liga usando os campos de agrupamento
                    temporadas_disponiveis = ligas_filtradas[
                        (ligas_filtradas['liga_base'] == liga_info['liga_base']) & 
                        (ligas_filtradas['divisao'] == liga_info['divisao']) &
                        (ligas_filtradas['pais'] == liga_info['pais'])
                    ]['temporada'].unique()
                    
                    if len(temporadas_disponiveis) > 0:
                        temporada_selecionada = st.sidebar.selectbox('📅 Selecione a Temporada', sorted(temporadas_disponiveis, reverse=True))
                        
                        liga_temporada = ligas_filtradas[
                            (ligas_filtradas['liga_base'] == liga_info['liga_base']) &
                            (ligas_filtradas['divisao'] == liga_info['divisao']) &
                            (ligas_filtradas['pais'] == liga_info['pais']) &
                            (ligas_filtradas['temporada'] == temporada_selecionada)
                        ]
                        
                        if not liga_temporada.empty:
                            id_selecionado = liga_temporada.iloc[0]['original_id']
                            st.header(f"🏆 {liga_selecionada} - {temporada_selecionada}")
                            st.sidebar.markdown("---")
                            st.sidebar.subheader("🔍 Filtros")
                            
                            dados_filtrados = dados_esporte[dados_esporte['id'] == id_selecionado].copy()
                            
                            if not dados_filtrados.empty:
                                rodadas_disponiveis = sorted(dados_filtrados['rodada'].unique())
                                
                                if len(rodadas_disponiveis) > 0:
                                    rodada_min, rodada_max = int(rodadas_disponiveis[0]), int(rodadas_disponiveis[-1])
                                    rodadas_selecionadas = st.sidebar.slider(
                                        "🗓️ Filtro de Rodadas",
                                        min_value=rodada_min, max_value=rodada_max,
                                        value=(rodada_min, rodada_max),
                                        help="Selecione o intervalo de rodadas para filtrar"
                                    )
                                    
                                    dados_filtrados = dados_filtrados[
                                        (dados_filtrados['rodada'] >= rodadas_selecionadas[0]) &
                                        (dados_filtrados['rodada'] <= rodadas_selecionadas[1])
                                    ]
                                
                                times_disponiveis = sorted(set(list(dados_filtrados['home'].unique()) + list(dados_filtrados['away'].unique())))
                                time_filtro = st.sidebar.selectbox("🏃‍♂️ Filtrar por Time", ["Todos"] + times_disponiveis)
                                
                                if time_filtro != "Todos":
                                    dados_filtrados = dados_filtrados[(dados_filtrados['home'] == time_filtro) | (dados_filtrados['away'] == time_filtro)]
                                
                                if len(rodadas_disponiveis) > 0:
                                    st.sidebar.info(f"📊 Mostrando {len(dados_filtrados)} partidas das rodadas {rodadas_selecionadas[0]} a {rodadas_selecionadas[1]}")
                                
                                exibir_visao_individual(liga_selecionada, temporada_selecionada, id_selecionado, dados_filtrados, dados_competitividade, estatisticas_gerais)
                            else:
                                st.warning("⚠️ Nenhuma partida encontrada para esta seleção.")
                        else:
                            st.error("❌ Não foi possível encontrar dados para esta liga e temporada.")
                    else:
                        st.sidebar.warning("⚠️ Nenhuma temporada disponível para esta liga.")
                else:
                    st.sidebar.warning("⚠️ Nenhuma liga disponível para este país.")

            else: # Modo Comparar Ligas
                st.sidebar.subheader("🔍 Seleção para Comparação")
                col1, col2 = st.sidebar.columns(2)
                id1, id2 = None, None

                with col1:
                    pais1 = st.selectbox('🌍 País 1', ['Todos'] + paises_disponiveis, key='pais1')
                    ligas_filtradas1 = df_ligas if pais1 == 'Todos' else df_ligas[df_ligas['pais'] == pais1]
                    
                    # Agrupar ligas por liga_base, divisao e pais para evitar duplicatas de temporadas
                    ligas_filtradas1['grupo_liga'] = ligas_filtradas1.apply(
                        lambda row: f"{row['pais']}|||{row['divisao']}|||{row['liga_base']}", axis=1
                    )
                    ligas_unicas1 = ligas_filtradas1.groupby('grupo_liga').first().reset_index()
                    ligas_unicas1 = ligas_unicas1.sort_values(['divisao', 'liga_base', 'pais'])
                    ligas_disponiveis1 = sorted(ligas_unicas1['liga'].unique())
                    
                    if ligas_disponiveis1:
                        liga1 = st.selectbox('🏆 Liga 1', ligas_disponiveis1, key='liga1')
                        liga_info1 = ligas_unicas1[ligas_unicas1['liga'] == liga1].iloc[0]
                        temporadas_liga1 = ligas_filtradas1[
                            (ligas_filtradas1['liga_base'] == liga_info1['liga_base']) & 
                            (ligas_filtradas1['divisao'] == liga_info1['divisao']) & 
                            (ligas_filtradas1['pais'] == liga_info1['pais'])
                        ]['temporada'].unique()
                        if len(temporadas_liga1) > 0:
                            temporada1 = st.selectbox('📅 Temporada 1', sorted(temporadas_liga1, reverse=True), key='temp1')
                            liga_temporada1 = ligas_filtradas1[
                                (ligas_filtradas1['liga_base'] == liga_info1['liga_base']) & 
                                (ligas_filtradas1['divisao'] == liga_info1['divisao']) & 
                                (ligas_filtradas1['pais'] == liga_info1['pais']) & 
                                (ligas_filtradas1['temporada'] == temporada1)
                            ]
                            if not liga_temporada1.empty:
                                id1 = liga_temporada1.iloc[0]['original_id']

                with col2:
                    pais2 = st.selectbox('🌍 País 2', ['Todos'] + paises_disponiveis, key='pais2')
                    ligas_filtradas2 = df_ligas if pais2 == 'Todos' else df_ligas[df_ligas['pais'] == pais2]
                    
                    # Agrupar ligas por liga_base, divisao e pais para evitar duplicatas de temporadas
                    ligas_filtradas2['grupo_liga'] = ligas_filtradas2.apply(
                        lambda row: f"{row['pais']}|||{row['divisao']}|||{row['liga_base']}", axis=1
                    )
                    ligas_unicas2 = ligas_filtradas2.groupby('grupo_liga').first().reset_index()
                    ligas_unicas2 = ligas_unicas2.sort_values(['divisao', 'liga_base', 'pais'])
                    ligas_disponiveis2 = sorted(ligas_unicas2['liga'].unique())
                    
                    if ligas_disponiveis2:
                        liga2 = st.selectbox('🏆 Liga 2', ligas_disponiveis2, key='liga2')
                        liga_info2 = ligas_unicas2[ligas_unicas2['liga'] == liga2].iloc[0]
                        temporadas_liga2 = ligas_filtradas2[
                            (ligas_filtradas2['liga_base'] == liga_info2['liga_base']) & 
                            (ligas_filtradas2['divisao'] == liga_info2['divisao']) & 
                            (ligas_filtradas2['pais'] == liga_info2['pais'])
                        ]['temporada'].unique()
                        if len(temporadas_liga2) > 0:
                            temporada2 = st.selectbox('📅 Temporada 2', sorted(temporadas_liga2, reverse=True), key='temp2')
                            liga_temporada2 = ligas_filtradas2[
                                (ligas_filtradas2['liga_base'] == liga_info2['liga_base']) & 
                                (ligas_filtradas2['divisao'] == liga_info2['divisao']) & 
                                (ligas_filtradas2['pais'] == liga_info2['pais']) & 
                                (ligas_filtradas2['temporada'] == temporada2)
                            ]
                            if not liga_temporada2.empty:
                                id2 = liga_temporada2.iloc[0]['original_id']
                
                if id1 and id2:
                    dados_liga1 = dados_esporte[dados_esporte['id'] == id1].copy()
                    dados_liga2 = dados_esporte[dados_esporte['id'] == id2].copy()
                    
                    if not dados_liga1.empty and not dados_liga2.empty:
                        st.header(f"🔍 Comparação: {liga1} ({temporada1}) vs {liga2} ({temporada2})")
                        liga1_info = {'id': id1, 'nome': f"{liga1} {temporada1}", 'dados': dados_liga1}
                        liga2_info = {'id': id2, 'nome': f"{liga2} {temporada2}", 'dados': dados_liga2}
                        comparar_ligas(liga1_info, dados_liga1, liga2_info, dados_liga2, dados_competitividade, estatisticas_gerais)
                    else:
                        st.error("❌ Não foi possível carregar dados para uma ou ambas as ligas selecionadas.")
                else:
                    st.error("❌ Selecione ligas e temporadas válidas para comparação.")
        else:
            st.error("❌ Nenhuma liga encontrada nos dados.")
    else:
        st.error("❌ Coluna 'id' não encontrada nos dados.")
        st.stop()