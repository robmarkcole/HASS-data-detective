from setuptools import setup, find_packages

REQUIRES = [
    "pandas>=1.1.4",
    "ruamel.yaml>=0.15.78",
    "SQLAlchemy>=2.0.7",
    "pytz",
]

PROJECT_DESCRIPTION = "Tools for studying Home Assistant data."
PROJECT_LONG_DESCRIPTION = (
    "Home Assistant is an open-source "
    "home automation platform running on Python 3. "
    "This package provides a set of convenience "
    "functions and classes to analyse the data "
    "in your Home Assistant database. "
)

setup(
    name="HASS-data-detective",
    version="3.2",
    packages=find_packages(exclude=("tests",)),
    url="https://github.com/robmarkcole/HASS-data-detective",
    keywords=["home", "automation"],
    author="Robin Cole",
    author_email="robmarkcole@gmail.com",
    description=PROJECT_DESCRIPTION,
    long_description=PROJECT_LONG_DESCRIPTION,
    install_requires=REQUIRES,
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
