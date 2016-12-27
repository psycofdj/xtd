# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import sys
import os
import optparse
import termcolor
import unittest2 as unittest

from xtd.core.logger import formatter

#------------------------------------------------------------------#

class Rec(object):
  def __init__(self):
    pass

#------------------------------------------------------------------#

class LocationFormatterTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(LocationFormatterTest, self).__init__(*p_args, **p_kwds)

  def makeRec(self, p_data = None):
    if p_data == None:
      p_data = {
        "pathname" : "path",
        "lineno" : 20,
        "funcName" : "testfunc"
      }
    l_obj = Rec()
    for c_key, c_val in p_data.items():
      setattr(l_obj, c_key, c_val)
    return l_obj

  def setUp(self, *p_args, **p_kwds):
    if (not p_args) and (not p_kwds):
      p_kwds["locstyle"] = { "colors" : [ "red" ], "attrs" : [ "bold" ] }
    self.m_obj = formatter.LocationFormatter(*p_args, **p_kwds)

  def test__get_loc(self):
    l_rec = self.makeRec()
    l_rawResult = "at path:20 -> testfunc"
    l_coloredResult = termcolor.colored(l_rawResult, "red", attrs=["bold"])
    self.assertEqual(self.m_obj._get_loc(l_rec), l_coloredResult)

    self.setUp(locstyle={ "colors" : [ "red", "on_blue" ], "attrs" : "bold" })
    l_rec = self.makeRec()
    l_rawResult = "at path:20 -> testfunc"
    l_coloredResult = termcolor.colored(l_rawResult, "red", "on_blue", attrs=["bold"])
    self.assertEqual(self.m_obj._get_loc(l_rec), l_coloredResult)

  def test__get_loc_error(self):
    self.setUp(locstyle={ "colors" : [ "red" ], "attrs" : "bold" })
    l_rec = self.makeRec()
    l_rawResult = "at path:20 -> testfunc"
    l_coloredResult = termcolor.colored(l_rawResult, "red", attrs=["bold"])
    self.assertEqual(self.m_obj._get_loc(l_rec), l_coloredResult)

    self.setUp(locstyle={ "colors" : "red", "attrs" : [ "bold" ] })
    l_rec = self.makeRec()
    l_rawResult = "at path:20 -> testfunc"
    l_coloredResult = termcolor.colored(l_rawResult, "red", attrs=["bold"])
    self.assertEqual(self.m_obj._get_loc(l_rec), l_coloredResult)

if __name__ == "__main__":
  unittest.main()
