# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import time
import sys
import os
import termcolor
import unittest2 as unittest

from xtd.core.stat.counter import BaseCounter, Value, Int32, Int64
from xtd.core.stat.counter import UInt32, UInt64, Float, Double
from xtd.core.stat.counter import Composed, TimedSample, Perf, CounterError

#------------------------------------------------------------------#


class BaseCounterTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(BaseCounterTest, self).__init__(*p_args, **p_kwds)

  def test___init__(self):
    l_val = BaseCounter("toto")
    self.assertEqual(l_val.m_name, "toto")

  def test__visit_safe(self):
    l_val = BaseCounter("toto")
    with self.assertRaises(NotImplementedError):
      l_val._visit_safe(lambda x: True)

  def test_visit(self):
    l_val = BaseCounter("toto")
    with self.assertRaises(NotImplementedError):
      l_val.visit(lambda x:True)

  def test__update_safe(self):
    l_val = BaseCounter("toto")
    with self.assertRaises(NotImplementedError):
      l_val._update_safe()

  def test_update(self):
    l_val = BaseCounter("toto")
    with self.assertRaises(NotImplementedError):
      l_val.update()


class ValueTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(ValueTest, self).__init__(*p_args, **p_kwds)

  def test___init__(self):
    l_val = Value("toto")
    self.assertTrue(l_val.m_unset)
    l_val = Value("toto", 20)
    self.assertFalse(l_val.m_unset)
    self.assertEqual(l_val.m_value.value, 20)

    with self.assertRaises(TypeError):
      l_val = Value("toto", 20, 'V')

    with self.assertRaises(TypeError):
      l_val = Value("toto", 4.5, 'i')

  def test_unset(self):
    l_val = Value("toto", 20)
    self.assertFalse(l_val.m_unset)
    self.assertEqual(l_val.m_value.value, 20)
    l_val.unset()
    self.assertTrue(l_val.m_unset)

  def test_val(self):
    l_val = Value("toto", 20)
    self.assertFalse(l_val.m_unset)
    self.assertEqual(l_val.val, 20)

    l_val.unset()
    self.assertEqual(l_val.val, None)

    l_val.val = 300
    self.assertEqual(l_val.val, 300)

    l_val.val = None
    self.assertEqual(l_val.val, None)
    self.assertTrue(l_val.m_unset)


    with self.assertRaises(TypeError):
      l_val.val = "no a val"

  def test_incr(self):
    l_val = Value("toto", 20)
    self.assertEqual(l_val.val, 20)
    l_val.incr()
    self.assertEqual(l_val.val, 21)
    l_val.incr(10)
    self.assertEqual(l_val.val, 31)
    with self.assertRaises(TypeError):
      l_val.incr("no a val")

  def test_decr(self):
    l_val = Value("toto", 20)
    self.assertEqual(l_val.val, 20)
    l_val.decr()
    self.assertEqual(l_val.val, 19)
    l_val.decr(10)
    self.assertEqual(l_val.val, 9)
    with self.assertRaises(TypeError):
      l_val.incr("no a val")

  def test_visit_ok(self):
    # check values from visitor
    def visitor_ok(p_name, p_value):
      self.assertEqual(p_name, "toto")
      self.assertEqual(p_value, 15)
    l_val = Value("toto", 15)
    l_val.visit(visitor_ok)

    # check that visitor is executed
    def visitor_ko(p_name, p_value):
      self.assertEqual(p_name, "toto")
      self.assertEqual(p_value, 21)
    with self.assertRaises(AssertionError):
      l_val.visit(visitor_ko)

  def test_visit_nan(self):
    # check values from visitor
    def visitor_nan(p_name, p_value):
      self.assertEqual(p_name, "toto")
      self.assertEqual(p_value, "NaN")
    l_val = Value("toto", 15)
    l_val.unset()
    l_val.visit(visitor_nan)

  def test_visit_error(self):
    def bad_visitor(p_name):
      pass
    l_val = Value("toto", 15)
    with self.assertRaises(TypeError):
      l_val.visit(bad_visitor)

  def test_update(self):
    l_val = Value("toto", 2)
    l_val.update()

  def test_all_concrete_values(self):
    Int32("name", -1)
    Int64("name", -2)
    UInt32("name", 1)
    UInt64("name", 2)
    Float("name", 0.2)
    Double("name", 0.5)


class ComposedTest(unittest.TestCase):
  def test__init__(self):
    l_group = Composed("with_name")
    l_group.register(Int64("int64", 64))
    l_group.register(Int32("int32", 32))
    l_group.register(Int32("unset"))

    def visitor(p_name, p_value):
      if p_name == "with_name.int64":
        self.assertEqual(p_value, 64)
      elif p_name == "with_name.int32":
        self.assertEqual(p_value, 32)
      elif p_name == "with_name.unset":
        self.assertEqual(p_value, "NaN")
      else:
        self.fail("unexpected counter name")
    l_group.update()
    l_group.visit(visitor)



class TimedSampleTest(unittest.TestCase):
  def test_push(self):
    l_obj = TimedSample("avg", p_timeMs=10*1000, p_maxSamples = 1000)
    for c_val in range(0, 500):
      l_obj.push(c_val)
    self.assertEqual(len(l_obj.m_samples), 500)

    for c_val in range(0, 500):
      l_obj.push(c_val)
    self.assertEqual(len(l_obj.m_samples), 1000)

    for c_val in range(0, 500):
      l_obj.push(c_val)
    self.assertEqual(len(l_obj.m_samples), 1000)

    with self.assertRaises(TypeError):
      l_obj.push("toto")

  def test_update(self):
    l_obj = TimedSample("avg", p_timeMs=100, p_maxSamples = 1000)
    # visitor to get data
    l_data = {}
    def visitor(p_name, p_val):
      l_data[p_name] = p_val
    # fill with [10, 19] for t=0
    for c_val in range(10, 20):
      l_obj.push(c_val)
    # fill with [0, 9] for t=500ms
    time.sleep(0.05)
    for c_val in range(0, 10):
      l_obj.push(c_val)

    # check all data
    l_obj.update()
    l_obj.visit(visitor)
    self.assertDictEqual(l_data, {
      "avg.min" : 0,
      "avg.max" : 19,
      "avg.avg" : 9
    })

    # check half data
    time.sleep(0.05)
    l_obj.update()
    l_obj.visit(visitor)
    self.assertDictEqual(l_data, {
      "avg.min" : 0,
      "avg.max" : 9,
      "avg.avg" : 4
    })

    # check no data
    time.sleep(0.05)
    l_obj.update()
    l_obj.visit(visitor)
    self.assertDictEqual(l_data, {
      "avg.min" : "NaN",
      "avg.max" : "NaN",
      "avg.avg" : "NaN"
    })


class PerfTest(unittest.TestCase):
  def test_work_begin(self):
    l_obj = Perf("perf")
    l_obj.work_begin()
    with self.assertRaises(CounterError):
      l_obj.work_begin()
    time.sleep(0.1)
    l_obj.work_end()
    with self.assertRaises(CounterError):
      l_obj.work_end()
    self.assertEqual(len(l_obj.m_samples), 1)
    self.assertAlmostEqual(l_obj.m_samples[0][1], 100000, delta=500)

# Local Variables:
# ispell-local-dictionary: "american"
# End:
