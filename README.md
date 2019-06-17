[![PyPI Version](https://img.shields.io/pypi/v/HASS-data-detective.svg)](https://pypi.org/project/HASS-data-detective/)
[![build status](http://img.shields.io/travis/robmarkcole/HASS-data-detective/master.svg?style=flat)](https://travis-ci.org/robmarkcole/HASS-data-detective)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/robmarkcole/HASS-data-detective/master?filepath=notebooks)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Introduction
The `HASS-data-detective` package, which we may also refer to as 'detective' or 'data-detective', provides classes and functions to help you explore and analyse the data in your Home Assistant database. If you are using [Hassio](https://www.home-assistant.io/hassio/), it will automatically discover your sqlite database and by default collect information about the entities in your database. The recommended workflow is to then load the database content into a [Pandas dataframe](https://pandas.pydata.org/pandas-docs/version/0.23.4/generated/pandas.DataFrame.html) using the `fetch_all_data` method. This is recommended as all of the work of formatting the data for analysis is done up front, but it could take a couple of minutes. However if you have a very large database and cannot load it into a Pandas dataframe due to memory limits, you will have to adopt a different workflow where you query and process only the data you are interested in. [Usage of detective.ipynb](https://github.com/robmarkcole/HASS-data-detective/tree/master/usage) shows examples of using the detective with both of these workflows.

**Note** that not all python packages can be installed on Hassio yet - [scipy](https://github.com/scipy/scipy) is in this category. Notable packages which have scipy as a dependency include Seaborn.

## Try out detective online
You can try out detective online without installing anything. If you click on the 'launch binder' button above, detective will be started in a Docker container online using the [Binderhub](https://binderhub.readthedocs.io) service. Run the `Usage of detective` notebook to explore detective, and you can also use the `Upload` button to upload your own `home-assistant_v2.db` database file for analysis. Note that all data is deleted when the container closes down, so this service is just for trying out detective.

## Installation on you machine
You can either: `pip install HASS-data-detective` for the latest released version from pypi, or `pip install git+https://github.com/robmarkcole/HASS-data-detective.git --upgrade` for the bleeding edge version from github. Alternatively if you wish to contribute to the development of detective, clone this repository and install in editable mode with `pip install -e .`

## Initialise HassDatabase
Detective first needs to know the location of your database in order to initialise the `HassDatabase` object which handles communication with your database. If you are using the default sqlite database and have the `home-assistant_v2.db` file locally just supply the path:

```python
from detective.core import HassDatabase

db = HassDatabase('sqlite:////' + 'path_to/home-assistant_v2.db') # on hassio path_to is config
```

If you are running a database server for Home Assistant (e.g. mysql) you need to initialise the `HassDatabase` directly with [the correct connection string](https://www.home-assistant.io/components/recorder/#custom-database-engines), for example:

```python
db = HassDatabase("mysql://scott:tiger@localhost/test")
```

Alternatively if you are using detective on Hassio, there are two possible ways to initialise the `HassDatabase`. The easiest is with `db_from_hass_config`. This will initialise a `HassDatabase` based on the the information found in your Home Assistant config folder, which it will automatically discover:

```python
from detective.core import db_from_hass_config

db = db_from_hass_config() # Auto detect
```

Alternatively it's possible to pass the path in:
```python
db = db_from_hass_config("/home/homeassistant/config") # Pass in path to config
```

Initialisation of `HassDatabase` accepts keyword arguments to influence how the object is initialised:

| Argument | Description |
| -------- | ----------- |
| `fetch_entities` | Boolean to indicate if we should fetch the entities when constructing the database. If not, you will have to call `db.fetch_entities()` at a later stage before being able to use `self.entities` and `self.domains`.

By default with `fetch_entities=True`, on initialisation `HassDatabase` will query the database and list the available domains and their entities in its `domains` and `entities` attributes:

```python
db.domains
```

    ['persistent_notification',
     'remote',
     'script',
     'camera',
     'group',
     'light',
     'zone',
     'alarm_control_panel',
     'switch',
     'automation',
     'media_player',
     'device_tracker',
     'binary_sensor',
     'sensor',
     'input_select',
     'updater',
     'sun']

The attribute `entities` is a dictionary accessed via a domain name:

```python
db.entities['binary_sensor']
```

    ['binary_sensor.motion_at_home',
     'binary_sensor.living_room_motion_sensor',
     'binary_sensor.in_bed_bayesian',
     'binary_sensor.hall_motion_sensor',
     'binary_sensor.bedroom_motion_sensor',
     'binary_sensor.blink_armed_status',
     'binary_sensor.blink_blink_camera_percy_motion_enabled',
     'binary_sensor.workday_sensor',
     'binary_sensor.living_room_nest_protect_online',
     'binary_sensor.bayesianbinary']


### Simple query
Note that at this point we still haven't downloaded any actual data. Lets query a single sensor using SQL and demonstrate the data formatting steps performed by detective, in order to convery raw data into a format suitable for plotting and analysing:


```python
query = text(
    """
    SELECT state, last_changed
    FROM states
    WHERE entity_id in ('sensor.hall_light_sensor')
    AND NOT state='unknown'
    """
    )
response = db.perform_query(query)

df = pd.DataFrame(response.fetchall()) # Convert the response to a dataframe

df.columns = ['state', 'last_changed'] # Set the columns

df = df.set_index('last_changed') # Set the index on datetime

df.index = pd.to_datetime(df.index) # Convert string to datetime

df = df.mask(df.eq('None')).dropna().astype(float) #  Convert state strings to floats for plotting
```
We can then plot the data:
```python
df.plot(figsize=(16, 6));
```

![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_13_0.png)


## Fetch all raw data
Use `fetch_all_data` to cache all your raw database data into a Pandas dataframe in memory. It is useful to keep this raw data in case you mess up your processed data and don't want to go through the process of fetching the raw data all over again.

```python
%%time
db.fetch_all_data()
```

    Querying the database, this could take a while
    master_df created successfully.
    CPU times: user 11.7 s, sys: 12.8 s, total: 24.4 s
    Wall time: 1min 1s

We now have the raw data in a Pandas dataframe on the `master_df` attribute. We must use another class to process this data into a format suitable for plotting and processing. There are separate classes for numerical and binary sensors, which allows them to both implement a `plot` method correctly.

## NumericalSensors class
The `NumericalSensors` class is for formatting numerical data. Create a dataframe with formatted numerical data like so:

```python
sensors_num_df = detective.NumericalSensors(db.master_df)
```

We can access the list of sensor entities:

```python
sensors_num_df.entities[0:10]
```

    ['sensor.next_train_to_wat',
     'sensor.next_bus_to_new_malden',
     'sensor.darksky_sensor_temperature',
     'sensor.darksky_sensor_precip_probability',
     'sensor.iphone_battery_level',
     'sensor.robins_iphone_battery_level',
     'sensor.blink_blink_camera_percy_temperature',
     'sensor.blink_blink_camera_percy_notifications',
     'sensor.next_train_in',
     'sensor.home_to_waterloo']

Now lets look at the Pandas dataframe which is on the `data` attribute:

```python
sensors_num_df.data.head()
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>entity</th>
      <th>sensor.average_indoor_temp</th>
      <th>sensor.bedroom_light_sensor</th>
      <th>sensor.bedroom_temperature</th>
      <th>sensor.blink_blink_camera_percy_notifications</th>
      <th>sensor.blink_blink_camera_percy_temperature</th>
      <th>sensor.bme680air_qual</th>
      <th>sensor.bme680humidity</th>
      <th>sensor.bme680pressure</th>
      <th>sensor.bme680temperature</th>
      <th>sensor.breaches_fredallcardgmailcom</th>
      <th>...</th>
      <th>sensor.next_train_to_wat</th>
      <th>sensor.next_train_to_wim</th>
      <th>sensor.remote_living_room_button</th>
      <th>sensor.robins_iphone_battery_level</th>
      <th>sensor.speedtest_download</th>
      <th>sensor.volume_used_volume_1</th>
      <th>sensor.wipy_humidity</th>
      <th>sensor.wipy_memory</th>
      <th>sensor.wipy_temperature</th>
      <th>sensor.work_to_home</th>
    </tr>
    <tr>
      <th>last_changed</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2017-10-28 06:48:00.143377</th>
      <td>20.2</td>
      <td>15621.0</td>
      <td>18.89</td>
      <td>1.0</td>
      <td>21.0</td>
      <td>98.51</td>
      <td>43.58</td>
      <td>1033.93</td>
      <td>21.07</td>
      <td>0.0</td>
      <td>...</td>
      <td>1125.0</td>
      <td>87.0</td>
      <td>1002.0</td>
      <td>94.0</td>
      <td>36.37</td>
      <td>20.7</td>
      <td>14.0</td>
      <td>38112.0</td>
      <td>32.0</td>
      <td>25.0</td>
    </tr>
    <tr>
      <th>2017-10-28 06:48:01.060922</th>
      <td>20.2</td>
      <td>15621.0</td>
      <td>18.89</td>
      <td>1.0</td>
      <td>21.0</td>
      <td>98.51</td>
      <td>43.50</td>
      <td>1033.93</td>
      <td>21.07</td>
      <td>0.0</td>
      <td>...</td>
      <td>1125.0</td>
      <td>87.0</td>
      <td>1002.0</td>
      <td>94.0</td>
      <td>36.37</td>
      <td>20.7</td>
      <td>14.0</td>
      <td>38112.0</td>
      <td>32.0</td>
      <td>25.0</td>
    </tr>
    <tr>
      <th>2017-10-28 06:48:01.069416</th>
      <td>20.2</td>
      <td>15621.0</td>
      <td>18.89</td>
      <td>1.0</td>
      <td>21.0</td>
      <td>98.51</td>
      <td>43.50</td>
      <td>1033.93</td>
      <td>21.06</td>
      <td>0.0</td>
      <td>...</td>
      <td>1125.0</td>
      <td>87.0</td>
      <td>1002.0</td>
      <td>94.0</td>
      <td>36.37</td>
      <td>20.7</td>
      <td>14.0</td>
      <td>38112.0</td>
      <td>32.0</td>
      <td>25.0</td>
    </tr>
    <tr>
      <th>2017-10-28 06:48:01.076784</th>
      <td>20.2</td>
      <td>15621.0</td>
      <td>18.89</td>
      <td>1.0</td>
      <td>21.0</td>
      <td>98.51</td>
      <td>43.50</td>
      <td>1033.95</td>
      <td>21.06</td>
      <td>0.0</td>
      <td>...</td>
      <td>1125.0</td>
      <td>87.0</td>
      <td>1002.0</td>
      <td>94.0</td>
      <td>36.37</td>
      <td>20.7</td>
      <td>14.0</td>
      <td>38112.0</td>
      <td>32.0</td>
      <td>25.0</td>
    </tr>
    <tr>
      <th>2017-10-28 06:48:01.079950</th>
      <td>20.2</td>
      <td>15621.0</td>
      <td>18.89</td>
      <td>1.0</td>
      <td>21.0</td>
      <td>98.54</td>
      <td>43.50</td>
      <td>1033.95</td>
      <td>21.06</td>
      <td>0.0</td>
      <td>...</td>
      <td>1125.0</td>
      <td>87.0</td>
      <td>1002.0</td>
      <td>94.0</td>
      <td>36.37</td>
      <td>20.7</td>
      <td>14.0</td>
      <td>38112.0</td>
      <td>32.0</td>
      <td>25.0</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 52 columns</p>
</div>

Lets check for correlations in the data:

```python
corrs = sensors_num_df.correlations()

corrs[(corrs['value'] > 0.8) | (corrs['value'] < -0.8)]
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>sensor.next_train_in-sensor.next_train_to_wim</th>
      <td>0.999961</td>
    </tr>
    <tr>
      <th>sensor.iphone_battery_level-sensor.robins_iphone_battery_level</th>
      <td>0.923446</td>
    </tr>
    <tr>
      <th>sensor.bme680air_qual-sensor.bme680pressure</th>
      <td>0.862630</td>
    </tr>
    <tr>
      <th>sensor.mean_temperature-sensor.bedroom_temperature</th>
      <td>0.814340</td>
    </tr>
    <tr>
      <th>sensor.living_room_temperature-sensor.bme680temperature</th>
      <td>0.801827</td>
    </tr>
    <tr>
      <th>sensor.bme680pressure-sensor.darksky_sensor_temperature</th>
      <td>-0.810146</td>
    </tr>
    <tr>
      <th>sensor.bme680humidity-sensor.bme680pressure</th>
      <td>-0.862619</td>
    </tr>
    <tr>
      <th>sensor.memory_usage_real-sensor.volume_used_volume_1</th>
      <td>-0.902779</td>
    </tr>
    <tr>
      <th>sensor.bme680humidity-sensor.bme680air_qual</th>
      <td>-0.999989</td>
    </tr>
  </tbody>
</table>
</div>

Unsurprisingly the mean temperature is strongly correlated with all of the temperature sensors. Interestingly my iphone battery level is somewhat inversely correlated with the travel time from home to waterloo, which gets longer late at night when my battery level is more likely to be low.

#### Plot numerical sensor data
We can pass a single entity to plot:

```python
sensors_num_df.plot('sensor.darksky_sensor_temperature')
```

![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_32_0.png)

We can pass a list of entities to plot:

```python
to_plot = ['sensor.living_room_temperature',
           'sensor.bedroom_temperature',
           'sensor.darksky_sensor_temperature']

sensors_num_df.plot(to_plot)
```

![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_34_0.png)


## BinarySensors class
The `BinarySensors` class is for binary sensor data with on/off states.

```python
sensors_binary_df = detective.BinarySensors(db.master_df)

sensors_binary_df.entities
```

    ['binary_sensor.workday_sensor',
     'binary_sensor.blink_blink_camera_percy_motion_enabled',
     'binary_sensor.living_room_nest_protect_online',
     'binary_sensor.blink_armed_status',
     'binary_sensor.hall_motion_sensor',
     'binary_sensor.bedroom_motion_sensor',
     'binary_sensor.living_room_motion_sensor',
     'binary_sensor.motion_at_home',
     'binary_sensor.bayesianbinary',
     'binary_sensor.in_bed_bayesian']


 We can plot a single binary sensor:

```python
sensors_binary_df.plot('binary_sensor.motion_at_home')
```

![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_43_0.png)


OK now we have demonstrated the basic classes and functionality of detective, lets move on to some analysis!

### Day of week analysis
Lets analyse the **motion_at_home** binary sensor data. We first create features from the raw data for the day-of-the-week and time categories, then perform analysis on these features.

```python
from detective.time import is_weekday, time_category

motion_df = sensors_binary_df.data[['binary_sensor.motion_at_home']] # Must pass a list to return correctly indexed df

motion_df['weekday'] = motion_df.index.weekday_name # get the weekday name

motion_df['is_weekday'] = motion_df.index.map(lambda x: is_weekday(x)) # determine if day is a weekday or not

motion_df = motion_df[motion_df['binary_sensor.motion_at_home'] == True] # Keep only true detection events

motion_df['time_category'] = motion_df.index.map(lambda x: time_category(x)) # Generate a time_category feature

motion_df.head()
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>entity</th>
      <th>binary_sensor.motion_at_home</th>
      <th>weekday</th>
      <th>is_weekday</th>
      <th>time_category</th>
    </tr>
    <tr>
      <th>last_changed</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2017-08-07 20:08:17.810800</th>
      <td>True</td>
      <td>Monday</td>
      <td>True</td>
      <td>evening</td>
    </tr>
    <tr>
      <th>2017-08-07 20:08:26.921077</th>
      <td>True</td>
      <td>Monday</td>
      <td>True</td>
      <td>evening</td>
    </tr>
    <tr>
      <th>2017-08-07 20:10:20.017217</th>
      <td>True</td>
      <td>Monday</td>
      <td>True</td>
      <td>evening</td>
    </tr>
    <tr>
      <th>2017-08-07 20:11:31.024414</th>
      <td>True</td>
      <td>Monday</td>
      <td>True</td>
      <td>evening</td>
    </tr>
    <tr>
      <th>2017-08-07 20:12:02.027471</th>
      <td>True</td>
      <td>Monday</td>
      <td>True</td>
      <td>evening</td>
    </tr>
  </tbody>
</table>
</div>

Lets now do a [groupby](https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.groupby.html) operation:
```python
motion_df['binary_sensor.motion_at_home'].groupby(motion_df['is_weekday']).describe()['count']
```

    is_weekday
    False     4452
    True     10862
    Name: count, dtype: object

```python
motion_df_gb = motion_df['binary_sensor.motion_at_home'].groupby([motion_df['weekday'], motion_df['time_category']]).sum().unstack()

motion_df_gb.fillna(value=0, inplace=True) # Replace NaN with 0

motion_df_gb = motion_df_gb.astype('int') # Ints rather than floats

motion_df_gb = motion_df_gb.T

motion_df_gb
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>weekday</th>
      <th>Friday</th>
      <th>Monday</th>
      <th>Saturday</th>
      <th>Sunday</th>
      <th>Thursday</th>
      <th>Tuesday</th>
      <th>Wednesday</th>
    </tr>
    <tr>
      <th>time_category</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>daytime</th>
      <td>1000</td>
      <td>690</td>
      <td>962</td>
      <td>631</td>
      <td>844</td>
      <td>880</td>
      <td>800</td>
    </tr>
    <tr>
      <th>evening</th>
      <td>394</td>
      <td>599</td>
      <td>239</td>
      <td>496</td>
      <td>453</td>
      <td>532</td>
      <td>545</td>
    </tr>
    <tr>
      <th>morning</th>
      <td>839</td>
      <td>688</td>
      <td>1047</td>
      <td>833</td>
      <td>664</td>
      <td>655</td>
      <td>619</td>
    </tr>
    <tr>
      <th>night</th>
      <td>92</td>
      <td>93</td>
      <td>131</td>
      <td>113</td>
      <td>163</td>
      <td>149</td>
      <td>163</td>
    </tr>
  </tbody>
</table>
</div>

We see that there is a lot of activity on saturday mornings, when I hoover the house. We can also visualise this data using Seaborn.

#### Seaborn
Seaborn is a python package for doing statistical plots. Unfortunately it is not yet supported on Hassio, but if you are on a Mac or PC you can use it like follows:

```python
import seaborn as sns
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(14, 6))
days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
times_list = ['morning', 'daytime', 'evening', 'night']
ax = sns.heatmap(motion_df_gb[days_list].loc[times_list], annot=True, linewidths=.5, fmt="d", ax=ax, cmap='Reds');
ax.set_title('Activity at home by day and time category')
#fig.savefig('heatmap.jpg')
```

![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_54_1.png)

### Auth helpers
When querying the database, you might end up with user IDs and refresh token IDs. We've included a helper to help load the auth from Home Assistant and help you process this data.

```python
from detective.auth import auth_from_hass_config

auth = auth_from_hass_config()
```

```python
auth.users
```

    {
      "user-id": {
        "id": "id of user",
        "name": "Name of user",
      }
    }

```python
auth.refresh_tokens
```

    "refresh-token-id": {
      "id": "id of token",
      "user": "user object related to token",
      "client_name": "Name of client that created token",
      "client_id": "ID of client that created token",
    }

```python
> auth.user_name('some-user-id')
Paulus
```
