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
import pickle
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import gc

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

# Configurar caminhos base
current_dir = Path(__file__).parent
base_data_dir = current_dir.parent / "data"

@dataclass
class PositionDefinitionResult:
    """Classe para armazenar informações sobre quando as posições foram definidas."""
    champion_round: Optional[int] = None
    second_round: Optional[int] = None
    third_round: Optional[int] = None
    fourth_round: Optional[int] = None
    relegation_rounds: Optional[Dict[int, int]] = None  # {posição: rodada}
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para facilitar exportação."""
        result = {
            'Champion Round': self.champion_round,
            'Second Round': self.second_round,
            'Third Round': self.third_round,
            'Fourth Round': self.fourth_round
        }
        
        if self.relegation_rounds:
            for pos, round_num in self.relegation_rounds.items():
                result[f'Position {pos} Round'] = round_num
                
        return result


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
    position_definitions: Optional[PositionDefinitionResult] = None
    strength_calculation_method: str = "static"  # "static" ou "dynamic"


class PositionDefinitionCalculator:
    """Classe para calcular em que rodada cada posição foi definida."""
    
    def __init__(self, games_df: pd.DataFrame, teams: List[str], total_rounds: int):
        """
        Inicializa o calculador de definição de posições.
        
        Args:
            games_df: DataFrame com os jogos do campeonato
            teams: Lista de times do campeonato
            total_rounds: Número total de rodadas
        """
        self.games_df = games_df
        self.teams = teams
        self.total_rounds = total_rounds
        self.points_progression = self._calculate_points_progression()
        
    def _calculate_points_progression(self) -> Dict[str, List[int]]:
        """Calcula a progressão de pontos de cada time rodada a rodada."""
        points_progression = {team: [0] for team in self.teams}
        
        for round_num in range(1, self.total_rounds + 1):
            round_games = self.games_df[self.games_df['rodada'] == round_num]
            
            # Inicializar pontos da rodada
            round_points = {team: 0 for team in self.teams}
            
            # Processar jogos da rodada
            for _, game in round_games.iterrows():
                home_team = game['home']
                away_team = game['away']
                home_score = game['goal_home']
                away_score = game['goal_away']
                
                # Atribuir pontos
                if home_score > away_score:
                    round_points[home_team] += 3
                elif home_score < away_score:
                    round_points[away_team] += 3
                else:  # Empate
                    round_points[home_team] += 1
                    round_points[away_team] += 1
            
            # Atualizar progressão
            for team in self.teams:
                previous_total = points_progression[team][-1]
                points_progression[team].append(previous_total + round_points[team])
        
        return points_progression
    
    def _get_standings_at_round(self, round_num: int) -> List[Tuple[str, int]]:
        """Retorna a classificação em uma rodada específica."""
        if round_num < 1 or round_num > self.total_rounds:
            return []
        
        team_points = {}
        for team in self.teams:
            team_points[team] = self.points_progression[team][round_num]
        
        # Ordenar por pontos (decrescente)
        return sorted(team_points.items(), key=lambda x: x[1], reverse=True)
    
    def _is_position_defined(self, position: int, round_num: int) -> bool:
        """
        Verifica se uma posição específica já foi definida em uma rodada.
        Uma posição está definida quando o time não pode ser ultrapassado por ninguém abaixo
        E não pode ultrapassar ninguém acima.
        
        Args:
            position: Posição na tabela (1 = campeão, 2 = vice, etc.)
            round_num: Número da rodada
            
        Returns:
            True se a posição já foi matematicamente definida
        """
        if round_num >= self.total_rounds:
            return True  # Última rodada, todas as posições estão definidas
        
        standings = self._get_standings_at_round(round_num)
        if position > len(standings):
            return False
        
        # Time na posição atual
        current_team = standings[position - 1][0]
        current_points = standings[position - 1][1]
        
        # Calcular pontos máximos possíveis para os times
        remaining_rounds = self.total_rounds - round_num
        max_possible_points = remaining_rounds * 3
        
        # 1. Verificar se algum time ABAIXO pode ultrapassar o time atual
        for i in range(position, len(standings)):
            team_below = standings[i][0]
            points_below = standings[i][1]
            
            if points_below + max_possible_points > current_points:
                return False  # Time abaixo pode ultrapassar
        
        # 2. Verificar se o time atual pode ultrapassar algum time ACIMA
        for i in range(position - 1):
            team_above = standings[i][0]
            points_above = standings[i][1]
            
            if current_points + max_possible_points > points_above:
                return False  # Time atual pode ultrapassar alguém acima
        
        return True
    
    def calculate_position_definitions(self) -> PositionDefinitionResult:
        """Calcula em que rodada cada posição foi definida."""
        result = PositionDefinitionResult()
        
        # Calcular para as primeiras 4 posições
        for pos in range(1, 5):
            if pos > len(self.teams):
                break
                
            for round_num in range(1, self.total_rounds + 1):
                if self._is_position_defined(pos, round_num):
                    if pos == 1:
                        result.champion_round = round_num
                    elif pos == 2:
                        result.second_round = round_num
                    elif pos == 3:
                        result.third_round = round_num
                    elif pos == 4:
                        result.fourth_round = round_num
                    break
        
        # Calcular para as últimas 4 posições (rebaixamento)
        result.relegation_rounds = {}
        last_positions = list(range(max(1, len(self.teams) - 3), len(self.teams) + 1))
        
        for pos in last_positions:
            for round_num in range(1, self.total_rounds + 1):
                if self._is_position_defined(pos, round_num):
                    result.relegation_rounds[pos] = round_num
                    break
        
        return result


class DynamicStrengthCalculator:
    """Classe para cálculo dinâmico de forças dos times baseado nas últimas partidas."""
    
    @staticmethod
    def calculate_dynamic_strengths(games_df: pd.DataFrame, teams_list: List[str], 
                                  championship_id: str, current_round: Optional[int] = None) -> Dict[str, float]:
        """
        Calcula forças dos times dinamicamente baseado nas últimas X partidas.
        X = (N-1)*2 onde N é o número de times da liga.
        
        Args:
            games_df: DataFrame com todos os jogos
            teams_list: Lista de times do campeonato
            championship_id: ID do campeonato
            current_round: Rodada atual para cálculo (se None, usa todas as rodadas)
            
        Returns:
            Dicionário com forças normalizadas entre 0 e 1
        """
        # Filtrar jogos do campeonato específico
        champ_games = games_df[games_df['id'] == championship_id].copy()
        
        if champ_games.empty:
            logger.warning(f"Nenhum jogo encontrado para o campeonato {championship_id}")
            return {team: 0.5 for team in teams_list}
        
        # Ordenar por rodada para garantir ordem cronológica
        champ_games = champ_games.sort_values('rodada')
        
        # Se current_round for especificado, filtrar até essa rodada
        if current_round is not None:
            champ_games = champ_games[champ_games['rodada'] <= current_round]
        
        # Calcular X (número de partidas a considerar)
        N = len(teams_list)
        X = (N - 1) * 2  # Fórmula dinâmica
        logger.info(f"Calculando forças dinâmicas: N={N} times, X={X} partidas, Rodada atual: {current_round}")
        
        strengths = {}
        
        for team in teams_list:
            team_strength = DynamicStrengthCalculator._calculate_team_dynamic_strength(
                champ_games, team, X
            )
            strengths[team] = team_strength
        
        # Normalizar forças entre 0 e 1
        strengths = DynamicStrengthCalculator._normalize_strengths(strengths)
        
        logger.info(f"Forças dinâmicas calculadas para {len(strengths)} times")
        logger.info(f"Distribuição - Min: {min(strengths.values()):.3f}, "
                   f"Max: {max(strengths.values()):.3f}, "
                   f"Média: {np.mean(list(strengths.values())):.3f}")
        
        return strengths
    
    @staticmethod
    def _calculate_team_dynamic_strength(games_df: pd.DataFrame, team: str, lookback_games: int) -> float:
        """
        Calcula a força dinâmica de um time baseado nas últimas X partidas.
        
        Args:
            games_df: DataFrame com jogos do campeonato
            team: Nome do time
            lookback_games: Número de partidas para lookback
            
        Returns:
            Força do time não normalizada
        """
        # Encontrar todas as partidas do time
        team_games = games_df[
            (games_df['home'] == team) | (games_df['away'] == team)
        ].copy()
        
        if team_games.empty:
            logger.warning(f"Nenhuma partida encontrada para o time {team}")
            return 0.0
        
        # Ordenar por rodada (mais recentes primeiro)
        team_games = team_games.sort_values('rodada', ascending=False)
        
        # Pegar as últimas X partidas (ou menos se não houver suficientes)
        recent_games = team_games.head(lookback_games)
        
        if len(recent_games) < lookback_games:
            logger.debug(f"Time {team} tem apenas {len(recent_games)} partidas disponíveis "
                        f"(solicitadas: {lookback_games})")
        
        if recent_games.empty:
            return 0.0
        
        total_points = 0
        total_goals_for = 0
        total_goals_against = 0
        games_played = 0
        recent_performance = 0
        
        # Peso maior para partidas mais recentes
        weights = np.linspace(1.0, 0.7, len(recent_games))  # Decrescente
        
        for idx, (_, game) in enumerate(recent_games.iterrows()):
            is_home = game['home'] == team
            is_away = game['away'] == team
            
            if not (is_home or is_away):
                continue
            
            if is_home:
                goals_for = game['goal_home']
                goals_against = game['goal_away']
                home_advantage = 1.1  # Pequeno bônus por jogar em casa
            else:  # is_away
                goals_for = game['goal_away']
                goals_against = game['goal_home']
                home_advantage = 0.9  # Pequena penalidade por jogar fora
            
            # Calcular pontos
            if goals_for > goals_against:
                points = 3
            elif goals_for == goals_against:
                points = 1
            else:
                points = 0
            
            # Aplicar peso temporal
            weight = weights[idx] if idx < len(weights) else 1.0
            
            total_points += points * weight
            total_goals_for += goals_for * weight * home_advantage
            total_goals_against += goals_against * weight
            games_played += 1
        
        if games_played == 0:
            return 0.0
        
        # Calcular métricas de performance
        avg_points = total_points / games_played
        avg_goal_difference = (total_goals_for - total_goals_against) / games_played
        
        # Calcular eficiência ofensiva e defensiva
        offensive_efficiency = total_goals_for / games_played
        defensive_efficiency = 1.0 / (1.0 + total_goals_against / games_played)  # Inverso dos gols sofridos
        
        # Ponderar as métricas
        strength = (
            0.4 * (avg_points / 3.0) +  # Pontos (40%)
            0.2 * ((avg_goal_difference + 3) / 6.0) +  # Saldo de gols (20%)
            0.2 * offensive_efficiency / 3.0 +  # Eficiência ofensiva (20%)
            0.2 * defensive_efficiency  # Eficiência defensiva (20%)
        )
        
        return max(0.0, min(1.0, strength))  # Garantir entre 0 e 1
    
    @staticmethod
    def _normalize_strengths(strengths: Dict[str, float]) -> Dict[str, float]:
        """
        Normaliza as forças para ficarem entre 0 e 1.
        
        Args:
            strengths: Dicionário com forças não normalizadas
            
        Returns:
            Dicionário com forças normalizadas entre 0 e 1
        """
        if not strengths:
            return strengths
        
        values = list(strengths.values())
        min_val = min(values)
        max_val = max(values)
        
        # Se todos os valores forem iguais, retornar 0.5 para todos
        if max_val == min_val:
            return {team: 0.5 for team in strengths.keys()}
        
        normalized = {}
        for team, strength in strengths.items():
            normalized_strength = (strength - min_val) / (max_val - min_val)
            # Suavizar para evitar extremos
            normalized_strength = 0.1 + 0.8 * normalized_strength  # Entre 0.1 e 0.9
            normalized[team] = normalized_strength
        
        return normalized


class RankingProcessor:
    """Classe para processar dados de ranking e calcular forças dos times."""
    
    @staticmethod
    def load_rankings(rankings_df: pd.DataFrame, tournament_id: str, season: str) -> Optional[pd.DataFrame]:
        """
        Carrega rankings para um torneio específico e temporada.
        """
        if rankings_df is None or rankings_df.empty:
            logger.warning(f"DataFrame de rankings está vazio ou None")
            return None
            
        base_tournament = tournament_id
        
        logger.info(f"Buscando rankings para torneio: '{tournament_id}' na temporada '{season}'")
        
        # Busca genérica por nome da liga
        filtered_rankings = rankings_df[
            (rankings_df['tournament'].str.contains(base_tournament, case=False, na=False)) &
            (rankings_df['season'] == season)
        ].copy()

        if filtered_rankings.empty:
            logger.warning(f"Nenhum ranking encontrado para '{base_tournament}' temporada '{season}'")
            return None
            
        logger.info(f"Rankings encontrados para '{base_tournament}' -> '{filtered_rankings['tournament'].iloc[0]}' na temporada '{filtered_rankings['season'].iloc[0]}'.") 
        return filtered_rankings
    
    @staticmethod
    def calculate_team_strengths(rankings_df: pd.DataFrame, teams_list: List[str]) -> Dict[str, float]:
        """
        Calcula forças dos times baseado nos rankings.
        """
        strengths = {}
        
        # Mapear nomes de times
        team_mapping = RankingProcessor._create_team_mapping(rankings_df['Team'].tolist(), teams_list)
        
        # Calcular força baseada na posição inversa
        max_position = len(rankings_df)
        
        for _, row in rankings_df.iterrows():
            team_name = row['Team']
            mapped_name = team_mapping.get(team_name, team_name)
            
            if mapped_name in teams_list:
                position_strength = (max_position - row.get('#', max_position)) / max_position
                
                if 'Pts' in row and pd.notna(row['Pts']):
                    max_pts = rankings_df['Pts'].max()
                    min_pts = rankings_df['Pts'].min()
                    if max_pts > min_pts:
                        points_strength = (row['Pts'] - min_pts) / (max_pts - min_pts)
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
            
            # Busca por similaridade
            ranking_clean = RankingProcessor._clean_team_name(ranking_team)
            
            best_match = None
            best_similarity = 0
            
            for actual_team in actual_teams:
                actual_clean = RankingProcessor._clean_team_name(actual_team)
                
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
        clean = re.sub(r'[^\w\s]', '', str(name).lower())
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean


class ImprovedMatchSimulator:
    """Simulador de partidas melhorado com base nas forças dos times."""
    
    def __init__(self, team_strengths: Optional[Dict[str, float]] = None):
        self.team_strengths = team_strengths or {}
        self.home_advantage = 0.1
    
    def calculate_match_probabilities(self, home_team: str, away_team: str, 
                                    global_ph: float, global_pd: float, global_pa: float) -> Tuple[float, float, float]:
        """
        Calcula probabilidades específicas para uma partida baseada nas forças dos times.
        """
        if not self.team_strengths:
            return global_ph, global_pd, global_pa
        
        home_strength = self.team_strengths.get(home_team, 0.5)
        away_strength = self.team_strengths.get(away_team, 0.5)
        
        home_strength_adj = min(0.95, home_strength + self.home_advantage)
        strength_diff = home_strength_adj - away_strength
        
        def sigmoid(x, sharpness=3):
            return 1 / (1 + np.exp(-sharpness * x))
        
        base_home_prob = sigmoid(strength_diff)
        blend_factor = 0.7
        
        ph_adjusted = blend_factor * base_home_prob + (1 - blend_factor) * global_ph
        remaining_prob = 1 - ph_adjusted
        total_global_remaining = global_pd + global_pa
        
        if total_global_remaining > 0:
            pd_adjusted = remaining_prob * (global_pd / total_global_remaining)
            pa_adjusted = remaining_prob * (global_pa / total_global_remaining)
        else:
            pd_adjusted = remaining_prob * 0.3
            pa_adjusted = remaining_prob * 0.7
        
        total = ph_adjusted + pd_adjusted + pa_adjusted
        if total > 0:
            return ph_adjusted/total, pd_adjusted/total, pa_adjusted/total
        else:
            return global_ph, global_pd, global_pa
    
    def simulate_match_result(self, home_team: str, away_team: str,
                            global_ph: float, global_pd: float, global_pa: float) -> Tuple[int, int]:
        """
        Simula o resultado de uma partida.
        """
        ph, pd, pa = self.calculate_match_probabilities(home_team, away_team, global_ph, global_pd, global_pa)
        
        rand = np.random.random()
        
        if rand < ph:
            return np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2]), np.random.choice([0, 1], p=[0.7, 0.3])
        elif rand < ph + pd:
            score = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
            return score, score
        else:
            return np.random.choice([0, 1], p=[0.7, 0.3]), np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])


class DataValidator:
    """Classe para validação e limpeza de dados."""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Valida e limpa o DataFrame de entrada."""
        required_columns = ['id', 'rodada', 'home', 'away', 'goal_home', 'goal_away']
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
        
        df_clean = df.copy()
        
        for col in ['goal_home', 'goal_away']:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        df_clean['rodada'] = pd.to_numeric(df_clean['rodada'], errors='coerce')
        df_clean = df_clean.dropna(subset=['goal_home', 'goal_away', 'rodada'])
        
        invalid_goals = df_clean[(df_clean['goal_home'] < 0) | (df_clean['goal_away'] < 0)]
        if not invalid_goals.empty:
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
        df_clean['#'] = pd.to_numeric(df_clean['#'], errors='coerce')
        
        if 'Pts' in df_clean.columns:
            df_clean['Pts'] = pd.to_numeric(df_clean['Pts'], errors='coerce')
        
        df_clean = df_clean.dropna(subset=['#'])
        
        return df_clean


