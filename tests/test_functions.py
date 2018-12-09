from detective import functions
import math


def test_binary_state():
    """Test binary_state"""
    assert functions.binary_state('on') is True
    assert functions.binary_state('off') is False
    assert math.isnan(functions.binary_state(None))


def test_isfloat():
    """Test isfloat"""
    assert functions.isfloat(5.0) is True
    assert functions.isfloat('foo') is False