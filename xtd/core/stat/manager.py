# -*- coding: utf-8
# pylint: disable=unused-import
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

from future.utils import with_metaclass
from ..error      import XtdError
from ..           import mixin
from ..tools      import thread
from ..           import error
from .counter     import BaseCounter
from .handler     import BaseHandler
    
#------------------------------------------------------------------#

class StatManager(with_metaclass(mixin.Singleton, thread.SafeThreadGroup)):
  def __init__(self):
    super(StatManager, self).__init__(__name__)
    self.m_counters  = {}

  def exists(self, p_ns, p_name):
    l_list     = self.m_counters.get(p_ns, [])
    l_counters = [ x for x in l_list if x.m_name == p_name ]
    return len(l_counters) != 0

  def register_counter(self, p_ns, p_counter):
    """ Register a counter in global statistics

    Args:
      p_ns (str):              namespace
      p_counter (BaseCounter): counter object to add

    Raises:
      XtdError: counter already defined for this namespace
      XtdError: ``p_counter`` is not a valid :py:class:`~xtd.core.stat.counter.BaseCounter` object
    """
    if not issubclass(p_counter.__class__, BaseCounter):
      raise XtdError(__name__, "attempt to add invalid object type")

    if self.exists(p_ns, p_counter.m_name):
      raise XtdError(__name__, "already defined counter '%s' in namespace '%s'",
                     p_counter.m_name, p_ns)

    if not p_ns in self.m_counters:
      self.m_counters[p_ns] = []

    self.m_counters[p_ns].append(p_counter)

  def register_handler(self, p_handler):
    """ Register an counter output handler

    Args:
      p_handler (BaseHandler) : new handler to add

    Raises:
     XtdError: given ``p_handler`` is not a valid :py:class:`~xtd.core.stat.handler.BaseHandler`
    """
    if not issubclass(p_handler.__class__, BaseHandler):
      raise error.XtdError(__name__, "handlers must be BaseHandler based class")
    self.add_thread(p_handler)

  def get(self, p_ns, p_name):
    """ Get a counter in a particular namespace

    Returns:
      BaseCounter: requests counter

    Raises:
      XtdError: undefined namespace ``p_ns``
      XtdError: undefined counter ``p_name`` for given namespace
    """
    if not p_ns in self.m_counters:
      raise error.XtdError(__name__, "undefined namespace '%s'" % p_ns)
    for c_counter in self.m_counters[p_ns]:
      if c_counter.m_name == p_name:
        return c_counter
    raise error.XtdError(__name__, "undefined counter '%s' in namespace '%s'" % (p_name, p_ns))

  def write(self):
    """ Output counter is all registered handlers """
    for c_handler in self.m_threads:
      c_handler.write()

  def get_all(self):
    """ Get registered counters

    Example:

      ::

        {
          "name.space.1" : [ <counter-object-1>, <counter-object-2>, ... ],
          ...
          "name.space.N" : [ <counter-object-N>, <counter-object-N+1>, ... ],
        }


    Returns:
      dict: dictionary containing raw counters
    """
    return self.m_counters

  def get_json(self):
    """ Get counter data in a dictionary

    Example:

      ::

        {
          "name.space.1" : {
            "counter1" : <value1>,
            "counter2" : <value2>
          },
          ...
          "name.space" : {
            "counterN" : <valueN>
          }
        }


    Returns:
      dict: counter's name and value organized by namespace

    """
    l_res = {}
    for c_ns, c_counters in self.m_counters.items():
      l_res[c_ns] = {}
      for c_counter in c_counters:
        c_counter.update()
        def functor(p_name, p_value):
          # pylint: disable=cell-var-from-loop
          l_res[c_ns][p_name] = p_value
        c_counter.visit(functor)
    return l_res

#------------------------------------------------------------------#

# Local Variables:
# ispell-local-dictionary: "american"
# End:
