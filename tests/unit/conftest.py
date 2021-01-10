from unittest.mock import Mock

import github
import pytest


@pytest.fixture
def mock_client():
    return Mock(spec=github.Github)
