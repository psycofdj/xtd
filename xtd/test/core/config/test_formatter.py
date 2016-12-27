# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import optparse
import unittest2 as unittest
from xtd.core.config import formatter

#------------------------------------------------------------------#


class FormatterTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(FormatterTest, self).__init__(*p_args, **p_kwds)

  def test_basic(self):
    """
    Nothing really tested, only checks compilation
    """
    l_formatter = formatter.IndentedHelpFormatterWithNL()
    l_formatter.format_description("dsajdsa\ndsadas\nsandsadsadsa\n\n")
    l_option = optparse.Option("-c", action="store", type="complex", dest="c", metavar="VAL")
    l_formatter.format_option(l_option)


if __name__ == "__main__":
  unittest.main(module=__name__)
