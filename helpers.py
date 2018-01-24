"""
Helper functions.
"""
import json


def load_url(filename):
    """Convenience for loading a url from a json file."""
    try:
        with open(filename, 'r') as fp:
            url = json.load(fp)
    except Exception as e:
        print('Failed to load url')
        url = None
    return url['url']


def isfloat(value):
    """
    Check if string can be parsed to a float.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False
