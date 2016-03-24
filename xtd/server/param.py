# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import cherrypy

from ..core.param.manager import ParamManager

#------------------------------------------------------------------#

class ParamPage:
  def __init__(self, p_credentials = None):
    self.m_credentials = p_credentials

  def get_data(self):
    l_list = ParamManager().get_names()
    l_data = { c_name : ParamManager().get(c_name) for c_name in l_list }
    return l_data

  def check_password(self, p_realm, p_username, p_password):
    if not self.m_credentials:
      return True
    return (p_username in self.m_credentials) and (p_password == self.m_credentials[p_username])

  @cherrypy.expose
  @cherrypy.tools.json_out()
  def write(self, *p_args, **p_kwds):
    for c_name, c_val in p_kwds.items():
      l_status = ParamManager().set(c_name, c_val)
      if not l_status:
        cherrypy.response.status = 500
        return {
          "status"  : "error",
          "message" : "unable to set parameters '%s' to value '%s'" % (c_name, str(c_val))
        }
    return {
      "status"  : "success",
      "message" : None
    }

  @cherrypy.expose
  @cherrypy.tools.json_out()
  def default(self, *p_args, **p_kwds):
    return self.get_data()
