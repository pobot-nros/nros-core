#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(name='nros_core',
      version='1.0',
      description='Core part of nROS framework',
      license='LGPL',
      author='Eric Pascual',
      author_email='eric@pobot.org',
      url='http://www.pobot.org',
      download_url='https://github.com/Pobot/PyBot',
      packages=find_packages("src"),
      package_dir={'': 'src'},
      include_package_date=True
      )
