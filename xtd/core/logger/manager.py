# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import inspect
import sys
import logging
import importlib
import json

from .. import logger
from ..tools import mergedicts
from .. import mixin
from ..error.exception import BaseException

#------------------------------------------------------------------#

DEFAULT_CONFIG = {
  "loggers" : {
    "root" : {
      "handlers" : [ "stdout", "rotfile", "syslog"],
      "level"    : 10
    }
  },

  "handlers" : {
    "rotfile" : {
      "class"       : "logging.handlers.RotatingFileHandler",
      "filename"    : "out.log",
      "formatter"   : "default",
      "maxBytes"    : 15*1024*1024,
      "backupCount" : 3
    },
    "stdout" : {
      "class"       : "logging.StreamHandler",
      "formatter"   : "colored",
      "stream"      : "stdout"
    },
    "syslog" : {
      "class"       : "logging.handlers.SysLogHandler",
      "formatter"   : "default",
      "address"     : "/dev/log"
    },
    "memory" : {
      "class"       : "xtd.core.logger.handler.MemoryHandler",
      "formatter"   : "default",
      "max_records" : 2000
    }
  },

  "formatters" : {
    "default" : {
      "class"   : "logging.Formatter",
      "fmt"     : "%(asctime)s (%(name)s) [%(levelname)s] : %(message)s",
      "datefmt" : "%a %d %b %Y at %H-%M",
    },
    "colored" : {
      "class"   : "xtd.core.logger.formatter.FieldFormatter",
      "fmt"     : "%(asctime)s (%(name)s) [%(levelname)s] : %(message)s %(location)s",
      "locfmt"  : "at %(pathname)s:%(lineno)s -> %(funcName)s",
      "datefmt" : "%Y-%m-%d %H:%M:%S",
      "fields"  : {
        "name" : {
          "pad"    : "left",
          "colors" : [ "red"  ],
          "attrs"  : [ "bold" ]
        },
        "levelname" : {
          "pad"    : "left",
          "colors" : [ "yellow"  ],
          "attrs"  : [ "bold" ]
        },
        "location" : {
          "colors" : [ "grey" ],
          "attrs"  : [ "bold" ]
        }
      }
    }
  }
}

#------------------------------------------------------------------#

class WrapperLogger(logging.Logger):
  def __init__(self, p_name):
    super().__init__(p_name)

  def __sys_version(self, p_result):
    if sys.version_info.major != 2:
      return (p_result[0], p_result[1], p_result[2], None)
    return p_result

  def findCaller(self, p_stack):
    l_curFrame  = inspect.currentframe()
    l_outFrames = inspect.getouterframes(l_curFrame)
    l_sourceFrame = None
    for c_pos in range(0, len(l_outFrames)):
      l_frame, l_file, l_lineno, l_func, l_a, l_b = l_outFrames[c_pos]
      if l_file.endswith("core/logger/__init__.py") and l_func == "__wrap":
        l_sourceFrame = l_outFrames[c_pos + 2]
    if l_sourceFrame:
      return self.__sys_version((l_sourceFrame[1], l_sourceFrame[2], l_sourceFrame[3]))
    return logging.Logger.findCaller(self, p_stack)


#------------------------------------------------------------------#

class LogManager(metaclass=mixin.Singleton):
  def __init__(self):
    self.m_logs       = []
    self.m_handlers   = {}
    self.m_formatters = {}
    self.m_loggers    = {}
    self.m_config     = DEFAULT_CONFIG

  def add_formatter(self, p_name, p_obj):
    if p_name in self.m_formatters:
      raise BaseException("multiply definied logging formatter '%s'" % p_name, "logging")
    self.m_formatters[p_name] = p_obj

  def add_handler(self, p_name, p_obj):
    if p_name in self.m_handlers:
      raise BaseException("multiply definied logging handler '%s'" % p_name, "logging")
    self.m_handlers[p_name] = p_obj

  def get_formatter(self, p_name):
    if not p_name in self.m_formatters:
      raise BaseException("undefinied logging formatter '%s'" % p_name, "logging")
    return self.m_formatters[p_name]

  def get_handler(self, p_name):
    if not p_name in self.m_handlers:
      raise BaseException("undefinied logging handler '%s' " % p_name, "logging")
    return self.m_handlers[p_name]

  def _get_class(self, p_name):
    l_parts      = p_name.split('.')
    l_moduleName = '.'.join(l_parts[:-1])
    l_className  = '.'.join(l_parts[-1:])

    try:
      l_module = importlib.import_module(l_moduleName)
    except Exception as l_error:
      raise BaseException("unable to import module '%s' : %s" % (l_moduleName, str(l_error)), "logging")

    try:
      return getattr(l_module, l_className)
    except Exception as l_error:
      raise BaseException("unable to find class '%s' in module '%s'" % (l_className, l_moduleName), "logging")

  def load_config(self, p_file, p_override):
    l_conf = p_file
    if not p_file:
      l_conf = self.m_config
    else:
      try:
        l_file    = open(p_file, mode="r", encoding="utf-8")
        l_content = l_file.read()
        l_conf = json.loads(l_content)
      except Exception as l_error:
        raise BaseException("unable to load json configuration %s : %s" % (p_file, str(l_error)), "logging")

    try:
      l_conf = dict(mergedicts.mergedicts(l_conf, p_override))
      self.m_config = l_conf
    except Exception as l_error:
      raise BaseException("unable to override logging configuration '%s' : %s" % (str(p_override), str(l_error)), "logging")

  def initialize(self, p_file = None, p_override = {}):
    logging.setLoggerClass(WrapperLogger)
    self.load_config(p_file, p_override)

    for c_name, c_conf in self.m_config["formatters"].items():
      l_class = self._get_class(c_conf["class"])
      l_params = { x : y for x,y in c_conf.items() if x != "class" }
      l_obj = l_class(**l_params)
      self.add_formatter(c_name, l_obj)

    for c_name, c_conf in self.m_config["handlers"].items():
      l_class = self._get_class(c_conf["class"])
      l_formatterName = c_conf.get("formatter", "default")
      l_params = { x : y for x,y in c_conf.items() if x not in [ "class", "formatter" ] }

      if "stream" in l_params:
        if l_params["stream"] == "stdout":
          l_params["stream"] = sys.stdout
        elif l_params["stream"] == "stderr":
          l_params["stream"] = sys.stderr
        else:
          l_params["stream"] = open(l_params["stream"], mode="w+")

      l_obj = l_class(**l_params)
      l_formatter = self.get_formatter(l_formatterName)
      l_obj.setFormatter(l_formatter)
      self.add_handler(c_name, l_obj)

    for c_name, c_conf in self.m_config["loggers"].items():
      l_handlers = c_conf.get("handlers", [])
      l_level    = c_conf.get("level", 40)

      if c_name == "root":
        l_logger = logging.getLogger()
      else:
        l_logger = logging.getLogger(c_name)

      l_logger.setLevel(l_level)
      for c_handler in l_handlers:
        l_handler = self.get_handler(c_handler)
        l_logger.addHandler(l_handler)

    logger.info(__name__, "facility initialized")
