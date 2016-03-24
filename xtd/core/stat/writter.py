# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import requests
import os

from .handler          import StatHandler
from ..                import logger
from ..error.exception import BaseException

#------------------------------------------------------------------#

class DiskWritter(StatHandler):
  def __init__(self, p_directory, p_interval = 50):
    super().__init__(__name__ + "." + __class__.__name__, p_interval)
    self.m_dir = p_directory
    self._create_dir(self.m_dir)

  def _create_dir(self, p_dir):
    if not os.path.isdir(p_dir):
      try:
        os.makedirs(p_dir, mode=0o0750)
      except Exception as l_error:
        raise BaseException(__name__, "unable to create output directory '%s' : %s", p_dir, str(l_error))

  def _write_item(self, p_path, p_name, p_value):
    l_path = os.path.join(self.m_dir, p_path.replace(".", "/"))
    self._create_dir(l_path)
    l_path = os.path.join(l_path, p_name)
    with open(l_path, mode="w") as l_file:
      l_file.write(str(p_value))

  def write(self, p_counters):
    for c_path, c_counter in p_counters.items():
      c_counter.update()
      c_counter.visit(lambda name,val : self._write_item(c_path, name, val))

#------------------------------------------------------------------#

class HttpWritter(StatHandler):
  def __init__(self, p_url, p_interval = 50):
    super().__init__(__name__ + "." + __class__.__name__, p_interval)
    self.m_url = p_url

  def send_request(self, p_json):
    try:
      l_req = requests.post(self.m_url, data=p_json)
      if l_req.status_code != 200:
        logger.error(self.m_name, "timeout received invalid http reponse '%d' on posting json", l_req.status_code)
    except requests.exceptions.RequestException as l_error:
      logger.error(self.m_name, "error while sending counters data : '%s'", str(l_error))

  def write(self, p_counters):
    l_res = {}
    for c_path, c_counter in p_counters.items():
      c_counter.update()
      l_item = l_res
      for c_part in c_path.split("."):
        if not c_part in l_item:
          l_item[c_part] = {}
        l_item = l_item[c_part]
      def visitor(p_name, p_value):
        l_item[p_name] = p_value
      c_counter.visit(visitor)
    self.send_request(l_res)

#------------------------------------------------------------------#
