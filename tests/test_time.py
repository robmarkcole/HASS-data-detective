"""Tests for time helper."""
from datetime import datetime
from time import time as builtin_time

import pytest

from detective import time


def test_sqlalch_datetime():
    # a datetime string should return a datetime
    result = time.sqlalch_datetime('2018-12-05 10:36:44.900394')
    assert result.year == 2018
    assert result.month == 12
    assert result.day == 5
    assert result.hour == 10
    assert result.minute == 36
    assert result.second == 44
    assert result.microsecond == 900394
    assert result.tzinfo is time.UTC
    
    # a datetime should return a datetime
    result2 = time.sqlalch_datetime(result)
    assert result2 == result
    
    with pytest.raises(ValueError):
        result = time.sqlalch_datetime('garbage')


def test_localize():
    now_time = builtin_time()
    now = datetime.fromtimestamp(now_time)
    utcnow = datetime.utcfromtimestamp(now_time).replace(tzinfo=time.UTC)
    # There is always a little offset because of how LOCAL_UTC_OFFSET is
    # calculated. We calculate here it's not more than 1 second off
    assert -1 < (time.localize(utcnow) - now).total_seconds() < 1
