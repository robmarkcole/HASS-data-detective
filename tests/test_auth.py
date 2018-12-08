"""Tests for auth package."""
import json
from unittest.mock import mock_open, patch

from detective.auth import Auth


def test_auth_from_hass_config():
    """Test extracting users from hass config."""
    mopen = mock_open(read_data=json.dumps({
        'key': 'auth',
        'version': 1,
        'data': {
            'users': [{
                'id': 'mock-user-id',
                'name': 'mock-user-name'
            }],
            'refresh_tokens': [{
                'id': 'mock-refresh-id',
                'user_id': 'mock-user-id',
                'client_name': 'mock-client-name',
                'client_id': 'mock-client-id',
            }]
        }
    }))

    with patch('detective.auth.open', mopen):
        auth = Auth('/some/path')

    assert auth.users == {
        'mock-user-id': {
            'id': 'mock-user-id',
            'name': 'mock-user-name'
        }
    }
    assert auth.refresh_tokens == {
        'mock-refresh-id': {
            'id': 'mock-refresh-id',
            'user': auth.users['mock-user-id'],
            'client_id': 'mock-client-id',
            'client_name': 'mock-client-name',
        }
    }
