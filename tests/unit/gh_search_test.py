from unittest.mock import Mock, patch

import github
import pytest

from ghsearch.filters import FilterException
from ghsearch.gh_search import GHSearch

from . import MockPaginatedList, MockRateLimit, build_mock_content_file


@pytest.fixture
def mock_result_1():
    return build_mock_content_file("org/repo1", "1.txt")


@pytest.fixture
def mock_result_2():
    return build_mock_content_file("org/repo1", "2.txt")


@pytest.fixture
def mock_result_3():
    return build_mock_content_file("org/repo2", "3.txt")


@pytest.fixture
def mock_client(mock_result_1, mock_result_2, mock_result_3):
    mock = Mock(spec=github.Github)
    mock.search_code.return_value = MockPaginatedList(mock_result_1, mock_result_2, mock_result_3)
    mock.get_rate_limit.return_value = MockRateLimit(10, 10, "now", 10, 10, "now")
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

    assert repos == [mock_result_1, mock_result_2, mock_result_3]


def test_get_filtered_results_with_filters(mock_client, mock_result_1, mock_result_2, mock_result_3):
    ghsearch = GHSearch(mock_client, [Mock(side_effect=[True, False, True])])
    repos = ghsearch.get_filtered_results(["query", "org:bort"])

    assert repos == [mock_result_1, mock_result_3]


def test_get_filtered_results_with_exception_when_filtering(mock_client, mock_result_1, mock_progress_printer):
    mock_client.search_code.return_value = MockPaginatedList(mock_result_1)

    ghsearch = GHSearch(mock_client, [Mock(side_effect=FilterException(Mock(), "BOOO"))])

    repos = ghsearch.get_filtered_results(["query", "org:bort"])

    assert len(repos) == 0
    mock_progress_printer.return_value.__enter__.return_value.assert_any_call("BOOO", force=True)


def test_get_filtered_results_verbose(mock_client, mock_result_1, mock_result_2, mock_result_3, mock_click):
    ghsearch = GHSearch(
        mock_client, [Mock(side_effect=[True, True, False]), Mock(side_effect=[False, True, False])], verbose=True
    )

    repos = ghsearch.get_filtered_results(["query", "org:bort"])

    assert repos == [mock_result_2]
    mock_click.echo.assert_any_call("Skipping result for org/repo1 via Mock")
    mock_click.echo.assert_any_call("Skipping result for org/repo2 via Mock")


def test_get_filtered_results_near_limit(mock_client, mock_click):
    mock_client.get_rate_limit.return_value = MockRateLimit(1, 10, "sometime in the future", 10, 10, "now")
    mock_filter = Mock()
    mock_filter.uses_core_api = True

    ghsearch = GHSearch(mock_client, [mock_filter])
    ghsearch.get_filtered_results(["query", "org:bort"])

    mock_click.confirm.assert_called_once_with(
        """
Warning: you are at risk of going below 10% of your remaining core api rate limit.
Your search yielded 3 results, and gh-search may make up to 1 core api call(s) per result.

Your current core api usage is 1/10 (resets sometime in the future)

Do you want to continue?""".strip(),
        abort=True,
    )


def test_get_filtered_results_many_calls(mock_client, mock_click):
    mock_client.get_rate_limit.return_value = MockRateLimit(10000, 10000, "sometime in the future", 10, 10, "now")
    mock_client.search_code.return_value = MockPaginatedList(*[], total_count=257)
    mock_filter = Mock()
    mock_filter.uses_core_api = True

    ghsearch = GHSearch(mock_client, [mock_filter, mock_filter])
    ghsearch.get_filtered_results(["query", "org:bort"])

    mock_click.confirm.assert_called_once_with(
        """
Warning: you are about to potentially make more than 500 core api requests.
Your search yielded 257 results, and gh-search may make up to 2 core api call(s) per result.

Your current core api usage is 10000/10000 (resets sometime in the future)

Do you want to continue?""".strip(),
        abort=True,
    )

def test_get_filtered_results_rate_limiting_disabled(mock_client, mock_click):
    mock_client.get_rate_limit.side_effect = github.GithubException(404, "Not Found")
    mock_client.search_code.return_value = MockPaginatedList(*[], total_count=0)
    mock_filter = Mock()
    mock_filter.uses_core_api = True

    ghsearch = GHSearch(mock_client, [mock_filter], True)
    ghsearch.get_filtered_results(["query", "org:bort"])

    mock_click.echo.assert_any_call("(Rate limiting is disabled)")