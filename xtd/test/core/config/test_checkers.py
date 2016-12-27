# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import unittest2 as unittest

from xtd.core.config import checkers
from xtd.core        import error

#------------------------------------------------------------------#

class CheckersTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(CheckersTest, self).__init__(*p_args, **p_kwds)

  def test_check_file(self):
    checkers.check_file("section", "name", "/dev/null", p_read=True)
    checkers.check_file("section", "name", "/dev/null", p_write=True)
    checkers.check_file("section", "name", "/dev/null", p_read=True, p_write=True)
    with self.assertRaises(error.ConfigValueFileModeError):
      checkers.check_file("section", "name", "/dev/null", p_execute=True)
    with self.assertRaises(error.ConfigValueFileError):
      checkers.check_file("section", "name", "/dev", p_read=True)
    checkers.check_file("section", "name", "/tmp/does_not_exists", p_write=True)
    with self.assertRaises(error.ConfigValueFileModeError):
      checkers.check_file("section", "name", "/etc/does_not_exists", p_write=True)
    checkers.check_file("section", "name", "~/.profile", p_read=True)
    l_file = checkers.check_file("section", "name", "///dev/../dev/null", p_read=True)
    self.assertEqual(l_file, "/dev/null")


  def test_check_dir(self):
    checkers.check_dir("section", "name", "/", p_read=True)
    checkers.check_dir("section", "name", "/", p_execute=True)
    with self.assertRaises(error.ConfigValueDirModeError):
      checkers.check_dir("section", "name", "/", p_write=True)
    with self.assertRaises(error.ConfigValueDirError):
      checkers.check_dir("section", "name", "/dev/null", p_read=True)
    checkers.check_dir("section", "name", "~/", p_read=True)
    l_dir = checkers.check_dir("section", "name", "///dev/../dev//", p_read=True)
    self.assertEqual(l_dir, "/dev")


  def test_check_int(self):
    l_val = checkers.check_int("section", "name", "1")
    self.assertEqual(l_val, 1)
    l_val = checkers.check_int("section", "name", "01")
    self.assertEqual(l_val, 1)
    l_val = checkers.check_int("section", "name", 1)
    self.assertEqual(l_val, 1)
    l_val = checkers.check_int("section", "name", "1", p_min=1, p_max=2)
    self.assertEqual(l_val, 1)
    l_val = checkers.check_int("section", "name", "2", p_min=1, p_max=2)
    self.assertEqual(l_val, 2)
    with self.assertRaises(error.ConfigValueLimitsError):
      checkers.check_int("section", "name", "0", p_min=1, p_max=2)
    with self.assertRaises(error.ConfigValueLimitsError):
      checkers.check_int("section", "name", "3", p_min=1, p_max=2)
    with self.assertRaises(error.ConfigValueTypeError):
      checkers.check_int("section", "name", "str")
    with self.assertRaises(error.ConfigValueTypeError):
      checkers.check_int("section", "name", "0.5")
    with self.assertRaises(error.ConfigValueTypeError):
      checkers.check_int("section", "name", False)

  def test_check_float(self):
    l_val = checkers.check_float("section", "name", "1.2")
    self.assertEqual(l_val, 1.2)
    l_val = checkers.check_float("section", "name", "01.2")
    self.assertEqual(l_val, 1.2)
    l_val = checkers.check_float("section", "name", 1.2)
    self.assertEqual(l_val, 1.2)
    l_val = checkers.check_float("section", "name", "1.2", p_min=1.2, p_max=2.2)
    self.assertEqual(l_val, 1.2)
    l_val = checkers.check_float("section", "name", "2.2", p_min=1.2, p_max=2.2)
    self.assertEqual(l_val, 2.2)
    l_val = checkers.check_float("section", "name", "2")
    self.assertEqual(l_val, 2.0)
    with self.assertRaises(error.ConfigValueLimitsError):
      checkers.check_float("section", "name", "0.2", p_min=1.2, p_max=2.2)
    with self.assertRaises(error.ConfigValueLimitsError):
      checkers.check_float("section", "name", "3.2", p_min=1.2, p_max=2.2)
    with self.assertRaises(error.ConfigValueTypeError):
      checkers.check_float("section", "name", "str")
    with self.assertRaises(error.ConfigValueTypeError):
      checkers.check_float("section", "name", False)

  def test_check_bool(self):
    self.assertTrue(checkers.check_bool("section", "name", True))
    self.assertFalse(checkers.check_bool("section", "name", False))
    self.assertTrue(checkers.check_bool("section", "name", "yes"))
    self.assertFalse(checkers.check_bool("section", "name", "no"))
    self.assertTrue(checkers.check_bool("section", "name", "true"))
    self.assertFalse(checkers.check_bool("section", "name", "false"))
    self.assertTrue(checkers.check_bool("section", "name", "on"))
    self.assertFalse(checkers.check_bool("section", "name", "off"))
    with self.assertRaises(error.ConfigValueTypeError):
      checkers.check_bool("section", "name", "not_a_bool")
    with self.assertRaises(error.ConfigValueTypeError):
      checkers.check_bool("section", "name", 1)
    with self.assertRaises(error.ConfigValueTypeError):
      checkers.check_bool("section", "name", 1.5)

  def test_check_enum(self):
    with self.assertRaises(error.ConfigValueEnumError):
      checkers.check_enum("section", "name", "toto", ["tata", "tutu"])
    l_val = checkers.check_enum("section", "name", "toto", ["tata", "toto"])
    self.assertEqual(l_val, "toto")

  def test_check_mail(self):
    l_val = checkers.check_mail("section", "name", "xavier@marcelet.com")
    self.assertEqual(l_val, "xavier@marcelet.com")
    checkers.check_mail("section", "name", "xavier@domain.uk.co")
    with self.assertRaises(error.ConfigValueError):
      checkers.check_mail("section", "name", "not an enail")
    with self.assertRaises(error.ConfigValueError):
      checkers.check_mail("section", "name", "not@quite-an-email")

  def test_check_array(self):
    l_val = checkers.check_array("section", "name", "1,2,3,4")
    self.assertEqual(l_val, ["1", "2", "3", "4"])
    l_val = checkers.check_array("section", "name", ["1", "2", "3", "4"])
    self.assertEqual(l_val, ["1", "2", "3", "4"])
    l_val = checkers.check_array("section", "name", "1,2,3,4", p_check=checkers.check_int)
    self.assertEqual(l_val, [1, 2, 3, 4])
    l_value = "on,on;off,no;true,false"
    l_value = checkers.check_array("section", "name", l_value, checkers.is_array(p_check=checkers.check_bool), p_delim=";")
    self.assertEqual(l_value, [[True, True], [False, False], [True, False]])

  def test_check_host(self):
    l_val = checkers.check_host("section", "name", "www.github.com")
    self.assertEqual(l_val, "www.github.com")
    with self.assertRaises(error.ConfigValueError):
      checkers.check_host("section", "name", "www.github.comfdjs")

  def test_check_json(self):
    l_val = checkers.check_json("section", "name", { "a" : 1 })
    self.assertEqual(l_val, { "a" : 1 })
    l_val = checkers.check_json("section", "name", '{ "a" : 1 }')
    self.assertEqual(l_val, { "a" : 1 })
    l_val = checkers.check_json("section", "name", '{}')
    self.assertEqual(l_val, {})
    l_val = checkers.check_json("section", "name", {})
    self.assertEqual(l_val, {})
    with self.assertRaises(error.ConfigValueError):
      l_val = checkers.check_json("section", "name", '{ "a : 1 }')
    with self.assertRaises(error.ConfigValueError):
      l_val = checkers.check_json("section", "name", "{ 'a' : 1 }")


  def test_check_socket(self):
    checkers.check_socket("section", "name", "http://github.com/path?param=1")
    checkers.check_socket("section", "name", "ftp://use:pass@github.com:80/path?param=1")
    checkers.check_socket("section", "name", "http://github.com/path?param=1", p_schemes=['http', 'https'])
    with self.assertRaises(error.ConfigValueError):
      checkers.check_socket("section", "name", "ftp://github.com/", p_schemes=['http', 'https'])
    checkers.check_socket("section", "name", "unix:///var/run/does_not_exists.sock", p_schemes=['unix'], p_checkUnix=False)
    checkers.check_socket("section", "name", "unix:///dev/null",                     p_schemes=['unix'], p_checkUnix=True)
    with self.assertRaises(error.ConfigValueError):
      checkers.check_socket("section", "name", "unix:///var/run/does_not_exists.sock", p_schemes=['unix'], p_checkUnix=True)
    checkers.check_socket("section", "name", "http+unix://%2Fvar%2Frun%2Fdoes_not_exists.sock", p_schemes=['http+unix'], p_checkUnix=False)
    checkers.check_socket("section", "name", "http+unix://%2Fdev%2Fnull",                     p_schemes=['http+unix'], p_checkUnix=True)
    with self.assertRaises(error.ConfigValueError):
      checkers.check_socket("section", "name", "http+unix://%2Fvar%2Frun%2Fdoes_not_exists.sock", p_schemes=['http+unix'], p_checkUnix=True)

if __name__ == "__main__":
  unittest.main()
