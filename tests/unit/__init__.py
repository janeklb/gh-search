from types import SimpleNamespace
from unittest.mock import Mock

from github.ContentFile import ContentFile


class MockPaginatedList:
    def __init__(self, *items):
        self.items = items
        self.totalCount = len(items)

    def __iter__(self):
        return iter(self.items)


class MockRateLimit:
    def __init__(self, core_remaining, core_limit, core_reset, search_remaining, search_limit, search_reset):
        self.core = SimpleNamespace(remaining=core_remaining, limit=core_limit, reset=core_reset)
        self.search = SimpleNamespace(remaining=search_remaining, limit=search_limit, reset=search_reset)


def build_mock_result(repo_full_name: str, path: str, archived: bool = False, decoded_content: bytes = b""):
    mock = Mock(spec=ContentFile)
    mock.repository.full_name = repo_full_name
    mock.repository.archived = archived
    mock.repository.html_url = f"https://www.github.com/{repo_full_name}"
    mock.path = path
    mock.decoded_content = decoded_content
    return mock
