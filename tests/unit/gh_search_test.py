from unittest.mock import Mock, patch

import github
import pytest

from ghsearch.filters import FilterException
from ghsearch.gh_search import CodeSearchRateLimitError, GHSearch

from . import MockRateLimit, build_mock_content_file


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
    mock = Mock()
    mock._Github__requester.requestJsonAndCheck.return_value = (
        {"x-ratelimit-remaining": "9", "x-ratelimit-reset": "0"},
        {"items": [{}, {}, {}], "total_count": 3, "incomplete_results": False},
    )
    mock.create_from_raw_data.side_effect = [mock_result_1, mock_result_2, mock_result_3]
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


def test_get_filtered_results_requests_code_search_correctly(mock_client):
    ghsearch = GHSearch(mock_client, [])
    ghsearch.get_filtered_results(["name", "org:janeklb", "filename:setup.py"])

    mock_client._Github__requester.requestJsonAndCheck.assert_called_once_with(
        "GET",
        "/search/code",
        parameters={"q": "name org:janeklb filename:setup.py", "page": 1, "per_page": 100},
    )


def test_get_filtered_results_without_filters(mock_client, mock_result_1, mock_result_2, mock_result_3):
    ghsearch = GHSearch(mock_client, [])
    outcome = ghsearch.get_filtered_results(["query", "org:bort"])

    assert outcome.results == [mock_result_1, mock_result_2, mock_result_3]


def test_get_filtered_results_with_filters(mock_client, mock_result_1, mock_result_2, mock_result_3):
    ghsearch = GHSearch(mock_client, [Mock(side_effect=[True, False, True])])
    outcome = ghsearch.get_filtered_results(["query", "org:bort"])

    assert outcome.results == [mock_result_1, mock_result_3]


def test_get_filtered_results_with_exception_when_filtering(mock_client, mock_result_1, mock_progress_printer):
    mock_client._Github__requester.requestJsonAndCheck.return_value = (
        {"x-ratelimit-remaining": "9", "x-ratelimit-reset": "0"},
        {"items": [{}], "total_count": 1, "incomplete_results": False},
    )
    mock_client.create_from_raw_data.side_effect = [mock_result_1]

    ghsearch = GHSearch(mock_client, [Mock(side_effect=FilterException(Mock(), "BOOO"))])

    outcome = ghsearch.get_filtered_results(["query", "org:bort"])

    assert len(outcome.results) == 0
    mock_progress_printer.return_value.__enter__.return_value.assert_any_call("BOOO", force=True)


def test_get_filtered_results_verbose(mock_client, mock_result_1, mock_result_2, mock_result_3, mock_click):
    ghsearch = GHSearch(
        mock_client, [Mock(side_effect=[True, True, False]), Mock(side_effect=[False, True, False])], verbose=True
    )

    outcome = ghsearch.get_filtered_results(["query", "org:bort"])

    assert outcome.results == [mock_result_2]
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
        err=True,
    )


def test_get_filtered_results_many_calls(mock_client, mock_click):
    mock_client.get_rate_limit.return_value = MockRateLimit(10000, 10000, "sometime in the future", 10, 10, "now")
    mock_client._Github__requester.requestJsonAndCheck.return_value = (
        {"x-ratelimit-remaining": "9", "x-ratelimit-reset": "0"},
        {"items": [], "total_count": 257, "incomplete_results": False},
    )
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
        err=True,
    )


def test_get_filtered_results_rate_limiting_disabled(mock_client):
    mock_client.get_rate_limit.side_effect = github.GithubException(404, "Not Found")
    mock_filter = Mock()
    mock_filter.uses_core_api = True

    ghsearch = GHSearch(mock_client, [])
    ghsearch.get_filtered_results(["query", "org:bort"])

    # ensure get_rate_limit was called (and the side_effect above handled)
    mock_client.get_rate_limit.assert_called()


def test_get_filtered_results_reports_incomplete_results(mock_client, mock_result_1):
    mock_client._Github__requester.requestJsonAndCheck.return_value = (
        {"x-ratelimit-remaining": "9", "x-ratelimit-reset": "0"},
        {"items": [{}], "total_count": 1, "incomplete_results": True},
    )
    mock_client.create_from_raw_data.side_effect = [mock_result_1]

    outcome = GHSearch(mock_client, []).get_filtered_results(["query"])

    assert outcome.truncated is True
    assert outcome.truncation_reason == "incomplete_results"


def test_get_filtered_results_reports_result_ceiling(mock_client, mock_result_1, mock_result_2, mock_result_3):
    mock_client._Github__requester.requestJsonAndCheck.side_effect = [
        (
            {
                "link": '<https://api.github.com/search/code?page=2>; rel="next"',
                "x-ratelimit-remaining": "9",
                "x-ratelimit-reset": "0",
            },
            {"items": [{}, {}], "total_count": 4, "incomplete_results": False},
        ),
        (
            {"x-ratelimit-remaining": "9", "x-ratelimit-reset": "0"},
            {"items": [{}], "total_count": 4, "incomplete_results": False},
        ),
    ]
    mock_client.create_from_raw_data.side_effect = [mock_result_1, mock_result_2, mock_result_3]

    with patch("ghsearch.gh_search.MAX_SEARCH_RESULTS", 3):
        outcome = GHSearch(mock_client, []).get_filtered_results(["query"])

    assert outcome.retrieved_count == 3
    assert outcome.truncated is True
    assert outcome.truncation_reason == "result_ceiling"


def test_get_filtered_results_stops_at_search_rate_limit(mock_client, mock_result_1):
    mock_client._Github__requester.requestJsonAndCheck.return_value = (
        {
            "link": '<https://api.github.com/search/code?page=2>; rel="next"',
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": "0",
        },
        {"items": [{}], "total_count": 2, "incomplete_results": False},
    )
    mock_client.create_from_raw_data.side_effect = [mock_result_1]

    outcome = GHSearch(mock_client, []).get_filtered_results(["query"])

    assert outcome.truncated is True
    assert outcome.truncation_reason == "rate_limit"
    assert mock_client._Github__requester.requestJsonAndCheck.call_count == 1


def test_get_filtered_results_stops_at_max_results(mock_client, mock_result_1, mock_result_2):
    outcome = GHSearch(mock_client, []).get_filtered_results(["query"], max_results=1)

    assert outcome.results == [mock_result_1]
    assert outcome.truncated is True
    assert outcome.truncation_reason == "max_results"
    assert mock_client.create_from_raw_data.call_count == 3


def test_get_filtered_results_reports_refused_search_rate_limit(mock_client):
    mock_client._Github__requester.requestJsonAndCheck.side_effect = github.RateLimitExceededException(
        403,
        {"message": "API rate limit exceeded"},
        {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "0"},
    )

    with pytest.raises(CodeSearchRateLimitError, match=""):
        GHSearch(mock_client, []).get_filtered_results(["query"])
