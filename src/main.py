import config
import bet_explorer as bet


def main() -> None:
    params = config.parser.read_json_configuration("parameters.json")

    sports = params["sports"]

    scrape_dir = config.path.SCRAPE_PATH
    format_dir = config.path.FORMAT_PATH

    if params["should_scrape"]:
        scrape_dir.mkdir(exist_ok=True, parents=True)

        paths: list[str] = config.parser.get_url_paths(params["url_paths"], sports)
        unique_paths = sorted(set(paths))

        sport_to_matches = bet.scrape.web_scrape_from_provided_paths(
            unique_paths,
            params["seasons"]["first"],
            params["seasons"]["last"],
        )

        bet.scrape.save_web_scraped_matches(sport_to_matches, scrape_dir)

    if params["should_format"]:
        format_dir.mkdir(exist_ok=True, parents=True)

        bet.format.save_formatted_web_scraped_all_sports(sports, scrape_dir, format_dir)


if __name__ == "__main__":
    main()
