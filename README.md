[![PyPI Version](https://img.shields.io/pypi/v/HASS-data-detective.svg)](https://pypi.org/project/HASS-data-detective/)

## Installation
You can either: `pip install HASS-data-detective` for the latest version from pypi, or clone this repo and install in editable mode with `pip install -e .`

## Usage
Jupyter notebook [Usage of detective.ipynb](https://github.com/robmarkcole/HASS-data-detective/tree/master/usage) shows usage of the data detective package. Examples can also be found in the repository https://github.com/robmarkcole/HASS-data-detective-analysis


To load from a local db, we just need the path


```python
db_path = 'Users/robincole/Documents/Home-assistant_database/home-assistant_v2.db'
DB_URL = 'sqlite:////' + db_path
```

Alternatively, to load from a cloud database we load from a json file containing the url as the url contains our credentials and we want to lkeep these a secret. To learn how the Google CLoud SQL recorder can be setup checkout https://github.com/robmarkcole/HASS-Google-Cloud-SQL


```python
# For cloud database with secret credentials, load from json. Time to load vaires, up to 3 mins.
#filename = '/Users/robincole/Desktop/hass_db_url.json'
#DB_URL = helpers.load_url(filename)
```

## Load the db data

We use the DataParser class to load data from the database. This class performs the SQL queries and parses the returned data. The class holds the master pandas dataframe master_df.

If you are running under Hass.io or are using the default configuration path, `HassDatabase` will be able to automatically detect your database url. If not, you can pass in either the `url` or `hass_config_path`.

```python
%%time
from detective.core import HassDatabase
# Example invocations
# Auto detect
db = HassDatabase()
# using DB url
db = HassDatabase(url=DB_URL)
# Using HASS config path
db = HassDatabase(hass_config_path='/home/homeassistant/config')
# Auto detect and not prefetching entities
db = HassDatabase(fetch_entities=False)
```

    Successfully connected to sqlite:////Users/robincole/Documents/Home-assistant_database/home-assistant_v2.db
    There are 261 entities with data
    CPU times: user 525 ms, sys: 2.44 s, total: 2.97 s
    Wall time: 13.3 s



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




```python
db.entities['sensor'][15:20]
```




    ['sensor.living_room_temperature',
     'sensor.hall_light_sensor',
     'sensor.home_to_waterloo',
     'sensor.work_to_home',
     'sensor.living_room_light_sensor']



## Simple query

Lets query a single sensor and demonstrate the data processing steps implemented by the library


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
df = pd.DataFrame(response.fetchall()) # Convert to dataframe
df.columns = ['state', 'last_changed'] # Set the columns
df = df.set_index('last_changed') # Set the index on datetime
df.index = pd.to_datetime(df.index) # Convert string to datetime
df = df.mask(df.eq('None')).dropna().astype(float) #  Convert state strings to floats for plotting
df.plot(figsize=(16, 6));
```


![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_13_0.png)


## Helper to query by list
Use `fetch_data_by_list` to query a list of numerical entities, must be from same domain and a minimum of 2 entities must be in the list. Returns a pandas dataframe.


```python
db.fetch_data_by_list(db.entities['sensor'][15])
```

    Must pass more than 1 entity.



```python
%%time
df = db.fetch_data_by_list(db.entities['sensor'][15:17])
```

    CPU times: user 159 ms, sys: 273 ms, total: 433 ms
    Wall time: 1.42 s



```python
df.head()
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th>entity</th>
      <th>sensor.hall_light_sensor</th>
      <th>sensor.living_room_temperature</th>
    </tr>
    <tr>
      <th>last_changed</th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2017-07-22 14:22:28.950795</th>
      <td>6858.0</td>
      <td>20.68</td>
    </tr>
    <tr>
      <th>2017-07-22 14:22:29.053893</th>
      <td>6858.0</td>
      <td>20.68</td>
    </tr>
    <tr>
      <th>2017-07-22 14:23:10.703517</th>
      <td>6858.0</td>
      <td>20.96</td>
    </tr>
    <tr>
      <th>2017-07-22 14:26:59.745763</th>
      <td>6334.0</td>
      <td>20.96</td>
    </tr>
    <tr>
      <th>2017-07-22 14:31:59.744730</th>
      <td>5864.0</td>
      <td>20.96</td>
    </tr>
  </tbody>
</table>
</div>




```python
df['sensor.hall_light_sensor'].describe()
```




    count    23213.000000
    mean      9263.393874
    std       5984.677651
    min          0.000000
    25%       4895.000000
    50%      10291.000000
    75%      13142.000000
    max      24845.000000
    Name: sensor.hall_light_sensor, dtype: float64



## Query all data
Data-detective takes care of parsing data from the database, intelligently sorting out numerical and categorical data and formatting them correctly. Use `fetch_all_data` to import all your db data into a pandas dataframe in memory -> this approach means it can take a while to load the data into memory, but subsequent processing and handling are much faster/easier.


```python
%%time
db.fetch_all_data()
```

    Querying the database, this could take a while
    master_df created successfully.
    CPU times: user 11.7 s, sys: 12.8 s, total: 24.4 s
    Wall time: 1min 1s


The `NumericalSensors` class is for parsing the numerical data. Lets create a dataframe for the numerical sensor data


```python
sensors_num_df = detective.NumericalSensors(db.master_df)
```

We can access the list of sensor entities using the list_sensors attribute


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



Now lets look at the dataframe


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



Lets now check for correlations in the data using the all_corrs() method


```python
corrs = sensors_num_df.correlations()
```


```python
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



Unsurprisingly the mean temperature is strongly correlated with all of the temperature sensors.

Interestingly my iphone battery level is somewhat inversely correlated with the travel time from home to waterloo, which gets longer late at night when my battery level is more likely to be low.

#### Plot sensor data
Convenience to plot a sensor data.
Pass a single entity to plot:


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


Even mix up lists and single entites


```python
sensors_num_df.plot(to_plot, 'sensor.mean_temperature')
```


![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_36_0.png)


#### Pairplot
A seaborn pair plot to show correlations.


```python
%%time
sns.pairplot(sensors_num_df.data[to_plot]);
```

    CPU times: user 3.74 s, sys: 110 ms, total: 3.85 s
    Wall time: 3.85 s





    <seaborn.axisgrid.PairGrid at 0x13c61d4e0>




![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_38_2.png)


## Binary sensors
The `BinarySensors` class is for binary sensor data with on/off states.


```python
sensors_binary_df = detective.BinarySensors(db.master_df)
```


```python
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



Currently we can plot a single binary sensor with the plot() method


```python
sensors_binary_df.plot('binary_sensor.motion_at_home')
```


![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_43_0.png)


## Day of week analysis

Lets analyse the **motion_at_home**, create some features for day of week and time category, then analyse motion by these features.


```python
motion_df = sensors_binary_df.data[['binary_sensor.motion_at_home']] # Must pass a list to return correctly indexed df
```


```python
motion_df['weekday'] = motion_df.index.weekday_name
```


```python
motion_df['is_weekday'] = motion_df.index.map(lambda x: helpers.is_weekday(x))
```


```python
motion_df = motion_df[motion_df['binary_sensor.motion_at_home'] == True] # Keep only true detection events
```


```python
motion_df['time_category'] = motion_df.index.map(lambda x: helpers.time_category(x))
```


```python
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




```python
motion_df['binary_sensor.motion_at_home'].groupby(motion_df['is_weekday']).describe()['count']
```




    is_weekday
    False     4452
    True     10862
    Name: count, dtype: object




```python
motion_df_gb = motion_df['binary_sensor.motion_at_home'].groupby([motion_df['weekday'], motion_df['time_category']]).sum().unstack()
motion_df_gb.fillna(value=0, inplace=True)   # Replace NaN with 0
motion_df_gb = motion_df_gb.astype('int')              # Ints rather than floats
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




```python
fig, ax = plt.subplots(figsize=(14, 6))
days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
times_list = ['morning', 'daytime', 'evening', 'night']
ax = sns.heatmap(motion_df_gb[days_list].loc[times_list], annot=True, linewidths=.5, fmt="d", ax=ax, cmap='Reds');
ax.set_title('Activity at home by day and time category')
#fig.savefig('heatmap.jpg')
```




    Text(0.5,1,'Activity at home by day and time category')




![png](https://github.com/robmarkcole/HASS-data-detective/blob/master/docs/images/output_54_1.png)
