from unittest.mock import Mock, call, patch

import click
import pytest
from github import BadCredentialsException, Github, GithubException

from ghsearch.main import run

from . import MockPaginatedList, MockRateLimit, build_mock_content_file


@pytest.fixture(autouse=True)
def mock_progress_printer():
    with patch("ghsearch.gh_search.ProgressPrinter") as mock:
        yield mock


@pytest.fixture
def mock_github():
    mock = Mock(spec=Github)
    mock.search_code.return_value = MockPaginatedList(
        build_mock_content_file("org/repo1", "README.md", decoded_content=b"special content"),
        build_mock_content_file("org/repo1", "file.txt"),
        build_mock_content_file("org/repo2", "src/other.py", archived=True),
    )
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


def test_run(assert_click_echo_calls):
    run(["query"], "token")
    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
    )


def test_run_with_qualifiers(assert_click_echo_calls):
    run(["query", "org:foo", "filename:bar"], "token")
    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query%20filename%3Abar"),
        call("\t- README.md"),
        call("\t- file.txt"),
    )


def test_run_bad_credentials(assert_click_echo_calls, mock_github):
    mock_github.search_code.side_effect = BadCredentialsException(404, "No!")
    with pytest.raises(click.UsageError, match='Bad Credentials: 404 "No!"'):
        run(["query"], "bad-credentials")


def test_run_verbose(assert_click_echo_calls):
    run(["query"], "token", verbose=True)
    assert_click_echo_calls(
        call("Core rate limit: 45/50 (resets soon), Search rate limit: 10/10 (resets soon)"),
        call("Skipping result for org/repo2 via NotArchivedFilter"),
        call("Core rate limit: 43/50 (resets even sooner), Search rate limit: 9/10 (resets even sooner)"),
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
    )


def test_run_include_archived(assert_click_echo_calls):
    run(["query"], "token", include_archived=True)
    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
        call(" 1 - org/repo2: https://www.github.com/org/repo2/search?utf8=✓&q=query"),
        call("\t- src/other.py"),
    )


def test_run_content_filter(assert_click_echo_calls):
    run(["query"], "token", content_filter="special content")
    assert_click_echo_calls(
        call("Results:"),
        call(" 1 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
    )


def test_run_path_filter(assert_click_echo_calls):
    run(["query"], "token", path_filter="file.txt")
    assert_click_echo_calls(
        call("Results:"),
        call(" 1 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- file.txt"),
    )


def test_run_no_results(assert_click_echo_calls, mock_github):
    mock_github.search_code.return_value = MockPaginatedList()
    run(["query"], "token")
    assert_click_echo_calls(call("No results!"))


def test_run_when_raises_github_exception_422(mock_github):
    mock_github.search_code.side_effect = GithubException(
        422, {"message": "Fail!", "errors": [{"message": "reason1"}, {"message": "reason2"}]}
    )

    with pytest.raises(click.UsageError, match="Fail! \\(GitHub Exception\\): reason1, reason2"):
        run(["query"], "token")


def test_run_when_raises_github_exception(mock_github):
    mock_github.search_code.side_effect = GithubException(400, "")

    with pytest.raises(GithubException):
        run(["query"], "token")
