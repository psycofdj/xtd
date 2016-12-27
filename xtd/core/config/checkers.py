# -*- coding: utf-8
#------------------------------------------------------------------#

__author__ = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#
try:
  from urlparse import urlparse
except ImportError:
  from urllib.parse import urlparse

import json
import os
import re
import socket
from functools import partial

from ..error import ConfigValueFileError, ConfigValueFileModeError
from ..error import ConfigValueDirError, ConfigValueDirModeError
from ..error import ConfigValueTypeError, ConfigValueLimitsError
from ..error import ConfigValueEnumError, ConfigValueError
from ..tools import url

#------------------------------------------------------------------#


def check_file(p_section, p_name, p_value, p_read=False, p_write=False, p_execute=False):
  """check that given config parameter is a valid file with given rwx attributes

  If p_value does not exists and only write attribute is requested,
  the function checks that the file can be created in its parent directory

  Args:
      p_section (str): parameter section name
      p_name (str): parameter name
      p_value (str): parameter value
      p_read (str): target file should be readable, default ``False``
      p_write (str): target file should be writable, default ``False``
      p_execute (str): target file should be executable, default ``False``

  Returns:
      bool: file absolute path

  Raises:
     ConfigValueFileError: p_value is a directory
     ConfigValueFileModeError: p_value dosen't meet requested rwx attributes
  """
  l_absFilePath = os.path.expanduser(p_value)
  l_absFilePath = os.path.abspath(l_absFilePath)

  if os.path.isdir(l_absFilePath):
    raise ConfigValueFileError(p_section, p_name, l_absFilePath)

  if not os.path.exists(l_absFilePath):
    if p_read or not _check_mode(os.path.dirname(l_absFilePath), p_write=True):
      raise ConfigValueFileModeError(p_section, p_name, p_value, p_read, p_write, p_execute)
  else:
    if not _check_mode(l_absFilePath, p_read, p_write, p_execute):
      raise ConfigValueFileModeError(p_section, p_name, p_value, p_read, p_write, p_execute)
  return l_absFilePath

# ------------------------------------------------------------------------- #

def check_dir(p_section, p_name, p_value, p_read=False, p_write=False, p_execute=False):
  """check that given value is a valid directory for given rwx attributes

  Args:
      p_section (str): parameter section name
      p_name (str): parameter name
      p_value (str): target directory path
      p_read (str): target file should be readable, default ``False``
      p_write (str): target file should be writable, default ``False``
      p_execute (str): target file should be executable, default ``False``

  Returns:
      bool: directory absolute path

  Raises:
     ConfigValueDirError: p_value is not a directory
     ConfigValueDirModeError: directory  doesn't meet requested rwx attributes
  """
  l_absDirPath = os.path.expanduser(p_value)
  l_absDirPath = os.path.abspath(l_absDirPath)
  if not os.path.isdir(l_absDirPath):
    raise ConfigValueDirError(p_section, p_name, l_absDirPath)
  if not _check_mode(l_absDirPath, p_read, p_write, p_execute):
    raise ConfigValueDirModeError(p_section, p_name, p_value, p_read, p_write, p_execute)
  return l_absDirPath

# ------------------------------------------------------------------------- #

def check_int(p_section, p_name, p_value, p_min=None, p_max=None):
  """check that given value is a valid integer

  If not None, the function will insure that value fits the requested
  minimum and maximum parameters

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): target value
    p_min (int): minimum accepted value, default : ``None``
    p_max (int): maximum accepted value, default : ``None``

  Returns:
    int: integer converted value

  Raises:
    ConfigValueTypeError: value is not an integer, nor a int-convertible string
    ConfigValueLimitsError: value doesn't match requested min and max constraints
  """
  if isinstance(p_value, int) and not isinstance(p_value, bool):
    l_value = p_value
  else:
    if isinstance(p_value, str):
      try:
        l_value = int(p_value)
      except ValueError:
        raise ConfigValueTypeError(p_section, p_name, p_value, ConfigValueTypeError.INT)
    else:
      raise ConfigValueTypeError(p_section, p_name, p_value, ConfigValueTypeError.INT)

  if (p_min != None) and (l_value < p_min):
    raise ConfigValueLimitsError(p_section, p_name, l_value, p_min, p_max)
  if (p_max != None) and (l_value > p_max):
    raise ConfigValueLimitsError(p_section, p_name, l_value, p_min, p_max)
  return l_value

# ------------------------------------------------------------------------- #

