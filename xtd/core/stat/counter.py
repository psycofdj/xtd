# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import threading
import sys
import time
import multiprocessing

#------------------------------------------------------------------#

class Base:
  def __init__(self, p_name):
    self.m_lock = multiprocessing.Lock()
    self.m_name = p_name

  def visit(self, p_visitor):
    with self.m_lock:
      self.visit_safe(p_visitor)

  def update(self):
    with self.m_lock:
      self.update_safe()

  def visit_safe(self, p_visitor):
    raise NotImplemented

  def update_safe(self):
    raise NotImplemented

#------------------------------------------------------------------#

class Value(Base):
  def __init__(self, p_name, p_value = 0, p_type='i'):
    super().__init__(p_name)
    if p_value != None:
      self.m_unset = False
      self.m_value = multiprocessing.Value(p_type, p_value)
    else:
      self.m_unset = True
      self.m_value = multiprocessing.Value(p_type, 0)

  def unset(self):
    with self.m_lock:
      self.m_unset = True

  def incr(self, p_val = 1):
    with self.m_lock:
      self.m_value.value += p_val

  def decr(self, p_val = 1):
    self.incr(-1 * p_val)

  def val(self, p_val = None):
    with self.m_lock:
      if p_val != None:
        self.m_unset       = False
        self.m_value.value = p_val
      if self.m_unset:
        return "NaN"
      return self.m_value.value

  def visit_safe(self, p_visitor):
    l_val =  self.m_value.value
    if self.m_unset:
      l_val = "NaN"
    p_visitor(self.m_name, l_val)

  def update_safe(self):
    pass

#------------------------------------------------------------------#

class Int32(Value):
  def __init__(self, p_name, p_value = 0):
    super().__init__(p_name, p_value, 'i')

class Int64(Value):
  def __init__(self, p_name, p_value = 0):
    super().__init__(p_name, p_value, 'l')

class UInt32(Value):
  def __init__(self, p_name, p_value = 0):
    super().__init__(p_name, p_value, 'I')

class UInt64(Value):
  def __init__(self, p_name, p_value = 0):
    super().__init__(p_name, p_value, 'L')

class Float(Value):
  def __init__(self, p_name, p_value = 0.0):
    super().__init__(p_name, p_value, 'f')

class Double(Value):
  def __init__(self, p_name, p_value = 0.0):
    super().__init__(p_name, p_value, 'd')

#------------------------------------------------------------------#

class Composed(Base):
  def __init__(self, p_name):
    super().__init__(p_name)
    self.m_childs = []

  def register(self, p_counter):
    with self.m_lock:
      if self.m_name:
        p_counter.m_name = self.m_name + "." + p_counter.m_name
      self.m_childs.append(p_counter)
      return p_counter

  def visit_safe(self, p_visitor):
    [ x.visit(p_visitor) for x in self.m_childs ]

  def update_safe(self):
    [ x.update() for x in self.m_childs ]

#------------------------------------------------------------------#

class AvgTime(Composed):
  def __init__(self, p_name, p_timeMs = 10000, p_maxSamples = 20000):
    super().__init__(p_name)
    self.m_samples  = []
    self.m_timeMs   = p_timeMs
    self.m_maxSize  = p_maxSamples
    self.m_rtt_min  = UInt32("min", None)
    self.m_rtt_max  = UInt32("max", None)
    self.m_rtt_moy  = UInt32("moy", None)
    self.register(self.m_rtt_min)
    self.register(self.m_rtt_max)
    self.register(self.m_rtt_moy)

  def push(self, p_val):
    with self.m_lock:
      self.m_samples.append((time.time(), p_val))
      if len(self.m_samples) > self.m_maxSize:
        self.m_samples = self.m_samples[-self.m_maxSize:]

  def update_safe(self):
    l_max = time.time() - float(self.m_timeMs / 1000.0)
    self.m_samples = [ x for x in self.m_samples if x[0] >= l_max ]
    l_size = len(self.m_samples)
    if not l_size:
      self.m_rtt_min.unset()
      self.m_rtt_max.unset()
      self.m_rtt_moy.unset()
    else:
      l_max  = 0
      l_sum  = 0
      l_min  = sys.maxsize
      for c_val in self.m_samples:
        l_min = min(l_min, c_val[1])
        l_max = max(l_max, c_val[1])
        l_sum += c_val[1]
      self.m_rtt_min.val(int(l_min))
      self.m_rtt_max.val(int(l_max))
      self.m_rtt_moy.val(int(l_sum / l_size))

#------------------------------------------------------------------#

class AvgTimePerf(AvgTime):
  def __init__(self, p_name, p_timeMs = 10000, p_maxSamples = 20000):
    super().__init__(p_name, p_timeMs, p_maxSamples)
    self.m_startTimes = {}

  def work_begin(self):
    l_name = threading.current_thread().name
    self.m_startTimes[l_name] = time.time()

  def work_end(self):
    l_name = threading.current_thread().name
    self.push((time.time() - self.m_startTimes[l_name]) * 1000000)
    del self.m_startTimes[l_name]

#------------------------------------------------------------------#
