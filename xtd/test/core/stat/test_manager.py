# -*- coding: utf-8
# pylint: disable=protected-access
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import json
import logging
import tempfile
import shutil
import os
import unittest2 as unittest

from xtd.core              import mixin
from xtd.core.error        import XtdError
from xtd.core.stat.manager import StatManager
from xtd.core.stat.counter import Int32

#------------------------------------------------------------------#


class BaseHandlerTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(BaseHandlerTest, self).__init__(*p_args, **p_kwds)

  def setUp(self):
    mixin.Singleton.reset(StatManager)
    self.m_obj = StatManager()

  def test_register_counter(self):
    self.m_obj.register_counter("a.b.c", Int32("toto"))
    self.m_obj.register_counter("a.b.c", Int32("titi"))
    self.m_obj.register_counter("a.b",   Int32("toto"))

    with self.assertRaises(XtdError):
      self.m_obj.register_counter("a.b.c", Int32("titi"))

    with self.assertRaises(XtdError):
      self.m_obj.register_counter("a.b", object())


  def test_get(self):
    self.m_obj.register_counter("a.b.c", Int32("toto"))
    self.m_obj.register_counter("a.b.c", Int32("titi"))
    self.m_obj.register_counter("a.b",   Int32("toto"))

    self.m_obj.get("a.b.c", "toto")
    self.m_obj.get("a.b.c", "titi")
    self.m_obj.get("a.b",   "toto")

    with self.assertRaises(XtdError):
      self.m_obj.get("a", "toto")

    with self.assertRaises(XtdError):
      self.m_obj.get("a.b", "undef")

  def test_get_json(self):
    self.m_obj.register_counter("a.b.c", Int32("toto", 1))
    self.m_obj.register_counter("a.b.c", Int32("ti.ti", 2))
    self.m_obj.register_counter("a.b",   Int32("toto", 3))
    self.assertDictEqual(self.m_obj.get_json(), {
      "a.b.c" : {
        "toto" : 1,
        "ti.ti" : 2
      },
      "a.b" : {
        "toto" : 3
      }
    })
