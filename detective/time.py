"""
Helper functions for datetimes.
"""


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
