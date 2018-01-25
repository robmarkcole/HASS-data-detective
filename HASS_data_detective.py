"""
Classes for parsing home-assistant data.
"""

from fbprophet import Prophet
import helpers as helpers
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sqlalchemy import create_engine, text


class DataParser():
    """
    Initializing the parser fetches all of the data in a pandas dataframe
    (query_df). Also gets a dataframe of only the sensors (sensors_df)
    """
    def __init__(self, url):
        """
        Parameters
        ----------
        url : str
            The URL to the database.
        """
        self._engine = create_engine(url)

        # Query text
        stmt = text(
            """
            SELECT domain, entity_id, state, last_changed
            FROM states
            WHERE NOT state='unknown'
            """
            )

        query = self._engine.execute(stmt)
        result = query.fetchall()
        query_df = pd.DataFrame(result)  # Info to dataframe.
        query_df.columns = ['domain', 'entity', 'state', 'last_changed']

        df = query_df.copy()
        # Convert numericals to floats.
        df['numerical'] = df['state'].apply(lambda x: helpers.isfloat(x))

        # Fix timestamp
        df['last_changed'] = df['last_changed'].apply(
            lambda x: x.tz_localize(None))
        df['last_changed'] = pd.to_datetime(
            df['last_changed'], format="%Y:%m:%d %H:%M:%S")

        # Multiindexing
        df = df[['domain', 'entity', 'last_changed', 'numerical', 'state']]
        df = df.set_index(['domain', 'entity', 'numerical', 'last_changed'])

        # Extract all the sensors
        sensors_df = df.query('domain == "sensor" & numerical == True')
        sensors_df['state'] = sensors_df['state'].astype('float')

        # List of sensors
        sensors_list = list(
            sensors_df.index.get_level_values('entity').unique())
        self._sensors = sensors_list

        # Pivot sensor dataframe for plotting
        sensors_df = sensors_df.pivot_table(
            index='last_changed', columns='entity', values='state')
        sensors_df = sensors_df.fillna(method='ffill')
        sensors_df = sensors_df.dropna()  # Drop any remaining nan.
        sensors_df.index = pd.to_datetime(sensors_df.index)

        self._query_df = df.copy()
        self._sensors_df = sensors_df.copy()

    def plot_sensor(self, sensor):
        """
        Basic plot of a single sensor.
        Could also display statistics for more detailed plots.

        Parameters
        ----------
        sensor : str
            The entity_id to plot
        """
        df = self._sensors_df[sensor]  # Extract the dataframe
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))  # Create the plot
        ax.plot(df)
        plt.xlabel('Date')
        plt.ylabel('Reading')
        plt.title('{} Sensor History.'.format(sensor.split(".")[1]))
        plt.show()
        return

    def sensor_pairplot(self, sensor_list):
        """
        Seaborn pairplot.

        Parameters
        ----------
        sensor_list : list of str
            The list of entity_id to pairplot
        """
        df = self._sensors_df[sensor_list]
        sns.pairplot(df)
        return

    def single_sensor(self, sensor):
        """
        Extract a single sensor dataframe from the sql database.
        Returns the dataframe with columns 'ds' and 'y'.

        Parameters
        ----------
        sensor : str
            The entity_id to plot
        """

        stmt = text(
            """
            SELECT last_changed, state
            FROM states
            WHERE NOT state='unknown'
            AND states.entity_id = '%s'
            """
            % sensor)

        query = self._engine.execute(stmt)

        # get rows from query into a pandas dataframe
        df = pd.DataFrame(query.fetchall())

        df.columns = ['ds', 'y']

        df = df.set_index(pd.to_datetime(df['ds'], utc=None)).tz_localize(None)
        df['ds'] = df.index
        return df

    def create_prophet_model(self, **kwargs):
        """
        Creates a prophet model.
        Allows adjustment via keyword arguments
        """
        model = Prophet(**kwargs)
        return model

    def prophet_model(self, sensor, periods=0, freq='S', **kwargs):
        """
        Make a propet model for the given sensor for the number of periods.

        Parameters
        ----------
        sensor : str
            The entity_id to plot

        periods : int
            The default period is 0 (no forecast)

        freq : str
            Unit of time, defaults to seconds.

        """
        # Find the information for sensor
        df = self.single_sensor(sensor)

        try:
            # Check to make sure dataframe has correct columns
            assert ('ds' in df.columns) & ('y' in df.columns), \
                "DataFrame needs both ds (date) and y (value) columns"

            # Create the model and fit on dataframe
            model = self.create_prophet_model(**kwargs)
            model.fit(df)

            # Make a future dataframe for specified number of periods
            future = model.make_future_dataframe(periods=periods, freq=freq)
            future = model.predict(future)

            # Return the model and future dataframe for plotting
            return model, future

        except AssertionError as error:
            print(error)
            return

    def all_corrs(self):
        corr_df = self._sensors_df.corr()

        corr_names = []
        corrs = []

        for i in range(len(corr_df.index)):
            for j in range(len(corr_df.index)):
                c_name = corr_df.index[i]
                r_name = corr_df.columns[j]
                corr_names.append('%s-%s' % (c_name, r_name))
                corrs.append(corr_df.ix[i, j])


        corrs_all = pd.DataFrame(index = corr_names)
        corrs_all['value'] = corrs
        corrs_all = corrs_all.dropna().drop(corrs_all[(corrs_all['value'] == float(1))].index)
        corrs_all = corrs_all.drop(corrs_all[corrs_all['value'] == float(-1)].index) 

        corrs_all = corrs_all.sort_values('value', ascending=False)

        return corrs_all



    @property
    def list_sensors(self):
        """Return the list of sensors."""
        return self._sensors

    @property
    def get_sensors(self):
        """Return the dataframe holding sensor data."""
        return self._sensors_df
