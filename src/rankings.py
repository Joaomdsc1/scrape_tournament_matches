import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Garante que o diretório exista
output_dir = 'data/standings/hmtl'
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'serie_a_table.html')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.betexplorer.com/football/brazil/serie-a-betano/")
    page.wait_for_timeout(5000)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, 'html.parser')
table = soup.find('table', id='table-type-1')

if table:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(table.prettify())
    print(f"Tabela salva em '{output_path}'")
else:
    print("Tabela não encontrada.")
