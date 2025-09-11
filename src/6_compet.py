import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import seaborn as sns
from dataclasses import dataclass
from abc import ABC, abstractmethod
import warnings
import os
from scipy import stats
import itertools

warnings.filterwarnings('ignore')

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração visual
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


@dataclass
class AnalysisResult:
    """Classe para estruturar os resultados da análise."""
    championship_id: str
    league: str
    season: str
    num_teams: int
    total_rounds: int
    turning_point_round: Optional[int]
    turning_point_percent: Optional[float]
    final_imbalance: Optional[float]
    ph: float  # Probabilidade vitória mandante
    pd: float  # Probabilidade empate
    pa: float  # Probabilidade vitória visitante
    mean_simulation_imbalance: Optional[float]
    is_competitive: bool
    has_ranking_data: bool = False
    ranking_based_simulation: bool = False
    strength_variance: Optional[float] = None  # Variância das forças dos times


class RankingProcessor:
    """Classe para processar dados de ranking e calcular forças dos times."""
    
    @staticmethod
    def load_rankings(rankings_df: pd.DataFrame, tournament_id: str, season: str) -> Optional[pd.DataFrame]:
        """
        Carrega rankings para um torneio específico e temporada.
        Agora com busca mais específica para evitar confusão entre ligas diferentes.
        """
        if rankings_df is None or rankings_df.empty:
            logger.warning(f"DataFrame de rankings está vazio ou None")
            return None
            
        # Extrai o nome base do torneio (ex: 'serie-a-betano' -> 'serie-a-betano')
        # Mantém o nome completo para evitar confusão entre ligas diferentes
        base_tournament = tournament_id.split('@')[0] if '@' in tournament_id else tournament_id
        
        logger.info(f"Buscando rankings para torneio: '{tournament_id}' (base: '{base_tournament}') na temporada '{season}'")
        
        # 1. Tenta a busca exata primeiro
        filtered_rankings = rankings_df[
            (rankings_df['tournament'].str.contains(tournament_id, case=False, na=False)) &
            (rankings_df['season'] == season)
        ].copy()
        
        # 2. Se a busca exata falhar, tenta busca mais específica
        if filtered_rankings.empty:
            logger.warning(f"Busca exata falhou para '{tournament_id}' temporada '{season}'. Tentando busca específica...")
            
            # Para torneios brasileiros (serie-a-betano), busca por serie-a-YYYY
            if 'betano' in base_tournament.lower() or 'brasil' in base_tournament.lower():
                brazilian_pattern = f"serie-a-{season}"
                filtered_rankings = rankings_df[
                    (rankings_df['tournament'].str.contains(brazilian_pattern, case=False, na=False)) &
                    (rankings_df['season'] == season)
                ].copy()
                if not filtered_rankings.empty:
                    logger.info(f"Encontrados dados brasileiros: '{brazilian_pattern}' para '{tournament_id}'")
            
            # Para torneios italianos, busca por padrões específicos da Itália
            elif any(keyword in base_tournament.lower() for keyword in ['italy', 'italian', 'serie-a']) and 'betano' not in base_tournament.lower():
                # Busca por padrões italianos (se existirem no futuro)
                italian_patterns = [f"serie-a-italy-{season}", f"italy-serie-a-{season}", f"italian-serie-a-{season}"]
                for pattern in italian_patterns:
                    filtered_rankings = rankings_df[
                        (rankings_df['tournament'].str.contains(pattern, case=False, na=False)) &
                        (rankings_df['season'] == season)
                    ].copy()
                    if not filtered_rankings.empty:
                        logger.info(f"Encontrados dados italianos: '{pattern}' para '{tournament_id}'")
                        break
            
            # Se ainda não encontrou, tenta busca genérica apenas como último recurso
            if filtered_rankings.empty:
                logger.warning(f"Busca específica falhou. Tentando busca genérica por '{base_tournament}'...")
                filtered_rankings = rankings_df[
                    (rankings_df['tournament'].str.contains(base_tournament, case=False, na=False)) &
                    (rankings_df['season'] == season)
                ].copy()
        
        # 3. Se ainda falhar, tenta uma busca flexível por temporada
        if filtered_rankings.empty:
            logger.warning(f"Todas as buscas falharam. Tentando busca flexível por temporada...")
            
            # Procura por uma temporada que COMECE com o ano desejado (ex: '2014-2015')
            season_pattern = f"^{season}" # Usa regex para "começa com"
            
            filtered_rankings = rankings_df[
                (rankings_df['tournament'].str.contains(base_tournament, case=False, na=False)) &
                (rankings_df['season'].str.match(season_pattern))
            ].copy()

        if filtered_rankings.empty:
            logger.warning(f"Busca flexível também falhou. Nenhum dado de ranking encontrado para '{tournament_id}' na temporada '{season}' ou similar.")
            return None
            
        logger.info(f"Rankings encontrados para '{tournament_id}' -> '{filtered_rankings['tournament'].iloc[0]}' na temporada '{filtered_rankings['season'].iloc[0]}'.") 
        return filtered_rankings
    
    @staticmethod
    def calculate_team_strengths(rankings_df: pd.DataFrame, teams_list: List[str]) -> Dict[str, float]:
        """
        Calcula forças dos times baseado nos rankings.
        
        Args:
            rankings_df: DataFrame com rankings
            teams_list: Lista de times do campeonato
            
        Returns:
            Dicionário com forças normalizadas dos times
        """
        strengths = {}
        
        # Mapear nomes de times (caso haja diferenças de nomenclatura)
        team_mapping = RankingProcessor._create_team_mapping(rankings_df['Team'].tolist(), teams_list)
        
        # Calcular força baseada na posição inversa (1º lugar = maior força)
        max_position = len(rankings_df)
        
        for _, row in rankings_df.iterrows():
            team_name = row['Team']
            mapped_name = team_mapping.get(team_name, team_name)
            
            if mapped_name in teams_list:
                # Usar posição inversa normalizada + pontos normalizados
                position_strength = (max_position - row.get('#', max_position)) / max_position
                
                # Se tiver pontos, usar também
                if 'Pts' in row and pd.notna(row['Pts']):
                    max_pts = rankings_df['Pts'].max()
                    min_pts = rankings_df['Pts'].min()
                    if max_pts > min_pts:
                        points_strength = (row['Pts'] - min_pts) / (max_pts - min_pts)
                        # Média ponderada: 60% posição, 40% pontos
                        strength = 0.6 * position_strength + 0.4 * points_strength
                    else:
                        strength = position_strength
                else:
                    strength = position_strength
                
                strengths[mapped_name] = strength
        
        # Times não encontrados no ranking recebem menor força
        for team in teams_list:
            if team not in strengths:
                strengths[team] = 0.1
                logger.warning(f"Time {team} não encontrado no ranking, usando força abaixo da média")
        
        # Normalizar para que a média seja 0.5
        if strengths:
            current_mean = np.mean(list(strengths.values()))
            for team in strengths:
                strengths[team] = strengths[team] - current_mean + 0.5
            
            # Garantir que os valores estejam entre 0.1 e 0.9
            min_val, max_val = min(strengths.values()), max(strengths.values())
            if max_val > min_val:
                for team in strengths:
                    strengths[team] = 0.1 + 0.8 * (strengths[team] - min_val) / (max_val - min_val)
        
        return strengths
    
    @staticmethod
    def _create_team_mapping(ranking_teams: List[str], actual_teams: List[str]) -> Dict[str, str]:
        """Cria mapeamento entre nomes de times do ranking e nomes reais."""
        mapping = {}
        
        for ranking_team in ranking_teams:
            # Busca exata
            if ranking_team in actual_teams:
                mapping[ranking_team] = ranking_team
                continue
            
            # Busca por similaridade (case-insensitive, sem acentos/hifens)
            ranking_clean = RankingProcessor._clean_team_name(ranking_team)
            
            best_match = None
            best_similarity = 0
            
            for actual_team in actual_teams:
                actual_clean = RankingProcessor._clean_team_name(actual_team)
                
                # Similaridade simples
                if ranking_clean in actual_clean or actual_clean in ranking_clean:
                    similarity = min(len(ranking_clean), len(actual_clean)) / max(len(ranking_clean), len(actual_clean))
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = actual_team
            
            if best_match and best_similarity > 0.6:
                mapping[ranking_team] = best_match
        
        return mapping
    
    @staticmethod
    def _clean_team_name(name: str) -> str:
        """Limpa nome do time para comparação."""
        import re
        # Remove acentos, hifens, espaços extras e converte para minúscula
        clean = re.sub(r'[^\w\s]', '', str(name).lower())
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean


