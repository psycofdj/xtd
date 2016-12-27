# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import optparse
import unittest2 as unittest

from xtd.core.config import manager
from xtd.core        import error
from xtd.core        import mixin, config
from future.utils    import with_metaclass

#------------------------------------------------------------------#

class CrashDoll(with_metaclass(mixin.Singleton, object)):
  def __init__(self):
    self.m_attr = None
  def setAttr(self, p_attr):
    self.m_attr = p_attr

class SingletonTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(SingletonTest, self).__init__(*p_args, **p_kwds)

  def test_construct(self):
    l_obj = CrashDoll()
    self.assertEqual(None, l_obj.m_attr)
    l_obj.setAttr(True)
    self.assertTrue(l_obj.m_attr)
    l_obj2 = CrashDoll()
    self.assertTrue(l_obj2.m_attr)

  def test_reset(self):
    l_obj3 = CrashDoll()
    self.assertTrue(l_obj3.m_attr)
    mixin.Singleton.reset(CrashDoll)
    l_obj4 = CrashDoll()
    self.assertEqual(None, l_obj4.m_attr)

#------------------------------------------------------------------#


if __name__ == "__main__":
  unittest.main()
