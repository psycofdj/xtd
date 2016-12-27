# -*- coding: utf-8
#------------------------------------------------------------------#
"""

.. inheritance-diagram:: xtd.core.stat.counter
   :parts: 1

"""


__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import threading
import sys
import time
import multiprocessing

from ..error import XtdError

#------------------------------------------------------------------#


class BaseCounter(object):
  """ Abstract base counter

  The almost-empty shell insure base methods are protected
  by a lock.

  Args:
    p_name (str): object name
  """
  def __init__(self, p_name):
    self.m_lock = multiprocessing.Lock()
    self.m_name = p_name

  def visit(self, p_visitor):
    """ Visit object tree with visitor """
    with self.m_lock:
      self._visit_safe(p_visitor)

  def update(self):
    """ Update object

    Generally called by user just before visiting the object
    in order to gather "fresh" data
    """

    with self.m_lock:
      self._update_safe()

  def _visit_safe(self, p_visitor):
    raise NotImplementedError

  def _update_safe(self):
    raise NotImplementedError

#------------------------------------------------------------------#

class Value(BaseCounter):
  """Thread-safe numeric value holder

  Args:
    p_name (str): Object's name
    p_value (numeric): Internal value, type depends on ``p_type``
    p_type (str) : One character type spec, see :py:class:`multiprocessing.Value`

  Raises:
    TypeError: invalid ``p_type``
    TypeError: invalid ``p_value`` for given ``p_type``

  **Visitors**

  Value visitor must follow the following prototype:
  ``function(p_name, p_value)``

  - **p_name** (str): name of visited Value
  - **p_value** (numeric|str): internal value or ``NaN`` is unset

  """
  def __init__(self, p_name, p_value = None, p_type='i'):
    super(Value, self).__init__(p_name)
    if p_value != None:
      self.m_unset = False
      self.m_value = multiprocessing.Value(p_type, p_value)
    else:
      self.m_unset = True
      self.m_value = multiprocessing.Value(p_type, 0)

  def unset(self):
    """ Make the current value undefined """
    with self.m_lock:
      self.m_unset = True

  # pylint: disable=invalid-name
  @property
  def val(self):
    """ (Property) internal value

    If set to None, the current value is ``undefined``

    Returns:
      (numeric) : current internal value, None if unset

    Raises:
      TypeError: affected value dosen't match constructor type
    """
    with self.m_lock:
      if self.m_unset:
        return None
      return self.m_value.value

  @val.setter
  def val(self, p_val):
    with self.m_lock:
      if p_val != None:
        self.m_unset       = False
        self.m_value.value = p_val
      else:
        self.m_unset = True

  def incr(self, p_val = 1):
    """ Increments the current value

    Args:
      p_val (numeric): add p_val to current internal value

    Raises:
      TypeError: given value dosen't match constructor type
    """
    with self.m_lock:
      self.m_value.value += p_val

  def decr(self, p_val = 1):
    """ Decrements the current value

    Args:
      p_val (numeric): subtract p_val to current internal value

    Raises:
      TypeError: given value dosen't match constructor type
    """
    self.incr(-1 * p_val)

  def _visit_safe(self, p_visitor):
    """ Apply visitor to internal value

    Raises:
      TypeError: visitor as invalid prototype
    """
    l_val =  self.m_value.value
    if self.m_unset:
      l_val = "NaN"
    p_visitor(self.m_name, l_val)

  def _update_safe(self):
    """ Noop """
    pass

#------------------------------------------------------------------#

class Int32(Value):
  """ Value specialization for signed 32 bits integer """

  TYPE = 'i'
  """:py:class:`multiprocessing.Value` type spec"""

  def __init__(self, p_name, p_value = None):
    super(Int32, self).__init__(p_name, p_value, self.TYPE)

class Int64(Value):
  """ Value specialization for signed 64 bits integer """

  TYPE = 'l'
  """:py:class:`multiprocessing.Value` type spec"""

  def __init__(self, p_name, p_value = None):
    super(Int64, self).__init__(p_name, p_value, self.TYPE)

class UInt32(Value):
  """ Value specialization for unsigned 32 bits integer """

  TYPE = "I"
  """:py:class:`multiprocessing.Value` type spec"""

  def __init__(self, p_name, p_value = None):
    super(UInt32, self).__init__(p_name, p_value, self.TYPE)

class UInt64(Value):
  """ Value specialization for unsigned 64 bits integer """

  TYPE = "L"
  """:py:class:`multiprocessing.Value` type spec"""

  def __init__(self, p_name, p_value = None):
    super(UInt64, self).__init__(p_name, p_value, self.TYPE)

class Float(Value):
  """ Value specialization for float """

  TYPE = 'f'
  """:py:class:`multiprocessing.Value` type spec"""

  def __init__(self, p_name, p_value = None):
    super(Float, self).__init__(p_name, p_value, self.TYPE)

class Double(Value):
  """ Value specialization for double """

  TYPE = 'd'
  """:py:class:`multiprocessing.Value` type spec"""

  def __init__(self, p_name, p_value = None):
    super(Double, self).__init__(p_name, p_value, self.TYPE)

#------------------------------------------------------------------#

