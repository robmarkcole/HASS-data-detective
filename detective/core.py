"""
Classes and functions for parsing home-assistant data.
"""

from . import config, functions
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine, text
from typing import List


def db_from_hass_config(path=None, **kwargs):
    """Initialize a database from HASS config."""
    if path is None:
        path = config.find_hass_config()

    url = config.db_url_from_hass_config(path)
    return HassDatabase(url, **kwargs)


class HassDatabase():
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
        self._url = url
        self._master_df = None
        self._domains = None
        self._entities = None
        try:
            self.engine = create_engine(url)
            print("Successfully connected to database")
            if fetch_entities:
                self.fetch_entities()
        except:
            print("Connection error, check your URL")
            raise

    def perform_query(self, query):
        """Perform a query, where query is a string."""
        try:
            return self.engine.execute(query)
        except:
            print("Error with query: {}".format(query))
            raise

    def fetch_entities(self):
        """Fetch unique entities which have data (COUNT>0)."""
        query = text(
            """
            SELECT entity_id, COUNT(*)
            FROM states
            GROUP BY entity_id
            ORDER by 2 DESC
            """
            )
        response = self.perform_query(query)
        entities = [e[0] for e in list(response)]
        print("There are {} entities with data".format(len(entities)))

        # Parse the domains from the entities.
        self._domains = list(set([e.split('.')[0] for e in entities]))
        self._entities = {}

        # Parse entities into a dict indexed by domain.
        for d in self._domains:
            self._entities[d] = [
                e for e in entities if e.split('.')[0] == d]

    def fetch_data_by_list(self, entities: List[str]):
        """
        Basic query from list of entities. Must be from same domain.
        Attempts to unpack lists up to 2 deep.

        Parameters
        ----------
        entities : a list of entities

        returns a df
        """

        if not len(set([e.split('.')[0] for e in entities])) == 1:
            print("Error: entities must be from same domain.")
            return

        if len(entities) == 1:
            print("Must pass more than 1 entity.")
            return
        query = text(
            """
            SELECT entity_id, state, last_changed
            FROM states
            WHERE entity_id in {}
            AND NOT state='unknown'
            """.format(tuple(entities))
            )

        response = self.perform_query(query)
        df = pd.DataFrame(response.fetchall())
        df.columns = ['entity', 'state', 'last_changed']
        df = df.set_index('last_changed')  # Set the index on datetime
        df.index = pd.to_datetime(df.index, errors='ignore', utc=True)
        try:
            df['state'] = df['state'].mask(
                df['state'].eq('None')).dropna().astype(float)
            df = df.pivot_table(
                index='last_changed', columns='entity', values='state')
            df = df.fillna(method='ffill')
            df = df.dropna()  # Drop any remaining nan.
            return df
        except:
            print("Error: entities were not all numericals, unformatted df.")
            return df

    def fetch_all_data(self):
        """
        Fetch data for all enetites.
        """
        # Query text
        query = text(
            """
            SELECT domain, entity_id, state, last_changed
            FROM states
            WHERE NOT state='unknown'
            """
            )

        try:
            print("Querying the database, this could take a while")
            response = self.engine.execute(query)
            master_df = pd.DataFrame(response.fetchall())
            print("master_df created successfully.")
            self._master_df = master_df.copy()
            self.parse_all_data()
        except:
            raise ValueError("Error querying the database.")

    def parse_all_data(self):
        """Parses the master df."""
        self._master_df.columns = [
            'domain', 'entity', 'state', 'last_changed']

        # Check if state is float and store in numericals category.
        self._master_df['numerical'] = self._master_df['state'].apply(
            lambda x: functions.isfloat(x))

        # Multiindexing
        self._master_df.set_index(
            ['domain', 'entity', 'numerical', 'last_changed'],
            inplace=True)

    @property
    def master_df(self):
        """Return the dataframe holding numerical sensor data."""
        return self._master_df

    @property
    def domains(self):
        """Return the domains."""
        if self._domains is None:
            raise ValueError(
                "Not initialized! Call entities.fetch_entities() first")
        return self._domains

    @property
    def entities(self):
        """Return the entities dict."""
        if self._entities is None:
            raise ValueError(
                "Not initialized! Call entities.fetch_entities() first")
        return self._entities


class NumericalSensors():
    """
    Class handling numerical sensor data, acts on existing pandas dataframe.
    """
    def __init__(self, master_df):
        # Extract all the numerical sensors
        sensors_num_df = master_df.query(
            'domain == "sensor" & numerical == True')
        sensors_num_df = sensors_num_df.astype('float')

        # List of sensors
        entities = list(
            sensors_num_df.index.get_level_values('entity').unique())
        self._entities = entities

        # Pivot sensor dataframe for plotting
        sensors_num_df = sensors_num_df.pivot_table(
            index='last_changed', columns='entity', values='state')

        sensors_num_df.index = pd.to_datetime(
            sensors_num_df.index, errors='ignore', utc=True)
        sensors_num_df.index = sensors_num_df.index.tz_localize(None)

        # ffil data as triggered on events
        sensors_num_df = sensors_num_df.fillna(method='ffill')
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
                corr_names.append('%s-%s' % (c_name, r_name))
                corrs.append(corr_df.ix[i, j])

        corrs_all = pd.DataFrame(index=corr_names)
        corrs_all['value'] = corrs
        corrs_all = corrs_all.dropna().drop(
            corrs_all[(corrs_all['value'] == float(1))].index)
        corrs_all = corrs_all.drop(
            corrs_all[corrs_all['value'] == float(-1)].index)

        corrs_all = corrs_all.sort_values('value', ascending=False)
        corrs_all = corrs_all.drop_duplicates()
        return corrs_all

    def plot(self, entities: List[str]):
        """
        Basic plot of a numerical sensor data.
        Attempts to unpack lists up to 2 deep.

        Parameters
        ----------
        entities : a list of entities
        """

        ax = self._sensors_num_df[entities].plot(figsize=[12, 6])
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set_xlabel('Date')
        ax.set_ylabel('Reading')
        return

    @property
    def entities(self):
        """Return the list of sensors entities."""
        return self._entities

    @property
    def data(self):
        """Return the dataframe holding numerical sensor data."""
        return self._sensors_num_df


class BinarySensors():
    """
    Class handling binary sensor data.
    """
    def __init__(self, master_df):
        # Extract all the numerical sensors
        binary_df = master_df.query(
            'domain == "binary_sensor"')

        # List of sensors
        entities = list(
            binary_df.index.get_level_values('entity').unique())
        self._entities = entities

        # Binarise
        binary_df['state'] = binary_df['state'].apply(
            lambda x: functions.binary_state(x))

        # Pivot
        binary_df = binary_df.pivot_table(
            index='last_changed', columns='entity', values='state')

        # Index to datetime
        binary_df.index = pd.to_datetime(
            binary_df.index, errors='ignore', utc=True)
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
        resampled = df.resample('s').ffill()  # Sample at seconds and ffill
        resampled.columns = ['value']
        fig, ax = plt.subplots(1, 1, figsize=(16, 2))
        ax.fill_between(
            resampled.index, y1=0, y2=1, facecolor='royalblue', label='off')
        ax.fill_between(
            resampled.index, y1=0, y2=1, where=(
                resampled['value'] > 0), facecolor='red', label='on')
        ax.set_title(entity)
        ax.set_xlabel('Date')
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
