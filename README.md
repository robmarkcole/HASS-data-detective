[![PyPI Version](https://img.shields.io/pypi/v/HASS-data-detective.svg)](https://pypi.org/project/HASS-data-detective/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/robmarkcole/HASS-data-detective/master?filepath=notebooks)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Introduction
The `HASS-data-detective` package helps you explore and analyse the data in your [Home Assistant)](https://www.home-assistant.io/) database. If you are running `HASS-data-detective` on a machine with Home Assistant installed, it will automatically discover your database and by default collect information about the entities in your database. See the notebooks directory for examples of using the detective package. If you are on a Raspberry pi you should use the official [JupyterLab add-on](https://data.home-assistant.io/docs/quick-start/) which includes `HASS-data-detective`

## Prerequisites
* Python `3.12.x` is required.

## Installation on your machine
You can either: `pip install HASS-data-detective` for the latest released version from pypi, or `pip install git+https://github.com/robmarkcole/HASS-data-detective.git --upgrade` for the bleeding edge version from github. Note that due to the matplotlib dependency, libfreetype6-dev is a requirement on `aarch64` platforms (i.e. RPi).

## Which version to install?
The 3.0 version from pypi requires the existence of a `states_meta` table which is not present in older Home Assistant databases. If you get the error `(sqlite3.OperationalError) no such table: states_meta` then you should install the earlier release with `pip install HASS-data-detective==2.6`

## Development (VScode)
* Create a venv: `python3.12 -m venv venv`
* Activate venv: `source venv/bin/activate`
* Confirm Python version: `python --version` (should be `3.12.x`)
* Install requirements: `pip install -r requirements.txt`
* Install detective in development mode: `pip install -e .`
* Install Jupyterlab to run the notebooks: `pip install jupyterlab`
* Open the notebook at `notebooks/Getting started with detective.ipynb`

### Running tests
* Install dependencies: `pip install -r requirements_test.txt`
* Run: `python -m pytest tests`

## Contributors
Big thanks to [@balloob](https://github.com/balloob) and [@frenck](https://github.com/frenck), checkout their profiles!
