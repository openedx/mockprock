#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0111,W6005,W6100
from __future__ import absolute_import, print_function

import os
import sys

from setuptools import setup

def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns a list of requirement strings.
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split('#')[0].strip() for line in open(path)
            if is_requirement(line.strip())
        )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement;
    that is, it is not blank, a comment, a URL, or an included file.
    """
    return not (
        line == '' or
        line.startswith('-r') or
        line.startswith('#') or
        line.startswith('-e') or
        line.startswith('git+')
    )


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
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    packages=[
        'mockprock',
    ],
    include_package_data=True,
    install_requires=load_requirements("requirements/base.txt"),
    extras_require={
        'server': load_requirements("requirements/server.txt"),
    },
    entry_points={
        'openedx.proctoring': [
            'mockprock = mockprock.backend:MockProckBackend',
        ],
        'console_scripts': ['get-dashboard=mockprock.commands:get_url'],
    },
)
