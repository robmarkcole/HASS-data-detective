"""
Helper functions.
"""
import json
import pandas as pd


def format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Convert states to numeric where possible and format the last_updated_ts."""
    df["state"] = pd.to_numeric(df["state"], errors="coerce")

    df["last_updated_ts"] = pd.to_datetime(
        df["last_updated_ts"], unit="s", utc=True
    ).dt.tz_convert(None)

    df = df.dropna()
    return df