def check_float(p_section, p_name, p_value, p_min=None, p_max=None):
  """check that given value is a valid float

  Same as :py:func:`check_int`

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): target value
    p_min (float): minimum accepted value, default : None
    p_max (float): maximum accepted value, default : None

  Raises:
    ConfigValueTypeError: value is not an integer, nor a int-convertible string
    ConfigValueLimitsError: value doesn't match requested min and max constraints

  Returns:
    float: float converted value
  """
  if isinstance(p_value, float):
    l_value = p_value
  else:
    if isinstance(p_value, str):
      try:
        l_value = float(p_value)
      except ValueError:
        raise ConfigValueTypeError(p_section, p_name, p_value, ConfigValueTypeError.FLOAT)
    else:
      raise ConfigValueTypeError(p_section, p_name, p_value, ConfigValueTypeError.FLOAT)
  if (p_min != None) and (l_value < p_min):
    raise ConfigValueLimitsError(p_section, p_name, l_value, p_min, p_max)
  if (p_max != None) and (l_value > p_max):
    raise ConfigValueLimitsError(p_section, p_name, l_value, p_min, p_max)
  return l_value

# ------------------------------------------------------------------------- #

def check_bool(p_section, p_name, p_value):
  """check that given value is a valid boolean

  Valid boolean are :
    * native bool object
    * str object in the following list : ``["on", "yes", "true", "off", "no", "false"]``
      (case insensitive)

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): target value

  Raises:
    ConfigValueTypeError: invalid input boolean

  Returns:
    bool: converted value
  """
  if isinstance(p_value, bool):
    return p_value
  if not isinstance(p_value, str):
    raise ConfigValueTypeError(p_section, p_name, p_value, ConfigValueTypeError.BOOL)
  if ((p_value.lower() == 'true') or
      (p_value.lower() == 'yes') or
      (p_value.lower() == 'on')):
    return True
  if ((p_value.lower() == 'false') or
      (p_value.lower() == 'no') or
      (p_value.lower() == 'off')):
    return False
  raise ConfigValueTypeError(p_section, p_name, p_value, ConfigValueTypeError.BOOL)

# ------------------------------------------------------------------------- #

def check_enum(p_section, p_name, p_value, p_values):
  """ check that given value matches a set of possible values

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): input value
    p_values (list): set of possible authorized values

  Raises:
    ConfigValueEnumError: value not found in possible values

  Returns:
    bool: input value
  """
  if not p_value in p_values:
    raise ConfigValueEnumError(p_section, p_name, p_value, p_values)
  return p_value

# ------------------------------------------------------------------------- #

def _check_mode(p_path, p_read=False, p_write=False, p_execute=False):
  if not os.path.exists(p_path):
    return False
  l_mode = os.F_OK
  if p_read:
    l_mode = l_mode | os.R_OK
  if p_write:
    l_mode = l_mode | os.W_OK
  if p_execute:
    l_mode = l_mode | os.X_OK
  if os.access(p_path, l_mode):
    return True
  return False

# ------------------------------------------------------------------------- #


def check_mail(p_section, p_name, p_value):
  """ check that given value is a syntactical valid mail address

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): input value

  Raises:
    ConfigValueValueError: value not an email

  Returns:
    bool: input value
  """
  l_mailRgx = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}"
  if not re.match("^%s$" % l_mailRgx, p_value):
    if not re.match("^[^<]*<%s>$" % l_mailRgx, p_value):
      l_message = "value '%s' is not an email address" % p_value
      raise ConfigValueError(p_section, p_name, l_message)
  return p_value

# ------------------------------------------------------------------------- #

def check_array(p_section, p_name, p_value, p_check=None, p_delim=","):
  """ check that given value is convertible to array

  A str value is converted to array by splitting each comma separated
  elements

  Additionally, the function checks that each elements meets ``p_check``
  function requirement.

  Example:

  .. code-block:: python

     l_value = "1,2,3,4,5"
     l_value = check_array(l_value, check_float)
     print(l_value)
     # [1.0, 2.0, 3.0, 4.0]

     l_value = "on,on;off,no;true,false"
     l_value = check_array(l_value, is_array(p_check=check_bool), p_delim=";")
     print(l_value)
     # [[True, True], [False, False], [True, False]]

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): input value
    p_check (function): sub-checker to call on each elements, default ``None``
    p_delim (str) : used as delimiter to split  given str value

  Raises:
    ConfigValueValueError: value not an email

  Returns:
    list: array-converted value
  """
  l_res   = []
  l_value = p_value
  if not isinstance(l_value, list):
    l_value = l_value.split(p_delim)
  for c_val in l_value:
    if p_check:
      l_res.append(p_check(p_section, p_name, c_val))
    else:
      l_res.append(c_val)
  return l_res

