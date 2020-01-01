from unittest.mock import patch

from detective.core import get_db_type, stripped_db_url


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
