"""
Classes and functions for parsing home-assistant data.
"""
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
            return self.engine.execute(query, params)
        except:
            print(f"Error with query: {query}")
            raise

    def fetch_entities(self) -> None:
        """Fetch entities for which we have data."""
        query = text(
            """
            SELECT DISTINCT(entity_id) FROM states
            """
        )
        response = self.perform_query(query)

        # Parse the domains from the entities.
        self.entities = [e[0] for e in response]
        print(f"There are {len(self.entities)} entities with data")

    def fetch_all_sensor_data(self, limit=50000) -> pd.DataFrame:
        """
        Fetch data for all sensor entities.
        """
        query = f"""
            SELECT domain, entity_id, state, last_changed, attributes
            FROM states
            WHERE
                domain IN ('binary_sensor', 'sensor')
            AND
                state NOT IN ('unknown', 'unavailable')
            ORDER BY last_changed DESC
            LIMIT {limit}
            """
        df = pd.read_sql_query(query, self.url)
        print(f"The returned Pandas dataframe has {df.shape[0]} rows of data.")
        return df
