# -*- coding: utf-8
# pylint: disable=unused-import
#------------------------------------------------------------------#
"""
module doc top
"""

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import json
import os
from future.utils    import with_metaclass

from .. import mixin
from .. import logger
from .. import error

#------------------------------------------------------------------#

class Param(object):
  """Object that holds an JSON-serializable value

  Args:
     p_name (str)                     : Name of the parameter
     p_value (json-serializable)      : Initial parameter value
     p_callbacks (Optional[function]) : List of function to call whenever when the value changes\
                                        Can be an array of functions or a single function

  When changing value with the :meth:`set` method, all registered listerners are called
  and if none of them raises an error, the value in stored.

  New callbacks can be registered with :obj:`listen`

  Note:
     Each callback must respect the following prototype :
     ``function(p_parameter, p_oldValue, p_newValue)``

     - **p_parameter** (Param): the modified Param object
     - **p_oldValue** (json-serializable): parameter's old value
     - **p_newvalue** (json-serializable): parameter's new value

     Callback must raise :obj:`xtd.core.error.XtdError` is new value is not acceptable
  """
  def __init__(self, p_name, p_value, p_callbacks=None):
    if p_callbacks is None:
      p_callbacks = []
    if not isinstance(p_callbacks, list):
      p_callbacks = [ p_callbacks ]

    self.m_type       = type(p_value)
    self.m_name       = p_name
    self.m_callbacks = p_callbacks
    self.m_value      = p_value

  def listen(self, p_handler):
    self.m_callbacks.append(p_handler)
    return self

  def get(self):
    return self.m_value

  def set(self, p_value):
    if p_value == self.m_value:
      return True

    if not isinstance(p_value, self.m_type):
      try:
        p_value = json.loads(p_value)
      except (ValueError, TypeError):
        pass

    if not isinstance(p_value, self.m_type):
      logger.error(__name__,
                   "unable to change param '%s' value from '%s' to '%s' : type mismatch",
                   self.m_name, str(self.m_value), str(p_value))
      return False

    for c_ballback in self.m_callbacks:
      try:
        c_ballback(self, self.m_value, p_value)
      except error.XtdError as l_error:
        logger.error(__name__,
                     "unable to change param '%s' value from '%s' to '%s', %s",
                     self.m_name, str(self.m_value), str(p_value), str(l_error))
        return False
    logger.info(__name__, "parameter '%s' changed value from '%s' to '%s'",
                self.m_name, str(self.m_value), str(p_value))
    self.m_value = p_value
    return True

class ParamManager(with_metaclass(mixin.Singleton, object)):
  """Stores in memory global parameters
  """
  def __init__(self, p_adminDir):
    """Constructor

    Args:
      p_adminDir (str) : directory to dump-to/load-from synced parameters

    Raises:
       xtd.core.error.XtdError : p_adminDir is not writable

    """
    self.m_params = {}
    self.m_adminDir = p_adminDir
    self._create_dir(p_adminDir)

  @staticmethod
  def _create_dir(p_dir):
    if not os.path.isdir(p_dir):
      try:
        os.makedirs(p_dir, mode=0o0750)
      except Exception as l_error:
        raise error.XtdError(__name__, "unable to create output directory '%s' : %s",
                             p_dir, str(l_error))

  # pylint: disable=unused-argument
  def _write(self, p_param, p_oldValue, p_newValue):
    l_path = os.path.join(self.m_adminDir, p_param.m_name)
    try:
      with open(l_path, mode="w") as l_file:
        l_file.write(json.dumps(p_newValue))
    except (IOError, ValueError, TypeError) as l_error:
      raise error.XtdError(__name__, "unable to write param '%s' to file '%s', %s",
                           p_param.m_name, l_path, str(l_error))

  def _load(self, p_param):
    l_path = os.path.join(self.m_adminDir, p_param.m_name)
    if os.path.isfile(l_path):
      try:
        with open(l_path, mode="r") as l_file:
          l_content = l_file.read()
          l_value   = json.loads(l_content)
          p_param.set(l_value)
      except (IOError, ValueError, TypeError) as l_error:
        raise error.XtdError(__name__,
                             "unable to load param '%s' from value file '%s' : %s",
                             p_param.m_name, l_path, str(l_error))

  def register(self, p_name, p_value, p_callbacks=None, p_sync=False):
    l_param = Param(p_name, p_value, p_callbacks)
    return self.register_param(l_param, p_sync)

  def register_param(self, p_param, p_sync=False):
    if p_param.m_name in self.m_params:
      raise error.XtdError(__name__, "already defined parameter '%s'",
                           p_param.m_name)
    if p_sync:
      self._load(p_param)
      p_param.listen(self._write)
    self.m_params[p_param.m_name] = p_param
    return self

  def get_names(self):
    return sorted(list(self.m_params.keys()))

  def get_param(self, p_name):
    if not p_name in self.m_params:
      raise error.XtdError(__name__, "unregistered paramter '%s'" % p_name)
    return self.m_params[p_name]

  def get(self, p_name):
    return self.get_param(p_name).get()

  def set(self, p_name, p_value):
    return self.get_param(p_name).set(p_value)

  def listen(self, p_name, p_listener):
    return self.get_param(p_name).listen(p_listener)

# Local Variables:
# ispell-local-dictionary: "american"
# End:
