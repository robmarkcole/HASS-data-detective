"""Tests for helpers package."""
import os
import tempfile
from unittest.mock import patch

from detective import helpers


def test_find_hass_config():
    """Test finding HASS config."""
    with patch.dict(os.environ, {'HASSIO_TOKEN': 'yo'}):
        assert helpers.find_hass_config() == '/config'

    with patch.dict(os.environ, {}, clear=True), \
            patch('detective.helpers.default_hass_config_dir',
                  return_value='default-dir'), \
            patch('os.path.isdir', return_value=True):
        assert helpers.find_hass_config() == 'default-dir'

    with patch.dict(os.environ, {}, clear=True), \
            patch('os.path.isdir', return_value=False):
        assert helpers.find_hass_config() is None


def test_load_hass_config():
    """Test loading hass config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, 'configuration.yaml'), 'wt') as fp:
            fp.write("""
mock_secret: !secret some_secret
mock_env: !env_var MOCK_ENV
mock_dir_list: !include_dir_list ./zxc
mock_dir_merge_list: !include_dir_merge_list ./zxc
mock_dir_named: !include_dir_named ./zxc
mock_dir_merge: !include_dir_merge_named ./zxc
# Trigger duplicate error
mock_secret: !secret other_secret
        """)

        with open(os.path.join(tmpdir, 'secrets.yaml'), 'wt') as fp:
            fp.write("""
some_secret: test-some-secret
other_secret: test-other-secret
        """)

        config = helpers.load_hass_config(tmpdir)

    assert config['mock_secret'] == 'test-other-secret'


def test_db_url_from_hass_config():
    """Test extracting recorder url from config."""
    with patch('detective.helpers.load_hass_config', return_value={}):
        assert helpers.db_url_from_hass_config('mock-path') == \
            'sqlite:///mock-path/home-assistant_v2.db'

    with patch('detective.helpers.load_hass_config', return_value={
        'recorder': {
            'db_url': 'mock-url'
        }
    }):
        assert helpers.db_url_from_hass_config('mock-path') == 'mock-url'
