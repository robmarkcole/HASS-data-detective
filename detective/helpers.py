"""
Helper functions.
"""
import json
import os

from ruamel.yaml import YAML
from ruamel.yaml.constructor import SafeConstructor


def binary_state(value):
    """Return a binary for the state of binary sensors"""
    if value == 'on':
        return True
    elif value == 'off':
        return False
    else:
        return float('nan')


def ensure_list(*args):
    """
    Check if a list is passed, if not convert args to a list.

    Parameters
    ----------
    args : single entity or list of entities
        The entities of interest.

    Returns
    -------
    list
        A list of entities.
    """
    entities = []
    for arg in args:
        if isinstance(arg, list):
            entities += arg
        else:
            entities.append(arg)
    return entities


def isfloat(value):
    """
    Check if string can be parsed to a float.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_weekday(dtObj):
    """Check a datetime object dtObj is a weekday"""
    if dtObj.weekday() < 5:
        return True
    else:
        return False


def time_category(dtObj):
    """Return a time category, bed, home, work, given a dtObj."""
    if 9 <= dtObj.hour <= 17:
        return 'daytime'
    elif 5 <= dtObj.hour < 9:
        return 'morning'
    elif 17 < dtObj.hour < 23:
        return 'evening'
    else:
        return 'night'


def load_credentials(credentials_filepath):
    """Convenience to load db credentials from a json file, returns a dict."""
    try:
        with open(credentials_filepath, 'r') as fp:
            credentials = json.load(fp)
    except Exception as e:
        print('Failed to load API secrets key: {}'.format(e))
        credentials = None
    return credentials


def load_url(filename):
    """Convenience for loading a url from a json file."""
    try:
        with open(filename, 'r') as fp:
            url = json.load(fp)
    except Exception as e:
        print('Failed to load url')
        url = None
    return url['url']


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

    return None


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
