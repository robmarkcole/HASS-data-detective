[![PyPI Version](https://img.shields.io/pypi/v/HASS-data-detective.svg)](https://pypi.org/project/HASS-data-detective/)
[![build status](http://img.shields.io/travis/robmarkcole/HASS-data-detective/master.svg?style=flat)](https://travis-ci.org/robmarkcole/HASS-data-detective)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/robmarkcole/HASS-data-detective/master?filepath=notebooks)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Sponsor](https://img.shields.io/badge/sponsor-%F0%9F%92%96-green)](https://github.com/sponsors/robmarkcole)

## Introduction
The `HASS-data-detective` package provides classes and functions to help you explore and analyse the data in your Home Assistant database. If you are using [Hassio](https://www.home-assistant.io/hassio/), it will automatically discover your database and by default collect information about the entities in your database. See the notebooks directory for examples of using the detective package.

## Installation on your machine
You can either: `pip install HASS-data-detective` for the latest released version from pypi, or `pip install git+https://github.com/robmarkcole/HASS-data-detective.git --upgrade` for the bleeding edge version from github. Note that due to the matplotlib dependency, libfreetype6-dev is a requirement on `aarch64` platforms (i.e. RPi).

## Run with Docker locally
You can use the detective package within a Docker container so there is no need to install anything on your machine (assuming you already have docker installed). Note this will pull the [jupyter/scipy-notebook](https://github.com/jupyter/docker-stacks/blob/master/scipy-notebook/Dockerfile) docker image the first time you run it, but subsequent runs will be much faster.

From the root directory of this repo run:
```
docker run --rm -p 8888:8888 -e JUPYTER_ENABLE_LAB=yes -v "$PWD":/home/jovyan/work jupyter/scipy-notebook
```
Follow the URL printed to the terminal, which opens a Jupyter lab instance. Open a new terminal in Jupyter lab and navigate to the `work` directory containing `setup.py`, then run:
 ```
 ~/work$ pip install .
 ```
You can now navigate to the notebooks directory and start using the detective package. Note that you can install any package you want from pypi, but they will not persist on restarting the container.

## Try out detective online
You can try out the latest version of detective from pypi without installing anything. If you click on the 'launch binder' button above, detective will be started in a Docker container online using the [Binderhub](https://binderhub.readthedocs.io) service. Run the example notebook to explore detective, and use the `Upload` button to upload your own `home-assistant_v2.db` database file for analysis. Note that all data is deleted when the container closes down, so this service is just for trying out detective.

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

## Contributors
Big thanks to [@balloob](https://github.com/balloob) and [@frenck](https://github.com/frenck), checkout their profiles!

## ✨ Support this work

https://github.com/sponsors/robmarkcole

If you or your business find this work useful please consider becoming a sponsor at the link above, this really helps justify the time I invest in maintaining this repo. As we say in England, 'every little helps' - thanks in advance!
