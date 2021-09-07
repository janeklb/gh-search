from unittest.mock import Mock, call, patch

import click
import pytest
from github import BadCredentialsException, Github, GithubException

from ghsearch.main import run
from ghsearch.output import Printer

from . import MockPaginatedList, MockRateLimit, build_mock_content_file


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
def mock_content_file_repo2_src_other_archived():
    return build_mock_content_file("org/repo2", "src/other.py", archived=True)


@pytest.fixture
def mock_github(
    mock_content_file_repo1_readme, mock_content_file_repo1_file, mock_content_file_repo2_src_other_archived
):
    mock = Mock(spec=Github)
    mock.search_code.return_value = MockPaginatedList(
        mock_content_file_repo1_readme,
        mock_content_file_repo1_file,
        mock_content_file_repo2_src_other_archived,
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


@pytest.fixture()
def mock_printer():
    return Mock(spec=Printer)


def test_run_exclude_archived_by_default(
    assert_click_echo_calls, mock_printer, mock_content_file_repo1_readme, mock_content_file_repo1_file
):
    run(["query"], "token", mock_printer)
    mock_printer.print.assert_called_once_with(
        ["query"],
        [
            mock_content_file_repo1_readme,
            mock_content_file_repo1_file,
        ],
    )


def test_run_bad_credentials(assert_click_echo_calls, mock_github, mock_printer):
    mock_github.search_code.side_effect = BadCredentialsException(404, "No!")
    with pytest.raises(click.UsageError, match='Bad Credentials: 404 "No!"'):
        run(["query"], "bad-credentials", mock_printer)


def test_run_verbose(assert_click_echo_calls, mock_printer):
    run(["query"], "token", mock_printer, verbose=True)
    assert_click_echo_calls(
        call("Core rate limit: 45/50 (resets soon), Search rate limit: 10/10 (resets soon)"),
        call("Skipping result for org/repo2 via NotArchivedFilter"),
        call("Core rate limit: 43/50 (resets even sooner), Search rate limit: 9/10 (resets even sooner)"),
    )


def test_run_include_archived(
    assert_click_echo_calls,
    mock_printer,
    mock_content_file_repo1_readme,
    mock_content_file_repo1_file,
    mock_content_file_repo2_src_other_archived,
):
    run(["query"], "token", mock_printer, include_archived=True)
    mock_printer.print.assert_called_once_with(
        ["query"],
        [
            mock_content_file_repo1_readme,
            mock_content_file_repo1_file,
            mock_content_file_repo2_src_other_archived,
        ],
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
    run(["query"], "token", mock_printer, path_filter="file.txt")
    mock_printer.print.assert_called_once_with(["query"], [mock_content_file_repo1_file])


def test_run_when_raises_github_exception_422(mock_github, mock_printer):
    mock_github.search_code.side_effect = GithubException(
        422, {"message": "Fail!", "errors": [{"message": "reason1"}, {"message": "reason2"}]}
    )

    with pytest.raises(click.UsageError, match="Fail! \\(GitHub Exception\\): reason1, reason2"):
        run(["query"], "token", mock_printer)


def test_run_when_raises_github_exception(mock_github, mock_printer):
    mock_github.search_code.side_effect = GithubException(400, "")

    with pytest.raises(GithubException):
        run(["query"], "token", mock_printer)
