#!/usr/bin/env python3
"""
Script para comparar os resultados das versões 3 e 4 do algoritmo de geração de rodadas.
"""

import pandas as pd

def compare_versions():
    """
    Compara os resultados das versões 3 e 4 do algoritmo.
    """
    print("=== COMPARAÇÃO ENTRE VERSÕES ===")
    print()
    
    # Carregar dados das duas versões
    try:
        v3_file = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_final.csv"
        v4_file = "/Users/joaomdsc/Desktop/Faculdade/TCC/scrape_tournament_matches/data/5_matchdays/football_rodadas_v4.csv"
        
        df_v3 = pd.read_csv(v3_file)
        df_v4 = pd.read_csv(v4_file)
        
        # Criar coluna campeonato_temporada para V3 se não existir
        if 'campeonato_temporada' not in df_v3.columns:
            df_v3['campeonato_temporada'] = df_v3['campeonato'] + '_' + df_v3['temporada']
        
        print(f"Versão 3 (atual): {len(df_v3)} jogos")
        print(f"Versão 4 (nova): {len(df_v4)} jogos")
        print()
        
        # Extrair estatísticas por campeonato-temporada
        def get_stats(df, version_name):
            stats = []
            for camp_temp in sorted(df['campeonato_temporada'].unique()):
                season_data = df[df['campeonato_temporada'] == camp_temp]
                stats.append({
                    'campeonato_temporada': camp_temp,
                    'version': version_name,
                    'jogos': len(season_data),
                    'rodadas': season_data['rodada'].max()
                })
            return stats
        
        stats_v3 = get_stats(df_v3, 'V3')
        stats_v4 = get_stats(df_v4, 'V4')
        
        # Criar DataFrame para comparação
        comparison_data = []
        
        # Criar dicionários para acesso rápido
        v3_dict = {s['campeonato_temporada']: s for s in stats_v3}
        v4_dict = {s['campeonato_temporada']: s for s in stats_v4}
        
        all_seasons = set(v3_dict.keys()) | set(v4_dict.keys())
        
        for season in sorted(all_seasons):
            v3_rounds = v3_dict.get(season, {}).get('rodadas', 0)
            v4_rounds = v4_dict.get(season, {}).get('rodadas', 0)
            improvement = v3_rounds - v4_rounds
            improvement_pct = (improvement / v3_rounds * 100) if v3_rounds > 0 else 0
            
            comparison_data.append({
                'Campeonato-Temporada': season,
                'V3_Rodadas': v3_rounds,
                'V4_Rodadas': v4_rounds,
                'Melhoria': improvement,
                'Melhoria_%': f"{improvement_pct:.1f}%"
            })
        
        # Imprimir comparação detalhada
        print("COMPARAÇÃO DETALHADA:")
        print(f"{'Campeonato-Temporada':<25} {'V3':<4} {'V4':<4} {'Melhoria':<8} {'%':<6}")
        print("-" * 60)
        
        total_v3_rounds = 0
        total_v4_rounds = 0
        
        for item in comparison_data:
            print(f"{item['Campeonato-Temporada']:<25} {item['V3_Rodadas']:<4} {item['V4_Rodadas']:<4} {item['Melhoria']:<8} {item['Melhoria_%']:<6}")
            total_v3_rounds += item['V3_Rodadas']
            total_v4_rounds += item['V4_Rodadas']
        
        print("-" * 60)
        total_improvement = total_v3_rounds - total_v4_rounds
        total_improvement_pct = (total_improvement / total_v3_rounds * 100) if total_v3_rounds > 0 else 0
        print(f"{'TOTAL':<25} {total_v3_rounds:<4} {total_v4_rounds:<4} {total_improvement:<8} {total_improvement_pct:.1f}%")
        
        print()
        print("=== RESUMO DA MELHORIA ===")
        print(f"Rodadas totais V3: {total_v3_rounds}")
        print(f"Rodadas totais V4: {total_v4_rounds}")
        print(f"Redução total: {total_improvement} rodadas ({total_improvement_pct:.1f}%)")
        print(f"Rodada máxima V3: {df_v3['rodada'].max()}")
        print(f"Rodada máxima V4: {df_v4['rodada'].max()}")
        
        # Verificar casos problemáticos
        print()
        print("=== CASOS MAIS PROBLEMÁTICOS (V3) ===")
        problematic_v3 = [item for item in comparison_data if item['V3_Rodadas'] > 45]
        if problematic_v3:
            for item in problematic_v3:
                print(f"{item['Campeonato-Temporada']}: {item['V3_Rodadas']} rodadas")
        else:
            print("Nenhum caso com mais de 45 rodadas encontrado.")
        
        print()
        print("=== CASOS MAIS PROBLEMÁTICOS (V4) ===")
        problematic_v4 = [item for item in comparison_data if item['V4_Rodadas'] > 40]
        if problematic_v4:
            for item in problematic_v4:
                print(f"{item['Campeonato-Temporada']}: {item['V4_Rodadas']} rodadas")
        else:
            print("Nenhum caso com mais de 40 rodadas encontrado.")
            
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    compare_versions()