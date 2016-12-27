# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import sys
import os
import optparse
import termcolor
import unittest2 as unittest

from xtd.core.logger import filter

#------------------------------------------------------------------#

class Rec(object):
  def __init__(self):
    pass

class FilterTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(FilterTest, self).__init__(*p_args, **p_kwds)

  def makeRec(self, p_data = None):
    if p_data == None:
      p_data = {
        "field1" : "field1",
        "field2" : "field2"
      }
    l_obj = Rec()
    for c_key, c_val in p_data.items():
      setattr(l_obj, c_key, c_val)
    return l_obj

  def setUp(self, p_fields = None):
    if p_fields == None:
      p_fields = {
        "field1" : {
          "pad" : "left",
          "styles" : {
            "value1"  : { "colors" : [ "red", "on_yellow" ], "attrs" : [ "bold" ]  },
            "value2"  : { "colors" : [ "blue", "on_red" ] ,  "attrs" : [ "bold" ]  },
            "default" : { "colors" : [ "green", "on_red" ] , "attrs" : [ "blink" ] },
          }
        },
        "field2" : {
          "pad" : "right",
          "styles" : {
            "default" : { "colors" : [ "red", "on_blue" ] , "attrs" : [ "bold" ] }
          }
        }
      }
    self.m_obj = filter.FieldFilter(p_fields)

  def test__pad(self):
    l_rec = self.makeRec()
    self.m_obj._width(l_rec)
    self.m_obj._pad(l_rec)
    self.assertEqual(len(self.m_obj.m_widths.keys()), 2)
    self.assertEqual(self.m_obj.m_widths["field2"], len("field2"))
    self.assertEqual(self.m_obj.m_widths["field2"], len("field2"))
    self.assertEqual(l_rec.field1, "field1")
    self.assertEqual(l_rec.field2, "field2")

    l_rec = self.makeRec({"field1" : "longfield1"})
    self.m_obj._width(l_rec)
    self.m_obj._pad(l_rec)
    self.assertEqual(len(self.m_obj.m_widths.keys()), 2)
    self.assertEqual(self.m_obj.m_widths["field1"], len("longfield1"))
    self.assertEqual(l_rec.field1, "longfield1")

    l_rec = self.makeRec({"field1" : "field1"})
    self.m_obj.m_fields["field1"]["pad"] = "right"
    self.m_obj._width(l_rec)
    self.m_obj._pad(l_rec)
    self.assertEqual(len(self.m_obj.m_widths.keys()), 2)
    self.assertEqual(self.m_obj.m_widths["field1"], len("longfield1"))
    self.assertEqual(l_rec.field1, "    field1")

    self.m_obj.m_fields["field1"]["pad"] = "left"
    l_rec = self.makeRec({"field1" : "field1"})
    self.m_obj._width(l_rec)
    self.m_obj._pad(l_rec)
    self.assertEqual(len(self.m_obj.m_widths.keys()), 2)
    self.assertEqual(self.m_obj.m_widths["field1"], len("longfield1"))
    self.assertEqual(l_rec.field1, "field1    ")

    self.m_obj.m_fields["field1"]["pad"] = "unknown"
    l_rec = self.makeRec({"field1" : "field1"})
    self.m_obj._width(l_rec)
    self.m_obj._pad(l_rec)
    self.assertEqual(len(self.m_obj.m_widths.keys()), 2)
    self.assertEqual(self.m_obj.m_widths["field1"], len("longfield1"))
    self.assertEqual(l_rec.field1, "field1")

  def test__color(self):
    l_rec = self.makeRec()
    self.m_obj._color(l_rec)
    self.assertEqual(l_rec.field1, termcolor.colored("field1", "green", "on_red",  ["blink"]))
    self.assertEqual(l_rec.field2, termcolor.colored("field2", "red",   "on_blue", ["bold"]))

  def test__color_unknown(self):
    self.setUp({
      "field1" : {
        "styles" : {
          "default" : { "colors" : [ "unknown" ], "attrs" : [ "bold" ] }
        }
      }
    })
    l_rec = self.makeRec()
    self.m_obj._color(l_rec)
    self.assertEqual(l_rec.field1, "field1")

  def test__color_invalid(self):
    self.setUp({
      "field1" : {
        "styles" : {
          "colors" : [ "unknown" ], "attrs" : [ "bold" ]
        }
      }
    })
    l_rec = self.makeRec()
    self.m_obj._color(l_rec)
    self.assertEqual(l_rec.field1, "field1")


  def test__color_valued(self):
    self.setUp({
      "field1" : {
        "styles" : {
          "value1" : { "colors" : [ "blue" ], "attrs" : [ "bold" ] },
          "value2" : { "colors" : [ "red" ]  },
          "default" : { "colors" : [ "yellow" ] }
        }
      }
    })
    l_rec = self.makeRec({"field1" : "value1"})
    self.m_obj._color(l_rec)
    self.assertEqual(l_rec.field1, termcolor.colored("value1", "blue", attrs=["bold"]))

    l_rec = self.makeRec({"field1" : "value2"})
    self.m_obj._color(l_rec)
    self.assertEqual(l_rec.field1, termcolor.colored("value2", "red"))

    l_rec = self.makeRec({"field1" : "other value"})
    self.m_obj._color(l_rec)
    self.assertEqual(l_rec.field1, termcolor.colored("other value", "yellow"))


  def test_filter(self):
    self.setUp({
      "field1" : {
        "pad" : "left",
        "styles" : {
          "special" : { },
          "default" : { "colors" : [ "yellow", "on_red" ] }
        }
      }
    })

    l_rec = self.makeRec({"field1" : "value"})
    self.assertEqual(self.m_obj.filter(l_rec), True)
    self.assertEqual(l_rec.field1, termcolor.colored("value", "yellow", "on_red"))

    l_rec = self.makeRec({"field1" : "longvalue"})
    self.assertEqual(self.m_obj.filter(l_rec), True)
    self.assertEqual(l_rec.field1, termcolor.colored("longvalue", "yellow", "on_red"))

    l_rec = self.makeRec({"field1" : "special"})
    self.assertEqual(self.m_obj.filter(l_rec), True)
    self.assertEqual(l_rec.field1, "special  ")

    l_rec = self.makeRec({"field1" : "value"})
    self.assertEqual(self.m_obj.filter(l_rec), True)
    self.assertEqual(l_rec.field1, "%-23s" % termcolor.colored("value", "yellow", "on_red"))

if __name__ == "__main__":
  unittest.main()
