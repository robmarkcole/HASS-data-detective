from detective import functions
import math

MOCK_ATTRIBUTE = {
    "battery_level": 61,
    "unit_of_measurement": "°C",
    "friendly_name": "Living room sensor temperature",
    "device_class": "temperature",
}


def test_device_class():
    """Test get_device_class"""
    assert functions.get_device_class(MOCK_ATTRIBUTE) == MOCK_ATTRIBUTE["device_class"]
    assert functions.get_device_class({}) == functions.UNKNOWN


def test_get_unit_of_measurement():
    """Test get_unit_of_measurement"""
    assert (
        functions.get_unit_of_measurement(MOCK_ATTRIBUTE)
        == MOCK_ATTRIBUTE["unit_of_measurement"]
    )
    assert functions.get_unit_of_measurement({}) == functions.UNKNOWN


def test_get_friendly_name():
    """Test get_friendly_name"""
    assert (
        functions.get_friendly_name(MOCK_ATTRIBUTE) == MOCK_ATTRIBUTE["friendly_name"]
    )
    assert functions.get_friendly_name({}) == functions.UNKNOWN
