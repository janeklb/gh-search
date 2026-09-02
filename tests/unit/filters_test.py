from unittest.mock import PropertyMock

import pytest
from github.GithubException import GithubException

from ghsearch.filters import ContentFilter, FilterException, PathFilter, RegexContentFilter

from . import build_mock_content_file


@pytest.mark.parametrize(
    "path_matcher, path, expected_result",
    [
        ("file.py", "path/to/file.py", True),
        ("path", "path/to/file.py", True),
        ("to/file", "path/to/file.py", True),
        ("other.py", "path/to/file.py", False),
    ],
)
def test_build_path_filter(path_matcher, path, expected_result):
    path_filter = PathFilter(path_matcher)
    mock_content_file = build_mock_content_file(path=path)

    assert path_filter(mock_content_file) is expected_result
    assert path_filter.uses_core_api is False


@pytest.mark.parametrize(
    "content_matcher, content_bytes, expected_result",
    [
        ("this str", b"I'm looking for this string.", True),
        ("another str", b"I'm still looking for this str", False),
    ],
)
def test_build_content_filter(content_matcher, content_bytes, expected_result):
    content_filter = ContentFilter(content_matcher)
    mock_content_file = build_mock_content_file(decoded_content=content_bytes)

    assert content_filter(mock_content_file) is expected_result
    assert content_filter.uses_core_api is True


@pytest.mark.parametrize(
    "content_matcher, content_bytes, expected_result",
    [
        ("regex\\s{1}test", b"I'm looking for a regex test str", True),
        ("regex\\s{2}test", b"I'm looking for a regex test str", False),
    ],
)
def test_build_regex_content_filter(content_matcher, content_bytes, expected_result):
    content_filter = RegexContentFilter(content_matcher)
    mock_content_file = build_mock_content_file(decoded_content=content_bytes)

    assert content_filter(mock_content_file) is expected_result
    assert content_filter.uses_core_api is True


def test_build_regex_content_filter_invalid_regex():
    with pytest.raises(
        FilterException,
        match="Failed to compile regular expression from '\\[invalid regex': unterminated character set at position 0",
    ):
        RegexContentFilter("[invalid regex")


def test_content_filter_with_github_exception():
    content_filter = ContentFilter("something")
    mock_content_file = build_mock_content_file()
    type(mock_content_file).decoded_content = PropertyMock(side_effect=GithubException(403, {"message": "fail"}))

    with pytest.raises(FilterException, match="Error reading content from org/repo/path: fail") as exc_info:
        content_filter(mock_content_file)

    assert exc_info.value.filter == content_filter
