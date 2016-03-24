# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import configparser
import optparse
import sys


from .formatter        import IndentedHelpFormatterWithNL
from ..error.exception import ConfigValueException
from ..                import mixin

#------------------------------------------------------------------#

class Option:
  def __init__(self, p_section, p_name, p_prop = {}):
    self.m_section     = p_section
    self.m_name        = p_name
    self.m_config      = True
    self.m_cmdline     = True
    self.m_default     = None
    self.m_valued      = False
    self.m_description = "undocumented option"
    self.m_checks      = []
    self.m_longopt     = "--%s-%s" % (p_section, p_name)
    self.m_mandatory   = None
    self.update(p_prop)

  def update(self, p_props):
    for c_key in [ x for x in dir(self) if x[0:2] == "m_" ]:
      c_key = c_key[2:]
      if c_key in p_props:
        if c_key == "checks" and type(p_props[c_key]) != type([]):
          p_props[c_key] = [p_props[c_key]]
        setattr(self, "m_%s" % c_key, p_props[c_key])

    if self.m_default != None:
      self.m_valued = True

  def addCheck(self, p_functor):
    self.m_checks.append(p_functor)

  def validate(self, p_value):
    for c_check in self.m_checks:
      p_value = c_check(self.m_section, self.m_name, p_value)
    return p_value

class ConfigManager(metaclass=mixin.Singleton):
  def __init__(self):
    self.m_data          = {}
    self.m_options       = []
    self.m_sections      = {}
    self.m_usage         = "usage: %prog [options]"
    self.m_file_parser   = None
    self.m_cmd_parser    = None

  def register_section(self, p_section, p_title, p_options):
    self.m_sections[p_section] = p_title
    for c_opt in p_options:
      self.register(p_section, c_opt["name"], c_opt)
    return self

  def register(self, p_section, p_name, p_props):
    l_option = Option(p_section, p_name, p_props)
    self.m_options.append(l_option)
    if not p_section in self.m_data:
      self.m_data[p_section] = {}
    self.m_data[p_section][p_name] = l_option.m_default
    return self

  def sections(self):
    return self.m_data.keys()

  def section_exists(self, p_section):
    return p_section in self.m_data

  def options(self, p_section):
    if not p_section in self.m_data:
      raise ConfigException(p_section, p_name, "section '%s' dosent exist" % p_section)
    return self.m_data[p_section].keys()

  def option_exists(self, p_section, p_name):
    if not p_section in self.m_data:
      raise ConfigException(p_section, p_name, "section '%s' dosent exist" % p_section)
    return p_name in self.m_data[p_section].keys()

  def get(self, p_section, p_name):
    if not p_section in self.m_data or not p_name in self.m_data[p_section]:
      raise ConfigValueException(p_section, p_name, "unknown configuration entry")
    return self.m_data[p_section][p_name];

  def set(self, p_section, p_name, p_value):
    if not p_section in self.m_data or not p_name in self.m_data[p_section]:
      raise ConfigValueException(p_section, p_name, "unknown configuration entry")
    self.m_data[p_section][p_name] = p_value;

  def help(self):
    self.m_cmd_parser.print_help()

  def initialize(self):
    self._cmd_parser_create()
    self._file_parser_create()

  def parse(self, p_argv = sys.argv):
    self._cmd_parser_load(p_argv)
    self._file_parser_load()

  def _get_option(self, p_section, p_name):
    l_values = [ x for x in self.m_options if x.m_section == p_section and x.m_name == p_name ]
    if not len(l_values):
      raise ConfigValueException(p_section, p_name, "unknown configuration entry")
    return l_values[0]

  def _cmd_parser_create(self):
    self.m_cmd_parser = optparse.OptionParser(usage=self.m_usage, formatter=IndentedHelpFormatterWithNL())
    l_sections = set([ x.m_section for x in self.m_options ])
    for c_section in sorted(l_sections):
      l_sectionName = self.m_sections.get(c_section, "")
      l_group       = optparse.OptionGroup(self.m_cmd_parser, l_sectionName)
      l_options     = [ x for x in self.m_options if x.m_section == c_section and x.m_cmdline ]
      for c_opt in l_options:
        l_args = []
        l_kwds = {
          "help"    : c_opt.m_description,
          "default" : None,
          "action"  : "store",
          "dest"    : "parse_%(section)s_%(key)s" % {
            "section" : c_section,
            "key"     : c_opt.m_name.replace('-', '_')
          }
        }
        if not c_opt.m_valued:
          l_kwds["action"] = "store_true"
        else:
          l_kwds["metavar"] = "ARG"
        if c_opt.m_default != None:
          l_kwds["help"] += " [default:%s]" % str(c_opt.m_default)
        l_args.append(c_opt.m_longopt)
        l_group.add_option(*l_args, **l_kwds)
      self.m_cmd_parser.add_option_group(l_group)

  def _cmd_parser_load(self, p_argv):
    l_opts, l_args = self.m_cmd_parser.parse_args(p_argv)
    for c_option in [ x for x in self.m_options if x.m_cmdline ]:
      l_name  = c_option.m_name.replace('-', '_')
      l_value = getattr(l_opts, "parse_%s_%s" % (c_option.m_section, l_name))
      if l_value:
        l_value = self._validate(c_option.m_section, c_option.m_name, l_value)
        self.set(c_option.m_section, c_option.m_name, l_value)

  def _file_parser_create(self):
    self.m_file_parser = configparser.SafeConfigParser()

  def _file_parser_load(self):
    l_file = self._validate("general", "config-file")
    self.m_file_parser.read(l_file)
    for c_section in self.m_file_parser.sections():
      for c_option in self.m_file_parser.options(c_section):
        l_value  = self.m_file_parser.get(c_section, c_option)
        l_value  = self._validate(c_section, c_option, l_value)
        self.set(c_section, c_option, l_value)

  def _validate(self, p_section, p_name, p_value = None):
    if p_value == None:
      p_value = self.get(p_section, p_name)
    l_option = self._get_option(p_section, p_name)
    return l_option.validate(p_value)



