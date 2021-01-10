from unittest.mock import Mock

import pytest
from github.ContentFile import ContentFile

from ghsearch.filters import build_content_filter, build_not_archived_filter, build_path_filter


@pytest.fixture
def mock_content_file():
    return Mock(spec=ContentFile)


@pytest.mark.parametrize(
    "path_matcher, path, expected_result",
    [
        ("file.py", "path/to/file.py", True),
        ("path", "path/to/file.py", True),
        ("to/file", "path/to/file.py", True),
        ("other.py", "path/to/file.py", False),
    ],
)
def test_build_path_filter(path_matcher, path, expected_result, mock_content_file):
    path_filter = build_path_filter(path_matcher)
    mock_content_file.path = path

    assert path_filter(mock_content_file) is expected_result


@pytest.mark.parametrize(
    "content_matcher, content_bytes, expected_result",
    [
        ("this str", b"I'm looking for this string.", True),
        ("another str", b"I'm still looking for this str", False),
    ],
)
def test_build_content_filter(content_matcher, content_bytes, expected_result, mock_content_file):
    content_filter = build_content_filter(content_matcher)
    mock_content_file.decoded_content = content_bytes

    assert content_filter(mock_content_file) is expected_result


@pytest.mark.parametrize(
    "archived, expected_result",
    [
        (False, True),
        (True, False),
    ],
)
def test_build_not_archived_filter(archived, expected_result, mock_content_file):
    not_archived_filter = build_not_archived_filter()
    mock_content_file.repository.archived = archived

    assert not_archived_filter(mock_content_file) is expected_result
