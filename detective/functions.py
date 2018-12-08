"""
Helper functions.
"""


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