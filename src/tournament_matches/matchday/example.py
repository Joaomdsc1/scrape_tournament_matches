#!/usr/bin/env python3
"""
Example usage of the matchday module.

This script demonstrates how to use the matchday organization functionality
with sample data or existing CSV files.
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from tournament_matches.matchday import (
    process_all_tournaments,
    generate_quality_report,
    organize_tournament_rounds,
    analyze_round_quality
)


def create_sample_data() -> pd.DataFrame:
    """Create sample match data for testing.
    
    Returns:
        DataFrame with sample match data
    """
    # Sample data for a 4-team tournament
    matches = [
        {
            'id': 'sample-tournament@/football/test/sample-2023/',
            'date number': 1,
            'result': '2:1',
            'date': '01.01.2023',
            'home': 'Team A',
            'away': 'Team B'
        },
        {
            'id': 'sample-tournament@/football/test/sample-2023/',
            'date number': 1,
            'result': '1:0',
            'date': '01.01.2023',
            'home': 'Team C',
            'away': 'Team D'
        },
        {
            'id': 'sample-tournament@/football/test/sample-2023/',
            'date number': 2,
            'result': '3:2',
            'date': '08.01.2023',
            'home': 'Team A',
            'away': 'Team C'
        },
        {
            'id': 'sample-tournament@/football/test/sample-2023/',
            'date number': 2,
            'result': '0:1',
            'date': '08.01.2023',
            'home': 'Team B',
            'away': 'Team D'
        },
        {
            'id': 'sample-tournament@/football/test/sample-2023/',
            'date number': 3,
            'result': '2:2',
            'date': '15.01.2023',
            'home': 'Team A',
            'away': 'Team D'
        },
        {
            'id': 'sample-tournament@/football/test/sample-2023/',
            'date number': 3,
            'result': '1:3',
            'date': '15.01.2023',
            'home': 'Team B',
            'away': 'Team C'
        }
    ]
    
    return pd.DataFrame(matches)


def example_single_tournament():
    """Example: Organize a single tournament."""
    print("\n=== Single Tournament Example ===")
    
    # Create sample data
    df = create_sample_data()
    tournament_id = 'sample-tournament@/football/test/sample-2023/'
    
    print(f"Original data for {tournament_id}:")
    print(df[['date', 'home', 'away', 'result']].to_string(index=False))
    
    # Organize into rounds
    organized_df = organize_tournament_rounds(df, tournament_id)
    
    print(f"\nOrganized into rounds:")
    print(organized_df[['date', 'home', 'away', 'result', 'round']].to_string(index=False))
    
    # Analyze quality
    quality = analyze_round_quality(organized_df, tournament_id)
    print(f"\nQuality Analysis:")
    print(f"- Perfect rounds: {quality['perfect_rounds']}/{quality['total_rounds']}")
    print(f"- Quality percentage: {quality['perfect_percentage']:.1f}%")
    print(f"- Unassigned matches: {quality['unassigned_matches']}")


def example_multiple_tournaments():
    """Example: Process multiple tournaments."""
    print("\n=== Multiple Tournaments Example ===")
    
    # Create sample data with multiple tournaments
    df1 = create_sample_data()
    
    # Create second tournament data
    df2 = df1.copy()
    df2['id'] = 'another-tournament@/football/test/another-2023/'
    df2['home'] = df2['home'].str.replace('Team', 'Club')
    df2['away'] = df2['away'].str.replace('Team', 'Club')
    
    # Combine datasets
    combined_df = pd.concat([df1, df2], ignore_index=True)
    
    print(f"Processing {len(combined_df['id'].unique())} tournaments...")
    
    # Process all tournaments
    organized_df = process_all_tournaments(combined_df)
    
    # Generate quality report
    quality_report = generate_quality_report(organized_df)
    
    print(f"\nOverall Results:")
    stats = quality_report['overall_stats']
    print(f"- Total tournaments: {stats['total_tournaments']}")
    print(f"- Total matches: {stats['total_matches']}")
    print(f"- Overall quality: {stats['overall_perfect_percentage']:.1f}%")
    print(f"- Perfect tournaments: {stats['perfect_tournaments']}")
    
    print(f"\nTournament Details:")
    for analysis in quality_report['tournament_analyses']:
        tournament_name = analysis['tournament_id'].split('@')[0]
        print(f"- {tournament_name}: {analysis['perfect_percentage']:.1f}% quality")


def example_with_real_data():
    """Example: Process real data if available."""
    print("\n=== Real Data Example ===")
    
    # Try to load real data
    data_files = [
        '../../../data/football.csv',
        '../../../football.csv',
        'football.csv'
    ]
    
    df = None
    for file_path in data_files:
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded real data from {file_path}")
            break
        except FileNotFoundError:
            continue
    
    if df is None:
        print("No real data file found. Skipping real data example.")
        return
    
    # Process first tournament only (for speed)
    first_tournament = df['id'].iloc[0]
    tournament_df = df[df['id'] == first_tournament]
    
    print(f"Processing tournament: {first_tournament}")
    print(f"Matches: {len(tournament_df)}")
    
    # Organize and analyze
    organized_df = organize_tournament_rounds(df, first_tournament)
    quality = analyze_round_quality(organized_df, first_tournament)
    
    print(f"\nResults:")
    print(f"- Rounds created: {quality['total_rounds']}")
    print(f"- Perfect rounds: {quality['perfect_rounds']}")
    print(f"- Quality: {quality['perfect_percentage']:.1f}%")
    print(f"- Unassigned matches: {quality['unassigned_matches']}")


def main():
    """Run all examples."""
    print("Matchday Module Examples")
    print("=" * 50)
    
    try:
        example_single_tournament()
        example_multiple_tournaments()
        example_with_real_data()
        
        print("\n=== Examples completed successfully! ===")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()