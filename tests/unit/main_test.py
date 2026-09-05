from unittest.mock import Mock, call, patch

import click
import pytest
from github import BadCredentialsException, GithubException

from ghsearch.gh_search import TRUNCATION_REASON_INCOMPLETE_RESULTS, TRUNCATION_REASON_RESULT_CEILING, SearchOutcome
from ghsearch.main import _warn_if_search_is_truncated, run
from ghsearch.output import Printer

from . import MockRateLimit, build_mock_content_file


@pytest.fixture(autouse=True)
def mock_progress_printer():
    with patch("ghsearch.gh_search.ProgressPrinter") as mock:
        yield mock


@pytest.fixture
def mock_content_file_repo1_readme():
    return build_mock_content_file("org/repo1", "README.md", decoded_content=b"special content")


@pytest.fixture
def mock_content_file_repo1_file():
    return build_mock_content_file("org/repo1", "file.txt")


@pytest.fixture
def mock_github(mock_content_file_repo1_readme, mock_content_file_repo1_file):
    mock = Mock()
    mock._Github__requester.requestJsonAndCheck.return_value = (
        {"x-ratelimit-remaining": "9", "x-ratelimit-reset": "0"},
        {"items": [{}, {}], "total_count": 2, "incomplete_results": False},
    )
    mock.create_from_raw_data.side_effect = [mock_content_file_repo1_readme, mock_content_file_repo1_file]
    mock.get_rate_limit.side_effect = [
        MockRateLimit(45, 50, "soon", 10, 10, "soon"),
        MockRateLimit(43, 50, "even sooner", 9, 10, "even sooner"),
    ]
    return mock


@pytest.fixture(autouse=True)
def mock_build_client(mock_github):
    with patch("ghsearch.main.build_client") as mock:
        mock.return_value = mock_github
        yield mock


@pytest.fixture()
def mock_printer():
    return Mock(spec=Printer)


def test_run(assert_click_echo_calls, mock_printer, mock_content_file_repo1_readme, mock_content_file_repo1_file):
    run(["query"], "token", mock_printer)
    mock_printer.print.assert_called_once_with(
        ["query"],
        [
            mock_content_file_repo1_readme,
            mock_content_file_repo1_file,
        ],
    )


def test_run_bad_credentials(assert_click_echo_calls, mock_github, mock_printer):
    mock_github._Github__requester.requestJsonAndCheck.side_effect = BadCredentialsException(404, "No!")
    with pytest.raises(click.UsageError, match='Bad Credentials: 404 "No!"'):
        run(["query"], "bad-credentials", mock_printer)


def test_run_verbose(assert_click_echo_calls, mock_printer):
    run(["query"], "token", mock_printer, verbose=True)
    assert_click_echo_calls(
        call("Core rate limit: 45/50 (resets soon), Search rate limit: 10/10 (resets soon)"),
        call("Core rate limit: 43/50 (resets even sooner), Search rate limit: 9/10 (resets even sooner)"),
    )


def test_run_content_filter(assert_click_echo_calls, mock_printer, mock_content_file_repo1_readme):
    run(["query"], "token", mock_printer, content_filter="special content")
    mock_printer.print.assert_called_once_with(
        ["query"],
        [
            mock_content_file_repo1_readme,
        ],
    )


def test_run_regex_content_filter(assert_click_echo_calls, mock_printer, mock_content_file_repo1_readme):
    run(["query"], "token", mock_printer, regex_content_filter="special\\scontent")
    mock_printer.print.assert_called_once_with(
        ["query"],
        [
            mock_content_file_repo1_readme,
        ],
    )


def test_run_regex_content_filter_bad_regex(mock_printer):
    with pytest.raises(
        click.UsageError,
        match="Failed to compile regular expression from '\\[': unterminated character set at position 0",
    ):
        run(["query"], "token", mock_printer, regex_content_filter="[")


def test_run_path_filter(assert_click_echo_calls, mock_printer, mock_content_file_repo1_file):
    run(["query"], "token", mock_printer, path_filter=r"\.txt$")
    mock_printer.print.assert_called_once_with(["query"], [mock_content_file_repo1_file])


def test_run_path_filter_bad_regex(mock_printer):
    with pytest.raises(
        click.UsageError,
        match="Failed to compile path regular expression from '\\[': unterminated character set at position 0",
    ):
        run(["query"], "token", mock_printer, path_filter="[")


def test_run_when_raises_github_exception_422(mock_github, mock_printer):
    mock_github._Github__requester.requestJsonAndCheck.side_effect = GithubException(
        422, {"message": "Fail!", "errors": [{"message": "reason1"}, {"message": "reason2"}]}
    )

    with pytest.raises(click.UsageError, match="Fail! \\(GitHub Exception\\): reason1, reason2"):
        run(["query"], "token", mock_printer)


def test_run_when_raises_github_exception(mock_github, mock_printer):
    mock_github._Github__requester.requestJsonAndCheck.side_effect = GithubException(400, "")

    with pytest.raises(GithubException):
        run(["query"], "token", mock_printer)


@pytest.mark.parametrize(
    "reason, expected_message",
    [
        (
            TRUNCATION_REASON_INCOMPLETE_RESULTS,
            "Warning: GitHub reported incomplete code-search results. Narrow the query and retry.",
        ),
        (
            TRUNCATION_REASON_RESULT_CEILING,
            "Warning: GitHub returns at most 1,000 code-search results. Narrow the query and retry.",
        ),
    ],
)
def test_warn_if_search_is_truncated(mock_click_echo, reason, expected_message):
    _warn_if_search_is_truncated(SearchOutcome(truncated=True, truncation_reason=reason))

    mock_click_echo.assert_called_once_with(expected_message, err=True)
