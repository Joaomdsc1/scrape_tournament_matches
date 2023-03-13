import config
import tournament_matches as bet


def scrape() -> None:
    params = config.parser.read_json_configuration("scrape.json")

    sports = params["sports"]

    scrape_dir = config.path.SCRAPE_PATH
    scrape_dir.mkdir(exist_ok=True, parents=True)

    paths = config.parser.get_url_paths(params["url_paths"], sports)
    unique_paths = sorted(set(paths))

    sport_to_matches = bet.scrape.web_scrape_from_provided_paths(
        unique_paths,
        params["seasons"]["first"],
        params["seasons"]["last"],
    )

    bet.scrape.save_web_scraped_matches(sport_to_matches, scrape_dir)


if __name__ == "__main__":
    scrape()
