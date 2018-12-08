"""
Helper functions for config.
"""
import os

from ruamel.yaml import YAML
from ruamel.yaml.constructor import SafeConstructor


def default_hass_config_dir():
    """Put together the default configuration directory based on the OS."""
    data_dir = os.getenv('APPDATA') if os.name == "nt" \
        else os.path.expanduser('~')
    return os.path.join(data_dir, '.homeassistant')


def find_hass_config():
    """Try to find HASS config."""
    if 'HASSIO_TOKEN' in os.environ:
        return '/config'

    config_dir = default_hass_config_dir()

    if os.path.isdir(config_dir):
        return config_dir

    raise ValueError(
        "Unable to automatically find the location of Home Assistant "
        "config. Please pass it in.")


class HassSafeConstructor(SafeConstructor):
    """Hass specific SafeConstructor."""


def _secret_yaml(loader, node):
    """Load secrets and embed it into the configuration YAML."""
    fname = os.path.join(os.path.dirname(loader.name), 'secrets.yaml')

    try:
        with open(fname, encoding='utf-8') as secret_file:
            secrets = YAML(typ='safe').load(secret_file)
    except FileNotFoundError:
        raise ValueError("Secrets file {} not found".format(fname)) from None

    try:
        return secrets[node.value]
    except KeyError:
        raise ValueError("Secret {} not found".format(node.value)) from None


def _stub_dict(constructor, node):
    """Stub a constructor with a dictionary."""
    return {}


HassSafeConstructor.add_constructor('!include', _stub_dict)
HassSafeConstructor.add_constructor('!env_var', _stub_dict)
HassSafeConstructor.add_constructor('!secret', _secret_yaml)
HassSafeConstructor.add_constructor('!include_dir_list', _stub_dict)
HassSafeConstructor.add_constructor('!include_dir_merge_list', _stub_dict)
HassSafeConstructor.add_constructor('!include_dir_named', _stub_dict)
HassSafeConstructor.add_constructor('!include_dir_merge_named', _stub_dict)


def load_hass_config(path):
    """Load the HASS config."""
    fname = os.path.join(path, 'configuration.yaml')

    yaml = YAML(typ='safe')
    # Compat with HASS
    yaml.allow_duplicate_keys = True
    # Stub HASS constructors
    HassSafeConstructor.name = fname
    yaml.Constructor = HassSafeConstructor

    with open(fname, encoding='utf-8') as conf_file:
        # If configuration file is empty YAML returns None
        # We convert that to an empty dict
        return yaml.load(conf_file) or {}


def db_url_from_hass_config(path):
    """Find the recorder database url from a HASS config dir."""
    config = load_hass_config(path)
    default = 'sqlite:///{}'.format(os.path.join(path, 'home-assistant_v2.db'))

    recorder = config.get('recorder')

    if not recorder:
        return default

    return recorder.get('db_url', default)
