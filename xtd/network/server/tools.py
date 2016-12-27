# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__version__   = "0.3"

#------------------------------------------------------------------#

import json
import cherrypy

from xtd.core import logger, error, stat

#------------------------------------------------------------------#

def log_request_response(p_withResponse):
  def enc(p_val):
    if isinstance(p_val, bytes):
      return p_val.decode("utf-8")
    return p_val

  def print_part(p_part):
    return {
      "name"    : enc(p_part.name),
      "headers" : { enc(x):enc(y) for x,y in p_part.headers.items() },
      "value"   : enc(p_part.fullvalue())
    }

  l_request = cherrypy.serving.request
  l_remote  = l_request.remote

  l_data = {
    "request" : {
      "name"    : enc(l_remote.name),
      "ip"      : enc(l_remote.ip),
      "line"    : enc(l_request.request_line),
      "headers" : { enc(x):enc(y) for x,y in l_request.headers.items() },
      "body"    : {}
    }
  }

  # Request parameters from URL query string and
  # x-www-form-urlencoded POST data
  if l_request.body.params:
    l_body = l_data["request"]["body"]
    l_body["params"] = {}
    for c_name, c_value in l_request.body.params.items():
      if not c_name in l_body["params"]:
        l_body["params"][enc(c_name)] = {}
      if isinstance(c_value, list):
        for c_pos, c_item in enumerate(c_value):
          if not c_pos in l_body["params"][enc(c_name)]:
            l_body["params"][enc(c_name)][c_pos] = {}
          # pylint: disable=protected-access
          if isinstance(c_item, cherrypy._cpreqbody.Part):
            l_body["params"][enc(c_name)][c_pos] = print_part(c_item)
          else:
            l_body["params"][enc(c_name)][c_pos] = {
              "value" : enc(c_item)
            }
      else:
        l_body["params"][enc(c_name)] = enc(c_value)

  if not p_withResponse:
    return l_data

  # If the body is multipart format each of the parts
  if l_request.body.parts:
    l_body = l_data["request"]["body"]
    l_body["parts"] = {}
    for c_pos, c_part in enumerate(l_request.body.parts):
      l_body["parts"][c_pos] = print_part(c_part)

  l_headers = {}
  if cherrypy.response.header_list:
    l_headers = { enc(x):enc(y) for x,y in cherrypy.response.header_list }
  l_data["response"] = {
    "status"  : enc(cherrypy.response.status),
    "headers" : l_headers,
    "body"    : {
      "chunks" : []
    }
  }

  if not cherrypy.response.stream:
    try:
      for c_chunk in cherrypy.response.body:
        l_data["response"]["body"]["chunks"].append(enc(c_chunk))
    except BaseException:
      l_data["response"]["body"]["chunks"] = []
  return l_data

def request_logger():
  #pylint: disable=invalid-name
  def handle(level, module):
    l_data = log_request_response(False)
    l_val  = json.dumps(l_data, indent=2)
    for c_line in l_val.split("\n"):
      logger.log(level, module, c_line)
  return handle


def response_logger():
  #pylint: disable=invalid-name
  def handle(level, module):
    l_data = log_request_response(True)
    l_val  = json.dumps(l_data, indent=2)
    for c_line in l_val.split("\n"):
      logger.log(level, module, c_line)
  return handle

def perf_begin():
  #pylint: disable=invalid-name
  def handle(ns, name):
    try:
      l_counter = stat.manager.StatManager().get(ns, name)
    except error.XtdError:
      l_counter = stat.counter.Perf(name)
      stat.manager.StatManager().register_counter(ns, l_counter)
    l_counter.work_begin()
  return handle

def perf_end():
  #pylint: disable=invalid-name
  def handle(ns, name):
    try:
      l_counter = stat.manager.StatManager().get(ns, name)
    except error.XtdError:
      l_counter = stat.counter.Perf(name)
      stat.manager.StatManager().register_counter(ns, l_counter)
    l_counter.work_end()
  return handle

class JsonHTTPError(cherrypy.HTTPError):
  def __init__(self, p_status, p_message):
    super(JsonHTTPError, self).__init__(p_status, p_message)
    self.m_message = p_message

  def set_response(self):
    cherrypy.response.status = self.code
    cherrypy.response.headers["Content-Type"] = "application/json"
    cherrypy.response.body = json.dumps({
      "status"  : "%d - %s" % (self.code, self.reason),
      "message" : self.m_message
    }).encode("utf-8")
