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


def load_url(filename):
    """Convenience for loading a url from a json file."""
    try:
        with open(filename, 'r') as fp:
            url = json.load(fp)
    except Exception as e:
        print('Failed to load url')
        url = None
    return url['url']
