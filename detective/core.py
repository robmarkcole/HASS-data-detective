"""
Classes and functions for parsing home-assistant data.
"""
from urllib.parse import urlparse
from typing import List

import matplotlib.pyplot as plt
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
        self.domains = None
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
        """Perform a query, where query is a string."""
        try:
            return self.engine.execute(query, params)
        except:
            print("Error with query: {}".format(query))
            raise

    def fetch_entities(self):
        """Fetch entities for which we have data."""
        query = text(
            """
            SELECT entity_id
            FROM states
            GROUP BY entity_id
            """
        )
        response = self.perform_query(query)

        # Parse the domains from the entities.
        entities = {}
        domains = set()

        for [entity] in response:
            domain = entity.split(".")[0]
            domains.add(domain)
            entities.setdefault(domain, []).append(entity)
        print(f"There are {len(entities)} entities with data")
        self.entities = entities
        self.domains = domains

    def fetch_all_sensor_data(self, limit=50000):
        """
        Fetch data for all sensor entities.
        """
        query = text(
            """
            SELECT domain, entity_id, state, last_changed, attributes
            FROM states
            WHERE
                domain IN ('binary_sensor', 'sensor')
            AND
                state NOT IN ('unknown', 'unavailable')
            AND
                last_changed = last_updated
            ORDER BY last_changed DESC
            LIMIT :limit
            """
        )

        response = self.perform_query(query, limit=limit)
        df = pd.DataFrame(response.fetchall())
        print(f"The returned Pandas dataframe has {df.shape[0]} rows of data.")
        return df


class NumericalSensors:
    """
    Class handling numerical sensor data, acts on existing pandas dataframe.
    """

    def __init__(self, master_df):
        # Extract all the numerical sensors
        sensors_num_df = master_df.query('domain == "sensor" & numerical == True')
        sensors_num_df = sensors_num_df.astype("float")

        # List of sensors
        entities = list(sensors_num_df.index.get_level_values("entity").unique())
        self._entities = entities
        if len(entities) == 0:
            print("No sensor data available")
            return

        # Pivot sensor dataframe for plotting
        sensors_num_df = sensors_num_df.pivot_table(
            index="last_changed", columns="entity", values="state"
        )

        sensors_num_df.index = pd.to_datetime(
            sensors_num_df.index, errors="ignore", utc=True
        )
        sensors_num_df.index = sensors_num_df.index.tz_localize(None)

        # ffil data as triggered on events
        sensors_num_df = sensors_num_df.fillna(method="ffill")
        sensors_num_df = sensors_num_df.dropna()  # Drop any remaining nan.

        self._sensors_num_df = sensors_num_df.copy()

    def correlations(self):
        """
        Calculate the correlation coefficients.
        """
        corr_df = self._sensors_num_df.corr()
        corr_names = []
        corrs = []

        for i in range(len(corr_df.index)):
            for j in range(len(corr_df.index)):
                c_name = corr_df.index[i]
                r_name = corr_df.columns[j]
                corr_names.append("%s-%s" % (c_name, r_name))
                corrs.append(corr_df.ix[i, j])

        corrs_all = pd.DataFrame(index=corr_names)
        corrs_all["value"] = corrs
        corrs_all = corrs_all.dropna().drop(
            corrs_all[(corrs_all["value"] == float(1))].index
        )
        corrs_all = corrs_all.drop(corrs_all[corrs_all["value"] == float(-1)].index)

        corrs_all = corrs_all.sort_values("value", ascending=False)
        corrs_all = corrs_all.drop_duplicates()
        return corrs_all

    def export_to_csv(self, entities: List[str], filename="sensors.csv"):
        """
        Export selected sensor data to a csv.

        Parameters
        ----------
        filename : the name of the .csv file to create
        entities : a list of numerical sensor entities
        """
        if not set(entities).issubset(set(self._sensors_num_df.columns.tolist())):
            print("Invalid entities entered, aborting export_to_csv")
            return
        try:
            self._sensors_num_df[entities].to_csv(path_or_buf=filename)
            print(f"Successfully exported entered entities to {filename}")
        except Exception as exc:
            print(exc)

    def plot(self, entities: List[str]):
        """
        Basic plot of a numerical sensor data.

        Parameters
        ----------
        entities : a list of entities
        """

        ax = self._sensors_num_df[entities].plot(figsize=[12, 6])
        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        ax.set_xlabel("Date")
        ax.set_ylabel("Reading")
        return

    @property
    def entities(self):
        """Return the list of sensors entities."""
        return self._entities

    @property
    def data(self):
        """Return the dataframe holding numerical sensor data."""
        return self._sensors_num_df


class BinarySensors:
    """
    Class handling binary sensor data.
    """

    def __init__(self, master_df):
        # Extract all the binary sensors with binary values
        binary_df = master_df.query(
            'domain == "binary_sensor" & (state == "on" | state == "off")'
        )

        # List of sensors
        entities = list(binary_df.index.get_level_values("entity").unique())
        self._entities = entities
        if len(entities) == 0:
            print("No binary sensor data available")
            return

        # Binarise
        binary_df["state"] = binary_df["state"].apply(
            lambda x: functions.binary_state(x)
        )

        # Pivot
        binary_df = binary_df.pivot_table(
            index="last_changed", columns="entity", values="state"
        )

        # Index to datetime
        binary_df.index = pd.to_datetime(binary_df.index, errors="ignore", utc=True)
        binary_df.index = binary_df.index.tz_localize(None)

        self._binary_df = binary_df.copy()
        return

    def plot(self, entity):
        """
        Basic plot of a single binary sensor data.

        Parameters
        ----------
        entity : string
            The entity to plot
        """
        df = self._binary_df[[entity]]
        resampled = df.resample("s").ffill()  # Sample at seconds and ffill
        resampled.columns = ["value"]
        fig, ax = plt.subplots(1, 1, figsize=(16, 2))
        ax.fill_between(resampled.index, y1=0, y2=1, facecolor="royalblue", label="off")
        ax.fill_between(
            resampled.index,
            y1=0,
            y2=1,
            where=(resampled["value"] > 0),
            facecolor="red",
            label="on",
        )
        ax.set_title(entity)
        ax.set_xlabel("Date")
        ax.set_frame_on(False)
        ax.set_yticks([])
        plt.legend(loc=(1.01, 0.7))
        plt.show()
        return

    @property
    def data(self):
        """Return the dataframe holding numerical sensor data."""
        return self._binary_df

    @property
    def entities(self):
        """Return the list of sensors entities."""
        return self._entities
