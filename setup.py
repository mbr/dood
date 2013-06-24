#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='dood',
    version='0.1.2dev',
    description='A simplified API for creating polls on doodle.com.',
    long_description=read('README.rst'),
    author='Marc Brinkmann',
    author_email='git@marcbrinkmann.de',
    url='http://github.com/mbr/dood',
    license='MIT',
    packages=find_packages(exclude=['test']),
    install_requires=['lxml', 'rauth', 'requests', 'xmltodict'],
)