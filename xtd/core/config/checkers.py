# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import urllib
import json
import os
import re
import socket
from functools import partial

from ..error.exception import *

#------------------------------------------------------------------#


def check_file(p_section, p_name, p_value, p_read = False, p_write = False, p_execute = False):
  l_absFilePath = os.path.abspath(p_value)
  if os.path.isdir(l_absFilePath):
    raise ConfigValueFileException(p_section, p_name, l_absFilePath)
  if not os.path.isfile(l_absFilePath):
    if p_read or not check_mode(os.path.dirname(l_absFilePath), p_write=True):
      raise ConfigValueFileModeException(p_section, p_name, p_value, p_read, p_write, p_execute)
  else:
    if not check_mode(l_absFilePath, p_read, p_write, p_execute):
      raise ConfigValueFileModeException(p_section, p_name, p_value, p_read, p_write,p_execute)
  return p_value

# ------------------------------------------------------------------------- #

def check_dir(p_section, p_name, p_value, p_read = False, p_write = False, p_execute = False):
  l_absDirPath = os.path.abspath(p_value)
  if not os.path.isdir(l_absDirPath):
    raise ConfigValueDirException(p_section, p_name, l_absDirPath)
  if not check_mode(l_absDirPath, p_read, p_write, p_execute):
    raise ConfigValueDirModeException(p_section, p_name, p_value, p_read, p_write, p_execute)
  return p_value

# ------------------------------------------------------------------------- #

def check_int(p_section, p_name, p_value, p_min = None, p_max = None):
  try:
    l_intValue = int(p_value)
  except ValueError:
    raise ConfigValueTypeException(p_section, p_name, p_value, ConfigTypeException.INT)
  if (p_min != None) and (l_intValue < p_min):
    raise ConfigValueLimitsException(p_section, p_name, l_value, p_min, p_max)
  if (p_max != None) and (l_intValue > p_max):
    raise ConfigValueLimitsException(p_section, p_name, l_value, p_min, p_max)
  return l_intValue

# ------------------------------------------------------------------------- #

def check_float(p_section, p_name, p_value, p_min = None, p_max = None):
  try:
    l_floatValue = float(p_value)
  except ValueError:
    raise ConfigValueTypeException(p_section, p_name, p_value, ConfigTypeException.FLOAT)
  if (p_min != None) and (l_floatValue < p_min):
    raise ConfigValueLimitsException(p_section, p_name, p_value, p_min, p_max)
  if (p_max != None) and (l_floatValue > p_max):
    raise ConfigValueLimitsException(p_section, p_name, p_value, p_min, p_max)
  return l_floatValue

# ------------------------------------------------------------------------- #

def check_bool(p_section, p_name, p_value):
  if ((p_value.lower() == 'true') or
      (p_value.lower() == 'yes') or
      (p_value.lower() == 'on')):
    return True

  if ((p_value.lower() == 'false') or
      (p_value.lower() == 'no') or
      (p_value.lower() == 'off')):
    return False
  raise ConfigValueTypeException(p_section, p_name, l_value, ConfigTypeException.BOOL)

# ------------------------------------------------------------------------- #

def check_enum(p_section, p_name, p_value, p_values):
  if not p_value in p_values:
    raise ConfigValueEnumException(p_section, p_name, p_value, p_values)
  return p_value

# ------------------------------------------------------------------------- #

def check_mode(p_path, p_read = False, p_write = False, p_execute = False):
  if not os.path.exists(p_path):
      return False
  l_uid = os.getuid()
  l_gid = os.getgid()
  l_dir_stat       = os.stat(p_path)
  l_dir_uid        = l_dir_stat.st_uid
  l_dir_gid        = l_dir_stat.st_gid
  l_dir_mode       = l_dir_stat.st_mode
  l_dir_user_mode  = l_dir_mode & 0o0700
  l_dir_group_mode = l_dir_mode & 0o0070
  l_dir_other_mode = l_dir_mode & 0o0007
  if l_uid == l_dir_uid:
    if p_read and not (l_dir_user_mode & 0o0400):
      return False
    if p_write and not (l_dir_user_mode & 0o0200):
      return False
    if p_execute and not (l_dir_user_mode & 0o0100):
      return False
  elif l_gid == l_dir_gid:
    if p_read and not (l_dir_group_mode & 0o0040):
      return False
    if p_write and not (l_dir_group_mode & 0o0020):
      return False
    if p_execute and not (l_dir_group_mode & 0o0010):
      return False
  else:
    if p_read and not (l_dir_other_mode & 0o0004):
      return False
    if p_write and not (l_dir_other_mode & 0o0002):
      return False
    if p_execute and not (l_dir_other_mode & 0o0001):
      return False
  return True

# ------------------------------------------------------------------------- #


def check_mail(p_section, p_name, p_value):
  l_mail_regexp = "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}"
  if not re.match("^%s$" % l_mail_regexp, p_value):
    if not re.match("^[^<]*<%s>$" % l_mail_regexp, p_value):
      l_message = "value '%s' is not an email address" % p_value
      raise ConfigValueException(p_section, p_name, l_message)
  return p_value

# ------------------------------------------------------------------------- #

def check_array(p_section, p_name, p_value, p_check = None):
  l_res = []
  for c_val in p_value.split(","):
    if p_check:
      l_res.append(p_check(p_section, p_name, c_val))
    else:
      l_res.append(c_val)
  return l_res

# ------------------------------------------------------------------------- #

def check_host(p_section, p_name, p_value):
  try:
    socket.gethostbyname(p_value)
  except socket.gaierror:
    l_message = "host '%s' is not valid" % l_value
    raise ConfigValueException(p_section, p_name, l_message)
  return p_value

# ------------------------------------------------------------------------- #

def check_json(p_section, p_name, p_value):
  try:
    return json.loads(p_value)
  except Exception as l_error:
    raise ConfigValueException(p_section, p_name, "invalid json : %s" % str(l_error))

# ------------------------------------------------------------------------- #

def check_socket(p_section, p_name, p_value, p_schemes = []):
  l_data = urllib.parse.urlparse(p_value)
  if len(p_schemes) and (not l_data.scheme in p_schemes):
    raise ConfigValueException(p_section, p_name, "invalid url '%s', scheme '%s' not in '%s'" % (p_value, l_data.scheme, str(p_schemes)))
  if not l_data.port:
    raise ConfigValueException(p_section, p_name, "invalid url '%s', port is mandatory" % p_value)
  return p_value

# ------------------------------------------------------------------------- #

def is_file(*p_args, **p_kwds):
  return partial(check_file, *p_args, **p_kwds)
def is_dir(*p_args, **p_kwds):
  return partial(check_dir, *p_args, **p_kwds)
def is_int(*p_args, **p_kwds):
  return partial(check_int, *p_args, **p_kwds)
def is_float(*p_args, **p_kwds):
  return partial(check_float, *p_args, **p_kwds)
def is_bool(*p_args, **p_kwds):
  return partial(check_bool, *p_args, **p_kwds)
def is_enum(*p_args, **p_kwds):
  return partial(check_enum, *p_args, **p_kwds)
def is_mail(*p_args, **p_kwds):
  return partial(check_mail, *p_args, **p_kwds)
def is_array(*p_args, **p_kwds):
  return partial(check_array, *p_args, **p_kwds)
def is_host(*p_args, **p_kwds):
  return partial(check_host, *p_args, **p_kwds)
def is_json(*p_args, **p_kwds):
  return partial(check_json, *p_args, **p_kwds)
def is_socket(*p_args, **p_kwds):
  return partial(check_socket, *p_args, **p_kwds)

# ------------------------------------------------------------------------- #