class Composed(BaseCounter):
  """ Manage a collection child counters """
  def __init__(self, p_name):
    super(Composed, self).__init__(p_name)
    self.m_childs = []

  def register(self, p_counter):
    """ Register a child counter

    Current object name is prepend to registered child
    name with the following format : ``<parent-name>.<child-name>``

    Args:
      p_counter (BaseCounter): child counter to add
    """
    with self.m_lock:
      if self.m_name:
        p_counter.m_name = self.m_name + "." + p_counter.m_name
      self.m_childs.append(p_counter)

  def _visit_safe(self, p_visitor):
    for c_child in self.m_childs:
      c_child.visit(p_visitor)

  def _update_safe(self):
    for c_child in self.m_childs:
      c_child.update()

#------------------------------------------------------------------#

class TimedSample(Composed):
  """ Holds the min, max and average value of collected items over a fixed period of time

  When no items are available for the last ``p_timeMs``, the 3 sub counters are
  undefined, thus, collected by visitors as ``NaN``.

  Args:
    p_name (str) : counter name
    p_timeMs (int) : maximum amount of time (millisecond) to keep collected values
    p_maxSamples (int) : maximum amount of values to keep
    p_type (str) : internal type representation, see :py:class:`multiprocessing.Value`
  """
  def __init__(self, p_name, p_timeMs = 10000, p_maxSamples = 20000, p_type = Int32.TYPE):
    super(TimedSample, self).__init__(p_name)
    self.m_samples  = []
    self.m_timeMs   = p_timeMs
    self.m_maxSize  = p_maxSamples
    self.m_rttMin  = Value("min", None, p_type)
    self.m_rttMax  = Value("max", None, p_type)
    self.m_rttAvg  = Value("avg", None, p_type)
    self.register(self.m_rttMin)
    self.register(self.m_rttMax)
    self.register(self.m_rttAvg)

  def push(self, p_val):
    """ Add a value in collection

    p_val (int): value to add
    """
    with self.m_lock:
      try:
        l_val = int(p_val)
      except ValueError:
        raise TypeError

      self.m_samples.append((time.time(), l_val))
      if len(self.m_samples) > self.m_maxSize:
        self.m_samples = self.m_samples[-self.m_maxSize:]

  # pylint: disable=invalid-name
  def _update_safe(self):
    l_max = time.time() - float(self.m_timeMs / 1000.0)
    self.m_samples = [ x for x in self.m_samples if x[0] >= l_max ]
    l_size = len(self.m_samples)
    if not l_size:
      self.m_rttMin.unset()
      self.m_rttMax.unset()
      self.m_rttAvg.unset()
    else:
      l_max  = 0
      l_sum  = 0
      l_min  = sys.maxsize
      for c_val in self.m_samples:
        l_min = min(l_min, c_val[1])
        l_max = max(l_max, c_val[1])
        l_sum += c_val[1]
      self.m_rttMin.val = int(l_min)
      self.m_rttMax.val = int(l_max)
      self.m_rttAvg.val = int(l_sum / l_size)

#------------------------------------------------------------------#

class Perf(TimedSample):
  """ Designed to monitor the min, max and average time of an event

  At event start call :py:meth:`work_begin` to store the current time.
  At event end, call :py:meth:`work_end` to calculate the time detla and add it
  the base class samples that monitors the min max and average values

  The time resolution is the microsecond (10^-6 second).

  Note:
    Events beginnings and ends can't be interleaved in the same thread.
  """
  def __init__(self, p_name, p_timeMs = 10000, p_maxSamples = 20000):
    super(Perf, self).__init__(p_name, p_timeMs, p_maxSamples, p_type=UInt64.TYPE)
    self.m_startTimes = {}

  def work_begin(self):
    """ Record begin time of an event

    Raises:
      CounterError: called twice from same thread with no :py:meth:`work_end` between them
    """
    l_name = threading.current_thread().name
    l_value = self.m_startTimes.get(l_name, None)
    if l_value is not None:
      raise CounterError(__name__, self.m_name, "missing work_end for thread '%s'", l_name)
    self.m_startTimes[l_name] = time.time()

  def work_end(self):
    """ Record end time of an event and push it into base class

    Raises:
      CounterError: called without calling :py:meth:`work_begin` first from same thread
    """
    l_name = threading.current_thread().name
    l_value = self.m_startTimes.get(l_name, None)
    if l_value is None:
      raise CounterError(__name__, self.m_name, "missing work_begin for thread '%s'", l_name)
    self.push((time.time() - self.m_startTimes[l_name]) * 1000000)
    del self.m_startTimes[l_name]


class CounterError(XtdError):
  """ Generic counter error class

  Args:
    p_module (str)   : module name
    p_name   (str)   : counter name
    p_msg    (str)   : error message
    p_args   (tuple) : generic message format arguments
    p_kwds   (dict)  : generic message format keywords

  Attributes:
    m_name (str) : name of counter that raised the error
  """
  def __init__(self, p_module, p_name, p_msg, *p_args, **p_kwds):
    self.m_name = p_name
    l_msg = "error with counter '%(name)s' : %(msg)s" % {
      "name" : p_name,
      "msg"  : p_msg.format(*p_args, **p_kwds)
    }
    super(CounterError, self).__init__(p_module, l_msg)

#------------------------------------------------------------------#

# Local Variables:
# ispell-local-dictionary: "american"
# End:
