"""
Helper functions.
"""
import json
import pandas as pd


def format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert states to numeric where possible and format the last_changed."""
    df["state"] = pd.to_numeric(df["state"], errors="coerce")
    df["last_updated_ts"] = pd.to_datetime(
        df["last_updated_ts"].values, errors="ignore", utc=True
    ).tz_localize(None)
    df = df.dropna()
    return df
