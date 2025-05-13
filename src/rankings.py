import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd

base_paths = [
    "/football/brazil/serie-a",
    "/football/germany/bundesliga",
    "/football/brazil/serie-b",
    "/football/england/premier-league",
    "/football/italy/serie-a",
    "/basketball/usa/nba",
    "/basketball/brazil/nbb",
]

years = range(2011, 2022)

paths = []
for base in base_paths:
    for year in years:
        paths.append(f"{base}-{year}/")
        paths.append(f"{base}-{year-1}-{year}/")

output_dir = Path('data/standings/csv')
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / 'standings_2011_2021.csv'

# Mapeamento para corrigir nomes de torneios
slug_corrections = {
    "serie-a-betano": "serie-a",
    "serie-b-superbet": "serie-b",
}

all_dfs = []

for path in paths:
    sport = path.strip('/').split('/')[0]
    raw_slug = path.strip('/').split('/')[2]
    slug = slug_corrections.get(raw_slug, raw_slug)

    split = path.strip('/').split('-')
    season = f"{split[-2]}-{split[-1]}" if len(split) > 2 else split[-1]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.betexplorer.com" + path)
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', id='table-type-1')

    if table:
        try:
            df = pd.read_html(str(table))[0]
            df.insert(0, "season", season)
            df.insert(1, "tournament", slug)
            df.insert(2, "sport", sport)
            all_dfs.append(df)
            print(f"Tabela adicionada: {slug} {season}")
        except Exception as e:
            print(f"Erro ao processar {path}: {e}")
    else:
        print(f"Tabela não encontrada para {path}")

if all_dfs:
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv(output_path, index=False)
    print(f"\nTodas as tabelas salvas em '{output_path}'")
else:
    print("Nenhuma tabela foi coletada.")
