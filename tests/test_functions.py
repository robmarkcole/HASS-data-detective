"""Tests for helper functions."""
import pandas as pd

from detective.functions import format_dataframe


def test_format_dataframe_converts_types_and_drops_invalid_rows():
    df = pd.DataFrame(
        {
            "state": ["42.5", "unavailable", "7"],
            "last_updated_ts": [0, 60, None],
            "entity_id": ["sensor.temp", "sensor.temp", "sensor.temp"],
        }
    )

    result = format_dataframe(df)

    assert len(result) == 1
    assert result.iloc[0]["state"] == 42.5
    assert result.iloc[0]["last_updated_ts"] == pd.Timestamp("1970-01-01 00:00:00")
    assert pd.api.types.is_float_dtype(result["state"])
    assert pd.api.types.is_datetime64_any_dtype(result["last_updated_ts"])


def test_format_dataframe_removes_timezone_information():
    df = pd.DataFrame(
        {
            "state": ["1"],
            "last_updated_ts": [1700000000],
        }
    )

    result = format_dataframe(df)

    assert result.iloc[0]["last_updated_ts"].tzinfo is None
