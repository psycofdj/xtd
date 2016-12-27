# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import cherrypy
from xtd.core import config

#------------------------------------------------------------------#

class ConfigPage(object):
  @cherrypy.expose
  @cherrypy.tools.json_out()
  #pylint: disable=unused-argument,no-self-use
  def default(self, *p_args, **p_kwds):
    l_result   = {
      c_sec : {
        c_name : config.get(c_sec, c_name) for c_name in config.options(c_sec)
      } for c_sec in config.sections()
    }
    for c_sub in p_args:
      l_result = l_result.get(c_sub, {})
    return l_result
