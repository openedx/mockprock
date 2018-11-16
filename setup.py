#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0111,W6005,W6100
from __future__ import absolute_import, print_function

import os
import sys

from setuptools import setup

setup(
    name='mockprock',
    version='0.6',
    description='Mock proctoring backend for Open edX',
    author='Dave St.Germain',
    author_email='davestgermain@edx.org',
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    packages=[
        'mockprock',
    ],
    include_package_data=True,
    install_requires=[
        "setuptools",
    ],
    extras_require={
        'server': [
            "flask",
            "PyJWT",
            'edx_rest_api_client>=1.9.2',
        ]
    },
    entry_points={
        'openedx.proctoring': [
            'mockprock = mockprock.backend:MockProckBackend',
        ],
        'console_scripts': ['get-dashboard=mockprock.commands:get_url'],
    },

)
