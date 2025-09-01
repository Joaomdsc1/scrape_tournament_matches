import config
import tournament_matches as tm


def format() -> None:
    params = config.parser.read_json_configuration("scrape.json")
    sports = params["sports"]

    scrape_dir = config.path.SCRAPE_PATH
    format_dir = config.path.FORMAT_PATH
    format_dir.mkdir(exist_ok=True, parents=True)

    tm.format.save_formatted_web_scraped_all_sports(sports, scrape_dir, format_dir)


if __name__ == "__main__":
    format()
