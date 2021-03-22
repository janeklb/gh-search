from unittest.mock import PropertyMock

import pytest
from github.GithubException import GithubException

from ghsearch.filters import ContentFilter, FilterException, NotArchivedFilter, PathFilter

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


def test_content_filter_with_github_exception():
    content_filter = ContentFilter("something")
    mock_content_file = build_mock_content_file()
    type(mock_content_file).decoded_content = PropertyMock(side_effect=GithubException(403, {"message": "fail"}))

    with pytest.raises(FilterException, match="Error reading content from org/repo/path: fail") as exc_info:
        content_filter(mock_content_file)

    assert exc_info.value.filter == content_filter


@pytest.mark.parametrize(
    "archived, expected_result",
    [
        (False, True),
        (True, False),
    ],
)
def test_build_not_archived_filter(archived, expected_result):
    not_archived_filter = NotArchivedFilter()
    mock_content_file = build_mock_content_file(archived=archived)

    assert not_archived_filter(mock_content_file) is expected_result
    assert not_archived_filter.uses_core_api is True


def test_not_archived_filter_caches_access_to_archived_property():
    not_archived_filter = NotArchivedFilter()

    archived1_1 = PropertyMock(return_value=True)
    repo1_1 = build_mock_content_file("org/repo1", "file1.txt")
    type(repo1_1.repository).archived = archived1_1

    archived1_2 = PropertyMock(return_value=True)
    repo1_2 = build_mock_content_file("org/repo1", "file2.txt")
    type(repo1_2.repository).archived = archived1_2

    archived2_1 = PropertyMock(return_value=True)
    repo2_1 = build_mock_content_file("org/repo2", "file1.txt")
    type(repo2_1.repository).archived = archived2_1

    not_archived_filter(repo1_1)
    not_archived_filter(repo1_2)
    not_archived_filter(repo2_1)

    archived1_1.assert_called_once()
    archived1_2.assert_not_called()
    archived2_1.assert_called_once()
