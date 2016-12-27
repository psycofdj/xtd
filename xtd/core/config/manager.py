# -*- coding: utf-8
# pylint: disable=unused-import,deprecated-module
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import re
import json
import optparse
import sys
from future.utils    import with_metaclass

from .formatter        import IndentedHelpFormatterWithNL
from ..error           import ConfigValueError, ConfigError
from ..                import mixin

#------------------------------------------------------------------#

class Option(object):
  """ Option object for :py:class:`ConfigManager`

  Available option properties:

  config
    Allow option to be read from configuration file, default ``True``

  cmdline
    Allow option to be read from command line, default ``True``

  default
    Internal default value for option, default ``None``

  valued
    Expects a value for option. Default ``True`` if default value profived.
    For non-valued options, default value is ``False`` and reading them
    from command line will store a ``True`` value

  description
    Option description to display on usage message

  checks
    Array of functions to validate option value. You may provide a single
    function. Default ``[]``. See :py:mod:`xtd.core.config.checkers` for
    standard check functions.

  longopt
    Override long option name. Long options has be be unique. Default ``--<section>-<name>``.

  mandatory
    Option is mandatory on command line, often used with non-valued options. Default
    ``False``

  Note:

    Provided check callback must respect the following signature :

    .. code-block:: python

      def function(p_section, p_section, p_value)

    They must return the input ``p_value`` (possible possibly trans-typed)
    and raise :py:exc:`~xtd.core.error.ConfigError` if value is
    rejected

    See :py:mod:`xtd.core.config.checkers` for standard check functions.

  Args:
    p_section (str): option's section name
    p_name (str): option's name
    p_props (dict) : option definition


  Raises:
    xtd.core.error.ConfigError: encountered unknown property

  """
  def __init__(self, p_section, p_name, p_prop=None):
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

    if p_prop is not None:
      self._update(p_prop)

  def _update(self, p_props):
    l_keys = [ x[2:] for x in dir(self) if x[0:2] == "m_" ]

    for c_key,c_val in p_props.items():
      if not c_key in l_keys:
        raise ConfigError("invalid option property '%s'" % c_key)
      if c_key == "checks" and not isinstance(c_val, list):
        c_val = [ c_val ]
      setattr(self, "m_%s" % c_key, c_val)

    if self.m_default != None:
      self.m_valued = True
    if not self.m_valued:
      self.m_default = False

  def validate(self, p_value):
    for c_check in self.m_checks:
      p_value = c_check(self.m_section, self.m_name, p_value)
    return p_value