class ImprovedMatchSimulator:
    """Simulador de partidas melhorado com base nas forças dos times."""
    
    def __init__(self, team_strengths: Optional[Dict[str, float]] = None):
        self.team_strengths = team_strengths or {}
        self.home_advantage = 0.1  # Vantagem de jogar em casa
    
    def calculate_match_probabilities(self, home_team: str, away_team: str, 
                                    global_ph: float, global_pd: float, global_pa: float) -> Tuple[float, float, float]:
        """
        Calcula probabilidades específicas para uma partida baseada nas forças dos times.
        
        Args:
            home_team: Time mandante
            away_team: Time visitante
            global_ph, global_pd, global_pa: Probabilidades globais do campeonato
            
        Returns:
            Tupla com (P(casa vence), P(empate), P(visitante vence))
        """
        if not self.team_strengths:
            return global_ph, global_pd, global_pa
        
        # Obter forças dos times
        home_strength = self.team_strengths.get(home_team, 0.5)
        away_strength = self.team_strengths.get(away_team, 0.5)
        
        # Aplicar vantagem de casa
        home_strength_adj = min(0.95, home_strength + self.home_advantage)
        
        # Calcular diferença de força
        strength_diff = home_strength_adj - away_strength
        
        # Converter diferença de força em probabilidades
        # Usar função sigmóide para converter diferença em probabilidade
        def sigmoid(x, sharpness=3):
            return 1 / (1 + np.exp(-sharpness * x))
        
        # Probabilidade base de vitória do mandante baseada na diferença de força
        base_home_prob = sigmoid(strength_diff)
        
        # Ajustar probabilidades mantendo a característica global do campeonato
        # Interpolar entre probabilidades globais e baseadas em força
        blend_factor = 0.7  # 70% força dos times, 30% padrão global
        
        ph_adjusted = blend_factor * base_home_prob + (1 - blend_factor) * global_ph
        
        # Para empates e vitórias visitantes, usar interpolação similar
        remaining_prob = 1 - ph_adjusted
        total_global_remaining = global_pd + global_pa
        
        if total_global_remaining > 0:
            pd_adjusted = remaining_prob * (global_pd / total_global_remaining)
            pa_adjusted = remaining_prob * (global_pa / total_global_remaining)
        else:
            pd_adjusted = remaining_prob * 0.3
            pa_adjusted = remaining_prob * 0.7
        
        # Normalizar para garantir que soma = 1
        total = ph_adjusted + pd_adjusted + pa_adjusted
        if total > 0:
            return ph_adjusted/total, pd_adjusted/total, pa_adjusted/total
        else:
            return global_ph, global_pd, global_pa
    
    def simulate_match_result(self, home_team: str, away_team: str,
                            global_ph: float, global_pd: float, global_pa: float) -> Tuple[int, int]:
        """
        Simula o resultado de uma partida.
        
        Returns:
            Tupla com (gols_casa, gols_visitante)
        """
        ph, pd, pa = self.calculate_match_probabilities(home_team, away_team, global_ph, global_pd, global_pa)
        
        rand = np.random.random()
        
        if rand < ph:
            # Vitória do mandante
            return np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2]), np.random.choice([0, 1], p=[0.7, 0.3])
        elif rand < ph + pd:
            # Empate
            score = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
            return score, score
        else:
            # Vitória do visitante
            return np.random.choice([0, 1], p=[0.7, 0.3]), np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])


