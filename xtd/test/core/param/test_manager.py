# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import logging
import os
import unittest2 as unittest

from xtd.core.param import manager
from xtd.core       import error
from xtd.core       import mixin

#------------------------------------------------------------------#

# pylint: disable=protected-access
class ParamTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(ParamTest, self).__init__(*p_args, **p_kwds)

  def setUp(self, p_name="name", p_value="value", p_listeners=None):
    self.m_obj = manager.Param(p_name, p_value, p_listeners)


  def test_set(self):
    self.assertTrue(self.m_obj.set("value2"))
    self.assertEqual(self.m_obj.get(), "value2")

    self.setUp(p_value=3)
    self.assertTrue(self.m_obj.set(4))
    self.assertEqual(self.m_obj.get(), 4)
    self.assertTrue(self.m_obj.set("66"))
    self.assertEqual(self.m_obj.get(), 66)
    with self.assertLogs(logging.getLogger("xtd.core.param.manager"), "ERROR"):
      self.assertFalse(self.m_obj.set([2,3,4]))

    def only_even(p_param, p_old, p_new):
      if p_new % 2 == 1:
        raise error.XtdError(__name__, "must be even")
    def only_switch(p_param, p_old, p_new):
      if (p_new % 2) == (p_old % 2):
        raise error.XtdError(__name__, "must change even <-> odd")

    self.setUp(p_value = 0, p_listeners=only_even)
    self.assertTrue(self.m_obj.set(2))
    self.assertTrue(self.m_obj.set(4))
    with self.assertLogs(logging.getLogger("xtd.core.param.manager"), "ERROR"):
      self.assertFalse(self.m_obj.set(5))

    self.setUp(p_value = 0, p_listeners=only_switch)
    self.assertTrue(self.m_obj.set(1))
    self.assertTrue(self.m_obj.set(4))
    with self.assertLogs(logging.getLogger("xtd.core.param.manager"), "ERROR"):
      self.assertFalse(self.m_obj.set(6))

# pylint: disable=protected-access
class ConfigManagerTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(ConfigManagerTest, self).__init__(*p_args, **p_kwds)
    self.m_obj = None

  def setUp(self, p_path="/tmp/xtd_test_param_manager"):
    mixin.Singleton.reset(manager.ParamManager)
    self.m_obj = manager.ParamManager(p_path)

  def test__create_dir(self):
    # permission denied
    with self.assertRaises(error.XtdError):
      self.m_obj._create_dir("/cant_write")

    # is a file
    with self.assertRaises(error.XtdError):
      self.m_obj._create_dir("/dev/null")

    # simple create
    self.m_obj._create_dir("/tmp/xtd/can_write")
    self.assertTrue(os.path.isdir("/tmp/xtd/can_write"))
    self.m_obj._create_dir("/dev")
    self.assertTrue(os.path.isdir("/dev"))

    # recursive create
    self.m_obj._create_dir("/tmp/xtd/a/b/c")
    self.assertTrue(os.path.isdir("/tmp/xtd/a/b/c"))

    # already_exists
    self.m_obj._create_dir("/tmp")
    self.assertTrue(os.path.isdir("/tmp"))

  def test__write(self):
    l_param = manager.Param("int", 2)
    self.m_obj._write(l_param, l_param.get(), 3)
    with open("/tmp/xtd_test_param_manager/int") as l_file:
      l_content = l_file.readlines()
      self.assertEqual(l_content[0], "3")

    l_param = manager.Param("list", [1,2,3,4])
    self.m_obj._write(l_param, l_param.get(), [4,5,6,7])
    with open("/tmp/xtd_test_param_manager/list") as l_file:
      l_content = l_file.readlines()
      self.assertEqual(l_content[0], "[4, 5, 6, 7]")

    # not seriable value
    with self.assertRaises(error.XtdError):
      l_param = manager.Param("list", [1,2,3,4])
      self.m_obj._write(l_param, l_param.get(), self)

    # file note writable
    self.setUp("/dev")
    with self.assertRaises(error.XtdError):
      l_param = manager.Param("int", 1)
      self.m_obj._write(l_param, l_param.get(), 2)

  def test__load(self):
    l_param = manager.Param("int", 2)
    self.m_obj._write(l_param, l_param.get(), 3)
    self.m_obj._load(l_param)
    self.assertEqual(l_param.get(), 3)

  def test_register(self):
    # normal register
    self.m_obj.register("name", "value")

    # duplicated register
    with self.assertRaises(error.XtdError):
      self.m_obj.register("name", "other")

    # synced register
    l_param = manager.Param("synced", 2)
    self.m_obj._write(l_param, l_param.get(), 3)
    l_other = manager.Param("synced", 1)
    self.m_obj.register_param(l_other, p_sync=True)
    self.assertEqual(l_other.get(), 3)

  def test_get(self):
    self.m_obj.register("name", "value")
    self.assertEqual(self.m_obj.get("name").get(), "value")

    with self.assertRaises(error.XtdError):
      self.m_obj.get("name")

  def test_get(self):
    self.m_obj.register("name", "value")
    self.assertEqual(self.m_obj.set("name", "value2"), True)
    self.assertEqual(self.m_obj.get("name"), "value2")

    with self.assertRaises(error.XtdError):
      self.m_obj.set("doesnotexist", "value")

  def test_listen(self):
    self.m_obj.register("name", "value")
    self.m_obj.listen("name", lambda x,y: x)

    with self.assertRaises(error.XtdError):
      self.m_obj.listen("doesnotexist", lambda x,y: x)

  def test_get_names(self):
    self.m_obj.register("name1", "value")
    self.m_obj.register("name2", "value")
    self.m_obj.register("name3", "value")
    self.assertListEqual(self.m_obj.get_names(), ["name1", "name2", "name3"])

if __name__ == "__main__":
  unittest.main()
