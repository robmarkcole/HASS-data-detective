from unittest.mock import patch, MagicMock
import pandas as pd

from detective.core import get_db_type, stripped_db_url, HassDatabase


def test_get_db_type():
    assert get_db_type("mysql://localhost") == "mysql"
    assert get_db_type("mysql+pymysql://localhost") == "mysql"


def test_stripped_db_url():
    assert stripped_db_url("mysql://localhost") == "mysql://localhost"
    assert stripped_db_url("mysql://paulus@localhost") == "mysql://paulus@localhost"
    assert (
        stripped_db_url("mysql://paulus:password@localhost")
        == "mysql://paulus:***@localhost"
    )


def test_fetch_entities(mock_db):
    with patch.object(
        mock_db,
        "perform_query",
        return_value=[["light.kitchen"], ["light.living_room"], ["switch.ac"],],
    ):
        mock_db.fetch_entities()

    assert mock_db.entities == ["light.kitchen", "light.living_room", "switch.ac"]


mock_data = pd.DataFrame({
    "state": ["20.2", "50.1"],
    "last_updated_ts": ["2025-10-01 12:00:00", "2025-10-01 12:05:00"],
    "entity_id": ["sensor.temperature", "sensor.humidity"],
    "shared_attrs": ["{}", "{}"]
})

@patch("sqlalchemy.create_engine")
def test_fetch_all_sensor_data(mock_create_engine):
    """Test that fetch_all_sensor_data returns a Pandas DataFrame."""
    mock_con = MagicMock()
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_con
    mock_create_engine.return_value = mock_engine

    # fetch_all_sensor_data uses read_sql_query under the hood
    with patch("pandas.read_sql_query") as mock_read_sql:
        mock_read_sql.return_value = mock_data

        db = HassDatabase(url="sqlite:///tests/test.db", fetch_entities=False)
        db.con = mock_con

        result = db.fetch_all_sensor_data()
        assert isinstance(result, pd.DataFrame)
