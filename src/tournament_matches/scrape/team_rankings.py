import requests
import os
import json

def load_urls(file_path):
    """
    Carrega as URLs de um arquivo JSON.
    O formato do JSON é:
    {
        "paths": [
            "/football/brazil/serie-a-betano/",
            "/football/germany/bundesliga/",
            "/football/brazil/serie-b-superbet/"
        ]
    }
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Mapeia os esportes para suas URLs
            sports = ["football"]  # Lista de esportes disponíveis
            urls = {sport: data["paths"][index] for index, sport in enumerate(sports)}
            return urls
    except (IOError, json.JSONDecodeError) as e:
        print(f"Erro ao carregar URLs de {file_path}: {e}")
        return {}

def get_team_rankings(urls):
    """
    Coleta os rankings de times usando as URLs fornecidas.
    """
    rankings = {}
    for sport, url in urls.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            rankings[sport] = response.json()
        except requests.RequestException as e:
            print(f"Erro ao obter rankings para {sport}: {e}")
    return rankings

def save_team_rankings(rankings, scrape_dir):
    """
    Salva os rankings coletados em arquivos JSON no diretório especificado.
    """
    os.makedirs(scrape_dir, exist_ok=True)
    for sport, ranking in rankings.items():
        file_path = os.path.join(scrape_dir, f"{sport}_rankings.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(ranking, f, ensure_ascii=False, indent=4)
            print(f"Rankings de {sport} salvos em {file_path}")
        except IOError as e:
            print(f"Erro ao salvar rankings de {sport}: {e}")

# Exemplo de uso (caso o script seja executado diretamente)
if __name__ == "__main__":
    urls_file = "../data/url_paths.json"
    scrape_dir = "../data/rankings"
    
    # Carregar URLs
    urls = load_urls(urls_file)
    
    # Exemplo de esportes (garanta que esses nomes correspondam aos esportes que você deseja)
    sports = ["football"]  # Ajuste conforme necessário
    
    # Filtrar URLs apenas para os esportes presentes
    valid_urls = {sport: urls[sport] for sport in sports if sport in urls}
    
    if valid_urls:
        # Coletar rankings
        rankings = get_team_rankings(valid_urls)
        # Salvar rankings
        save_team_rankings(rankings, scrape_dir)
    else:
        print("Nenhuma URL válida encontrada para os esportes selecionados.")
