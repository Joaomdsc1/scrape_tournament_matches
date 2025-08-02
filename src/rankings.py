import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import re

# Lista de ligas base
base_paths = [
    "/football/brazil/serie-a",
    "/football/germany/bundesliga",
    "/football/brazil/serie-b",
    "/football/england/premier-league",
    "/football/italy/serie-a",
    "/football/spain/la-liga",
    "/football/france/ligue-1",
    "/basketball/usa/nba",
    "/basketball/brazil/nbb",
]

years = range(2011, 2022)

# Correções apenas para scraping
slug_corrections = {
    "serie-a-betano": "serie-a",
    "serie-b-superbet": "serie-b",
}

# Gerar caminhos
paths = []
for base in base_paths:
    for year in years:
        paths.append((base, f"{base}-{year}/"))
        paths.append((base, f"{base}-{year-1}-{year}/"))

# Diretório de saída
output_dir = Path('data/standings/csv')
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / 'standings_2011_2021.csv'

all_dfs = []

for base_path, path in paths:
    sport = base_path.strip('/').split('/')[0]

    # Extração do nome da liga conforme aparece na URL (ex: serie-a-betano)
    raw_slug = path.strip('/').split('/')[2].split('-')[0]
    tournament_slug = path.strip('/').split('/')[2]  # como aparece na URL (ex: serie-a-betano)
    slug = slug_corrections.get(tournament_slug, tournament_slug)

    # Extrair temporada com regex
    match = re.search(r'(\d{4})(?:-(\d{4}))?/?$', path)
    if match:
        if match.group(2):
            season = f"{match.group(1)}-{match.group(2)}"
        else:
            season = match.group(1)
    else:
        season = "unknown"

    url_path = path.replace(tournament_slug, slug)  # usar slug corrigido para acessar URL

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.betexplorer.com" + url_path)
        page.wait_for_timeout(5000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', id='table-type-1')

    if table:
        try:
            df = pd.read_html(str(table))[0]
            df.insert(0, "season", season)
            df.insert(1, "tournament", tournament_slug)  # valor original da URL
            df.insert(2, "sport", sport)
            all_dfs.append(df)
            print(f"Tabela adicionada: {tournament_slug} {season}")
        except Exception as e:
            print(f"Erro ao processar {path}: {e}")
    else:
        print(f"Tabela não encontrada para {path}")

# Salvar resultado
if all_dfs:
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv(output_path, index=False)
    print(f"\nTodas as tabelas salvas em '{output_path}'")
else:
    print("Nenhuma tabela foi coletada.")