class ConfigManager(with_metaclass(mixin.Singleton, object)):
  """Unified command-line & file config option manager

  The main user methods are :

  * :py:meth:`register_section`
  * :py:meth:`get`
  * :py:meth:`set_usage`


  Main documentation for option definition : :py:class:`Option`

  Attributes:
    __metaclass__ (:py:class:`xtd.core.mixin.Singleton`) : makes this object a singleton
  """

  def __init__(self):
    self.m_data      = {}
    self.m_options   = []
    self.m_sections  = {}
    self.m_usage     = "usage: %prog [options]"
    self.m_cmdParser = None
    self.m_cmdOpts   = None
    self.m_cmdArgs   = []

  def register_section(self, p_section, p_title, p_options):
    """ Register a set of options to a given section

    See :py:class:`Option` for full documentation of option properties

    Args:
      p_section (str): section tag
      p_title (str): the section title in the command-line usage
      p_options (list of dict): options definition

    Returns:
     ConfigManager: self

    Raises:
      xtd.core.error.ConfigError: invalid option definition
    """
    self.m_sections[p_section] = p_title
    for c_opt in p_options:
      if not "name" in c_opt:
        raise ConfigError("missing mandatory option property 'name'")
      self.register(p_section, c_opt["name"], c_opt)
    return self

  def register(self, p_section, p_name, p_props):
    """ Register an option in a specific section

    See :py:class:`Option` for full documentation of option properties

    Args:
      p_name (str): option name
      p_section (str): section name
      p_props (dict): option properties

    Returns:
     ConfigManager: self
    """
    l_option = Option(p_section, p_name, p_props)
    self.m_options.append(l_option)
    return self

  def sections(self):
    """ Get sections tags

    Returns:
      (list): array of str of all section names
    """
    return list(self.m_data.keys())

  def section_exists(self, p_section):
    """ Indicates if specified section has been registered

    Args:
      p_section (str): section name

    Returns:
      bool : true is ``p_section`` is registered
    """
    return p_section in self.m_data

  def options(self, p_section):
    """ Get the list of all registered option names for specefic a section

    Args:
      p_section (str): section name

    Raises:
      xtd.core.error.ConfigError: ``p_section`` not registered

    Returns:
      list: array of str of option names
    """
    if not p_section in self.m_data:
      raise ConfigError("section '%s' doesn't exist" % p_section)
    return list(self.m_data[p_section].keys())

  def option_exists(self, p_section, p_name):
    """ Indicates if specified option has been registered in section

    Args:
      p_section (str): section name
      p_option (str): option name

    Returns:
      bool : true is ``p_section`` is registered and contains ``p_option``
    """
    if not p_section in self.m_data:
      return False
    return p_name in self.m_data[p_section].keys()

  def get(self, p_section, p_name):
    """ Get option value

    Args:
      p_section (str): section name
      p_option (str): option name

    Raises:
      xtd.core.error.ConfigValueError: section/option not found

    Returns:
      (undefined): current option value
    """
    if not p_section in self.m_data or not p_name in self.m_data[p_section]:
      raise ConfigValueError(p_section, p_name, "unknown configuration entry")
    return self.m_data[p_section][p_name]

  def set(self, p_section, p_name, p_value):
    """set option value

    Warning:
      This method stores the input value immediately without validating
      it against option's checks.

    Args:
      p_section (str): section name
      p_option (str): option name

    Raises:
      xtd.core.error.ConfigValueError: section/option not found
    """
    if not p_section in self.m_data or not p_name in self.m_data[p_section]:
      raise ConfigValueError(p_section, p_name, "unknown configuration entry")
    self.m_data[p_section][p_name] = p_value

  def help(self, p_file=None):
    """ Display command line help message

    Args:
      p_file (file): output stream, defaults to sys.stdout
    """
    self.m_cmdParser.print_help(p_file)

  def initialize(self):
    """ Initializes object

    Usually called by :py:class:`~xtd.core.application.Application` object.
    """
    self.m_cmdParser = None
    self.m_cmdOpts   = None
    self.m_cmdArgs   = []
    self.m_data      = {}
    self._load_data()
    self._cmd_parser_create()

  def parse(self, p_argv=None):
    """ Parses command line and file options

    Usually called by :py:class:`~xtd.core.application.Application` object.

    Args:
      p_argv (list of str) : list of command line arguments
    """
    if p_argv is None:
      p_argv = sys.argv
    self._cmd_parser_load(p_argv)
    self._file_parser_load()

  def get_name(self):
    """Get parsed application name ``sys.argv[0]``

    Returns:
      str: program's ``sys.argv[0]``
    """
    return self.m_cmdArgs[0]

  def get_args(self):
    """Get command line post-parse remaining options

    Returns:
      list: unparsed command line options
    """
    return self.m_cmdArgs[1:]

  def set_usage(self, p_usage):
    """Set command line usage message

    See :py:class:`optparse.OptionParser`

    Args:
      p_usage (str): usage string
    """
    self.m_usage = p_usage


  def _get_option(self, p_section, p_name):
    l_values = [ x for x in self.m_options if x.m_section == p_section and x.m_name == p_name ]
    if not len(l_values):
      raise ConfigValueError(p_section, p_name, "unknown configuration entry")
    return l_values[0]

  def _load_data(self):
    for c_option in self.m_options:
      if not c_option.m_section in self.m_data:
        self.m_data[c_option.m_section] = {}
      self.m_data[c_option.m_section][c_option.m_name] = c_option.m_default

  @staticmethod
  def _cmd_attribute_name(p_section, p_option):
    return "parse_%(section)s_%(key)s" % {
      "section" : p_section,
      "key"     : p_option.replace("-", "_")
    }

  def _cmd_parser_create(self):
    self.m_cmdParser = optparse.OptionParser(usage=self.m_usage,
                                             formatter=IndentedHelpFormatterWithNL())
    l_sections = set([ x.m_section for x in self.m_options ])
    for c_section in sorted(l_sections):
      l_sectionName = self.m_sections.get(c_section, "")
      l_group       = optparse.OptionGroup(self.m_cmdParser, l_sectionName)
      l_options     = [ x for x in self.m_options if x.m_section == c_section and x.m_cmdline ]
      for c_opt in l_options:
        l_args = []
        l_kwds = {
          "help"    : c_opt.m_description,
          "default" : None,
          "action"  : "store",
          "dest"    : self._cmd_attribute_name(c_section, c_opt.m_name)
        }
        if not c_opt.m_valued:
          l_kwds["action"] = "store_true"
        else:
          l_kwds["metavar"] = "ARG"
        if c_opt.m_default != None:
          l_kwds["help"] += " [default:%s]" % str(c_opt.m_default)
        l_args.append(c_opt.m_longopt)
        l_group.add_option(*l_args, **l_kwds)
      self.m_cmdParser.add_option_group(l_group)

  def _cmd_parser_load(self, p_argv):
    self.m_cmdOpts, self.m_cmdArgs = self.m_cmdParser.parse_args(p_argv)
    for c_option in [ x for x in self.m_options if x.m_cmdline ]:
      l_attribute = self._cmd_attribute_name(c_option.m_section, c_option.m_name)
      l_value     = getattr(self.m_cmdOpts, l_attribute)
      if l_value != None:
        l_value = self._validate(c_option.m_section, c_option.m_name, l_value)
        self.set(c_option.m_section, c_option.m_name, l_value)
      elif c_option.m_mandatory:
        raise ConfigValueError(c_option.m_section, c_option.m_name, "option is mandatory")

  def option_cmdline_given(self, p_section, p_option):
    if self.option_exists(p_section, p_option):
      l_name  = self._cmd_attribute_name(p_section, p_option)
      l_value = getattr(self.m_cmdOpts, l_name)
      return l_value != None
    return False

  def _file_parser_load(self):
    if not self.section_exists("general") or not self.option_exists("general", "config-file"):
      return
    l_fileName = self._validate("general", "config-file")
    try:
      with open(l_fileName, mode="r", encoding="utf-8") as l_file:
        l_lines = [ x for x in l_file.readlines() if not re.match(r"^\s*//.*" ,x) ]
        l_content = "\n".join(l_lines)
        l_data = json.loads(l_content)
    except Exception as l_error:
      l_message = "invalid json configuration : %s" % str(l_error)
      raise ConfigValueError("general", "config-file", l_message)

    for c_section, c_data in l_data.items():
      for c_option, c_value in c_data.items():
        l_option = self._get_option(c_section, c_option)
        if l_option.m_config and not self.option_cmdline_given(c_section, c_option):
          l_value = self._validate(c_section, c_option, c_value)
          self.set(c_section, c_option, l_value)

  def _validate(self, p_section, p_name, p_value = None):
    if p_value is None:
      p_value = self.get(p_section, p_name)
    l_option = self._get_option(p_section, p_name)
    return l_option.validate(p_value)

# Local Variables:
# ispell-local-dictionary: "american"
# End:
