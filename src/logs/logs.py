import logging
from pathlib import Path

LOG_DIR: Path = Path("../logs/")
LOG_DIR.mkdir(exist_ok=True, parents=True)

LOG_PATH: Path = LOG_DIR / "web_scrape.log"

logging.basicConfig(
    filename=LOG_PATH,
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.DEBUG,
)
