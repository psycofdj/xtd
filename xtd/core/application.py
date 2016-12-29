# -*- coding: utf-8
# pylint: disable=unused-import
#------------------------------------------------------------------#
from __future__   import print_function

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import sys
from future.utils import with_metaclass

from .      import stat, logger, config, param, mixin
from .error import ConfigError, XtdError

#------------------------------------------------------------------#

class Application(with_metaclass(mixin.Singleton, object)):
  """XTD main application object

  Users must inherit this class :

  * register program's arguments in their ``__init__`` method
  * and optionally override :py:meth:`initialize`
  * override :py:meth:`process` and code their program behavior
  * call :py:meth:`execute` at top level


  ``p_name`` parameter is used for various purpose such as:

    * default usage
    * default --config-file value
    * default disk-synced parameters output directory path
    * default statistic disk output directory path


  Args:
    p_name (str): application's name (optional). Defaults to ``sys.argv[0]``

  Attributes:
    m_name (str): application's name

  """
  def __init__(self, p_name=None):
    self.m_name    = p_name
    self.m_argv    = []
    self.m_config  = config.manager.ConfigManager()
    self.m_stat    = None
    self.m_param   = None
    self.m_logger  = None
    if self.m_name is None:
      self.m_name = sys.argv[0]

    self.m_config.set_usage("%s [options]" % self.m_name)

    self.m_config.register_section("general", "General Settings", [{
      "name"        : "config-file",
      "default"     : "%(name)s/%(name)s.json" % {"name" : self.m_name},
      "description" : "use FILE as configuration file",
      "longopt"     : "--config-file",
      "checks"      : config.checkers.is_file(p_read=True)

    }])

    self.config().register_section("log", "Logging Settings", [{
      "name"        : "config",
      "default"     : {},
      "description" : "Logging configuration",
      "checks"      : config.checkers.is_json()
    },{
      "name"        : "override",
      "default"     : {},
      "description" : "override part of logging configuration",
      "checks"      : config.checkers.check_json
    }])

    self.config().register_section("stat", "Stats Settings", [{
      "name"        : "handlers",
      "default"     : ["disk"],
      "description" : """Enabled given stat output handler. Possibles values :\n
                         * disk : write counters to --stat-disk-directory
                                  path each --stat-disk-interval seconds\n
                         * http : post counters in json format to --stat-http-url
                                  url each --stat-http-interval seconds\n
                         Can specify a comma separated combinaison of theses values\n
      """,
      "checks"      : config.checkers.is_array(
        p_check=config.checkers.is_enum(p_values=["", "disk", "http"])
      )
    },{
      "name"        : "disk-directory",
      "default"     : "/tmp/snmp/%s/stat/" % self.m_name,
      "description" : "Destination directory for counter disk handler"
    },{
      "name"        : "disk-interval",
      "default"     : 50,
      "description" : "Interval in second between two disk outputs",
      "checks"      : config.checkers.is_int()
    },{
      "name"        : "http-url",
      "default"     : "http://localhost/counter",
      "description" : "Destination POST url for http stat handler"
    },{
      "name"        : "http-interval",
      "default"     : 50,
      "description" : "Interval in second between two http outputs",
      "checks"      : config.checkers.is_int()
    }])

    self.config().register_section("param", "Persistent parameter settings", [{
      "name"        : "directory",
      "default"     : "/tmp/snmp/%s/admin" % self.m_name,
      "description" : "Destination directory for admin persistent parameters"
    }])

  def config(self):
    """Get the :py:class:`~xtd.core.config.manager.ConfigManager` instance

    Returns:
      config.manager.ConfigManager: ConfigManager instance
    """
    return self.m_config

  def stat(self):
    """Get the :py:class:`~xtd.core.stat.manager.StatManager` instance

    Returns:
      stat.manager.StatManager: StatManager instance
    """
    return self.m_stat

  # pylint: disable=no-self-use
  def process(self):
    """Main application body

    The child class must override this method. Since default behavior
    is to log an error, you should not call parent's method

    Returns:
      int, bool: program's exit code and True if object should call stop method before
        joining

    """
    logger.info(__name__, "default process() method, you probably want to override it")
    return 1, True

  def initialize(self):
    """Initializes application

    Specifically:

      * application's configuration facility, See :py:mod:`xtd.core.config`
      * application's logging facility, See :py:mod:`xtd.core.logger`
      * application's memory parameters, See :py:mod:`xtd.core.param`
      * application's statistics, See :py:mod:`xtd.core.stat`

    Any child class that overrides this method should call
    ``super(Application, self).initialize()``
    """
    self._initialize_config()
    self._initialize_log()
    self._initialize_stat()
    self._initialize_param()

  def start(self):
    """Start background modules

    Any child class that overrides this method should call
    ``super(Application, self).start()`` or start
    :py:class:`~xtd.core.stat.manager.StatManager` by hand
    """
    self.m_stat.start()

  def stop(self):
    """Stop background modules

    Any child class that overrides this method should call
    ``super(Application, self).stop()`` or stop
    :py:class:`~xtd.core.stat.manager.StatManager` by hand
    """
    self.m_stat.stop()

  def join(self):
    """Join background modules

    Any child class that overrides this method should call
    ``super(Application, self).join()`` or join
    :py:class:`~xtd.core.stat.manager.StatManager` by hand
    """
    self.m_stat.join()


  def execute(self, p_argv=None):
    """Main application entry point

    Exits with code returned by :py:meth:`process`.

    .. note:: During the initializing phase :

      * Any :py:class:`~xtd.core.error.ConfigError` leads to the display
        of the error, followed by the program usage and ends with a ``sys.exit(1)``.
      * Any :py:class:`~xtd.core.error.XtdError` leads to the display
        of the error and ends with a ``sys.exit(1)``.

      During the process phase :

      * Any :py:class:`~xtd.core.error.XtdError` leads to the log
        of the error and ends with a ``sys.exit(1)``.

    Args:
      p_argv (list) : program's command-line argument. Defaults to None.
        If none, arguments are taken from :py:obj:`sys.argv`

    """
    if p_argv is None:
      p_argv = sys.argv
    self.m_argv = p_argv

    try:
      self.initialize()
    except ConfigError as l_error:
      print(l_error)
      self.m_config.help()
      sys.exit(1)
    except XtdError as l_error:
      print(l_error)
      sys.exit(1)

    try:
      logger.info(__name__, "starting process")
      self.start()
      l_code, l_stop = self.process()
      if l_stop:
        self.stop()
      self.join()
      logger.info(__name__, "process finished (status=%d)", l_code)
      sys.exit(l_code)
    except XtdError as l_error:
      logger.exception(__name__, "uncaught exception '%s', exit(1)", l_error)
      sys.exit(1)


  def _initialize_config(self):
    self.m_config.initialize()
    self.m_config.parse(self.m_argv)

  def _initialize_stat(self):
    self.m_stat = stat.manager.StatManager()
    l_outputters = self.config().get("stat", "handlers")
    for c_name in l_outputters:
      if c_name == "disk":
        l_dir      = config.get("stat", "disk-directory")
        l_interval = config.get("stat", "disk-interval")
        l_disk     = stat.handler.DiskHandler(l_dir, l_interval)
        self.m_stat.register_handler(l_disk)
      elif c_name == "http":
        l_url      = config.get("stat", "http-url")
        l_interval = config.get("stat", "http-interval")
        l_http      = stat.handler.HttpHandler(l_url, l_interval)
        self.m_stat.register_handler(l_http)

  def _initialize_log(self):
    self.m_logger = logger.manager.LogManager()
    self.m_logger.initialize(config.get("log", "config"), config.get("log", "override"))

  def _initialize_param(self):
    self.m_param = param.manager.ParamManager(config.get("param", "directory"))

# Local Variables:
# ispell-local-dictionary: "american"
# End:
