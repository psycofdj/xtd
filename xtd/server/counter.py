# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import cherrypy

from ..core.stat.manager import StatManager

#------------------------------------------------------------------#

class CounterPage:
  @cherrypy.expose
  @cherrypy.tools.json_out()
  def default(self, *p_args, **p_kwds):
    l_counters = StatManager().get_json()
    for c_sub in p_args:
      l_counters = l_counters.get(c_sub, {})
    return l_counters
