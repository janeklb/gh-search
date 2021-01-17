from types import SimpleNamespace as StubObject
from unittest.mock import Mock, call, patch

import pytest
from github import BadCredentialsException, Github

from ghsearch.main import run

from . import build_mock_result


@pytest.fixture(autouse=True)
def mock_progress_printer():
    with patch("ghsearch.gh_search.ProgressPrinter") as mock:
        yield mock


@pytest.fixture
def mock_github():
    mock = Mock(spec=Github)
    mock.search_code.return_value = [
        build_mock_result("org/repo1", "README.md", decoded_content=b"special content"),
        build_mock_result("org/repo1", "file.txt"),
        build_mock_result("org/repo2", "src/other.py", archived=True),
    ]
    mock.get_rate_limit.side_effect = [StubObject(search=10), StubObject(search=9)]
    return mock


@pytest.fixture(autouse=True)
def mock_build_client(mock_github):
    with patch("ghsearch.main.build_client") as mock:
        mock.return_value = mock_github
        yield mock


def test_run(assert_click_echo_calls):
    run("query", [], "token")
    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
    )


def test_run_with_qualifiers(assert_click_echo_calls):
    run("query", ["org:foo", "filename:bar"], "token")
    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query%20filename%3Abar"),
        call("\t- README.md"),
        call("\t- file.txt"),
    )


def test_run_bad_credentials(assert_click_echo_calls, mock_github):
    mock_github.search_code.side_effect = BadCredentialsException(404, "No!")
    run("query", [], "bad-credentials")
    assert_click_echo_calls(call('Bad Credentials: 404 "No!"\n\nrun gh-search --help', err=True))


def test_run_verbose(assert_click_echo_calls):
    run("query", [], "token", verbose=True)
    assert_click_echo_calls(
        call("Starting with GH Rate limit: 10"),
        call("Skipping result for org/repo2 via not_archived_filter"),
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
        call("Ending with GH Rate limit: 9"),
    )


def test_run_include_archived(assert_click_echo_calls):
    run("query", [], "token", include_archived=True)
    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
        call(" 1 - org/repo2: https://www.github.com/org/repo2/search?utf8=✓&q=query"),
        call("\t- src/other.py"),
    )


def test_run_content_filter(assert_click_echo_calls):
    run("query", [], "token", content_filter="special content")
    assert_click_echo_calls(
        call("Results:"),
        call(" 1 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
    )


def test_run_path_filter(assert_click_echo_calls):
    run("query", [], "token", path_filter="file.txt")
    assert_click_echo_calls(
        call("Results:"),
        call(" 1 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- file.txt"),
    )
