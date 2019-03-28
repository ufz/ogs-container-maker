#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for hpccm."""

import os

from setuptools import find_packages
from setuptools import setup

from ogscm.version import __version__

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.md')) as fp:
    long_description = fp.read()

setup(
    name='ogscm',
    version=__version__,
    description='OGS Container Maker',
    long_description=long_description,
    long_description_content_type='text/markdown',
    maintainer='Lars Bilke',
    maintainer_email='lars.bilke@ufz.de',
    license='BSD 3-Clause',
    url='https://github.com/ufz/ogs-container-maker',
    packages=find_packages(),
    classifiers=[
      "License :: OSI Approved :: BSD License",
      "Programming Language :: Python :: 3",
      "Operating System :: OS Independent",
    ],
    # Make build.py available from the command line as `ogscm`.
    install_requires=['enum34', 'six', 'requests', 'hpccm'],
    # scripts=['ogscm']
    entry_points={
        'console_scripts': [
            'ogscm=ogscm.cli:main']}
)
