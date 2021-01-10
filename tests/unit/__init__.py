from unittest.mock import Mock

from github.ContentFile import ContentFile


def build_mock_result(repo_full_name: str, path: str, archived: bool = False, decoded_content: bytes = b""):
    mock = Mock(spec=ContentFile)
    mock.repository.full_name = repo_full_name
    mock.repository.archived = archived
    mock.repository.html_url = f"https://www.github.com/{repo_full_name}"
    mock.path = path
    mock.decoded_content = decoded_content
    return mock
