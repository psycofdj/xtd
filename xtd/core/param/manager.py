# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import json
import os

from .. import mixin
from .. import logger

#------------------------------------------------------------------#

class Param:
  def __init__(self, p_name, p_value, p_listeners = []):
    if not type(p_listeners) == type([]):
      p_listeners = [ p_listeners ]
    self.m_type       = type(p_value)
    self.m_name       = p_name
    self.m_listerners = p_listeners
    self.m_value      = p_value

  def listen(self, p_handler):
    self.m_listerners.append(p_handler)
    return self

  def get(self):
    return self.m_value

  def set(self, p_value):
    if p_value == self.m_value:
      return True

    if type(p_value) != self.m_type:
      try:
        p_value = json.loads(p_value)
      except Exception:
        pass

    if type(p_value) != self.m_type:
      logger.error(__name__, "unable to change param '%s' value from '%s' to '%s' : type mismatch", self.m_name, str(self.m_value), str(p_value))
      return False

    for c_listener in self.m_listerners:
      try:
        c_listener(self, self.m_value, p_value)
      except BaseException as l_error:
        logger.error(__name__, "unable to change param '%s' value from '%s' to '%s' : %s", self.m_name, str(self.m_value), str(p_value), str(l_error))
        return False
    logger.info(__name__, "parameter '%s' changed value from '%s' to '%s'", self.m_name, str(self.m_value), str(p_value))
    self.m_value = p_value
    return True

class ParamManager(metaclass=mixin.Singleton):
  def __init__(self, p_adminDir):
    self.m_params = {}
    self.m_adminDir = p_adminDir
    self._create_dir(p_adminDir)

  def _create_dir(self, p_dir):
    if not os.path.isdir(p_dir):
      try:
        os.makedirs(p_dir, mode=0o0750)
      except Exception as l_error:
        raise BaseException(__name__, "unable to create output directory '%s' : %s", p_dir, str(l_error))

  def _write(self, p_param, p_oldValue, p_newValue):
    l_path = os.path.join(self.m_adminDir, p_param.m_name)
    try:
      with open(l_path, mode="w") as l_file:
        l_file.write(json.dumps(p_newValue))
    except Exception as l_error:
      logger.error(__name__, "unable to write param '%s' to file '%s' : %s", p_param.m_name, l_path, str(l_error))

  def _load(self, p_param):
    l_path = os.path.join(self.m_adminDir, p_param.m_name)
    if os.path.isfile(l_path):
      try:
        with open(l_path, mode="r") as l_file:
          l_content = l_file.read()
          l_value   = json.loads(l_content)
          p_param.set(l_value)
      except Exception as l_error:
        logger.error(__name__, "unable to load param '%s' from value file '%s' : %s", p_param.m_name, l_path, str(l_error))
        return False
    return True

  def get_names(self):
    return self.m_params.keys()

  def get_param(self, p_name):
    if not p_name in self.m_params:
      logger.error(__name__, "unable to retreive parameter '%s' : unknown parameter", p_name)
      return None
    return self.m_params[p_name]

  def get(self, p_name):
    l_param = self.get_param(p_name)
    if not l_param:
      return None
    return l_param.get()

  def set(self, p_name, p_value):
    l_param = self.get_param(p_name)
    if not l_param:
      return None
    return l_param.set(p_value)

  def listen(self, p_name, p_listener):
    l_param = self.get_param(p_name)
    if not l_param:
      return None
    return l_param.listen(p_listener)

  def register(self, p_name, p_value, p_listeners = [], p_sync = False):
    l_param = Param(p_name, p_value, p_listeners)
    return self.register_param(l_param, p_sync)

  def register_param(self, p_param, p_sync = False):
    if p_param.m_name in self.m_params:
      logger.error(__name__, "unable to register parameter '%s' : parameter already defined", p_name)
    if p_sync:
      if not self._load(p_param):
        return False
      p_param.listen(self._write)
    self.m_params[p_param.m_name] = p_param
    return self
