from unittest.mock import patch

import pytest

from ghsearch.client import build_client


@pytest.fixture
def mock_github():
    with patch("ghsearch.client.Github", autospec=True) as mock:
        yield mock


def test_build_client_returns_github_instance(mock_github):
    assert build_client("foo-token") == mock_github.return_value


def test_build_client_passes_expected_parameters(mock_github):
    build_client("foo-token", "https://github.example.org/api/v3")

    mock_github.assert_called_once_with(
        login_or_token="foo-token",
        base_url="https://github.example.org/api/v3",
        per_page=1000,
    )


def test_build_client_passes_expected_parameters_defaults_github(mock_github):
    build_client("foo-token")

    mock_github.assert_called_once_with(
        login_or_token="foo-token",
        per_page=1000,
    )
