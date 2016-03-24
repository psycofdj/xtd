#!/usr/bin/env python3
# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__version__   = "0.3"

#------------------------------------------------------------------#

from xtd.server.application import ServerApplication

#------------------------------------------------------------------#



def main():
  l_app = ServerApplication("myapp")
  return l_app.execute()

main()

