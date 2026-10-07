"""
Classes and functions for parsing home-assistant data.
"""

from typing import Dict, Tuple
from urllib.parse import urlparse

import pandas as pd
from sqlalchemy import create_engine, text

from . import config, functions


def db_from_hass_config(path=None, **kwargs):
    """Initialize a database from HASS config."""
    if path is None:
        path = config.find_hass_config()

    url = config.db_url_from_hass_config(path)
    return HassDatabase(url, **kwargs)


def get_db_type(url):
    return urlparse(url).scheme.split("+")[0]


def stripped_db_url(url):
    """Return a version of the DB url with the password stripped out."""
    parsed = urlparse(url)

    if parsed.password is None:
        return url

    return parsed._replace(
        netloc="{}:***@{}".format(parsed.username, parsed.hostname)
    ).geturl()


class HassDatabase:
    """
    Initializing the parser fetches all of the data from the database and
    places it in a master pandas dataframe.
    """

    def __init__(self, url, *, fetch_entities=True):
        """
        Parameters
        ----------
        url : str
            The URL to the database.
        """
        self.url = url
        self.entities = None
        try:
            self.engine = create_engine(url)
            print("Successfully connected to database", stripped_db_url(url))
            self.con = self.engine.connect()
            if fetch_entities:
                self.fetch_entities()
        except Exception as exc:
            if isinstance(exc, ImportError):
                raise RuntimeError(
                    "The right dependency to connect to your database is "
                    "missing. Please make sure that it is installed."
                )

            print(exc)
            raise

        self.db_type = get_db_type(url)

    def perform_query(self, query, **params):
        """Perform a query."""
        try:
            if isinstance(query, str):
                query = text(query)
            with self.engine.connect() as conn:
                return conn.execute(query, params)
        except:
            print(f"Error with query: {query}")
            raise

    def fetch_entities(self) -> None:
        """Fetch entities for which we have data."""
        query = text(
            """
            SELECT DISTINCT(entity_id) FROM states_meta
            """
        )
        response = self.perform_query(query)

        # Parse the domains from the entities.
        self.entities = [e[0] for e in response]
        print(f"There are {len(self.entities)} entities with data")

    def fetch_all_sensor_data(self, limit=50000) -> pd.DataFrame:
        """
        Fetch data for all sensor entities.

        Arguments:
        - limit (default: 50000): Limit the maximum number of state changes loaded.
            If None, there is no limit.
        - get_attributes: If True, LEFT JOIN the attributes table to retrieve event's attributes.
        """

        query = """
        SELECT states.state,
            datetime(states.last_updated_ts, 'unixepoch', 'subsec') as last_updated_ts,
            states_meta.entity_id,
            state_attributes.shared_attrs
        FROM states
        JOIN states_meta ON states.metadata_id = states_meta.metadata_id
        LEFT JOIN state_attributes ON states.attributes_id = state_attributes.attributes_id
        WHERE states_meta.entity_id LIKE '%sensor%'
        AND states.state NOT IN ('unknown',
                                'unavailable')
        ORDER BY last_updated_ts DESC
        """

        query, params = _apply_limit(text(query), limit)
        print(query)
        df = pd.read_sql_query(query, con=self.con, params=params)
        print(f"The returned Pandas dataframe has {df.shape[0]} rows of data.")
        return df

    def fetch_all_data_of(self, sensors: Tuple[str], limit=50000) -> pd.DataFrame:
        """
        Fetch data for sensors.

        Arguments:
        - limit (default: 50000): Limit the maximum number of state changes loaded.
            If None, there is no limit.
        - get_attributes: If True, LEFT JOIN the attributes table to retrieve event's attributes.
        """
        sensor_ids = _normalise_sensor_ids(sensors)
        sensors_str, params = _sensor_filter(sensor_ids)

        query = f"""
            WITH combined_states AS (
                SELECT states.state, states.last_updated_ts, states_meta.entity_id
                FROM states
                JOIN states_meta
                ON states.metadata_id = states_meta.metadata_id
            )
            SELECT *
            FROM combined_states
            WHERE 
                entity_id IN ({sensors_str})
            AND
                state NOT IN ('unknown', 'unavailable')
            ORDER BY last_updated_ts DESC
        """

        query, limit_params = _apply_limit(text(query), limit)
        params.update(limit_params)
        print(query)
        df = pd.read_sql_query(query, con=self.con, params=params)
        print(f"The returned Pandas dataframe has {df.shape[0]} rows of data.")
        return df

    def fetch_all_statistics_of(self, sensors: Tuple[str], limit=50000) -> pd.DataFrame:
        """
        Fetch aggregated statistics for sensors.

        Arguments:
        - limit (default: 50000): Limit the maximum number of state changes loaded.
            If None, there is no limit.
        """
        # Statistics imported from an external source are similar to entity_id,
        # but use a : instead of a . as a delimiter between the domain and object ID.
        sensor_ids = _normalise_sensor_ids(sensors)
        sensors_with_semicolons = [sensor.replace(".", ":") for sensor in sensor_ids]
        sensors_combined = list(sensor_ids) + sensors_with_semicolons
        sensors_str, params = _sensor_filter(sensors_combined)

        query = f"""
            WITH combined_states AS (
                SELECT
                    statistics.created_ts,
                    statistics.start_ts,
                    statistics.last_reset_ts,
                    statistics.mean,
                    statistics.max,
                    statistics.sum,
                    statistics.state,
                    statistics_meta.statistic_id,
                    statistics_meta.source,
                    statistics_meta.unit_of_measurement,
                    statistics_meta.has_mean,
                    statistics_meta.has_sum
                FROM statistics
                JOIN statistics_meta
                ON statistics.metadata_id = statistics_meta.id
            )
            SELECT *
            FROM combined_states
            WHERE 
                statistic_id IN ({sensors_str})
            ORDER BY created_ts DESC
        """

        query, limit_params = _apply_limit(text(query), limit)
        params.update(limit_params)
        print(query)
        df = pd.read_sql_query(query, con=self.con, params=params)
        print(f"The returned Pandas dataframe has {df.shape[0]} rows of data.")
        return df


def _normalise_sensor_ids(sensors: Tuple[str, ...]) -> Tuple[str, ...]:
    """Return non-empty sensor identifiers as a validated tuple."""
    if isinstance(sensors, str):
        sensors = (sensors,)

    sensor_ids = tuple(sensors)
    if not sensor_ids or any(
        not isinstance(sensor, str) or not sensor for sensor in sensor_ids
    ):
        raise ValueError("sensors must contain at least one non-empty string")
    return sensor_ids


def _sensor_filter(sensors: Tuple[str, ...]) -> Tuple[str, Dict[str, str]]:
    """Build a bound SQL IN list without interpolating user input."""
    params = {f"sensor_{index}": sensor for index, sensor in enumerate(sensors)}
    placeholders = ", ".join(f":{name}" for name in params)
    return placeholders, params


def _apply_limit(query, limit):
    """Add a validated bound LIMIT clause when requested."""
    if limit is None:
        return query, {}
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("limit must be a non-negative integer or None")
    return text(f"{query.text} LIMIT :limit"), {"limit": limit}