class OptimizedCompetitiveBalanceAnalyzer:
    """Versão otimizada do analisador com melhorias de performance."""
    
    def __init__(self, games_df: pd.DataFrame, championship_id: str,
                 rankings_df: Optional[pd.DataFrame] = None,
                 alpha: float = 0.05, num_simulations: int = 100,
                 current_season_weight: float = 0.5,
                 optimize_simulations: bool = True,
                 use_vectorization: bool = True,
                 use_dynamic_strengths: bool = True):
        """
        Inicializa o analisador de competitividade otimizado.
        
        Args:
            use_dynamic_strengths: Se True, usa forças dinâmicas baseadas nas últimas partidas
        """
        self.alpha = alpha
        self.num_simulations = num_simulations
        self.championship_id = championship_id
        self.rankings_df = rankings_df
        self.current_season_weight = current_season_weight
        self.optimize_simulations = optimize_simulations
        self.use_vectorization = use_vectorization
        self.use_dynamic_strengths = use_dynamic_strengths
        
        self.season_games = games_df[
            games_df['id'] == championship_id
        ].copy().sort_values(['rodada', 'home'])
        
        if self.season_games.empty:
            raise ValueError(f"Nenhum jogo encontrado para: {championship_id}")
        
        self._initialize_championship_info()
        self._load_team_strengths()
        self._reset_results()
        self._calculate_position_definitions()
        
    def _initialize_championship_info(self):
        """Inicializa informações do campeonato."""
        self.league = self._extract_league_name()
        self.season = self._extract_season()
        
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
            if '@' in self.championship_id and '/' in self.championship_id:
                path_parts = self.championship_id.split('/')
                if len(path_parts) > 3:
                    liga_temporada = path_parts[3].rstrip('/')
                    if '-' in liga_temporada:
                        parts = liga_temporada.split('-')
                        for i, part in enumerate(parts):
                            if part.isdigit() and len(part) == 4:
                                return '-'.join(parts[:i])
                        return liga_temporada
                    return liga_temporada
                else:
                    return self.championship_id.split('@')[0]
            elif '@' in self.championship_id:
                return self.championship_id.split('@')[0]
            else:
                return self.championship_id
        except Exception as e:
            logger.warning(f"Erro ao extrair nome da liga de '{self.championship_id}': {e}")
            return "Liga Desconhecida"
    
    def _extract_season(self) -> str:
        """Extrai a temporada do ID."""
        try:
            if '@' in self.championship_id and '/' in self.championship_id:
                path_parts = self.championship_id.split('/')
                if len(path_parts) > 3:
                    liga_temporada = path_parts[3].rstrip('/')
                    if '-' in liga_temporada:
                        parts = liga_temporada.split('-')
                        for i, part in enumerate(parts):
                            if part.isdigit() and len(part) == 4:
                                season_parts = parts[i:]
                                if len(season_parts) == 1:
                                    return season_parts[0]
                                elif len(season_parts) == 2 and season_parts[1].isdigit() and len(season_parts[1]) == 4:
                                    return f"{season_parts[0]}-{season_parts[1]}"
                                else:
                                    return season_parts[0]
                        import re
                        year_match = re.search(r'(\d{4}(?:-\d{4})?)', liga_temporada)
                        return year_match.group(1) if year_match else "Temporada Desconhecida"
                    else:
                        import re
                        year_match = re.search(r'(\d{4})$', liga_temporada)
                        return year_match.group(1) if year_match else "Temporada Desconhecida"
            elif '@' in self.championship_id:
                path_part = self.championship_id.split('@')[1]
                import re
                year_match = re.search(r'(\d{4}(?:-\d{4})?)', path_part)
                return year_match.group(1) if year_match else "Temporada Desconhecida"
            return "Temporada Desconhecida"
        except Exception as e:
            logger.warning(f"Erro ao extrair temporada de '{self.championship_id}': {e}")
            return "Temporada Desconhecida"
    
    def _load_team_strengths(self):
        """Carrega forças dos times usando método dinâmico ou rankings."""
        self.team_strengths = {}
        self.has_ranking_data = False
        self.strength_calculation_method = "static"
        
        # Usar forças dinâmicas se solicitado
        if self.use_dynamic_strengths:
            try:
                # Usar todos os jogos disponíveis para cálculo dinâmico
                self.team_strengths = DynamicStrengthCalculator.calculate_dynamic_strengths(
                    games_df=self.season_games,
                    teams_list=self.teams,
                    championship_id=self.championship_id
                )
                self.has_ranking_data = True
                self.strength_calculation_method = "dynamic"
                logger.info(f"Forças dinâmicas calculadas para {len(self.team_strengths)} times")
                
                # Calcular variância das forças
                if self.team_strengths:
                    self.strength_variance = np.var(list(self.team_strengths.values()))
                    logger.info(f"Variância das forças dinâmicas: {self.strength_variance:.4f}")
                
                self.match_simulator = ImprovedMatchSimulator(self.team_strengths)
                return
                
            except Exception as e:
                logger.error(f"Erro ao calcular forças dinâmicas: {e}. Continuando com métodos tradicionais.")
        
        # Método tradicional com rankings
        if self.rankings_df is None:
            self.match_simulator = ImprovedMatchSimulator(self.team_strengths)
            return

        # Tentar carregar rankings da temporada anterior
        prev_season = self.season
        try:
            if '-' in self.season:
                start_year, end_year = map(int, self.season.split('-'))
                prev_season = f"{start_year - 1}-{end_year - 1}"
            elif self.season.isdigit():
                prev_season = str(int(self.season) - 1)
        except (ValueError, IndexError):
            logger.warning(f"Formato de temporada inválido: '{self.season}'.")
            prev_season = self.season
            
        rankings_prev = RankingProcessor.load_rankings(self.rankings_df, self.league, prev_season)
        strengths_prev = {}
        if rankings_prev is not None:
            strengths_prev = RankingProcessor.calculate_team_strengths(rankings_prev, self.teams)
            logger.info(f"Carregadas forças da temporada anterior ({prev_season}) para {len(strengths_prev)} times.")

        # Tentar carregar rankings da temporada atual
        rankings_curr = RankingProcessor.load_rankings(self.rankings_df, self.league, self.season)
        strengths_curr = {}
        if rankings_curr is not None:
            strengths_curr = RankingProcessor.calculate_team_strengths(rankings_curr, self.teams)
            logger.info(f"Carregadas forças da temporada atual ({self.season}) para {len(strengths_curr)} times.")

        # Combinar as forças
        if not strengths_prev and not strengths_curr:
            logger.warning("Nenhum dado de ranking encontrado. Simulação será probabilística simples.")
            self.match_simulator = ImprovedMatchSimulator(self.team_strengths)
            return

        combined_strengths = {}
        w_curr = self.current_season_weight
        w_prev = 1.0 - w_curr

        for team in self.teams:
            s_prev = strengths_prev.get(team, 0.5)
            s_curr = strengths_curr.get(team, 0.5)
            
            if not strengths_prev:
                final_strength = s_curr
            elif not strengths_curr:
                final_strength = s_prev
            else:
                final_strength = (w_prev * s_prev) + (w_curr * s_curr)
            
            combined_strengths[team] = final_strength
            
        self.team_strengths = combined_strengths
        self.has_ranking_data = True
        self.strength_calculation_method = "static"
        
        # Normalizar as forças combinadas
        if self.team_strengths:
            mean_val = np.mean(list(self.team_strengths.values()))
            min_val, max_val = min(self.team_strengths.values()), max(self.team_strengths.values())
            
            if max_val > min_val:
                for team in self.team_strengths:
                    norm_strength = (self.team_strengths[team] - min_val) / (max_val - min_val)
                    self.team_strengths[team] = 0.1 + 0.8 * norm_strength

        self.strength_variance = np.var(list(self.team_strengths.values()))
        
        logger.info(f"Forças combinadas de {len(self.team_strengths)} times calculadas (Peso atual: {w_curr*100}%)")
        logger.info(f"Variância final das forças: {self.strength_variance:.4f}")

        self.match_simulator = ImprovedMatchSimulator(self.team_strengths)
        
    def _calculate_position_definitions(self):
        """Calcula em que rodada cada posição foi definida."""
        try:
            calculator = PositionDefinitionCalculator(
                games_df=self.season_games,
                teams=self.teams,
                total_rounds=self.total_rounds
            )
            self.position_definitions = calculator.calculate_position_definitions()
            logger.info("Cálculo de definição de posições concluído")
        except Exception as e:
            logger.error(f"Erro ao calcular definição de posições: {e}")
            self.position_definitions = None
        
    def _reset_results(self):
        """Reseta variáveis de resultado."""
        self.observed_imbalance_curve = None
        self.simulation_curves = None
        self.envelope_upper_bound = None
        self.ph = self.pd = self.pa = None
        
    def _calculate_points_progression_optimized(self, games_schedule: pd.DataFrame) -> np.ndarray:
        """
        Versão otimizada do cálculo de progressão de pontos.
        """
        # Converter para arrays numpy para operações vetorizadas
        teams_array = np.array(self.teams)
        team_indices = {team: idx for idx, team in enumerate(self.teams)}
        
        # Inicializar matriz de pontos
        points_matrix = np.zeros((len(self.teams), self.total_rounds + 1), dtype=int)
        
        # Pré-processar jogos por rodada
        for round_num in range(1, self.total_rounds + 1):
            round_games = games_schedule[games_schedule['rodada'] == round_num]
            
            # Operações vetorizadas
            for _, game in round_games.iterrows():
                home_team = game['home']
                away_team = game['away']
                home_score = game['goal_home']
                away_score = game['goal_away']
                
                home_idx = team_indices[home_team]
                away_idx = team_indices[away_team]
                
                if home_score > away_score:
                    points_matrix[home_idx, round_num] += 3
                elif home_score < away_score:
                    points_matrix[away_idx, round_num] += 3
                else:  # empate
                    points_matrix[home_idx, round_num] += 1
                    points_matrix[away_idx, round_num] += 1
        
        # Acumular pontos
        points_cumulative = np.cumsum(points_matrix, axis=1)
        
        # Calcular variância normalizada rodada a rodada
        variance_curve = []
        for round_num in range(1, self.total_rounds + 1):
            points_round = points_cumulative[:, round_num]
            if len(points_round) > 1:
                variance = np.var(points_round, ddof=0)
                theoretical_max_var = self._calculate_theoretical_max_variance(round_num)
                normalized_variance = variance / theoretical_max_var if theoretical_max_var > 0 else 0
            else:
                normalized_variance = 0
            variance_curve.append(normalized_variance)
        
        return np.array(variance_curve)
    
    def _calculate_theoretical_max_variance(self, round_num: int) -> float:
        """Calcula a variância teórica máxima para uma rodada."""
        if self.num_teams <= 1:
            return 1.0
        
        dominant_teams = max(1, int(0.2 * self.num_teams))
        weak_teams = self.num_teams - dominant_teams
        
        total_points = round_num * 3 * self.num_teams // 2
        points_dominant = int(0.8 * total_points) // dominant_teams
        points_weak = int(0.2 * total_points) // weak_teams if weak_teams > 0 else 0
        
        points_dist = [points_dominant] * dominant_teams + [points_weak] * weak_teams
        return np.var(points_dist, ddof=0)
    
    def calculate_observed_imbalance(self):
        """Calcula a curva de desequilíbrio observada."""
        try:
            self.observed_imbalance_curve = self._calculate_points_progression_optimized(self.season_games)
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
    
    def run_null_model_optimized(self):
        """Versão otimizada do modelo nulo."""
        logger.info("Iniciando modelo nulo otimizado...")
        
        self._calculate_match_probabilities()
        template_games = self.season_games[['rodada', 'home', 'away']].copy()
        
        # Pré-alocar array para resultados
        self.simulation_curves = np.zeros((self.num_simulations, self.total_rounds))
        
        if self.use_vectorization and not self.has_ranking_data:
            # Versão vetorizada para simulação sem rankings
            self._run_vectorized_simulations(template_games)
        else:
            # Versão com otimizações para simulação com rankings
            self._run_optimized_rankings_simulations(template_games)
    
    def _run_vectorized_simulations(self, template_games: pd.DataFrame):
        """Executa simulações vetorizadas."""
        n_games = len(template_games)
        
        for sim in range(self.num_simulations):
            if (sim + 1) % max(1, self.num_simulations // 10) == 0:
                logger.info(f"Progresso: {sim + 1}/{self.num_simulations}")
            
            # Gerar todos os resultados de uma vez
            random_vals = np.random.random(n_games)
            home_wins = random_vals < self.ph
            draws = (random_vals >= self.ph) & (random_vals < self.ph + self.pd)
            
            # Criar DataFrame simulado de forma eficiente
            simulated_games = template_games.copy()
            simulated_games['goal_home'] = 0
            simulated_games['goal_away'] = 0
            
            # Atribuir resultados de forma vetorizada
            simulated_games.loc[home_wins, 'goal_home'] = 2
            simulated_games.loc[home_wins, 'goal_away'] = 0
            
            simulated_games.loc[draws, 'goal_home'] = 1
            simulated_games.loc[draws, 'goal_away'] = 1
            
            away_wins = ~(home_wins | draws)
            simulated_games.loc[away_wins, 'goal_home'] = 0
            simulated_games.loc[away_wins, 'goal_away'] = 2
            
            # Calcular curva
            sim_curve = self._calculate_points_progression_optimized(simulated_games)
            self.simulation_curves[sim] = sim_curve
    
    def _run_optimized_rankings_simulations(self, template_games: pd.DataFrame):
        """Versão otimizada para simulações com rankings."""
        # Cache para probabilidades calculadas
        probability_cache = {}
        
        for sim in range(self.num_simulations):
            if (sim + 1) % max(1, self.num_simulations // 10) == 0:
                logger.info(f"Progresso: {sim + 1}/{self.num_simulations}")
            
            simulated_games = template_games.copy()
            
            for idx, row in simulated_games.iterrows():
                home_team, away_team = row['home'], row['away']
                cache_key = f"{home_team}_{away_team}"
                
                if cache_key in probability_cache:
                    ph, pd, pa = probability_cache[cache_key]
                else:
                    ph, pd, pa = self.match_simulator.calculate_match_probabilities(
                        home_team, away_team, self.ph, self.pd, self.pa
                    )
                    probability_cache[cache_key] = (ph, pd, pa)
                
                # Simular resultado
                rand = np.random.random()
                if rand < ph:
                    home_goals = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
                    away_goals = np.random.choice([0, 1], p=[0.7, 0.3])
                elif rand < ph + pd:
                    goals = np.random.choice([0, 1, 2], p=[0.3, 0.5, 0.2])
                    home_goals = away_goals = goals
                else:
                    home_goals = np.random.choice([0, 1], p=[0.7, 0.3])
                    away_goals = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
                
                simulated_games.loc[idx, 'goal_home'] = home_goals
                simulated_games.loc[idx, 'goal_away'] = away_goals
            
            sim_curve = self._calculate_points_progression_optimized(simulated_games)
            self.simulation_curves[sim] = sim_curve

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
        strength_method = "dinâmico" if self.strength_calculation_method == "dynamic" else "estático"
        logger.info(f"Envelope de confiança calculado (α={self.alpha}, {simulation_type}, método: {strength_method})")
        
    def find_turning_point(self) -> Tuple[Optional[int], Optional[float]]:
        """Encontra o ponto de virada com critérios mais rigorosos."""
        if self.observed_imbalance_curve is None or self.envelope_upper_bound is None:
            raise ValueError("Execute os cálculos da análise primeiro")
        
        min_consecutive_rounds = max(3, int(0.1 * self.total_rounds))
        min_percentage_above = 0.7
        
        if self.has_ranking_data:
            min_percentage_above = 0.75
        
        for round_idx in range(len(self.observed_imbalance_curve) - min_consecutive_rounds):
            if self.observed_imbalance_curve[round_idx] > self.envelope_upper_bound[round_idx]:
                
                consecutive_above = 0
                for i in range(round_idx, min(round_idx + min_consecutive_rounds, len(self.observed_imbalance_curve))):
                    if self.observed_imbalance_curve[i] > self.envelope_upper_bound[i]:
                        consecutive_above += 1
                    else:
                        break
                
                if consecutive_above >= min_consecutive_rounds:
                    remaining_rounds = self.observed_imbalance_curve[round_idx:]
                    remaining_envelope = self.envelope_upper_bound[round_idx:]
                    
                    above_envelope = np.sum(remaining_rounds > remaining_envelope)
                    if above_envelope / len(remaining_rounds) >= min_percentage_above:
                        tau = round_idx + 1
                        tau_percent = tau / self.total_rounds
                        return tau, tau_percent
        
        return None, None

    def save_round_by_round_data(self, save_path: str):
        """Salva os dados de competitividade rodada a rodada."""
        if self.observed_imbalance_curve is None or self.envelope_upper_bound is None:
            raise ValueError("Execute a análise primeiro")
        
        # Garantir que o diretório existe
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        round_data = []
        tau, _ = self.find_turning_point()
        
        for round_idx in range(len(self.observed_imbalance_curve)):
            round_num = round_idx + 1
            round_data.append({
                'championship_id': self.championship_id,
                'rodada': round_num,
                'observed_imbalance': self.observed_imbalance_curve[round_idx],
                'envelope_upper': self.envelope_upper_bound[round_idx],
                'is_turning_point': (tau == round_num)
            })
        
        df_round = pd.DataFrame(round_data)
        df_round.to_csv(save_path, index=False)
        logger.info(f"Dados rodada a rodada salvos em: {save_path}")
        
    def plot_results(self, save_path: Optional[str] = None, show_simulations: bool = True):
        """Plota os resultados com melhor visualização."""
        if self.observed_imbalance_curve is None:
            raise ValueError("Execute a análise primeiro")
        
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 1], width_ratios=[2, 1])
        
        ax_main = fig.add_subplot(gs[0, :])
        rounds = np.arange(1, len(self.observed_imbalance_curve) + 1)
        
        if self.envelope_upper_bound is not None:
            ax_main.fill_between(rounds, 0, self.envelope_upper_bound, 
                               alpha=0.3, color='lightblue', 
                               label=f'Envelope {(1-self.alpha)*100:.0f}% confiança')
            ax_main.plot(rounds, self.envelope_upper_bound, '--', 
                        color='blue', alpha=0.8, linewidth=2)
        
        if self.simulation_curves is not None and show_simulations:
            sample_sims = np.random.choice(len(self.simulation_curves), 
                                         min(20, len(self.simulation_curves)), 
                                         replace=False)
            for i in sample_sims:
                ax_main.plot(rounds, self.simulation_curves[i], '-', 
                           alpha=0.1, color='gray', linewidth=0.5)
        
        ax_main.plot(rounds, self.observed_imbalance_curve, 'r-', 
                    linewidth=3, label='Observado', marker='o', markersize=3)
        
        tau, tau_percent = self.find_turning_point()
        if tau is not None:
            ax_main.axvline(x=tau, color='red', linestyle=':', alpha=0.7, linewidth=2,
                           label=f'Ponto de virada (rodada {tau})')
            ax_main.text(tau + 1, ax_main.get_ylim()[1] * 0.8, 
                        f'Rodada {tau}\n({tau_percent:.1%})', 
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
        
        simulation_method = "com Rankings" if self.has_ranking_data else "Probabilístico"
        strength_method = "Dinâmico" if self.strength_calculation_method == "dynamic" else "Estático"
        title = f'Análise de Competitividade - {self.league} {self.season}\n(Simulação: {simulation_method}, Forças: {strength_method})'
        ax_main.set_title(title, fontsize=14, fontweight='bold')
        
        ax_main.set_xlabel('Rodada', fontsize=12)
        ax_main.set_ylabel('Desequilíbrio Normalizado', fontsize=12)
        ax_main.legend(fontsize=10)
        ax_main.grid(True, alpha=0.3)
        
        ax_hist = fig.add_subplot(gs[1, 0])
        if self.simulation_curves is not None:
            final_simulated = self.simulation_curves[:, -1]
            final_observed = self.observed_imbalance_curve[-1]
            
            ax_hist.hist(final_simulated, bins=30, alpha=0.7, color='lightblue', 
                        density=True, label='Simulações (final)')
            ax_hist.axvline(final_observed, color='red', linestyle='-', linewidth=3,
                           label=f'Observado: {final_observed:.3f}')
            
            percentile = (np.sum(final_simulated < final_observed) / len(final_simulated)) * 100
            ax_hist.text(0.05, 0.95, f'Percentil: {percentile:.1f}%',
                        transform=ax_hist.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
            
            ax_hist.set_xlabel('Desequilíbrio Final', fontsize=10)
            ax_hist.set_ylabel('Densidade', fontsize=10)
            ax_hist.set_title('Distribuição Final', fontsize=11)
            ax_hist.legend(fontsize=9)
            ax_hist.grid(True, alpha=0.3)
        
        ax_info = fig.add_subplot(gs[1, 1])
        ax_info.axis('off')
        
        info_text = f"INFORMAÇÕES DO CAMPEONATO\n\n"
        info_text += f"Times: {self.num_teams}\n"
        info_text += f"Rodadas: {self.total_rounds}\n"
        info_text += f"Simulações: {self.num_simulations}\n"
        info_text += f"Método Forças: {self.strength_calculation_method.upper()}\n\n"
        info_text += f"Probabilidades Globais:\n"
        info_text += f"  Casa: {self.ph:.3f}\n"
        info_text += f"  Empate: {self.pd:.3f}\n"
        info_text += f"  Visitante: {self.pa:.3f}\n\n"
        
        if self.position_definitions:
            info_text += f"DEFINIÇÃO DE POSIÇÕES:\n"
            if self.position_definitions.champion_round:
                info_text += f"  Campeão: Rodada {self.position_definitions.champion_round}\n"
            if self.position_definitions.second_round:
                info_text += f"  Vice: Rodada {self.position_definitions.second_round}\n"
            if self.position_definitions.third_round:
                info_text += f"  3º Lugar: Rodada {self.position_definitions.third_round}\n"
            if self.position_definitions.fourth_round:
                info_text += f"  4º Lugar: Rodada {self.position_definitions.fourth_round}\n"
            
            if self.position_definitions.relegation_rounds:
                info_text += f"  Rebaixamento:\n"
                for pos, round_num in sorted(self.position_definitions.relegation_rounds.items()):
                    info_text += f"    Posição {pos}: Rodada {round_num}\n"
            info_text += "\n"
        
        if self.has_ranking_data:
            info_text += f"DADOS DE FORÇAS:\n"
            info_text += f"Variância das forças: {self.strength_variance:.4f}\n"
            info_text += f"Método: {self.strength_calculation_method.upper()}\n\n"
        else:
            info_text += f"SEM DADOS DE FORÇAS\n"
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
        
        if self.has_ranking_data and self.team_strengths:
            ax_strength = fig.add_subplot(gs[2, :])
            
            teams = list(self.team_strengths.keys())
            strengths = list(self.team_strengths.values())
            
            sorted_data = sorted(zip(teams, strengths), key=lambda x: x[1], reverse=True)
            teams_sorted, strengths_sorted = zip(*sorted_data)
            
            colors = ['darkred' if s > 0.7 else 'red' if s > 0.6 else 'orange' if s > 0.4 else 'lightblue' if s > 0.3 else 'blue' 
                     for s in strengths_sorted]
            
            bars = ax_strength.bar(range(len(teams_sorted)), strengths_sorted, color=colors, alpha=0.7)
            ax_strength.set_xticks(range(len(teams_sorted)))
            ax_strength.set_xticklabels(teams_sorted, rotation=45, ha='right', fontsize=8)
            ax_strength.set_ylabel('Força do Time', fontsize=10)
            ax_strength.set_title(f'Forças dos Times (método: {self.strength_calculation_method})', fontsize=11)
            ax_strength.grid(True, alpha=0.3, axis='y')
            
            mean_strength = np.mean(strengths_sorted)
            ax_strength.axhline(y=mean_strength, color='black', linestyle='--', alpha=0.5, label=f'Média: {mean_strength:.3f}')
            ax_strength.legend(fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            # Garantir que o diretório existe
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Gráfico salvo em: {save_path}")
        
        plt.close(fig)
        
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
            strength_variance=self.strength_variance,
            position_definitions=self.position_definitions,
            strength_calculation_method=self.strength_calculation_method
        )


class ParallelLeagueAnalyzer:
    """Versão paralelizada do analisador de ligas."""
    
    def __init__(self, alpha: float = 0.05, num_simulations: int = 500,
                 current_season_weight: float = 0.5, max_workers: int = None,
                 use_dynamic_strengths: bool = True):
        self.alpha = alpha
        self.num_simulations = num_simulations
        self.current_season_weight = current_season_weight
        self.max_workers = max_workers or mp.cpu_count()
        self.use_dynamic_strengths = use_dynamic_strengths
        
    def _analyze_single_championship(self, args):
        """Função auxiliar para análise de um único campeonato."""
        champ_id, df_clean, df_rankings_clean, output_dir, save_round_data = args
        
        try:
            analyzer = OptimizedCompetitiveBalanceAnalyzer(
                games_df=df_clean,
                championship_id=champ_id,
                rankings_df=df_rankings_clean,
                alpha=self.alpha,
                num_simulations=self.num_simulations,
                current_season_weight=self.current_season_weight,
                optimize_simulations=True,
                use_vectorization=True,
                use_dynamic_strengths=self.use_dynamic_strengths
            )
            
            analyzer.calculate_observed_imbalance()
            analyzer.run_null_model_optimized()
            analyzer.calculate_confidence_envelope()
            
            # Salvar dados por rodada se solicitado
            if output_dir and save_round_data:
                round_filename = f"round_data_{champ_id.replace('/', '_').replace('@', '_')}.csv"
                round_path = Path(output_dir) / round_filename
                analyzer.save_round_by_round_data(round_path)
            
            result = analyzer.get_analysis_result()
            logger.info(f"Concluído: {champ_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro em {champ_id}: {e}")
            return None

    def analyze_all_leagues_parallel(self, df_jogos: pd.DataFrame, 
                                   df_rankings: Optional[pd.DataFrame] = None,
                                   output_dir: Optional[str] = None,
                                   save_plots: bool = False,
                                   save_round_data: bool = True,
                                   chunk_size: int = 10) -> List[AnalysisResult]:
        """
        Versão paralelizada da análise de múltiplas ligas.
        """
        logger.info("Validando dados...")
        df_clean = DataValidator.validate_dataframe(df_jogos)
        
        df_rankings_clean = None
        if df_rankings is not None:
            try:
                df_rankings_clean = DataValidator.validate_rankings_dataframe(df_rankings)
            except Exception as e:
                logger.warning(f"Erro nos rankings: {e}")
        
        championship_ids = df_clean['id'].unique()
        logger.info(f"Analisando {len(championship_ids)} campeonatos com {self.max_workers} processos")
        
        # Garantir que o diretório de saída existe
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Preparar argumentos
        tasks = []
        for champ_id in championship_ids:
            tasks.append((champ_id, df_clean, df_rankings_clean, output_dir, save_round_data))
        
        # Processar em chunks para evitar sobrecarga de memória
        results = []
        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i:i + chunk_size]
            
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_champ = {
                    executor.submit(self._analyze_single_championship, task): task[0] 
                    for task in chunk
                }
                
                for future in as_completed(future_to_champ):
                    champ_id = future_to_champ[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Falha em {champ_id}: {e}")
            
            logger.info(f"Progresso: {min(i + chunk_size, len(tasks))}/{len(tasks)}")
            
            # Limpar memória entre chunks
            gc.collect()
        
        return results


class BatchLeagueProcessor:
    """Processador em lotes com checkpoint e retomada de processamento."""
    
    def __init__(self, batch_size: int = 20, checkpoint_interval: int = 5,
                 use_dynamic_strengths: bool = True):
        self.batch_size = batch_size
        self.checkpoint_interval = checkpoint_interval
        self.use_dynamic_strengths = use_dynamic_strengths
        
    def process_in_batches(self, df_jogos: pd.DataFrame, 
                         df_rankings: Optional[pd.DataFrame] = None,
                         output_dir: Optional[str] = None,
                         alpha: float = 0.05,
                         num_simulations: int = 200,
                         current_season_weight: float = 0.5,
                         resume: bool = True) -> List[AnalysisResult]:
        """
        Processa ligas em lotes com capacidade de retomada.
        """
        checkpoint_file = Path(output_dir) / "processing_checkpoint.pkl" if output_dir else None
        completed_ids = set()
        results = []
        
        # Garantir que o diretório de saída existe
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Tentar retomar processamento anterior
        if resume and checkpoint_file and checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'rb') as f:
                    checkpoint_data = pickle.load(f)
                completed_ids = set(checkpoint_data.get('completed_ids', []))
                results = checkpoint_data.get('results', [])
                logger.info(f"Retomando processamento: {len(completed_ids)} ligas concluídas")
            except Exception as e:
                logger.warning(f"Erro ao carregar checkpoint: {e}")
        
        df_clean = DataValidator.validate_dataframe(df_jogos)
        championship_ids = [cid for cid in df_clean['id'].unique() 
                          if cid not in completed_ids]
        
        total_batches = (len(championship_ids) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(0, len(championship_ids), self.batch_size):
            batch_ids = championship_ids[batch_idx:batch_idx + self.batch_size]
            logger.info(f"Processando lote {batch_idx//self.batch_size + 1}/{total_batches}")
            
            batch_results = self._process_batch(
                batch_ids, df_clean, df_rankings, output_dir,
                alpha, num_simulations, current_season_weight
            )
            results.extend(batch_results)
            
            # Atualizar checkpoint
            completed_ids.update(batch_ids)
            if checkpoint_file and (batch_idx % (self.checkpoint_interval * self.batch_size) == 0 or 
                                  batch_idx + self.batch_size >= len(championship_ids)):
                self._save_checkpoint(checkpoint_file, completed_ids, results)
            
            # Limpar memória entre lotes
            gc.collect()
        
        # Limpar checkpoint ao finalizar
        if checkpoint_file and checkpoint_file.exists():
            checkpoint_file.unlink()
            
        return results
    
    def _process_batch(self, batch_ids: List[str], df_clean: pd.DataFrame,
                     df_rankings: pd.DataFrame, output_dir: str,
                     alpha: float, num_simulations: int, current_season_weight: float) -> List[AnalysisResult]:
        """Processa um lote de ligas."""
        batch_results = []
        
        for champ_id in batch_ids:
            try:
                analyzer = OptimizedCompetitiveBalanceAnalyzer(
                    games_df=df_clean,
                    championship_id=champ_id,
                    rankings_df=df_rankings,
                    alpha=alpha,
                    num_simulations=num_simulations,
                    current_season_weight=current_season_weight,
                    optimize_simulations=True,
                    use_vectorization=True,
                    use_dynamic_strengths=self.use_dynamic_strengths
                )
                
                analyzer.calculate_observed_imbalance()
                analyzer.run_null_model_optimized()
                analyzer.calculate_confidence_envelope()
                
                result = analyzer.get_analysis_result()
                batch_results.append(result)
                
                # Salvar dados por rodada
                if output_dir:
                    round_filename = f"round_data_{champ_id.replace('/', '_').replace('@', '_')}.csv"
                    round_path = Path(output_dir) / round_filename
                    analyzer.save_round_by_round_data(round_path)
                
            except Exception as e:
                logger.error(f"Erro em {champ_id}: {e}")
                continue
        
        return batch_results
    
    def _save_checkpoint(self, checkpoint_file: Path, completed_ids: set, results: List[AnalysisResult]):
        """Salva ponto de controle."""
        try:
            # Garantir que o diretório existe
            checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            
            checkpoint_data = {
                'completed_ids': list(completed_ids),
                'results': [r.__dict__ for r in results]
            }
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            logger.info(f"Checkpoint salvo: {len(completed_ids)} ligas processadas")
        except Exception as e:
            logger.warning(f"Erro ao salvar checkpoint: {e}")


class MultiLeagueAnalyzer:
    """Analisador para múltiplos campeonatos com suporte a paralelização e lotes."""
    
    def __init__(self, alpha: float = 0.05, num_simulations: int = 500,
                 current_season_weight: float = 0.5, max_workers: int = None,
                 processing_mode: str = "parallel",
                 use_dynamic_strengths: bool = True):
        self.alpha = alpha
        self.num_simulations = num_simulations
        self.current_season_weight = current_season_weight
        self.max_workers = max_workers or mp.cpu_count()
        self.processing_mode = processing_mode
        self.use_dynamic_strengths = use_dynamic_strengths
        self.results: List[AnalysisResult] = []
        
    def analyze_all_leagues(self, df_jogos: pd.DataFrame, 
                          df_rankings: Optional[pd.DataFrame] = None,
                          output_dir: Optional[str] = None,
                          save_plots: bool = False,
                          save_round_data: bool = True,
                          batch_size: int = 10,
                          resume: bool = True) -> List[AnalysisResult]:
        """
        Executa análise para todos os campeonatos usando o modo selecionado.
        """
        logger.info(f"Iniciando análise no modo: {self.processing_mode}")
        logger.info(f"Usando forças dinâmicas: {self.use_dynamic_strengths}")
        
        # Garantir que o diretório de saída existe
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if self.processing_mode == "parallel":
            parallel_analyzer = ParallelLeagueAnalyzer(
                alpha=self.alpha,
                num_simulations=self.num_simulations,
                current_season_weight=self.current_season_weight,
                max_workers=self.max_workers,
                use_dynamic_strengths=self.use_dynamic_strengths
            )
            self.results = parallel_analyzer.analyze_all_leagues_parallel(
                df_jogos=df_jogos,
                df_rankings=df_rankings,
                output_dir=output_dir,
                save_round_data=save_round_data,
                chunk_size=batch_size
            )
            
        elif self.processing_mode == "batch":
            batch_processor = BatchLeagueProcessor(
                batch_size=batch_size,
                use_dynamic_strengths=self.use_dynamic_strengths
            )
            self.results = batch_processor.process_in_batches(
                df_jogos=df_jogos,
                df_rankings=df_rankings,
                output_dir=output_dir,
                alpha=self.alpha,
                num_simulations=self.num_simulations,
                current_season_weight=self.current_season_weight,
                resume=resume
            )
            
        else:  # sequential (modo original)
            self.results = self._analyze_sequential(
                df_jogos, df_rankings, output_dir, save_plots, save_round_data
            )
        
        # Gerar plots sequencialmente se solicitado
        if save_plots and output_dir:
            self._generate_plots_sequential(output_dir)
        
        return self.results
    
    def _analyze_sequential(self, df_jogos: pd.DataFrame, 
                          df_rankings: Optional[pd.DataFrame] = None,
                          output_dir: Optional[str] = None,
                          save_plots: bool = False,
                          save_round_data: bool = True) -> List[AnalysisResult]:
        """Modo sequencial original."""
        logger.info("Validando dados de entrada...")
        df_clean = DataValidator.validate_dataframe(df_jogos)
        
        df_rankings_clean = None
        if df_rankings is not None:
            try:
                df_rankings_clean = DataValidator.validate_rankings_dataframe(df_rankings)
                logger.info(f"Rankings validados: {len(df_rankings_clean)} registros")
            except Exception as e:
                logger.warning(f"Erro ao validar rankings: {e}. Continuando sem rankings.")
        
        championship_ids = df_clean['id'].unique()
        logger.info(f"Analisando {len(championship_ids)} campeonatos")
        
        self.results = []
        all_round_data = []
        
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for i, champ_id in enumerate(championship_ids, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"ANÁLISE {i}/{len(championship_ids)}: {champ_id}")
            logger.info(f"{'='*60}")
            
            try:
                analyzer = OptimizedCompetitiveBalanceAnalyzer(
                    games_df=df_clean,
                    championship_id=champ_id,
                    rankings_df=df_rankings_clean,
                    alpha=self.alpha,
                    num_simulations=self.num_simulations,
                    current_season_weight=self.current_season_weight,
                    optimize_simulations=True,
                    use_vectorization=True,
                    use_dynamic_strengths=self.use_dynamic_strengths
                )
                
                analyzer.calculate_observed_imbalance()
                analyzer.run_null_model_optimized()
                analyzer.calculate_confidence_envelope()
                
                if output_dir and save_round_data:
                    round_filename = f"round_data_{champ_id.replace('/', '_').replace('@', '_')}.csv"
                    round_path = Path(output_dir) / round_filename
                    analyzer.save_round_by_round_data(round_path)
                    
                    round_df = pd.read_csv(round_path)
                    all_round_data.append(round_df)
                
                if output_dir and save_plots:
                    filename = f"{champ_id.replace('/', '_').replace('@', '_')}.png"
                    save_path = Path(output_dir) / filename
                    analyzer.plot_results(save_path=save_path)
                
                result = analyzer.get_analysis_result()
                self.results.append(result)
                
                strength_method = "dinâmicas" if result.strength_calculation_method == "dynamic" else "estáticas"
                ranking_info = f" (com {strength_method})" if result.has_ranking_data else " (sem rankings)"
                if result.turning_point_round:
                    logger.info(f"Ponto de virada detectado na rodada {result.turning_point_round}{ranking_info}")
                else:
                    logger.info(f"Liga permanece competitiva{ranking_info}")
                    
            except Exception as e:
                logger.error(f"ERRO ao analisar {champ_id}: {e}")
                continue
        
        if output_dir and save_round_data and all_round_data:
            consolidated_round_data = pd.concat(all_round_data, ignore_index=True)
            consolidated_path = Path(output_dir) / "round_by_round_competitiveness.csv"
            consolidated_round_data.to_csv(consolidated_path, index=False)
            logger.info(f"Dados consolidados de competitividade rodada a rodada salvos em: {consolidated_path}")
        
        return self.results
    
    def _generate_plots_sequential(self, output_dir: str):
        """Gera plots sequencialmente após análise paralela."""
        logger.info("Gerando plots sequencialmente...")
        
        for result in self.results:
            try:
                # Recriar analyzer para gerar plot
                # Nota: Isso é ineficiente, mas necessário para gerar plots
                analyzer = OptimizedCompetitiveBalanceAnalyzer(
                    games_df=pd.DataFrame(),  # Será substituído
                    championship_id=result.championship_id,
                    rankings_df=None,
                    alpha=self.alpha,
                    num_simulations=50,  # Reduzido para plots
                    current_season_weight=self.current_season_weight,
                    use_dynamic_strengths=(result.strength_calculation_method == "dynamic")
                )
                
                # Aqui precisaríamos recarregar os dados para gerar o plot
                # Por simplicidade, pulamos os plots no modo paralelo
                logger.warning("Geração de plots não suportada em modo paralelo")
                break
                
            except Exception as e:
                logger.error(f"Erro ao gerar plot para {result.championship_id}: {e}")
    
    def generate_summary_report(self, save_path: Optional[str] = None) -> pd.DataFrame:
        """Gera relatório resumo de todos os resultados."""
        if not self.results:
            raise ValueError("Nenhuma análise foi executada ainda")
        
        # Garantir que o diretório existe
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        summary_data = []
        for result in self.results:
            row_data = {
                'ID Campeonato': result.championship_id,
                'Liga': result.league,
                'Temporada': result.season,
                'Times': result.num_teams,
                'Rodadas': result.total_rounds,
                'Tem Rankings': 'Sim' if result.has_ranking_data else 'Não',
                'Método Forças': result.strength_calculation_method,
                'Variância Forças': f"{result.strength_variance:.4f}" if result.strength_variance else 'N/A',
                'Ponto Virada (Rodada)': result.turning_point_round or 'N/A',
                'Ponto Virada (%)': f"{result.turning_point_percent:.1%}" if result.turning_point_percent else 'N/A',
                'Desequilíbrio Final': f"{result.final_imbalance:.4f}" if result.final_imbalance else 'N/A',
                'É Competitivo': 'Sim' if result.is_competitive else 'Não',
                'P(Casa)': f"{result.ph:.3f}",
                'P(Empate)': f"{result.pd:.3f}",
                'P(Fora)': f"{result.pa:.3f}",
                'Simulação': 'Rankings' if result.ranking_based_simulation else 'Probabilística'
            }
            
            if result.position_definitions:
                pos_def = result.position_definitions
                row_data.update({
                    'Campeão (Rodada)': pos_def.champion_round or 'N/A',
                    'Vice (Rodada)': pos_def.second_round or 'N/A',
                    '3º Lugar (Rodada)': pos_def.third_round or 'N/A',
                    '4º Lugar (Rodada)': pos_def.fourth_round or 'N/A'
                })
                
                if pos_def.relegation_rounds:
                    for pos, round_num in pos_def.relegation_rounds.items():
                        row_data[f'Posição {pos} (Rodada)'] = round_num
            else:
                row_data.update({
                    'Campeão (Rodada)': 'N/A',
                    'Vice (Rodada)': 'N/A',
                    '3º Lugar (Rodada)': 'N/A',
                    '4º Lugar (Rodada)': 'N/A'
                })
            
            summary_data.append(row_data)
        
        summary_df = pd.DataFrame(summary_data)
        
        if save_path:
            summary_df.to_csv(save_path, index=False, encoding='utf-8')
            logger.info(f"Relatório resumo salvo em: {save_path}")
        
        return summary_df


def main_optimized():
    """Função principal otimizada com paralelização e processamento em lotes."""
    try:
        # Configurações
        GAMES_CSV_PATH = base_data_dir / "5_matchdays/football.csv"
        RANKINGS_CSV_PATH = base_data_dir / "4_standings/standings.csv"  
        OUTPUT_DIR = base_data_dir / "6_analysis_optimized"
        
        # Parâmetros de performance
        ALPHA = 0.05
        NUM_SIMULATIONS = 500
        CURRENT_SEASON_WEIGHT = 0.5
        PROCESSING_MODE = "parallel"
        BATCH_SIZE = 10
        MAX_WORKERS = mp.cpu_count() - 1
        USE_DYNAMIC_STRENGTHS = True  # Ativar forças dinâmicas
        
        if not GAMES_CSV_PATH.exists():
            raise FileNotFoundError(f"Arquivo de jogos não encontrado: {GAMES_CSV_PATH}")
        
        logger.info(f"Carregando jogos de: {GAMES_CSV_PATH}")
        df_jogos = pd.read_csv(GAMES_CSV_PATH)
        logger.info(f"Jogos carregados: {len(df_jogos)} registros")
        
        df_rankings = None
        if RANKINGS_CSV_PATH.exists():
            logger.info(f"Carregando rankings de: {RANKINGS_CSV_PATH}")
            df_rankings = pd.read_csv(RANKINGS_CSV_PATH)
            logger.info(f"Rankings carregados: {len(df_rankings)} registros")
        else:
            logger.warning(f"Arquivo de rankings não encontrado: {RANKINGS_CSV_PATH}")
        
        # Garantir que o diretório de saída existe
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Usar analisador otimizado
        analyzer = MultiLeagueAnalyzer(
            alpha=ALPHA, 
            num_simulations=NUM_SIMULATIONS,
            current_season_weight=CURRENT_SEASON_WEIGHT,
            max_workers=MAX_WORKERS,
            processing_mode=PROCESSING_MODE,
            use_dynamic_strengths=USE_DYNAMIC_STRENGTHS
        )
        
        results = analyzer.analyze_all_leagues(
            df_jogos=df_jogos,
            df_rankings=df_rankings,
            output_dir=OUTPUT_DIR,
            save_plots=False,
            save_round_data=True,
            batch_size=BATCH_SIZE,
            resume=True
        )
        
        # Gerar relatório
        logger.info("\n" + "="*60)
        logger.info("GERANDO RELATÓRIO RESUMO")
        logger.info("="*60)
        
        summary_df = analyzer.generate_summary_report(
            save_path=OUTPUT_DIR / 'optimized_summary_report.csv'
        )
        
        # Estatísticas
        total_leagues = len(results)
        competitive_leagues = sum(1 for r in results if r.is_competitive)
        with_rankings = sum(1 for r in results if r.has_ranking_data)
        dynamic_strengths = sum(1 for r in results if r.strength_calculation_method == "dynamic")
        
        print(f"\n{'='*60}")
        print("ESTATÍSTICAS GERAIS (OTIMIZADO):")
        print(f"{'='*60}")
        print(f"Total de campeonatos analisados: {total_leagues}")
        print(f"Campeonatos com dados de ranking: {with_rankings} ({with_rankings/total_leagues:.1%})")
        print(f"Campeonatos com forças dinâmicas: {dynamic_strengths} ({dynamic_strengths/total_leagues:.1%})")
        print(f"Campeonatos competitivos: {competitive_leagues} ({competitive_leagues/total_leagues:.1%})")
        print(f"Campeonatos não competitivos: {total_leagues-competitive_leagues} ({(total_leagues-competitive_leagues)/total_leagues:.1%})")
        print(f"Modo de processamento: {PROCESSING_MODE}")
        print(f"Núcleos utilizados: {MAX_WORKERS}")

        if total_leagues - competitive_leagues > 0:
            turning_points = [r.turning_point_percent for r in results if r.turning_point_percent is not None]
            if turning_points:
                avg_turning_point = np.mean(turning_points)
                print(f"Ponto de virada médio: {avg_turning_point:.1%} da temporada")
        
        logger.info("Análise otimizada concluída com sucesso!")
        
    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {e}")
        print("ERRO: Certifique-se de que os arquivos estão nos diretórios corretos.")
        
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Usar a versão otimizada
    main_optimized()