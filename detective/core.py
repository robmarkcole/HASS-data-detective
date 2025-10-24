"""
Classes and functions for parsing home-assistant data.
"""
from typing import Tuple

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

        if limit is not None:
            query += f"LIMIT {limit}"
        print(query)
        query = text(query)
        df = pd.read_sql_query(query, con=self.con)
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
        sensors_str = str(tuple(sensors))
        if len(sensors) == 1:
            sensors_str = sensors_str.replace(",", "")

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
                entity_id IN {sensors_str}
            AND
                state NOT IN ('unknown', 'unavailable')
            ORDER BY last_updated_ts DESC
        """

        if limit is not None:
            query += f"LIMIT {limit}"
        print(query)
        query = text(query)
        df = pd.read_sql_query(query, con=self.con)
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
        sensors_with_semicolons = [sensor.replace('.', ':') for sensor in sensors]
        sensors_combined = list(sensors) + sensors_with_semicolons
        sensors_str = str(tuple(sensors_combined))
        if len(sensors_combined) == 1:
            sensors_str = sensors_str.replace(",", "")

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
                statistic_id IN {sensors_str}
            ORDER BY created_ts DESC
        """

        if limit is not None:
            query += f"LIMIT {limit}"
        print(query)
        query = text(query)
        df = pd.read_sql_query(query, con=self.con)
        print(f"The returned Pandas dataframe has {df.shape[0]} rows of data.")
        return df
