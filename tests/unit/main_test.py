from types import SimpleNamespace as StubObject
from unittest.mock import call, patch

import pytest

from ghsearch.main import run

from . import build_mock_result


@pytest.fixture(autouse=True)
def mock_build_client():
    with patch("ghsearch.main.build_client") as mock:
        mock.return_value.search_code.return_value = [
            build_mock_result("org/repo1", "README.md", decoded_content=b"special content"),
            build_mock_result("org/repo1", "file.txt"),
            build_mock_result("org/repo2", "src/other.py", archived=True),
        ]
        mock.return_value.get_rate_limit.side_effect = [StubObject(search=10), StubObject(search=9)]
        yield mock


@pytest.fixture(autouse=True)
def mock_click_echo():
    with patch("click.echo") as mock:
        yield mock


@pytest.fixture
def assert_click_echo_calls(mock_click_echo):
    def _fn(*calls):
        mock_click_echo.assert_has_calls(calls, any_order=False)
        assert mock_click_echo.call_count == len(calls)

    return _fn


def test_run(assert_click_echo_calls):
    run("query")
    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
    )


def test_run_verbose(assert_click_echo_calls):
    run("query", verbose=True)
    assert_click_echo_calls(
        call("Starting with GH Rate limit: 10"),
        call("Checking result for org/repo1"),
        call("Checking result for org/repo1"),
        call("Checking result for org/repo2"),
        call("Skipping result for org/repo2 via not_archived_filter"),
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
        call("Ending with GH Rate limit: 9"),
    )


def test_run_include_archived(assert_click_echo_calls):
    run("query", include_archived=True)
    assert_click_echo_calls(
        call("Results:"),
        call(" 2 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
        call("\t- file.txt"),
        call(" 1 - org/repo2: https://www.github.com/org/repo2/search?utf8=✓&q=query"),
        call("\t- src/other.py"),
    )


def test_run_content_filter(assert_click_echo_calls):
    run("query", content_filter="special content")
    assert_click_echo_calls(
        call("Results:"),
        call(" 1 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- README.md"),
    )


def test_run_path_filter(assert_click_echo_calls):
    run("query", path_filter="file.txt")
    assert_click_echo_calls(
        call("Results:"),
        call(" 1 - org/repo1: https://www.github.com/org/repo1/search?utf8=✓&q=query"),
        call("\t- file.txt"),
    )
