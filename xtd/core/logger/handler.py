# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import logging

#------------------------------------------------------------------#

class MemoryHandler(logging.Handler):
  def __init__(self, max_records):
    super().__init__()
    self.m_max_records = max_records



