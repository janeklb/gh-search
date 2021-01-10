import contextlib
from unittest.mock import ANY, patch

import pytest

from ghsearch.gh_search import GHSearch

from . import build_mock_result


@pytest.fixture(autouse=True)
def mock_click():
    with patch("ghsearch.gh_search.click") as mock:

        @contextlib.contextmanager
        def passthroughcontext(iterable, *args, **kwargs):
            yield iterable

        mock.progressbar.side_effect = passthroughcontext
        yield mock


@pytest.fixture
def mock_result_1():
    return build_mock_result("org/repo1", "1.txt")


@pytest.fixture
def mock_result_2():
    return build_mock_result("org/repo1", "2.txt")


@pytest.fixture
def mock_result_3():
    return build_mock_result("org/repo2", "3.txt")


def test_get_filtered_results_without_filters(mock_client, mock_result_1, mock_result_2, mock_result_3):
    mock_client.search_code.return_value = [mock_result_1, mock_result_2, mock_result_3]

    ghsearch = GHSearch(mock_client, [])
    repos = ghsearch.get_filtered_results(ANY)

    assert repos == {"org/repo1": [mock_result_1, mock_result_2], "org/repo2": [mock_result_3]}


def test_get_filtered_results_with_filters(mock_client, mock_result_1, mock_result_2, mock_result_3):
    mock_client.search_code.return_value = [mock_result_1, mock_result_2, mock_result_3]

    ghsearch = GHSearch(mock_client, [lambda x: x.path != "2.txt"])
    repos = ghsearch.get_filtered_results(ANY)

    assert repos == {"org/repo1": [mock_result_1], "org/repo2": [mock_result_3]}


def test_get_filtered_results_verbose(mock_client, mock_result_1, mock_result_2, mock_result_3, mock_click):
    mock_client.search_code.return_value = [mock_result_1, mock_result_2, mock_result_3]

    def filter_fn(result):
        return result.path != "3.txt"

    ghsearch = GHSearch(mock_client, [filter_fn], verbose=True)

    repos = ghsearch.get_filtered_results(ANY)

    assert repos == {
        "org/repo1": [mock_result_1, mock_result_2],
    }
    mock_click.echo.assert_any_call("Skipping result for org/repo2 via filter_fn")
