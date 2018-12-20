from detective.core import get_db_type


def test_get_db_type():
    assert get_db_type('mysql://localhost') == 'mysql'
    assert get_db_type('mysql+pymysql://localhost') == 'mysql'
