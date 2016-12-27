#!/usr/bin/env python
# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import sys
from setuptools import setup
sys.path.insert(0, ".")
import xtd

setup(
  name     = 'xtd',
  packages = ['xtd',                 'xtd.core',        'xtd.network',
              'xtd.core.param',      'xtd.core.stat',   'xtd.core.tools',
              'xtd.core.logger',     'xtd.core.config', 'xtd.network.client',
              'xtd.network.server'],
  install_requires = ["cherrypy", "termcolor", "pycurl", "requests", "future"],
  test_suite   = 'xtd.test',
  version      = xtd.__version__,
  description  = xtd.__description__,
  author       = xtd.__author__.split("<")[0].strip(),
  author_email = xtd.__author__.split("<")[1].split(">")[0].strip(),
  url          = xtd.__url__,
  download_url = xtd.__download_url__,
  keywords     = xtd.__keywords__,
  classifiers  = xtd.__classifiers__
)
