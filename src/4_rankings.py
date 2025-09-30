import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import logging
from io import StringIO
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar configurações do arquivo scrape.json
config_path = Path(__file__).parent / "scrape.json"
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# Obter os caminhos das ligas a partir do scrape.json
paths_list = config["url_paths"]["list"]
base_paths = []
for path_group in paths_list:
    base_paths.extend(path_group["names"])

# Obter os anos das temporadas
years = range(2010, 2022)

# Correções apenas para scraping
slug_corrections = {
    "serie-a-betano": "serie-a",
    "serie-b-superbet": "serie-b",
}

# Gerar caminhos - criar lista de tentativas por liga/ano
tournament_attempts = []
for base in base_paths:
    for year in years:
        # Lista de tentativas para esta liga/ano (em ordem de prioridade)
        attempts = [
            (base, f"{base}-{year-1}-{year}/"),  # Primeiro: AAAA-AAAA (ex: 2009-2010)
            (base, f"{base}-{year}/")            # Segundo: AAAA (ex: 2010)
        ]
        tournament_attempts.append(attempts)

# Diretório de saída
base_dir = Path(__file__).parent.parent  # Vai para o diretório raiz do projeto
output_dir = base_dir / 'data' / '4_standings'
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / 'standings.csv'

all_dfs = []
failed_urls = []

def scrape_page_with_retry(url_path, max_retries=5, delay=10):
    """Tenta fazer scraping de uma página com retry logic"""
    for attempt in range(max_retries):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                page = browser.new_page()
                
                # Configurar timeout maior
                page.set_default_timeout(60000)  # 60 segundos
                
                logger.info(f"Tentativa {attempt + 1}: Acessando {url_path}")
                page.goto("https://www.betexplorer.com" + url_path, wait_until='domcontentloaded')
                page.wait_for_timeout(6000)
                html = page.content()
                browser.close()
                return html
                
        except PlaywrightTimeoutError as e:
            logger.warning(f"Timeout na tentativa {attempt + 1} para {url_path}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))  # Backoff exponencial
            else:
                logger.error(f"Falha definitiva após {max_retries} tentativas para {url_path}")
                return None
        except Exception as e:
            logger.error(f"Erro inesperado na tentativa {attempt + 1} para {url_path}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                return None
    
    return None

def try_tournament_formats(attempts, slug_corrections):
    """Tenta diferentes formatos de URL para uma liga/ano até encontrar uma tabela válida"""
    for base_path, path in attempts:
        sport = base_path.strip('/').split('/')[0]
        country = base_path.strip('/').split('/')[1]
        
        # Extração do nome da liga conforme aparece na URL
        tournament_slug = path.strip('/').split('/')[2]
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
        
        url_path = path.replace(tournament_slug, slug)
        
        logger.info(f"Tentando formato: {url_path}")
        
        # Fazer scraping
        html = scrape_page_with_retry(url_path)
        
        if html is None:
            logger.warning(f"Falha ao obter HTML para {url_path}")
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', id='table-type-1')
        
        if table:
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                df.insert(0, "season", season)
                df.insert(1, "tournament", tournament_slug)
                df.insert(2, "sport", sport)
                df.insert(3, "country", country)
                
                logger.info(f"✅ ✅ ✅ Tabela encontrada: {tournament_slug} {season}")
                return df, url_path
                
            except Exception as e:
                logger.error(f"Erro ao processar tabela de {path}: {e}")
                continue
        else:
            logger.warning(f"❌ Tabela não encontrada para {url_path}")
    
    return None, None

logger.info(f"Iniciando scraping de {len(tournament_attempts)} ligas/anos...")

for i, attempts in enumerate(tournament_attempts, 1):
    # Extrair informações do primeiro formato para logging
    base_path, first_path = attempts[0]
    tournament_name = first_path.strip('/').split('/')[2].split('-')[0]
    year = first_path.strip('/').split('/')[2].split('-')[-1]
    
    logger.info(f"Processando {i}/{len(tournament_attempts)}: {tournament_name} {year}")
    
    # Tentar diferentes formatos até encontrar um que funcione
    df, successful_url = try_tournament_formats(attempts, slug_corrections)
    
    if df is not None:
        all_dfs.append(df)
        logger.info(f"✅ Sucesso para {tournament_name} {year}")
    else:
        # Se nenhum formato funcionou, adicionar todas as URLs tentadas como falhas
        for _, path in attempts:
            tournament_slug = path.strip('/').split('/')[2]
            slug = slug_corrections.get(tournament_slug, tournament_slug)
            url_path = path.replace(tournament_slug, slug)
            failed_urls.append(url_path)
        logger.error(f"❌ Falha completa para {tournament_name} {year}")
    
    # Pequeno delay entre requisições para não sobrecarregar o servidor
    time.sleep(3)

# Salvar resultado
if all_dfs:
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv(output_path, index=False)
    logger.info(f"\n✓ Todas as tabelas salvas em '{output_path}'")
    logger.info(f"Total de tabelas coletadas: {len(all_dfs)}")
else:
    logger.warning("Nenhuma tabela foi coletada.")

# Relatório de URLs que falharam
if failed_urls:
    logger.warning(f"\n⚠️  {len(failed_urls)} URLs falharam:")
    for url in failed_urls:
        logger.warning(f"  - {url}")
    
    # Salvar URLs que falharam em um arquivo para análise posterior
    failed_urls_path = output_dir / 'failed_urls.txt'
    with open(failed_urls_path, 'w') as f:
        for url in failed_urls:
            f.write(f"{url}\n")
    logger.info(f"URLs que falharam salvas em: {failed_urls_path}")

logger.info("Scraping concluído!")
