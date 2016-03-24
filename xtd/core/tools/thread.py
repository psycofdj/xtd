# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import threading
import time

from .. import logger

#-----------------------------------------------------------------------------#

class SafeThread(threading.Thread):
    def __init__(self, p_name, p_interval):
      super().__init__(name=p_name)
      self.m_name         = p_name
      self.m_terminated   = False
      self.m_loopInterval = p_interval
      self.m_interrupted  = False

    def work(self):
      raise NotImplemented

    def run(self):
      self.m_terminated = False
      logger.info(self.m_name, "starting thread...")
      while not self.m_terminated:
        logger.debug(self.m_name, "starting loop...")
        self.work()
        logger.debug(self.m_name, "loop ended")
        if not self.m_terminated:
          logger.debug(self.m_name, "sleeping...")
          l_count = self.m_loopInterval
          while l_count and not self.m_terminated:
            time.sleep(1)
            l_count -= 1
      logger.info(self.m_name, "thread ended")

    def stop(self):
      logger.info(self.m_name, "stopping thread...")
      self.m_terminated = True

    def safe_join(self):
      logger.info(self.m_name, "joining thread...")
      while True:
        try:
          self.join(1)
          if not self.isAlive():
            break
        except KeyboardInterrupt:
          logger.warning(self.m_name, "recieved keyboard interrupt, preaparing for exit")
          self.stop()
      logger.info(self.m_name, "thread joined")

#-----------------------------------------------------------------------------#

class SafeThreadGroup:
  def __init__(self, p_name):
    self.m_name    = p_name
    self.m_threads = []

  def add_thread(self, p_obj):
    if not issubclass(p_obj.__class__, SafeThread):
      raise BaseException(self.m_name, "child thread must be SafeThread objects")
    self.m_threads.append(p_obj)

  def start(self):
    logger.debug(self.m_name, "starting all %d threads", len(self.m_threads))
    [ x.start() for x in self.m_threads ]

  def stop(self):
    logger.debug(self.m_name, "stopping all %d threads", len(self.m_threads))
    [ x.stop() for x in self.m_threads ]

  def join(self):
    logger.debug(self.m_name, "joinning all %d threads", len(self.m_threads))
    while True:
      try:
        l_alive = False
        for c_thread in self.m_threads:
          c_thread.join(1)
          l_alive = l_alive or c_thread.isAlive()
        if not l_alive:
          break
      except KeyboardInterrupt:
        logger.warning(self.m_name, "recieved keyboard interrupt, preaparing for exit")
        [ x.stop() for x in self.m_threads ]
    logger.debug(self.m_name, "all %d threads joinned", len(self.m_threads))

#-----------------------------------------------------------------------------#
