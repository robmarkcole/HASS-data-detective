import detective.core as detective
import detective.functions as functions
import pandas as pd

db_url = "sqlite:///tests/test.db"

def test_db():
    db = detective.HassDatabase(db_url)
    assert db is not None
    assert len(db.entities) > 0

    df = db.fetch_all_data_of(('zone.home',))
    assert df is not None

    df = db.fetch_all_sensor_data(limit=100000)
    assert df is not None
