"""
Helper functions for datetimes.
"""
from datetime import datetime
import time

import pytz

UTC = pytz.UTC
# Ordered list of time categories that `time_category` produces
TIME_CATEGORIES = ['morning', 'daytime', 'evening', 'night']

# To localize the returned UTC times to local times
LOCAL_UTC_OFFSET = (
    datetime.fromtimestamp(time.time()) -
    datetime.utcfromtimestamp(time.time()))


def localize(dt):
    """Localize a datetime object to local time."""
    if dt.tzinfo is UTC:
        return (dt + LOCAL_UTC_OFFSET).replace(tzinfo=None)
    # No TZ info so not going to assume anything, return as-is.
    return dt


def is_weekday(dtObj):
    """Check a datetime object dtObj is a weekday"""
    return dtObj.weekday() < 5


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


def sqlalch_datetime(dt_str):
    """Convert a SQLAlchemy datetime string to a datetime object."""
    return datetime.strptime(
        dt_str, '%Y-%m-%d %H:%M:%S.%f'
    ).replace(tzinfo=UTC)
