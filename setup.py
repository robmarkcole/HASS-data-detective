from setuptools import setup, find_packages

PROJECT_DESCRIPTION = ('Tools for studying Home-Assistant data.')
PROJECT_LONG_DESCRIPTION = ('Home Assistant is an open-source '
                            'home automation platform running on Python 3. '
                            'This package provides a set of convenience '
                            'functions and classes to analyse the data '
                            'in your Home-Assistant database. ')

REQUIRED = [
    'matplotlib>=2.2.2',
    'numpy>=1.14.3',
    'pandas>=0.23.0',
    'requests>=2.18.4',
    'ruamel.yaml>=0.15.78',
    'SQLAlchemy>=1.2.8',
    'pytz',
]

setup(
    name='HASS-data-detective',
    version='0.7',
    packages=find_packages(exclude=('tests',)),
    url='https://github.com/robmarkcole/HASS-data-detective',
    keywords=['home', 'automation'],
    author='Robin Cole',
    author_email='robmarkcole@gmail.com',
    description=PROJECT_DESCRIPTION,
    long_description=PROJECT_LONG_DESCRIPTION,
    install_requires=REQUIRED,
    license='MIT',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3"]
)
