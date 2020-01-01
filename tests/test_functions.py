from detective import functions
import math

MOCK_ATTRIBUTE = {"friendly_name": "Office sensor motion", "device_class": "motion"}


def test_format_binary_state():
    """Test format_binary_state"""
    assert functions.format_binary_state("on") == 1
    assert functions.format_binary_state("off") == 0
    assert functions.format_binary_state("foo") == "foo"


def test_device_class():
    """Test device_class"""
    assert functions.get_device_class(MOCK_ATTRIBUTE) == "motion"
    assert functions.get_device_class({}) == functions.UNKNOWN
