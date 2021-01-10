from unittest.mock import patch

import pytest


@pytest.fixture
def mock_click_echo():
    with patch("click.echo") as mock:
        yield mock


@pytest.fixture
def assert_click_echo_calls(mock_click_echo):
    def _fn(*calls):
        mock_click_echo.assert_has_calls(calls, any_order=False)
        assert mock_click_echo.call_count == len(calls)

    return _fn
