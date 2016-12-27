# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import collections
import logging
import cherrypy

from xtd.core import logger

#------------------------------------------------------------------#

class LogPage(object):
  def __init__(self, p_credentials = None):
    self.m_credentials = p_credentials

  def check_password(self, p_realm, p_username, p_password):
    p_realm=p_realm
    if not self.m_credentials:
      return True
    return (p_username in self.m_credentials) and (p_password == self.m_credentials[p_username])

  @staticmethod
  def _level_to_name(p_level):
    if p_level == 10:
      return "debug"
    elif p_level == 20:
      return "info"
    elif p_level == 30:
      return "warning"
    elif p_level == 40:
      return "error"
    elif p_level == 50:
      return "exception"
    return "notset"

  @staticmethod
  def _name_to_level(p_level):
    p_level = p_level.lower()
    if p_level == "debug":
      return 10
    elif p_level == "info":
      return 20
    elif p_level == "warning":
      return 30
    elif p_level == "error":
      return 40
    elif p_level == "exception":
      return 50
    else:
      return 0

  @cherrypy.expose
  @cherrypy.tools.json_out()
  def write(self, *p_args, **p_kwds):
    p_args  = p_args
    l_count = len(p_kwds.items())
    for c_name, c_val in p_kwds.items():
      if c_name == "root":
        l_logger = logging.getLogger()
      else:
        l_logger = logging.getLogger(c_name)
      l_levelName    = self._level_to_name(l_logger.level)
      l_newLevel     = self._name_to_level(c_val)
      l_newLevelName = self._level_to_name(l_newLevel)
      l_logger.setLevel(l_newLevel)
      if l_levelName != l_newLevelName:
        logger.info(__name__, "changing level of logger '%s' from '%s' to '%s'",
                    c_name, l_levelName, l_newLevelName)
    return {
      "status"  : "success",
      "message" : "modified '%d' loggers" % l_count
    }

  @cherrypy.expose
  @cherrypy.tools.json_out()
  def default(self, *p_args, **p_kwds):
    p_args    = p_args
    l_res     = {}
    l_loggers = logging.Logger.manager.loggerDict.items()
    l_list    = { x:y for x,y in l_loggers if not x.startswith("cherrypy") }
    for c_name in l_list:
      l_logger = logging.getLogger(c_name)
      if "effective" in p_kwds:
        l_level  = self._level_to_name(l_logger.getEffectiveLevel())
      else:
        l_level  = self._level_to_name(l_logger.level)
      l_res[c_name] = l_level

    l_logger = logging.getLogger()
    l_level  = self._level_to_name(l_logger.level)
    l_res["root"] = l_level

    return collections.OrderedDict(sorted(l_res.items()))
