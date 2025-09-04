"""Quality analysis functions for matchday organization."""

import pandas as pd
from collections import Counter
from typing import Dict, List, Tuple
import logging

from .utils import (
    get_tournament_teams,
    calculate_expected_matches_per_round,
    get_teams_in_matches,
    has_team_conflict
)


def analyze_round_quality(df: pd.DataFrame, tournament_id: str) -> Dict:
    """Analyze the quality of round organization for a tournament.
    
    Args:
        df: DataFrame containing organized match data
        tournament_id: Tournament identifier
        
    Returns:
        Dictionary containing quality metrics
    """
    tournament_matches = df[df['id'] == tournament_id]
    teams = get_tournament_teams(df, tournament_id)
    n_teams = len(teams)
    expected_matches_per_round = calculate_expected_matches_per_round(n_teams)
    
    # Group by rounds
    rounds = tournament_matches.groupby('round')
    
    perfect_rounds = 0
    total_rounds = 0
    round_details = []
    unassigned_matches = len(tournament_matches[tournament_matches['round'] == -1])
    
    for round_num, round_matches in rounds:
        if round_num == -1:  # Skip unassigned matches
            continue
            
        total_rounds += 1
        n_matches = len(round_matches)
        teams_in_round = get_teams_in_matches(round_matches)
        has_conflict = has_team_conflict(round_matches)
        
        is_perfect = (
            n_matches == expected_matches_per_round and 
            not has_conflict
        )
        
        if is_perfect:
            perfect_rounds += 1
        
        round_details.append({
            'round': round_num,
            'matches': n_matches,
            'expected_matches': expected_matches_per_round,
            'teams_count': len(teams_in_round),
            'has_conflict': has_conflict,
            'is_perfect': is_perfect
        })
    
    perfect_percentage = (perfect_rounds / total_rounds * 100) if total_rounds > 0 else 0
    
    return {
        'tournament_id': tournament_id,
        'total_teams': n_teams,
        'total_matches': len(tournament_matches),
        'total_rounds': total_rounds,
        'perfect_rounds': perfect_rounds,
        'perfect_percentage': perfect_percentage,
        'unassigned_matches': unassigned_matches,
        'expected_matches_per_round': expected_matches_per_round,
        'round_details': round_details
    }


def generate_quality_report(df: pd.DataFrame, output_file: str = None) -> Dict:
    """Generate a comprehensive quality report for all tournaments.
    
    Args:
        df: DataFrame containing organized match data
        output_file: Optional file path to save the report
        
    Returns:
        Dictionary containing overall quality metrics
    """
    tournaments = df['id'].unique()
    tournament_analyses = []
    
    logging.info(f"Analyzing quality for {len(tournaments)} tournaments...")
    
    for tournament_id in tournaments:
        analysis = analyze_round_quality(df, tournament_id)
        tournament_analyses.append(analysis)
    
    # Calculate overall statistics
    total_matches = sum(analysis['total_matches'] for analysis in tournament_analyses)
    total_rounds = sum(analysis['total_rounds'] for analysis in tournament_analyses)
    total_perfect_rounds = sum(analysis['perfect_rounds'] for analysis in tournament_analyses)
    total_unassigned = sum(analysis['unassigned_matches'] for analysis in tournament_analyses)
    
    overall_perfect_percentage = (total_perfect_rounds / total_rounds * 100) if total_rounds > 0 else 0
    
    # Sort tournaments by quality
    tournament_analyses.sort(key=lambda x: x['perfect_percentage'], reverse=True)
    
    # Classify tournaments
    perfect_tournaments = sum(1 for analysis in tournament_analyses if analysis['perfect_percentage'] == 100)
    good_tournaments = sum(1 for analysis in tournament_analyses if 80 <= analysis['perfect_percentage'] < 100)
    
    report = {
        'overall_stats': {
            'total_tournaments': len(tournaments),
            'total_matches': total_matches,
            'total_rounds': total_rounds,
            'perfect_rounds': total_perfect_rounds,
            'overall_perfect_percentage': overall_perfect_percentage,
            'unassigned_matches': total_unassigned,
            'perfect_tournaments': perfect_tournaments,
            'good_tournaments': good_tournaments
        },
        'tournament_analyses': tournament_analyses
    }
    
    # Generate markdown report if output file specified
    if output_file:
        _write_markdown_report(report, output_file)
    
    return report


def _write_markdown_report(report: Dict, output_file: str) -> None:
    """Write quality report to markdown file.
    
    Args:
        report: Quality report dictionary
        output_file: Output file path
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Matchday Organization Quality Report\n\n")
        
        # Overall statistics
        stats = report['overall_stats']
        f.write("## Overall Statistics\n\n")
        f.write(f"- **Total Tournaments**: {stats['total_tournaments']}\n")
        f.write(f"- **Total Matches**: {stats['total_matches']}\n")
        f.write(f"- **Total Rounds**: {stats['total_rounds']}\n")
        f.write(f"- **Perfect Rounds**: {stats['perfect_rounds']}\n")
        f.write(f"- **Overall Quality**: {stats['overall_perfect_percentage']:.1f}%\n")
        f.write(f"- **Unassigned Matches**: {stats['unassigned_matches']}\n")
        f.write(f"- **Perfect Tournaments**: {stats['perfect_tournaments']}\n")
        f.write(f"- **Good Tournaments (80%+)**: {stats['good_tournaments']}\n\n")
        
        # Tournament ranking
        f.write("## Tournament Quality Ranking\n\n")
        f.write("| Rank | Tournament | Quality | Perfect Rounds | Total Rounds | Unassigned |\n")
        f.write("|------|------------|---------|----------------|--------------|------------|\n")
        
        for i, analysis in enumerate(report['tournament_analyses'], 1):
            tournament_name = analysis['tournament_id'].split('@')[0] if '@' in analysis['tournament_id'] else analysis['tournament_id']
            f.write(f"| {i} | {tournament_name} | {analysis['perfect_percentage']:.1f}% | "
                   f"{analysis['perfect_rounds']} | {analysis['total_rounds']} | "
                   f"{analysis['unassigned_matches']} |\n")
        
        # Detailed analysis for problematic tournaments
        f.write("\n## Detailed Analysis\n\n")
        
        for analysis in report['tournament_analyses']:
            if analysis['perfect_percentage'] < 100:
                tournament_name = analysis['tournament_id'].split('@')[0] if '@' in analysis['tournament_id'] else analysis['tournament_id']
                f.write(f"### {tournament_name}\n\n")
                f.write(f"- **Quality**: {analysis['perfect_percentage']:.1f}%\n")
                f.write(f"- **Teams**: {analysis['total_teams']}\n")
                f.write(f"- **Expected matches per round**: {analysis['expected_matches_per_round']}\n")
                
                if analysis['unassigned_matches'] > 0:
                    f.write(f"- **Unassigned matches**: {analysis['unassigned_matches']}\n")
                
                # Show problematic rounds
                problematic_rounds = [rd for rd in analysis['round_details'] if not rd['is_perfect']]
                if problematic_rounds:
                    f.write("\n**Problematic Rounds:**\n\n")
                    for rd in problematic_rounds[:5]:  # Show first 5 problematic rounds
                        f.write(f"- Round {rd['round']}: {rd['matches']} matches "
                               f"(expected {rd['expected_matches']})")
                        if rd['has_conflict']:
                            f.write(" - **Team conflict detected**")
                        f.write("\n")
                
                f.write("\n")
    
    logging.info(f"Quality report saved to {output_file}")