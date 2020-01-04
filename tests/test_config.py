"""Tests for config package."""
import os
import tempfile
from unittest.mock import patch

import pytest

from detective import config


def test_find_hass_config():
    """Test finding HASS config."""
    with patch.dict(os.environ, {"HASSIO_TOKEN": "yo"}):
        assert config.find_hass_config() == "/config"

    with patch.dict(os.environ, {}, clear=True), patch(
        "detective.config.default_hass_config_dir", return_value="default-dir"
    ), patch("os.path.isdir", return_value=True):
        assert config.find_hass_config() == "default-dir"

    with patch.dict(os.environ, {}, clear=True), patch(
        "os.path.isdir", return_value=False
    ), pytest.raises(ValueError):
        config.find_hass_config()


def test_load_hass_config():
    """Test loading hass config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "configuration.yaml"), "wt") as fp:
            fp.write(
                """
mock_secret: !secret some_secret
included: !include included.yaml
mock_env: !env_var MOCK_ENV
mock_env: !env_var MOCK_ENV
mock_dir_list: !include_dir_list ./zxc
mock_dir_merge_list: !include_dir_merge_list ./zxc
mock_dir_named: !include_dir_named ./zxc
mock_dir_merge: !include_dir_merge_named ./zxc
# Trigger duplicate error
mock_secret: !secret other_secret
        """
            )

        with open(os.path.join(tmpdir, "secrets.yaml"), "wt") as fp:
            fp.write(
                """
some_secret: test-some-secret
other_secret: test-other-secret
        """
            )

        with open(os.path.join(tmpdir, "included.yaml"), "wt") as fp:
            fp.write(
                """
some: value
        """
            )

        configuration = config.load_hass_config(tmpdir)

    # assert configuration["mock_secret"] == "test-other-secret"  # TODO: fix
    assert configuration["included"] == {"some": "value"}


def test_db_url_from_hass_config():
    """Test extracting recorder url from config."""
    with patch("detective.config.load_hass_config", return_value={}), patch(
        "os.path.isfile", return_value=False
    ), pytest.raises(ValueError):
        config.db_url_from_hass_config("mock-path")

    with patch("detective.config.load_hass_config", return_value={}), patch(
        "os.path.isfile", return_value=True
    ):
        assert (
            config.db_url_from_hass_config("mock-path")
            == "sqlite:///mock-path/home-assistant_v2.db"
        )

    with patch(
        "detective.config.load_hass_config",
        return_value={"recorder": {"db_url": "mock-url"}},
    ):
        assert config.db_url_from_hass_config("mock-path") == "mock-url"

