"""
Helper functions.
"""
UNKNOWN = "unknown"


def format_binary_state(state: str):
    """Return a binary for the state of binary sensors."""
    if state == "on":
        return 1
    elif state == "off":
        return 0
    return state


def get_device_class(attributes: dict):
    """Return the device class."""
    device_class = attributes.get("device_class")
    if device_class:
        return device_class
    return UNKNOWN
