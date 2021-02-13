from types import SimpleNamespace as StubObject
from unittest.mock import Mock, patch

import github
import pytest

from ghsearch.gh_search import GHSearch

from . import build_mock_result


@pytest.fixture
def mock_result_1():
    return build_mock_result("org/repo1", "1.txt")


@pytest.fixture
def mock_result_2():
    return build_mock_result("org/repo1", "2.txt")


@pytest.fixture
def mock_result_3():
    return build_mock_result("org/repo2", "3.txt")


@pytest.fixture
def mock_client(mock_result_1, mock_result_2, mock_result_3):
    mock = Mock(spec=github.Github)
    mock.search_code.return_value = [mock_result_1, mock_result_2, mock_result_3]
    mock.get_rate_limit.return_value = StubObject(
        search=StubObject(remaining=10, limit=10, reset="now"), core=StubObject(remaining=10, limit=10, reset="now")
    )
    return mock


@pytest.fixture(autouse=True)
def mock_click():
    with patch("ghsearch.gh_search.click") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_progress_printer():
    with patch("ghsearch.gh_search.ProgressPrinter") as mock:
        yield mock


def test_get_filtered_results_calls_search_code_correctly(mock_client):
    ghsearch = GHSearch(mock_client, [])
    ghsearch.get_filtered_results(["name", "org:janeklb", "filename:setup.py"])

    mock_client.search_code.assert_called_once_with(query="name org:janeklb filename:setup.py")


def test_get_filtered_results_without_filters(mock_client, mock_result_1, mock_result_2, mock_result_3):
    ghsearch = GHSearch(mock_client, [])
    repos = ghsearch.get_filtered_results(["query", "org:bort"])

    assert repos == {"org/repo1": [mock_result_1, mock_result_2], "org/repo2": [mock_result_3]}


def test_get_filtered_results_with_filters(mock_client, mock_result_1, mock_result_2, mock_result_3):
    ghsearch = GHSearch(mock_client, [Mock(side_effect=[True, False, True])])
    repos = ghsearch.get_filtered_results(["query", "org:bort"])

    assert repos == {"org/repo1": [mock_result_1], "org/repo2": [mock_result_3]}


def test_get_filtered_results_verbose(mock_client, mock_result_1, mock_result_2, mock_result_3, mock_click):
    ghsearch = GHSearch(
        mock_client, [Mock(side_effect=[True, True, False]), Mock(side_effect=[False, True, False])], verbose=True
    )

    repos = ghsearch.get_filtered_results(["query", "org:bort"])

    assert repos == {"org/repo1": [mock_result_2]}
    mock_click.echo.assert_any_call("Skipping result for org/repo1 via Mock")
    mock_click.echo.assert_any_call("Skipping result for org/repo2 via Mock")
