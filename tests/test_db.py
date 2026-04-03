import detective.core as detective
import detective.functions as functions
import pandas as pd

db_url = "sqlite:///tests/test.db"


def test_perform_query_accepts_raw_string_sql():
    db = detective.HassDatabase(db_url, fetch_entities=False)
    result = db.perform_query("SELECT 1")
    assert result.scalar_one() == 1


def test_db():
    db = detective.HassDatabase(db_url)
    assert db is not None
    assert len(db.entities) > 0

    df = db.fetch_all_data_of(('zone.home',))
    assert df is not None

    df = db.fetch_all_sensor_data(limit=100000)
    assert df is not None

    df = db.fetch_all_statistics_of(("sensor.kitchen", "sensor.living_room", "sensor.ac"), limit=100000)
    assert df is not None
