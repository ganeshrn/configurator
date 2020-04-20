#!/usr/bin/env python

from setuptools import setup, find_packages


setup(
    name="configurator",
    namespace_packages=['configurator'],
    version="0.0.1",
    author='Ganesh B. Nalawade',
    url="https://github.com/ganesrn/configurator",
    license='Apache',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    long_description_content_type='text/markdown',
    zip_safe=False,

)
