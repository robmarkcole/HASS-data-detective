"""
Classes for parsing home-assistant data.
"""

from . import helpers
from fbprophet import Prophet
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sqlalchemy import create_engine, text


class DataParser():
    """
    Initializing the parser fetches all of the data from the database and
    places it in a pandas dataframe.
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

        # Extract all the numerical sensors
        sensors_num_df = master_df.query(
            'domain == "sensor" & numerical == True')
        sensors_num_df['state'] = sensors_num_df['state'].astype('float')

        # List of sensors
        sensors_list = list(
            sensors_num_df.index.get_level_values('entity').unique())
        self._sensors = sensors_list

        # Pivot sensor dataframe for plotting
        sensors_num_df = sensors_num_df.pivot_table(
            index='last_changed', columns='entity', values='state')
        sensors_num_df = sensors_num_df.fillna(method='ffill')
        sensors_num_df = sensors_num_df.dropna()  # Drop any remaining nan.
        sensors_num_df.index = pd.to_datetime(sensors_num_df.index)
        sensors_num_df.index = sensors_num_df.index.tz_localize(None)
        self._sensors_num_df = sensors_num_df.copy()
        return

    def plot_numerical_sensor(self, sensor):
        """
        Basic plot of a single numerical sensor.
        Could also display statistics for more detailed plots.

        Parameters
        ----------
        sensor : str
            The entity_id to plot
        """
        df = self._sensors_num_df[sensor]  # Extract the dataframe
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))  # Create the plot
        ax.plot(df)
        plt.xlabel('Date')
        plt.ylabel('Reading')
        plt.title('{} Sensor History.'.format(sensor.split(".")[1]))
        plt.show()
        return

    def numerical_sensor_pairplot(self, sensor_list):
        """
        Seaborn pairplot.

        Parameters
        ----------
        sensor_list : list of str
            The list of entity_id to pairplot
        """
        df = self._sensors_num_df[sensor_list]
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

    @property
    def list_sensors(self):
        """Return the list of sensors."""
        return self._sensors

    @property
    def get_sensors_numerical(self):
        """Return the dataframe holding numerical sensor data."""
        return self._sensors_num_df

    @property
    def get_corrs(self):
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
