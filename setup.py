from setuptools import setup, find_packages

REQUIRED = [
    'requests', 'matplotlib', 'pandas', 'sqlalchemy',
]

setup(
    name='HASS-data-detective',
    version='0.4',
    packages=find_packages(exclude=('tests',)),
    url='https://github.com/robmarkcole/HASS-data-detective',
    keywords=['home', 'automation'],
    author='Robin Cole',
    author_email='robmarkcole@gmail.com',
    description='Tools for studying Home-Assistant data',
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
