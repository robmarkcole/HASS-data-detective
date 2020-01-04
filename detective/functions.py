"""
Helper functions.
"""
import json
import pandas as pd

UNKNOWN = "unknown"


def get_device_class(attributes: dict):
    """Return the device class."""
    return attributes.get("device_class", UNKNOWN)


def get_unit_of_measurement(attributes: dict):
    """Return the unit_of_measurement."""
    return attributes.get("unit_of_measurement", UNKNOWN)


def get_friendly_name(attributes: dict):
    """Return the friendly_name."""
    return attributes.get("friendly_name", UNKNOWN)


def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate features from the attributes."""
    df["attributes"] = df["attributes"].apply(json.loads)
    df["device_class"] = df["attributes"].apply(get_device_class)
    df["unit_of_measurement"] = df["attributes"].apply(get_unit_of_measurement)
    df["friendly_name"] = df["attributes"].apply(get_friendly_name)
    return df


def format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert states to numeric where possible and format the last_changed."""
    df["state"] = pd.to_numeric(df["state"], errors="coerce")
    df["last_changed"] = pd.to_datetime(
        df["last_changed"].values, errors="ignore", utc=True
    ).tz_localize(None)
    df = df.dropna()
    return df
