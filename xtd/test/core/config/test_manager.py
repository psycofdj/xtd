# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import optparse
import unittest2 as unittest

from xtd.core.config import manager
from xtd.core        import error
from xtd.core        import mixin, config

#------------------------------------------------------------------#


class ConfigManagerTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(ConfigManagerTest, self).__init__(*p_args, **p_kwds)
    self.m_obj = None

  def setUp(self):
    mixin.Singleton.reset(manager.ConfigManager)
    self.m_obj = manager.ConfigManager()

  def _basic_init(self, p_argv = ["script.py", "--test-value", "titi"]):
    self.m_obj.register_section("test", "Test", [{
      "name"    : "value",
      "cmdline" : True,
      "default" : "toto",
      "description" : "a description",
      "checks"      : lambda x,y,z: z
    }])
    self.m_obj.initialize()
    self.m_obj.parse(p_argv)

  def test_get(self):
    self._basic_init()
    self.assertEqual(self.m_obj.get("test", "value"), "titi")
    self.assertEqual(config.get("test", "value"), "titi")
    with self.assertRaises(error.ConfigValueError):
      self.m_obj.get("test", "does not exist")
    with self.assertRaises(error.ConfigValueError):
      self.m_obj.get("does not exist", "value")

  def test_set(self):
    self._basic_init()
    self.assertEqual(self.m_obj.get("test", "value"), "titi")
    self.m_obj.set("test", "value", "toto")
    self.assertEqual(self.m_obj.get("test", "value"), "toto")
    config.set("test", "value", "titi")
    self.assertEqual(config.get("test", "value"), "titi")

    with self.assertRaises(error.ConfigValueError):
      self.m_obj.set("test", "does not exist", "toto")
    with self.assertRaises(error.ConfigValueError):
      self.m_obj.set("does not exist", "value", "toto")

  def test_option_exists(self):
    self._basic_init()
    self.assertTrue(self.m_obj.option_exists("test", "value"))
    self.assertFalse(self.m_obj.option_exists("test", "fdjski"))
    self.assertFalse(self.m_obj.option_exists("fdss", "value"))
    self.assertTrue(config.option_exists("test", "value"))
    self.assertFalse(config.option_exists("test", "fdjski"))
    self.assertFalse(config.option_exists("fdss", "value"))

  def test_options(self):
    self._basic_init()
    l_options = self.m_obj.options("test")
    self.assertEqual(list(l_options), ["value"])
    self.assertEqual(self.m_obj.options("test"), config.options("test"))
    with self.assertRaises(error.ConfigError):
      self.m_obj.options("does not exist")

  def test_section_exists(self):
    self._basic_init()
    self.assertTrue(self.m_obj.section_exists("test"))
    self.assertFalse(self.m_obj.section_exists("fdsfds"))
    self.assertTrue(config.section_exists("test"))
    self.assertFalse(config.section_exists("fdsfds"))

  def test_sections(self):
    self._basic_init()
    l_sections = self.m_obj.sections()
    self.assertEqual(list(l_sections), ["test"])
    self.assertEqual(self.m_obj.sections(), config.sections())

  def test_help(self):
    self._basic_init()
    with open("/dev/null", mode="w") as l_out:
      self.m_obj.help(l_out)

  def test__get_option(self):
    self._basic_init()
    l_data = self.m_obj._get_option("test", "value")
    with self.assertRaises(error.ConfigValueError):
      self.m_obj._get_option("test", "does not exist")
    with self.assertRaises(error.ConfigValueError):
      self.m_obj._get_option("does not exist", "value")

  def test_option_cmdline_given(self):
    self.m_obj.register_section("test", "Test", [{
      "name"        : "value",
      "cmdline"     : True,
      "default"     : "toto",
      "description" : "a description"
    }])
    self.m_obj.initialize()
    self.m_obj.parse(["script.py", "--test-value", ""])
    self.assertTrue(self.m_obj.option_cmdline_given("test", "value"))
    self.m_obj.initialize()
    self.m_obj.parse(["script.py"])
    self.assertFalse(self.m_obj.option_cmdline_given("test", "value"))
    self.assertFalse(self.m_obj.option_cmdline_given("test", "does not exist"))
    self.assertFalse(self.m_obj.option_cmdline_given("does not exist", "value"))


  def test_option_cmdline_given_dash(self):
    self.m_obj.register_section("test", "Test", [{
      "name"        : "opt-with-dash",
      "default"     : "toto",
      "description" : "a description"
    }])
    self.m_obj.initialize()
    self.m_obj.parse(["script.py", "--test-opt-with-dash", "value"])
    self.assertTrue(self.m_obj.option_cmdline_given("test", "opt-with-dash"))
    self.assertFalse(self.m_obj.option_cmdline_given("test", "unknown-with-dash"))


  def test_get_args(self):
    self._basic_init(["script.py", "--test-value", "super", "a", "b", "c"])
    self.assertEqual(self.m_obj.get_args(), ["a", "b", "c"])

  def test_get_name(self):
    self._basic_init()
    self.assertEqual(self.m_obj.get_name(), "script.py")
    self.m_obj.initialize()
    self.m_obj.parse(["/dev/toto.py"])
    self.assertEqual(self.m_obj.get_name(), "/dev/toto.py")

  def test_storetrue_opt(self):
    self.m_obj.register_section("test", "Test", [{
      "name"        : "value",
      "cmdline"     : True,
      "valued"      : False,
      "description" : "a description"
    }])
    self.m_obj.initialize()
    self.m_obj.parse(["script.py", "--test-value"])
    self.assertTrue(self.m_obj.get("test", "value"), True)

    self.m_obj.initialize()
    self.m_obj.parse(["script.py"])
    self.assertEqual(self.m_obj.get("test", "value"), False)

  def test_register_section(self):
    with self.assertRaises(error.ConfigError):
      self.m_obj.register_section("test", "Test", [{}])

    with self.assertRaises(error.ConfigError):
      self.m_obj.register_section("test", "Test", [{
        "name"        : "value",
        "cmdline"     : True,
        "valued"      : False,
        "unknown"     : "a description"
      },{
        "name"        : "value",
        "cmdline"     : True,
        "valued"      : False,
        "unknown"     : "a description"
      }])
    with self.assertRaises(error.ConfigError):
      self.m_obj.register_section("test", "Test", [{
        "name"        : "value",
        "cmdline"     : True,
        "valued"      : False,
        "unknown"     : "a description"
      }])

  def test_mandatory(self):
    self.m_obj.register_section("test", "Test", [{
      "name"        : "value",
      "cmdline"     : True,
      "valued"      : True,
      "default"     : None,
      "mandatory"   : True
    }])
    self.m_obj.initialize()
    with self.assertRaises(error.ConfigError):
      self.m_obj.parse(["script.py"])


#------------------------------------------------------------------#


if __name__ == "__main__":
  unittest.main()
