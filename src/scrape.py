import config
import tournament_matches as tm


def scrape() -> None:
    params = config.parser.read_json_configuration("scrape.json")

    sports = params["sports"]

    scrape_dir = config.path.SCRAPE_PATH
    scrape_dir.mkdir(exist_ok=True, parents=True)

    paths_params = params["url_paths"]
    paths = config.parser.get_url_paths(paths_params, sports)
    unique_paths = sorted(set(paths))

    if paths_params["validate"]:
        tm.scrape.validate_url_paths(unique_paths)

    sport_to_matches = tm.scrape.web_scrape_from_provided_paths(
        unique_paths,
        params["seasons"]["first"],
        params["seasons"]["last"],
    )

    tm.scrape.save_web_scraped_matches(sport_to_matches, scrape_dir)


if __name__ == "__main__":
    scrape()
