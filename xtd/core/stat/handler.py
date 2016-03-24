# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import abc

from .manager          import StatManager
from ..tools.thread    import SafeThread

#------------------------------------------------------------------#

class StatHandler(SafeThread):
  def __init__(self, p_name, p_interval = 50):
    super().__init__(p_name, p_interval)

  @abc.abstractmethod
  def write(self, p_counters):
    raise NotImplemented

  def work(self):
    l_data = StatManager().get_all()
    self.write(l_data)
