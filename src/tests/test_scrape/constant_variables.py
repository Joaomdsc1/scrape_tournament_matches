from pathlib import Path

cwd = Path.cwd()

# This allows to run 'pytest' from command-line from 'src/' or from its parent
to_add = "" if cwd.name == "src" else "src"
directory = cwd / to_add

MOCK_PATH = directory / "tests/test_scrape/html_mocks/"
