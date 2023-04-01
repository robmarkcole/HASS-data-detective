[![PyPI Version](https://img.shields.io/pypi/v/HASS-data-detective.svg)](https://pypi.org/project/HASS-data-detective/)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/robmarkcole/HASS-data-detective/master?filepath=notebooks)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Introduction
The `HASS-data-detective` package provides classes and functions to help you explore and analyse the data in your [Home Assistant)](https://www.home-assistant.io/) database. If you are running `HASS-data-detective` on a machine with Home Assistant installed, it will automatically discover your database and by default collect information about the entities in your database. See the notebooks directory for examples of using the detective package. If you are on a Raspberry pi use the official [JupyterLab add-on.](https://data.home-assistant.io/docs/quick-start/) which includes `HASS-data-detective`.

## Installation on your machine
You can either: `pip install HASS-data-detective` for the latest released version from pypi, or `pip install git+https://github.com/robmarkcole/HASS-data-detective.git --upgrade` for the bleeding edge version from github. Note that due to the matplotlib dependency, libfreetype6-dev is a requirement on `aarch64` platforms (i.e. RPi).

## Run with Docker locally
You can use the detective package within a Docker container so there is no need to install anything on your machine (assuming you already have docker installed). Note this will pull the [jupyter/scipy-notebook](https://github.com/jupyter/docker-stacks/blob/master/scipy-notebook/Dockerfile) docker image the first time you run it, but subsequent runs will be much faster. Note there is no image available for Raspberry pi.

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

## Development (VScode)
* Create a venv: `python3 -m venv venv`
* Activate venv: `source venv/bin/activate`
* Install requirements: `pip3 install -r requirements.txt`
* Install detective in development mode: `pip3 install -e .`
* Install Jupyterlab to run the notebooks: `pip3 install jupyterlab`
* Open the notebook at `notebooks/Getting started with detective.ipynb`

### Running tests
* Install dependencies: `pip3 install -r requirements_test.txt`
* Run: `pytest tests`

## Contributors
Big thanks to [@balloob](https://github.com/balloob) and [@frenck](https://github.com/frenck), checkout their profiles!
