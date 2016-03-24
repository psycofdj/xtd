# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

from ..       import mixin
from ..       import logger
from ..tools  import thread

#------------------------------------------------------------------#

class StatManager(thread.SafeThreadGroup, metaclass=mixin.Singleton):
  def __init__(self):
    super().__init__(__name__)
    self.m_counters  = {}

  def add_handler(self, p_handler):
    from .handler import StatHandler
    if not issubclass(p_handler.__class__, StatHandler):
      raise BaseException(__name__, "handlers must be StatHandler based class")
    self.add_thread(p_handler)

  def add_counter(self, p_path, p_counter):
    if p_path in self.m_counters:
      raise BaseException(__name__, "already definied counter '%s'", p_path)
    self.m_counters[p_path] = p_counter

  def write(self):
    for c_handler in self.m_threads:
      c_handler.write()

  def get_all(self):
    return self.m_counters

  def get(self, p_path):
    if not p_path in self.m_counters:
      raise BaseException(__name__, "undefinied counter '%s'", p_path)
    return self.m_counters[p_path]

  def get_json(self):
    l_res = {}
    for c_path, c_counter in self.m_counters.items():
      c_counter.update()
      l_item = l_res
      for c_part in c_path.split("."):
        if not c_part in l_item:
          l_item[c_part] = {}
        l_item = l_item[c_part]
      def visitor(p_name, p_value):
        l_item[p_name] = p_value
      c_counter.visit(visitor)
    return l_res

#------------------------------------------------------------------#
