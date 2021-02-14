import pytest

from ghsearch.filters import ContentFilter, NotArchivedFilter, PathFilter

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
