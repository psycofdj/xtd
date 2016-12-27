# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import cherrypy

from xtd.core.stat.manager import StatManager

#------------------------------------------------------------------#

class CounterPage(object):
  @cherrypy.expose
  @cherrypy.tools.json_out()
  #pylint: disable=unused-argument,no-self-use
  def default(self, *p_args, **p_kwds):
    l_counters = StatManager().get_json()
    for c_sub in p_args:
      l_counters = l_counters.get(c_sub, {})
    return l_counters
