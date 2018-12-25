from unittest.mock import patch

import pytest

from detective.core import HassDatabase


@pytest.fixture
def mock_db():
    with patch('detective.core.create_engine'):
        return HassDatabase('mock://db')
