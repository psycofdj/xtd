# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

from .manager import ConfigManager

#------------------------------------------------------------------#

def get(p_section, p_name):
  return ConfigManager().get(p_section, p_name)

def set(p_section, p_name, p_value):
  return ConfigManager().set(p_section, p_name, p_value)

def sections():
  return ConfigManager().sections()

def section_exists(p_section):
  return ConfigManager().section_exists(p_section)

def options(p_section):
  return ConfigManager().options(p_section)

def option_exists(p_section, p_name):
  return ConfigManager().option_exists(p_section, p_name)
