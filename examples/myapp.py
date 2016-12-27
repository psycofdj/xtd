#!/usr/bin/env python
# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

# piece of code to use local xtd library, don't do this in in real life
import sys
sys.path.insert(0, "..")

from xtd.core.application import Application
from xtd.core             import logger

#------------------------------------------------------------------#

class MyApp(Application):
  def __init__(self):
    super().__init__("myapp")

  def process(self):
    logger.debug("test", "test log format %d", 5)
    return 0, True

def main():
  l_app = MyApp()
  return l_app.execute()

main()


# Local Variables:
# ispell-local-dictionary: "american"
# End:
