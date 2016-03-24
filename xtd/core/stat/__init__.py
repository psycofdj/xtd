# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

from .manager import StatManager

#------------------------------------------------------------------#

def get(p_name):
  return CounterManager().get(p_name);
