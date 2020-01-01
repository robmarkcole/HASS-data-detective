"""
Helper functions.
"""
import json
import pandas as pd

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


def get_unit_of_measurement(attributes: dict):
    """Return the unit_of_measurement."""
    unit_of_measurement = attributes.get("unit_of_measurement")
    if unit_of_measurement:
        return unit_of_measurement
    return UNKNOWN


def get_friendly_name(attributes: dict):
    """Return the friendly_name."""
    friendly_name = attributes.get("friendly_name")
    if friendly_name:
        return friendly_name
    return UNKNOWN


def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    df["attributes"] = df["attributes"].apply(json.loads)
    df["device_class"] = df["attributes"].apply(get_device_class)
    df["unit_of_measurement"] = df["attributes"].apply(get_unit_of_measurement)
    df["friendly_name"] = df["attributes"].apply(get_friendly_name)
    return df


def format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df["state"] = df["state"].apply(format_binary_state)
    df["state"] = pd.to_numeric(
        df["state"], errors="coerce"
    )  # coerce will return NaN if unable to convert
    df["last_changed"] = pd.to_datetime(
        df["last_changed"].values, errors="ignore", utc=True
    ).tz_localize(None)
    df = df.dropna()
    return df
