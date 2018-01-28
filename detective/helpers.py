"""
Helper functions.
"""
import json


def binary_state(value):
    """Return a binary for the state of binary sensors"""
    if value == 'on':
        return True
    elif value == 'off':
        return False
    else:
        return float('nan')


def isfloat(value):
    """
    Check if string can be parsed to a float.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


def load_url(filename):
    """Convenience for loading a url from a json file."""
    try:
        with open(filename, 'r') as fp:
            url = json.load(fp)
    except Exception as e:
        print('Failed to load url')
        url = None
    return url['url']