class DataValidator:
    """Classe para validação e limpeza de dados."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Valida e limpa o DataFrame de entrada."""
        required_columns = ['id', 'rodada', 'home', 'away', 'goal_home', 'goal_away']
        
        # Verificar colunas obrigatórias
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
        
        # Fazer uma cópia para não modificar o original
        df_clean = df.copy()
        
        # Converter colunas de gols para numérico
        for col in ['goal_home', 'goal_away']:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Converter rodada para inteiro
        df_clean['rodada'] = pd.to_numeric(df_clean['rodada'], errors='coerce')
        
        # Remover linhas com dados inválidos
        initial_rows = len(df_clean)
        df_clean = df_clean.dropna(subset=['goal_home', 'goal_away', 'rodada'])
        removed_rows = initial_rows - len(df_clean)
        
        if removed_rows > 0:
            logger.warning(f"Removidas {removed_rows} linhas com dados inválidos")
        
        # Validar valores lógicos
        invalid_goals = df_clean[(df_clean['goal_home'] < 0) | (df_clean['goal_away'] < 0)]
        if not invalid_goals.empty:
            logger.warning(f"Encontrados {len(invalid_goals)} jogos com gols negativos")
            df_clean = df_clean[(df_clean['goal_home'] >= 0) & (df_clean['goal_away'] >= 0)]
        
        return df_clean
    
    @staticmethod
    def validate_rankings_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Valida DataFrame de rankings."""
        required_columns = ['season', 'tournament', '#', 'Team']
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Colunas obrigatórias ausentes no ranking: {missing_cols}")
        
        df_clean = df.copy()
        
        # Converter posição para numérico
        df_clean['#'] = pd.to_numeric(df_clean['#'], errors='coerce')
        
        # Converter pontos se existir
        if 'Pts' in df_clean.columns:
            df_clean['Pts'] = pd.to_numeric(df_clean['Pts'], errors='coerce')
        
        # Remover linhas sem posição válida
        df_clean = df_clean.dropna(subset=['#'])
        
        return df_clean


class CompetitiveBalanceAnalyzer:
    """Analisador de equilíbrio competitivo melhorado com rankings."""
    
    def __init__(self, games_df: pd.DataFrame, championship_id: str,
                 rankings_df: Optional[pd.DataFrame] = None,
                 alpha: float = 0.05, num_simulations: int = 1000):
        """
        Inicializa o analisador de competitividade.
        
        Args:
            games_df: DataFrame com jogos validados
            championship_id: ID único do campeonato
            rankings_df: DataFrame com dados de ranking (opcional)
            alpha: Nível de significância
            num_simulations: Número de simulações Monte Carlo
        """
        self.alpha = alpha
        self.num_simulations = num_simulations
        self.championship_id = championship_id
        self.rankings_df = rankings_df
        
        # Filtrar e ordenar jogos do campeonato
        self.season_games = games_df[
            games_df['id'] == championship_id
        ].copy().sort_values(['rodada', 'home'])
        
        if self.season_games.empty:
            raise ValueError(f"Nenhum jogo encontrado para: {championship_id}")
        
        self._initialize_championship_info()
        self._load_team_strengths()
        self._reset_results()
        
    def _initialize_championship_info(self):
        """Inicializa informações do campeonato."""
        self.league = self._extract_league_name()
        self.season = self._extract_season()
        
        # Obter times únicos
        home_teams = set(self.season_games['home'].unique())
        away_teams = set(self.season_games['away'].unique())
        self.teams = sorted(list(home_teams.union(away_teams)))
        
        self.num_teams = len(self.teams)
        self.total_rounds = int(self.season_games['rodada'].max())
        
        logger.info(f"Campeonato inicializado: {self.league} {self.season}")
        logger.info(f"Times: {self.num_teams}, Jogos: {len(self.season_games)}, Rodadas: {self.total_rounds}")
        
    def _extract_league_name(self) -> str:
        """Extrai o nome da liga do ID."""
        try:
            return self.championship_id.split('@')[0] if '@' in self.championship_id else self.championship_id
        except:
            return "Liga Desconhecida"
    
    def _extract_season(self) -> str:
        """Extrai a temporada do ID."""
        try:
            if '@' in self.championship_id:
                path_part = self.championship_id.split('@')[1]
                # Procurar por ano (4 dígitos)
                import re
                year_match = re.search(r'(\d{4})', path_part)
                return year_match.group(1) if year_match else "Temporada Desconhecida"
            return "Temporada Desconhecida"
        except:
            return "Temporada Desconhecida"
    
    def _load_team_strengths(self):
        """Carrega forças dos times baseado nos rankings."""
        self.team_strengths = {}
        self.has_ranking_data = False
        
        if self.rankings_df is not None:
            # Tentar carregar rankings da temporada anterior
            prev_season = self.season # Define um valor padrão
            try:
                if '-' in self.season:
                    # Lida com o formato "YYYY-YYYY" (ex: "2015-2016" -> "2014-2015")
                    start_year, end_year = map(int, self.season.split('-'))
                    prev_season = f"{start_year - 1}-{end_year - 1}"
                elif self.season.isdigit():
                    # Lida com o formato "YYYY" (ex: "2015" -> "2014")
                    prev_season = str(int(self.season) - 1)
                # Se não for nenhum dos formatos, prev_season mantém o valor de self.season
            except (ValueError, IndexError):
                # Lida com strings mal formatadas como "2015-" ou "abc-def"
                logger.warning(f"Formato de temporada inválido: '{self.season}'. Usando o valor original.")
                prev_season = self.season
            
            rankings_data = RankingProcessor.load_rankings(
                self.rankings_df, self.league, prev_season
            )
            
            if rankings_data is not None:
                self.team_strengths = RankingProcessor.calculate_team_strengths(
                    rankings_data, self.teams
                )
                self.has_ranking_data = True
                
                # Calcular variância das forças (medida de desigualdade inicial)
                self.strength_variance = np.var(list(self.team_strengths.values()))
                
                logger.info(f"Carregadas forças de {len(self.team_strengths)} times do ranking da temporada {prev_season}")
                logger.info(f"Variância das forças: {self.strength_variance:.4f}")
            else:
                logger.warning(f"Não foi possível carregar rankings para {self.league} {prev_season}")
        
        # Criar simulador
        self.match_simulator = ImprovedMatchSimulator(self.team_strengths)
        
    def _reset_results(self):
        """Reseta variáveis de resultado."""
        self.observed_imbalance_curve = None
        self.simulation_curves = None
        self.envelope_upper_bound = None
        self.ph = self.pd = self.pa = None
        
    def _calculate_points_progression(self, games_schedule: pd.DataFrame) -> np.ndarray:
        """
        Calcula a progressão normalizada de pontos rodada a rodada.
        
        Args:
            games_schedule: DataFrame com os jogos
            
        Returns:
            Array com a variância normalizada por rodada
        """
        points = {team: 0 for team in self.teams}
        variance_curve = []
        
        for round_num in range(1, self.total_rounds + 1):
            round_games = games_schedule[games_schedule['rodada'] == round_num]
            
            # Processar jogos da rodada
            for _, game in round_games.iterrows():
                home_team, away_team = game['home'], game['away']
                home_score, away_score = game['goal_home'], game['goal_away']
                
                # Atribuir pontos
                if home_score > away_score:
                    points[home_team] += 3
                elif home_score < away_score:
                    points[away_team] += 3
                else:  # Empate
                    points[home_team] += 1
                    points[away_team] += 1
            
            # Calcular variância normalizada melhorada
            points_values = list(points.values())
            
            if len(points_values) > 1:
                variance = np.var(points_values, ddof=0)
                max_possible_points = round_num * 3
                
                # Normalização melhorada considerando distribuição teórica
                # Em um campeonato perfeitamente equilibrado, a variância seria mínima
                # Em um campeonato totalmente desequilibrado, alguns times teriam todos os pontos
                theoretical_max_var = self._calculate_theoretical_max_variance(round_num)
                normalized_variance = variance / theoretical_max_var if theoretical_max_var > 0 else 0
            else:
                normalized_variance = 0
                
            variance_curve.append(normalized_variance)
        
        return np.array(variance_curve)
    
    def _calculate_theoretical_max_variance(self, round_num: int) -> float:
        """Calcula a variância teórica máxima para uma rodada."""
        max_points = round_num * 3
        # Cenário de máximo desequilíbrio: um time tem todos os pontos, outros têm zero
        # Mas isso é irrealista, então usamos uma aproximação mais realista
        
        # Distribuição mais realista: alguns times dominantes, outros fracos
        if self.num_teams <= 1:
            return 1.0
        
        # Aproximação: 20% dos times ficam com 80% dos pontos disponíveis
        dominant_teams = max(1, int(0.2 * self.num_teams))
        weak_teams = self.num_teams - dominant_teams
        
        total_points = round_num * 3 * self.num_teams // 2  # Total de pontos no campeonato
        points_dominant = int(0.8 * total_points) // dominant_teams
        points_weak = int(0.2 * total_points) // weak_teams if weak_teams > 0 else 0
        
        # Calcular variância dessa distribuição
        points_dist = [points_dominant] * dominant_teams + [points_weak] * weak_teams
        return np.var(points_dist, ddof=0)
    
    def calculate_observed_imbalance(self):
        """Calcula a curva de desequilíbrio observada."""
        try:
            self.observed_imbalance_curve = self._calculate_points_progression(self.season_games)
            logger.info(f"Curva de desequilíbrio calculada: {len(self.observed_imbalance_curve)} rodadas")
        except Exception as e:
            logger.error(f"Erro ao calcular desequilíbrio observado: {e}")
            raise
    
    def _calculate_match_probabilities(self):
        """Calcula probabilidades globais dos resultados dos jogos."""
        total_games = len(self.season_games)
        
        home_wins = len(self.season_games[
            self.season_games['goal_home'] > self.season_games['goal_away']
        ])
        draws = len(self.season_games[
            self.season_games['goal_home'] == self.season_games['goal_away']
        ])
        away_wins = total_games - home_wins - draws
        
        self.ph = home_wins / total_games
        self.pd = draws / total_games
        self.pa = away_wins / total_games
        
        logger.info(f"Probabilidades globais - Casa: {self.ph:.3f}, Empate: {self.pd:.3f}, Fora: {self.pa:.3f}")
    
    def run_null_model(self):
        """Executa o modelo nulo com simulações Monte Carlo melhoradas."""
        logger.info("Iniciando modelo nulo...")
        
        self._calculate_match_probabilities()
        
        simulation_type = "baseada em rankings" if self.has_ranking_data else "probabilística simples"
        logger.info(f"Executando {self.num_simulations} simulações ({simulation_type})...")
        
        # Pré-alocar array para melhor performance
        self.simulation_curves = np.zeros((self.num_simulations, self.total_rounds))
        
        # Template do DataFrame para simulações
        template_games = self.season_games[['rodada', 'home', 'away']].copy()
        
        for sim in range(self.num_simulations):
            if (sim + 1) % (self.num_simulations // 10) == 0:
                logger.info(f"Progresso: {sim + 1}/{self.num_simulations}")
            
            # Criar jogos simulados
            simulated_games = template_games.copy()
            
            # Simular cada jogo individualmente se temos dados de ranking
            if self.has_ranking_data:
                for idx, row in simulated_games.iterrows():
                    home_goals, away_goals = self.match_simulator.simulate_match_result(
                        row['home'], row['away'], self.ph, self.pd, self.pa
                    )
                    simulated_games.loc[idx, 'goal_home'] = home_goals
                    simulated_games.loc[idx, 'goal_away'] = away_goals
            else:
                # Simulação probabilística simples (método original)
                random_vals = np.random.random(len(template_games))
                
                home_wins_mask = random_vals < self.ph
                draws_mask = (random_vals >= self.ph) & (random_vals < self.ph + self.pd)
                away_wins_mask = random_vals >= self.ph + self.pd
                
                simulated_games.loc[home_wins_mask, 'goal_home'] = 2
                simulated_games.loc[home_wins_mask, 'goal_away'] = 0
                
                simulated_games.loc[draws_mask, 'goal_home'] = 1
                simulated_games.loc[draws_mask, 'goal_away'] = 1
                
                simulated_games.loc[away_wins_mask, 'goal_home'] = 0
                simulated_games.loc[away_wins_mask, 'goal_away'] = 2
            
            # Calcular curva de desequilíbrio para esta simulação
            sim_curve = self._calculate_points_progression(simulated_games)
            self.simulation_curves[sim] = sim_curve
        
        logger.info("Simulações concluídas!")
        
    def calculate_confidence_envelope(self):
        """Calcula o envelope de confiança."""
        if self.simulation_curves is None:
            raise ValueError("Execute run_null_model() primeiro")
        
        self.envelope_upper_bound = np.percentile(
            self.simulation_curves, 
            (1 - self.alpha) * 100, 
            axis=0
        )
        
        simulation_type = "com rankings" if self.has_ranking_data else "probabilístico"
        logger.info(f"Envelope de confiança calculado (α={self.alpha}, {simulation_type})")
        
    def find_turning_point(self) -> Tuple[Optional[int], Optional[float]]:
        """Encontra o ponto de virada com critérios mais rigorosos."""
        if self.observed_imbalance_curve is None or self.envelope_upper_bound is None:
            raise ValueError("Execute os cálculos da análise primeiro")
        
        # Critérios adaptativos baseados no tamanho do campeonato
        min_consecutive_rounds = max(3, int(0.1 * self.total_rounds))
        min_percentage_above = 0.7
        
        # Se temos dados de ranking, ser mais rigoroso
        if self.has_ranking_data:
            min_percentage_above = 0.75
        
        for round_idx in range(len(self.observed_imbalance_curve) - min_consecutive_rounds):
            # Verificar se está acima do envelope
            if self.observed_imbalance_curve[round_idx] > self.envelope_upper_bound[round_idx]:
                
                # Verificar rodadas consecutivas
                consecutive_above = 0
                for i in range(round_idx, min(round_idx + min_consecutive_rounds, len(self.observed_imbalance_curve))):
                    if self.observed_imbalance_curve[i] > self.envelope_upper_bound[i]:
                        consecutive_above += 1
                    else:
                        break
                
                if consecutive_above >= min_consecutive_rounds:
                    # Verificar percentual das rodadas restantes
                    remaining_rounds = self.observed_imbalance_curve[round_idx:]
                    remaining_envelope = self.envelope_upper_bound[round_idx:]
                    
                    above_envelope = np.sum(remaining_rounds > remaining_envelope)
                    if above_envelope / len(remaining_rounds) >= min_percentage_above:
                        tau = round_idx + 1  # +1 porque index é 0-based
                        tau_percent = tau / self.total_rounds
                        return tau, tau_percent
        
        return None, None
        
    def plot_results(self, save_path: Optional[str] = None, show_simulations: bool = True):
        """Plota os resultados com melhor visualização."""
        if self.observed_imbalance_curve is None:
            raise ValueError("Execute a análise primeiro")
        
        # Criar figura maior para acomodar informações adicionais
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 1], width_ratios=[2, 1])
        
        # Gráfico principal (ocupando 2 colunas na primeira linha)
        ax_main = fig.add_subplot(gs[0, :])
        rounds = np.arange(1, len(self.observed_imbalance_curve) + 1)
        
        # Envelope de confiança
        if self.envelope_upper_bound is not None:
            ax_main.fill_between(rounds, 0, self.envelope_upper_bound, 
                               alpha=0.3, color='lightblue', 
                               label=f'Envelope {(1-self.alpha)*100:.0f}% confiança')
            ax_main.plot(rounds, self.envelope_upper_bound, '--', 
                        color='blue', alpha=0.8, linewidth=2)
        
        # Algumas simulações representativas
        if self.simulation_curves is not None and show_simulations:
            sample_sims = np.random.choice(len(self.simulation_curves), 
                                         min(20, len(self.simulation_curves)), 
                                         replace=False)
            for i in sample_sims:
                ax_main.plot(rounds, self.simulation_curves[i], '-', 
                           alpha=0.1, color='gray', linewidth=0.5)
        
        # Curva observada
        ax_main.plot(rounds, self.observed_imbalance_curve, 'r-', 
                    linewidth=3, label='Observado', marker='o', markersize=3)
        
        # Ponto de virada
        tau, tau_percent = self.find_turning_point()
        if tau is not None:
            ax_main.axvline(x=tau, color='red', linestyle=':', alpha=0.7, linewidth=2,
                           label=f'Ponto de virada (rodada {tau})')
            ax_main.text(tau + 1, ax_main.get_ylim()[1] * 0.8, 
                        f'Rodada {tau}\n({tau_percent:.1%})', 
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        # Título com informações sobre o método de simulação
        simulation_method = "com Rankings" if self.has_ranking_data else "Probabilístico"
        title = f'Análise de Competitividade - {self.league} {self.season}\n(Simulação: {simulation_method})'
        ax_main.set_title(title, fontsize=14, fontweight='bold')
        
        ax_main.set_xlabel('Rodada', fontsize=12)
        ax_main.set_ylabel('Desequilíbrio Normalizado', fontsize=12)
        ax_main.legend(fontsize=10)
        ax_main.grid(True, alpha=0.3)
        
        # Gráfico de distribuição final (segunda linha, primeira coluna)
        ax_hist = fig.add_subplot(gs[1, 0])
        if self.simulation_curves is not None:
            final_simulated = self.simulation_curves[:, -1]
            final_observed = self.observed_imbalance_curve[-1]
            
            ax_hist.hist(final_simulated, bins=30, alpha=0.7, color='lightblue', 
                        density=True, label='Simulações (final)')
            ax_hist.axvline(final_observed, color='red', linestyle='-', linewidth=3,
                           label=f'Observado: {final_observed:.3f}')
            
            # Percentil da observação
            percentile = (np.sum(final_simulated < final_observed) / len(final_simulated)) * 100
            ax_hist.text(0.05, 0.95, f'Percentil: {percentile:.1f}%',
                        transform=ax_hist.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
            
            ax_hist.set_xlabel('Desequilíbrio Final', fontsize=10)
            ax_hist.set_ylabel('Densidade', fontsize=10)
            ax_hist.set_title('Distribuição Final', fontsize=11)
            ax_hist.legend(fontsize=9)
            ax_hist.grid(True, alpha=0.3)
        
        # Informações sobre forças dos times (segunda linha, segunda coluna)
        ax_info = fig.add_subplot(gs[1, 1])
        ax_info.axis('off')
        
        info_text = f"INFORMAÇÕES DO CAMPEONATO\n\n"
        info_text += f"Times: {self.num_teams}\n"
        info_text += f"Rodadas: {self.total_rounds}\n"
        info_text += f"Simulações: {self.num_simulations}\n\n"
        info_text += f"Probabilidades Globais:\n"
        info_text += f"  Casa: {self.ph:.3f}\n"
        info_text += f"  Empate: {self.pd:.3f}\n"
        info_text += f"  Visitante: {self.pa:.3f}\n\n"
        
        if self.has_ranking_data:
            info_text += f"DADOS DE RANKING:\n"
            info_text += f"Variância das forças: {self.strength_variance:.4f}\n"
            info_text += f"Simulação baseada em rankings\n\n"
        else:
            info_text += f"SEM DADOS DE RANKING\n"
            info_text += f"Simulação probabilística simples\n\n"
        
        if tau is not None:
            info_text += f"RESULTADO:\n"
            info_text += f"NÃO COMPETITIVO\n"
            info_text += f"Ponto de virada: Rodada {tau}\n"
            info_text += f"({tau_percent:.1%} da temporada)"
        else:
            info_text += f"RESULTADO:\n"
            info_text += f"COMPETITIVO\n"
            info_text += f"Nenhum ponto de virada detectado"
        
        ax_info.text(0.05, 0.95, info_text, transform=ax_info.transAxes, 
                    verticalalignment='top', fontsize=9, fontfamily='monospace',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.3))
        
        # Gráfico de forças dos times (terceira linha, ambas colunas)
        if self.has_ranking_data and self.team_strengths:
            ax_strength = fig.add_subplot(gs[2, :])
            
            teams = list(self.team_strengths.keys())
            strengths = list(self.team_strengths.values())
            
            # Ordenar por força
            sorted_data = sorted(zip(teams, strengths), key=lambda x: x[1], reverse=True)
            teams_sorted, strengths_sorted = zip(*sorted_data)
            
            # Usar cores diferentes para times fortes e fracos
            colors = ['darkred' if s > 0.7 else 'red' if s > 0.6 else 'orange' if s > 0.4 else 'lightblue' if s > 0.3 else 'blue' 
                     for s in strengths_sorted]
            
            bars = ax_strength.bar(range(len(teams_sorted)), strengths_sorted, color=colors, alpha=0.7)
            ax_strength.set_xticks(range(len(teams_sorted)))
            ax_strength.set_xticklabels(teams_sorted, rotation=45, ha='right', fontsize=8)
            ax_strength.set_ylabel('Força do Time', fontsize=10)
            ax_strength.set_title('Forças dos Times (baseado em rankings anteriores)', fontsize=11)
            ax_strength.grid(True, alpha=0.3, axis='y')
            
            # Linha da média
            mean_strength = np.mean(strengths_sorted)
            ax_strength.axhline(y=mean_strength, color='black', linestyle='--', alpha=0.5, label=f'Média: {mean_strength:.3f}')
            ax_strength.legend(fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Gráfico salvo em: {save_path}")
        
        plt.show()
        
    def get_analysis_result(self) -> AnalysisResult:
        """Retorna um resultado estruturado da análise."""
        tau, tau_percent = self.find_turning_point()
        
        mean_sim_imbalance = None
        if self.simulation_curves is not None:
            mean_sim_imbalance = np.mean(self.simulation_curves[:, -1])
        
        return AnalysisResult(
            championship_id=self.championship_id,
            league=self.league,
            season=self.season,
            num_teams=self.num_teams,
            total_rounds=self.total_rounds,
            turning_point_round=tau,
            turning_point_percent=tau_percent,
            final_imbalance=self.observed_imbalance_curve[-1] if self.observed_imbalance_curve is not None else None,
            ph=self.ph or 0,
            pd=self.pd or 0,
            pa=self.pa or 0,
            mean_simulation_imbalance=mean_sim_imbalance,
            is_competitive=(tau is None),
            has_ranking_data=self.has_ranking_data,
            ranking_based_simulation=self.has_ranking_data,
            strength_variance=self.strength_variance
        )


class MultiLeagueAnalyzer:
    """Analisador para múltiplos campeonatos com rankings."""
    
    def __init__(self, alpha: float = 0.05, num_simulations: int = 1000):
        self.alpha = alpha
        self.num_simulations = num_simulations
        self.results: List[AnalysisResult] = []
        
    def analyze_all_leagues(self, df_jogos: pd.DataFrame, 
                          df_rankings: Optional[pd.DataFrame] = None,
                          output_dir: Optional[str] = None,
                          save_plots: bool = False) -> List[AnalysisResult]:
        """
        Executa análise para todos os campeonatos.
        
        Args:
            df_jogos: DataFrame com todos os jogos
            df_rankings: DataFrame com rankings (opcional)
            output_dir: Diretório para salvar resultados
            save_plots: Se deve salvar os gráficos
            
        Returns:
            Lista com os resultados de todos os campeonatos
        """
        # Validar dados
        logger.info("Validando dados de entrada...")
        df_clean = DataValidator.validate_dataframe(df_jogos)
        
        df_rankings_clean = None
        if df_rankings is not None:
            try:
                df_rankings_clean = DataValidator.validate_rankings_dataframe(df_rankings)
                logger.info(f"Rankings validados: {len(df_rankings_clean)} registros")
            except Exception as e:
                logger.warning(f"Erro ao validar rankings: {e}. Continuando sem rankings.")
        
        # Obter IDs únicos
        championship_ids = df_clean['id'].unique()
        logger.info(f"Analisando {len(championship_ids)} campeonatos")
        
        self.results = []
        
        # Criar diretório de saída se necessário
        if output_dir and save_plots:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for i, champ_id in enumerate(championship_ids, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"ANÁLISE {i}/{len(championship_ids)}: {champ_id}")
            logger.info(f"{'='*60}")
            
            try:
                analyzer = CompetitiveBalanceAnalyzer(
                    games_df=df_clean,
                    championship_id=champ_id,
                    rankings_df=df_rankings_clean,
                    alpha=self.alpha,
                    num_simulations=self.num_simulations
                )
                
                # Executar análise completa
                analyzer.calculate_observed_imbalance()
                analyzer.run_null_model()
                analyzer.calculate_confidence_envelope()
                
                # Plotar resultados
                save_path = None
                if output_dir and save_plots:
                    filename = f"{champ_id.replace('/', '_').replace('@', '_')}.png"
                    save_path = Path(output_dir) / filename
                
                analyzer.plot_results(save_path=save_path)
                
                # Guardar resultado
                result = analyzer.get_analysis_result()
                self.results.append(result)
                
                # Log do resultado
                ranking_info = " (com rankings)" if result.has_ranking_data else " (sem rankings)"
                if result.turning_point_round:
                    logger.info(f"Ponto de virada detectado na rodada {result.turning_point_round}{ranking_info}")
                else:
                    logger.info(f"Liga permanece competitiva{ranking_info}")
                    
            except Exception as e:
                logger.error(f"ERRO ao analisar {champ_id}: {e}")
                continue
        
        return self.results
    
    def generate_summary_report(self, save_path: Optional[str] = None) -> pd.DataFrame:
        """Gera relatório resumo de todos os resultados."""
        if not self.results:
            raise ValueError("Nenhuma análise foi executada ainda")
        
        # Converter resultados para DataFrame
        summary_data = []
        for result in self.results:
            summary_data.append({
                'ID Campeonato': result.championship_id,
                'Liga': result.league,
                'Temporada': result.season,
                'Times': result.num_teams,
                'Rodadas': result.total_rounds,
                'Tem Rankings': 'Sim' if result.has_ranking_data else 'Não',
                'Variância Forças': f"{result.strength_variance:.4f}" if result.strength_variance else 'N/A',
                'Ponto Virada (Rodada)': result.turning_point_round or 'N/A',
                'Ponto Virada (%)': f"{result.turning_point_percent:.1%}" if result.turning_point_percent else 'N/A',
                'Desequilíbrio Final': f"{result.final_imbalance:.4f}" if result.final_imbalance else 'N/A',
                'É Competitivo': 'Sim' if result.is_competitive else 'Não',
                'P(Casa)': f"{result.ph:.3f}",
                'P(Empate)': f"{result.pd:.3f}",
                'P(Fora)': f"{result.pa:.3f}",
                'Simulação': 'Rankings' if result.ranking_based_simulation else 'Probabilística'
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        if save_path:
            summary_df.to_csv(save_path, index=False, encoding='utf-8')
            logger.info(f"Relatório resumo salvo em: {save_path}")
        
        return summary_df
    
    def plot_comparative_analysis(self, save_path: Optional[str] = None):
        """Cria visualizações comparativas melhoradas."""
        if not self.results:
            raise ValueError("Nenhuma análise foi executada ainda")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        # Separar resultados por tipo de simulação
        with_rankings = [r for r in self.results if r.has_ranking_data]
        without_rankings = [r for r in self.results if not r.has_ranking_data]
        
        # 1. Comparação de competitividade por tipo de simulação
        def count_competitive(results_list):
            return sum(1 for r in results_list if r.is_competitive)
        
        categories = []
        competitive_counts = []
        total_counts = []
        
        if with_rankings:
            categories.append('Com Rankings')
            competitive_counts.append(count_competitive(with_rankings))
            total_counts.append(len(with_rankings))
        
        if without_rankings:
            categories.append('Sem Rankings')
            competitive_counts.append(count_competitive(without_rankings))
            total_counts.append(len(without_rankings))
        
        non_competitive_counts = [total - comp for total, comp in zip(total_counts, competitive_counts)]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, competitive_counts, width, label='Competitivos', color='lightgreen', alpha=0.8)
        bars2 = ax1.bar(x + width/2, non_competitive_counts, width, label='Não Competitivos', color='lightcoral', alpha=0.8)
        
        ax1.set_xlabel('Tipo de Análise')
        ax1.set_ylabel('Número de Campeonatos')
        ax1.set_title('Competitividade por Tipo de Simulação')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        
        # Adicionar valores nas barras
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom')
        
        # 2. Relação entre variância de forças e competitividade
        if with_rankings:
            strength_variances = [r.strength_variance for r in with_rankings if r.strength_variance is not None]
            is_competitive = [r.is_competitive for r in with_rankings if r.strength_variance is not None]
            
            colors = ['green' if comp else 'red' for comp in is_competitive]
            ax2.scatter(strength_variances, [1 if comp else 0 for comp in is_competitive], 
                       c=colors, alpha=0.6, s=60)
            ax2.set_xlabel('Variância das Forças dos Times')
            ax2.set_ylabel('Competitivo (1) / Não Competitivo (0)')
            ax2.set_title('Variância das Forças vs Competitividade')
            ax2.set_yticks([0, 1])
            ax2.set_yticklabels(['Não Competitivo', 'Competitivo'])
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'Sem dados de ranking\npara análise', 
                    transform=ax2.transAxes, ha='center', va='center')
            ax2.set_title('Variância das Forças vs Competitividade')
        
        # 3. Distribuição dos pontos de virada
        turning_points_with = [r.turning_point_percent for r in with_rankings if r.turning_point_percent is not None]
        turning_points_without = [r.turning_point_percent for r in without_rankings if r.turning_point_percent is not None]
        
        bins = np.linspace(0, 1, 11)
        
        if turning_points_with:
            ax3.hist(turning_points_with, bins=bins, alpha=0.7, color='orange', 
                    label=f'Com Rankings ({len(turning_points_with)})', density=True)
        if turning_points_without:
            ax3.hist(turning_points_without, bins=bins, alpha=0.7, color='skyblue', 
                    label=f'Sem Rankings ({len(turning_points_without)})', density=True)
        
        ax3.set_xlabel('Ponto de Virada (% da temporada)')
        ax3.set_ylabel('Densidade')
        ax3.set_title('Distribuição dos Pontos de Virada')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Desequilíbrio final por número de times
        teams_counts = [r.num_teams for r in self.results]
        final_imbalances = [r.final_imbalance for r in self.results if r.final_imbalance is not None]
        has_rankings = [r.has_ranking_data for r in self.results if r.final_imbalance is not None]
        
        colors = ['orange' if has_rank else 'skyblue' for has_rank in has_rankings]
        shapes = ['o' if has_rank else '^' for has_rank in has_rankings]
        
        for i, (teams, imbalance, has_rank) in enumerate(zip(teams_counts[:len(final_imbalances)], final_imbalances, has_rankings)):
            ax4.scatter(teams, imbalance, c=colors[i], marker=shapes[i], s=50, alpha=0.7)
        
        ax4.set_xlabel('Número de Times')
        ax4.set_ylabel('Desequilíbrio Final')
        ax4.set_title('Desequilíbrio Final vs Número de Times')
        ax4.grid(True, alpha=0.3)
        
        # Legenda personalizada
        import matplotlib.patches as mpatches
        orange_patch = mpatches.Patch(color='orange', label='Com Rankings')
        blue_patch = mpatches.Patch(color='skyblue', label='Sem Rankings')
        ax4.legend(handles=[orange_patch, blue_patch])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Análise comparativa salva em: {save_path}")
        
        plt.show()
        
        # Estatísticas resumidas
        print(f"\n{'='*60}")
        print("ESTATÍSTICAS COMPARATIVAS")
        print(f"{'='*60}")
        
        if with_rankings:
            comp_rate_with = count_competitive(with_rankings) / len(with_rankings) * 100
            print(f"Campeonatos com rankings: {len(with_rankings)}")
            print(f"  Taxa de competitividade: {comp_rate_with:.1f}%")
            
            if strength_variances:
                print(f"  Variância média das forças: {np.mean(strength_variances):.4f}")
        
        if without_rankings:
            comp_rate_without = count_competitive(without_rankings) / len(without_rankings) * 100
            print(f"Campeonatos sem rankings: {len(without_rankings)}")
            print(f"  Taxa de competitividade: {comp_rate_without:.1f}%")


def main():
    try:
        # Configurações
        GAMES_CSV_PATH = '../data/5_matchdays/football.csv'
        RANKINGS_CSV_PATH = '../data/4_standings/standings.csv'  
        OUTPUT_DIR = '../data/6_analysis'
        ALPHA = 0.05
        NUM_SIMULATIONS = 500
        
        # Verificar arquivos
        if not Path(GAMES_CSV_PATH).exists():
            raise FileNotFoundError(f"Arquivo de jogos não encontrado: {GAMES_CSV_PATH}")
        
        # Carregar dados de jogos
        logger.info(f"Carregando jogos de: {GAMES_CSV_PATH}")
        df_jogos = pd.read_csv(GAMES_CSV_PATH)
        logger.info(f"Jogos carregados: {len(df_jogos)} registros")
        
        # Carregar dados de rankings (opcional)
        df_rankings = None
        if Path(RANKINGS_CSV_PATH).exists():
            logger.info(f"Carregando rankings de: {RANKINGS_CSV_PATH}")
            df_rankings = pd.read_csv(RANKINGS_CSV_PATH)
            logger.info(f"Rankings carregados: {len(df_rankings)} registros")
        else:
            logger.warning(f"Arquivo de rankings não encontrado: {RANKINGS_CSV_PATH}")
            logger.info("Continuando análise sem dados de ranking")
        
        # Inicializar analisador
        analyzer = MultiLeagueAnalyzer(alpha=ALPHA, num_simulations=NUM_SIMULATIONS)
        
        # Executar análises
        results = analyzer.analyze_all_leagues(
            df_jogos=df_jogos,
            df_rankings=df_rankings,
            output_dir=OUTPUT_DIR,
            save_plots=True
        )
        
        # Gerar relatório resumo
        logger.info("\n" + "="*60)
        logger.info("GERANDO RELATÓRIO RESUMO")
        logger.info("="*60)
        
        summary_df = analyzer.generate_summary_report(
            save_path=Path(OUTPUT_DIR) / 'summary_report_enhanced.csv'
        )
        
        print("\n" + "="*100)
        print("RESUMO FINAL DE TODAS AS ANÁLISES")
        print("="*100)
        print(summary_df.to_string(index=False))
        
        # Estatísticas gerais melhoradas
        total_leagues = len(results)
        competitive_leagues = sum(1 for r in results if r.is_competitive)
        with_rankings = sum(1 for r in results if r.has_ranking_data)
        
        print(f"\n{'='*60}")
        print("ESTATÍSTICAS GERAIS:")
        print(f"{'='*60}")
        print(f"Total de campeonatos analisados: {total_leagues}")
        print(f"Campeonatos com dados de ranking: {with_rankings} ({with_rankings/total_leagues:.1%})")
        print(f"Campeonatos competitivos: {competitive_leagues} ({competitive_leagues/total_leagues:.1%})")
        print(f"Campeonatos não competitivos: {total_leagues-competitive_leagues} ({(total_leagues-competitive_leagues)/total_leagues:.1%})")
        
        if total_leagues - competitive_leagues > 0:
            avg_turning_point = np.mean([r.turning_point_percent for r in results if r.turning_point_percent is not None])
            print(f"Ponto de virada médio: {avg_turning_point:.1%} da temporada")
        
        # Gerar visualizações comparativas
        logger.info("Gerando análise comparativa...")
        analyzer.plot_comparative_analysis(
            save_path=Path(OUTPUT_DIR) / 'comparative_analysis_enhanced.png'
        )
        
        logger.info(f"\nTodos os resultados salvos em: {OUTPUT_DIR}/")
        logger.info("Análise concluída com sucesso!")
        
    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {e}")
        print("ERRO: Certifique-se de que os arquivos estão nos diretórios corretos.")
        
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()