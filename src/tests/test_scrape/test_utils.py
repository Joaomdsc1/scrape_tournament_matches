import tournament_matches.scrape.utils as utils


def test_concatenate_homepage_to_url():
    assert utils.concatenate_homepage_url_to_path("/") == "https://www.betexplorer.com/"
    assert (
        utils.concatenate_homepage_url_to_path("/test/")
        == "https://www.betexplorer.com/test/"
    )
    assert (
        utils.concatenate_homepage_url_to_path("/test/second")
        == "https://www.betexplorer.com/test/second"
    )


def test_empty_get_sport():
    assert utils.get_sport("//") == ""


def test_get_sport():
    assert utils.get_sport("/sport/rest/") == "sport"
    assert utils.get_sport("/sport/rest/rest2") == "sport"


def test_empty_get_name():
    assert utils.get_tournament_name("//") == ""


def test_get_name():
    assert utils.get_tournament_name("/rest/name/") == "name"
    assert utils.get_tournament_name("/rest2/rest/name/") == "name"
