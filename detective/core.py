"""
Classes and functions for parsing home-assistant data.
"""

from . import helpers
from fbprophet import Prophet
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine, text


class DataParser():
    """
    Initializing the parser fetches all of the data from the database and
    places it in a master pandas dataframe.
    """
    def __init__(self, url):
        """
        Parameters
        ----------
        url : str
            The URL to the database.
        """
        self._url = url
        self._engine = create_engine(url)

        # Query text
        query = text(
            """
            SELECT domain, entity_id, state, last_changed
            FROM states
            WHERE NOT state='unknown'
            """
            )

        try:
            response = self._engine.execute(query)
        except:
            raise ValueError("Check your database url is valid")
        print("Querying the database, this could take a while")

        master_df = pd.DataFrame(response.fetchall())  # Info to dataframe.
        master_df.columns = ['domain', 'entity', 'state', 'last_changed']

        # Check if state is float and store that info in numericals category.
        master_df['numerical'] = master_df['state'].apply(
            lambda x: helpers.isfloat(x))

        # Multiindexing
        master_df.set_index(
            ['domain', 'entity', 'numerical', 'last_changed'], inplace=True)
        self._master_df = master_df.copy()

    @property
    def master_df(self):
        """Return the dataframe holding numerical sensor data."""
        return self._master_df


class NumericalSensors():
    """
    Class handling numerical sensor data.
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

        sensors_num_df.index = pd.to_datetime(sensors_num_df.index)
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

    def plot(self, entities):
        """
        Basic plot of a numerical sensor data.
        Could also display statistics for more detailed plots.

        Parameters
        ----------
        entities : list of entities
            The entities to plot.
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
            lambda x: helpers.binary_state(x))

        # Pivot
        binary_df = binary_df.pivot_table(
            index='last_changed', columns='entity', values='state')

        # Index to datetime
        binary_df.index = pd.to_datetime(binary_df.index)
        binary_df.index = binary_df.index.tz_localize(None)

        self._binary_df = binary_df.copy()
        return

    def plot(self, entities):
        """
        Basic plot of a numerical sensor data.
        Could also display statistics for more detailed plots.

        Parameters
        ----------
        entities : list of entities
            The entities to plot.
            """

        f, ax = plt.subplots(figsize=(16, 6))
        ax.step(self._binary_df[entities], 'b', where="post")
        #ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set_xlabel('Date')
        ax.set_ylabel('State')
        return

    @property
    def data(self):
        """Return the dataframe holding numerical sensor data."""
        return self._binary_df

    @property
    def entities(self):
        """Return the list of sensors entities."""
        return self._entities


class Prediction():
    """
    Class handling predictions for a single numerical sensor.
    """
    def __init__(self, sensor_ds):
        """
        Parameters
        ----------
        sensor_ds : pandas series
            The pandas series for a single sensor.
        """

        self._sensor_ds = sensor_ds
        self._name = sensor_ds.name + "_prediction"

        sensor_df = self._sensor_ds.to_frame()  # Convert series to dataframe
        sensor_df.reset_index(level=0, inplace=True)  # Convert index to col.
        sensor_df.columns = ['ds', 'y']  # Rename cols.
        self._sensor_df = sensor_df
        return

    def create_prophet_model(self, **kwargs):
        """
        Creates a prophet model.
        Allows adjustment via keyword arguments
        """
        model = Prophet(**kwargs)
        return model

    def prophet_model(self, periods=0, freq='S', **kwargs):
        """
        Make a propet model for the given sensor for the number of periods.

        Parameters
        ----------

        periods : int
            The default period is 0 (no forecast)

        freq : str
            Unit of time, defaults to seconds.
        """

        # Create the model and fit on dataframe
        model = self.create_prophet_model(**kwargs)
        model.fit(self._sensor_df)

        # Make a future dataframe for specified number of periods
        future = model.make_future_dataframe(periods=periods, freq=freq)
        future = model.predict(future)

        self._model = model
        self._future = future
        return

    def plot_future(self):
        """Plot the prediction."""
        self._model.plot(self._future).show()
        return

    def plot_components(self):
        """Plot the prediction."""
        self._model.plot_components(self._future).show()
        return

    @property
    def name(self):
        """Return the prediction name."""
        return self._name

    @property
    def data(self):
        """Return the prediction name."""
        return self._sensor_df