# ------------------------------------------------------------------------- #

def check_host(p_section, p_name, p_value):
  """ check that value is locally resolvable hostname

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): input value

  Raises:
    ConfigValueValueError: value not an hostname

  Returns:
    str: input value
  """
  try:
    socket.gethostbyname(p_value)
  except socket.gaierror:
    l_message = "host '%s' is not valid" % p_value
    raise ConfigValueError(p_section, p_name, l_message)
  return p_value

# ------------------------------------------------------------------------- #

def check_json(p_section, p_name, p_value):
  """ check that value is a valid json

  if value is str, performs a :py:func:json.loads

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): input value

  Raises:
    ConfigValueValueError: value not a json

  Returns:
    dict: dict-converted value
  """
  if isinstance(p_value, dict):
    return p_value

  try:
    p_value = json.loads(p_value)
  except (ValueError, TypeError) as l_error:
    raise ConfigValueError(p_section, p_name, "invalid json : %s" % str(l_error))
  return p_value

# ------------------------------------------------------------------------- #

def check_socket(p_section, p_name, p_value, p_schemes=None, p_checkUnix=False):
  """ check that value is a valid socket url

  Args:
    p_section (str): parameter section name
    p_name (str): parameter name
    p_value (str): input value
    p_scheme (list) : valid url schemes
    p_checkUnix (bool) : authorize "unix+//<file>/path" based url

  Raises:
    ConfigValueValueError: value a valid socket url

  Returns:
    str: input value
  """
  if p_schemes is None:
    p_schemes = []
  l_parts = urlparse(p_value)
  if len(p_schemes) and (not l_parts[0] in p_schemes):
    l_format = "invalid url '%s', scheme '%s' not in '%s'"
    l_message = l_format % (p_value, l_parts[0], str(p_schemes))
    raise ConfigValueError(p_section, p_name, l_message)

  l_result = url.parse_unix(p_value)
  if p_checkUnix and l_result[1]:
    check_file(p_section, p_name, l_result[1], p_read=True, p_write=True)
  return p_value

# ------------------------------------------------------------------------- #

def is_file(*p_args, **p_kwds):
  """Currified version of :py:func:`check_file`"""
  return partial(check_file, *p_args, **p_kwds) # pragma: no cover
def is_dir(*p_args, **p_kwds):
  """Currified version of :py:func:`check_dir`"""
  return partial(check_dir, *p_args, **p_kwds) # pragma: no cover
def is_int(*p_args, **p_kwds):
  """Currified version of :py:func:`check_int`"""
  return partial(check_int, *p_args, **p_kwds) # pragma: no cover
def is_float(*p_args, **p_kwds):
  """Currified version of :py:func:`check_float`"""
  return partial(check_float, *p_args, **p_kwds) # pragma: no cover
def is_bool(*p_args, **p_kwds):
  """Currified version of :py:func:`check_bool`"""
  return partial(check_bool, *p_args, **p_kwds) # pragma: no cover
def is_enum(*p_args, **p_kwds):
  """Currified version of :py:func:`check_enum`"""
  return partial(check_enum, *p_args, **p_kwds) # pragma: no cover
def is_mail(*p_args, **p_kwds):
  """Currified version of :py:func:`check_mail`"""
  return partial(check_mail, *p_args, **p_kwds) # pragma: no cover
def is_array(*p_args, **p_kwds):
  """Currified version of :py:func:`check_array`"""
  return partial(check_array, *p_args, **p_kwds) # pragma: no cover
def is_host(*p_args, **p_kwds):
  """Currified version of :py:func:`check_host`"""
  return partial(check_host, *p_args, **p_kwds) # pragma: no cover
def is_json(*p_args, **p_kwds):
  """Currified version of :py:func:`check_json`"""
  return partial(check_json, *p_args, **p_kwds) # pragma: no cover
def is_socket(*p_args, **p_kwds):
  """Currified version of :py:func:`check_socket`"""
  return partial(check_socket, *p_args, **p_kwds) # pragma: no cover

# ------------------------------------------------------------------------- #


# Local Variables:
# ispell-local-dictionary: "american"
# End:
