# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import cherrypy

from xtd.core.param.manager import ParamManager

#------------------------------------------------------------------#

class ParamPage(object):
  def __init__(self, p_credentials = None):
    self.m_credentials = p_credentials

  @staticmethod
  def get_data():
    l_mgr = ParamManager(p_adminDir="unused")
    l_list = l_mgr.get_names()
    l_data = { c_name : l_mgr.get(c_name) for c_name in l_list }
    return l_data

  def check_password(self, p_realm, p_username, p_password):
    p_realm = p_realm
    if not self.m_credentials:
      return True
    return (p_username in self.m_credentials) and (p_password == self.m_credentials[p_username])

  @cherrypy.expose
  @cherrypy.tools.json_out()
  #pylint: disable=unused-argument,no-self-use
  def write(self, *p_args, **p_kwds):
    for c_name, c_val in p_kwds.items():
      l_status = ParamManager(p_adminDir="unused").set(c_name, c_val)
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
  #pylint: disable=unused-argument,no-self-use
  def default(self, *p_args, **p_kwds):
    return self.get_data()
