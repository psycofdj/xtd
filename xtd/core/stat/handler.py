# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import json
import abc
import os
import requests

from ..tools.thread import SafeThread
from ..error        import XtdError
from ..             import logger

#------------------------------------------------------------------#

class BaseHandler(SafeThread):
  """ Abstract statistic handler

  Spawns a dedicated thread that outputs a set counters every
  ``p_interval`` seconds.

  User can provide a custom function to get the counters to output.
  By default the object gets all counters registered in the
  :py:class:`~xtd.core.stat.manager.StatManager` singleton.

  User should inherit this class and define :py:meth:`write` method.

  Note:
    The functor must take no parameter and return something suitable for
    :py:meth:`write`


  Args:
    p_name (str): handler name
    p_interval (int) : interval, in second, between two outputs
    p_fetcher (function) : functor that retrieves data counters
  """
  def __init__(self, p_name, p_interval = 50, p_fetcher = None):
    super(BaseHandler, self).__init__(p_name, p_interval)

    self.m_fetcher = p_fetcher
    if p_fetcher is None:
      self.m_fetcher = self._fetch

  @staticmethod
  def _fetch():
    from .manager import StatManager
    return StatManager().get_all()

  @abc.abstractmethod
  def write(self, p_counters):
    """ Ouput available counter data (abstract)

    Args:
      p_counters (dict): dictionary holding all available counters assiciated with
       their namespace. ``{ "<namespace>" : [ <counter1>, <counter2>, ... ] }``
    """
    raise NotImplementedError

  def work(self):
    """ Output available counter data

    Implementation of :py:meth:`xtd.core.tools.thread.SafeThread.work`
    """
    self.write(self.m_fetcher())


#------------------------------------------------------------------#


class DiskHandler(BaseHandler):
  """ Output counters to filesystem

  Given :

   - a counter named ``counter.name`` of value ``55``
   - registered in :py:class:`xtd.core.stat.manager.StatManager` with namespace ``a.b.c``
   - a DiskHandler constructed with ``/var/snmp``

  This will create a file ``/var/snmp/a/b/c/counter.name`` containing the string ``55``


  Args:
    p_directory (str): target output directory path.  If given directory doesn't exist,
     the object will attempt to create it (and all necessary parent directories).
    p_interval (int): interval between two outputs (in seconds)

  Raises:
    XtdError: ``p_directory`` isn't writable or could ne be created
  """
  def __init__(self, p_directory, p_interval = 50, p_fetcher = None):
    super(DiskHandler, self).__init__(__name__ + "." + self.__class__.__name__, p_interval, p_fetcher)
    self.m_dir = p_directory
    self._create_dir(self.m_dir)

  def _create_dir(self, p_dir):
    if not os.path.isdir(p_dir):
      try:
        os.makedirs(p_dir, mode=0o0750)
      except Exception as l_error:
        l_fmt = "unable to create output directory '%s' : %s"
        raise XtdError(self.m_name,  l_fmt % (p_dir, str(l_error)))

  def _write_item(self, p_ns, p_name, p_value):
    l_path = os.path.join(self.m_dir, p_ns.replace(".", "/"))
    self._create_dir(l_path)
    l_path = os.path.join(l_path, p_name)
    try:
      with open(l_path, mode="w") as l_file:
        l_file.write(str(p_value))
    except IOError as l_error:
      logger.error(self.m_name, "unable to output counter file '%s' : %s", l_path, str(l_error))

  def write(self, p_counters):
    """ Write all available counters to filesystem

    When object fails to write a counte file, an error log is triggered. Raising an
    exception woudn't be helpfull since this part of the code runs in a dedicated
    thread.

    Args:
      p_counters (dict) : see :py:meth:`BaseHandler.write`
    """
    for c_path, c_counters in p_counters.items():
      for c_counter in c_counters:
        c_counter.update()
        def visitor(p_name, p_value):
          #pylint: disable=cell-var-from-loop
          self._write_item(c_path, p_name, p_value)
        c_counter.visit(visitor)

#------------------------------------------------------------------#

class HttpHandler(BaseHandler):
  """ Send counter values to a http server

  Counter values are gathered in a single json and sent to
  the target url as a POST request.

  HTTP Request details :

  - Method : ``POST``
  - Content-Type : ``application/json``
  - Body :

    ::

      {
        "<namespace>" : {
              "<name-of-counter-1>" : value-of-counter-1,
              "<name-of-counter-2>" : value-of-counter-2,
              ...
        },
        ...
        "<namespace>" : {
          <name-of-counter-N>" : value-of-counter-N
          ...
        }
      }

  Note:
    Keep in mind that counter values can be undefined.

    In such case, the json value is a string equals to ``"NaN"``.

  Args:
    p_url : target url for post request
    p_interval(int): interval, in second, between two outputs
    p_fetcher (function) : functor that retrieves data counters
  """
  def __init__(self, p_url, p_interval = 50, p_fetcher = None):
    super(HttpHandler, self).__init__(__name__ + "." + self.__class__.__name__, p_interval, p_fetcher)
    self.m_url = p_url

  def _send_request(self, p_json):
    try:
      l_headers = { "Content-Type" : "application/json" }
      l_req     = requests.post(self.m_url, headers=l_headers, data=json.dumps(p_json))
      if l_req.status_code != 200:
        l_message = "received invalid http response '%d' on posting json"
        logger.error(self.m_name, l_message, l_req.status_code)
    except requests.exceptions.RequestException as l_error:
      logger.error(self.m_name, "error while sending counters data : '%s'", str(l_error))

  def write(self, p_counters):
    """ Write all available counters to filesystem

    When object fails to send HTTP request, an error log is triggered. Raising an
    exception woudn't be helpfull since this part of the code runs in a dedicated
    thread.

    Args:
      p_counters (dict) : see :py:meth:`BaseHandler.write`
    """
    l_res = {}
    for c_ns, c_counters in p_counters.items():
      l_res[c_ns] = {}
      for c_counter in c_counters:
        c_counter.update()
        def visitor(p_name, p_value):
          #pylint: disable=cell-var-from-loop
          l_res[c_ns][p_name] = p_value
        c_counter.visit(visitor)
    self._send_request(l_res)


#------------------------------------------------------------------#

class LoggingHandler(BaseHandler):
  """ Output counter to application logs

  Args:
    p_name (str): logger module name
    p_interval(int): interval, in second, between two outputs
    p_fetcher (function) : functor that retrieves data counters
  """
  def __init__(self, p_name, p_interval = 50, p_fetcher = None):
    super(LoggingHandler, self).__init__(__name__ + "." + self.__class__.__name__, p_interval, p_fetcher)
    self.m_loggerName = p_name

  def write(self, p_counters):
    """ Output all available counters to logging facility
    Args:
      p_counters (dict) : see :py:meth:`BaseHandler.write`
    """
    l_res = {}
    for c_ns, c_counters in p_counters.items():
      l_res[c_ns] = {}
      for c_counter in c_counters:
        c_counter.update()
        # pylint: disable=cell-var-from-loop
        def visitor(p_name, p_value):
          logger.info(self.m_loggerName, "ns='%s', name='%s', value='%s'",
                      c_ns, p_name, p_value)
        c_counter.visit(visitor)

#------------------------------------------------------------------#

# Local Variables:
# ispell-local-dictionary: "american"
# End:

#  LocalWords:  XtdError
