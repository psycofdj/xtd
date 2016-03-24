# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import json
import io
import cherrypy
from ..core import logger

#------------------------------------------------------------------#

def log_request_response(p_withResponse):
  def s(p_val):
    if type(p_val) == bytes:
      return p_val.decode("utf-8")
    return p_val

  def print_part(part):
    return {
      "name"    : s(part.name),
      "headers" : { s(x):s(y) for x,y in part.headers.items() },
      "value"   : s(part.fullvalue())
    }

  request = cherrypy.serving.request
  remote = request.remote

  l_data = {
    "request" : {
      "name" : s(remote.name),
      "ip"   : s(remote.ip),
      "line" : s(request.request_line),
      "headers" : { s(x):s(y) for x,y in request.headers.items() },
      "body" : {}
    }
  }

  # Request parameters from URL query string and
  # x-www-form-urlencoded POST data
  if request.body.params:
    l_body = l_data["request"]["body"]
    l_body["params"] = {}
    for name, value in request.body.params.items():
      if not name in l_body["params"]:
        l_body["params"][s(name)] = {}
      if isinstance(value, list):
        for i, item in enumerate(value):
          if not i in l_body["params"][s(name)]:
            l_body["params"][s(name)][i] = {}
          if isinstance(item, cherrypy._cpreqbody.Part):
            l_body["params"][s(name)][i] = print_part(item)
          else:
            l_body["params"][s(name)][i] = {
              "value" : s(item)
            }
      else:
        l_body["params"][s(name)] = s(value)

  if not p_withResponse:
    return l_data

  # If the body is multipart format each of the parts
  if request.body.parts:
    l_body = l_data["request"]["body"]
    l_body["parts"] = {}
    for i, part in enumerate(request.body.parts):
      l_body["parts"][i] = print_part(part)

  l_data["response"] = {
    "status"  : s(cherrypy.response.status),
    "headers" : { s(x):s(y) for x,y in cherrypy.response.header_list },
    "body"    : {
      "chunks" : []
    }
  }

  if not cherrypy.response.stream:
    for c_chunk in cherrypy.response.body:
      l_data["response"]["body"]["chunks"].append(s(c_chunk))
  return l_data

def response_logger(p_module, p_level):
  def handle():
    l_data = log_request_response()
    l_val  = json.dumps(l_data, indent=2)
    for c_line in l_val.split("\n"):
      logger.log(p_level, p_module, c_line)
  return handle


def request_logger(p_module, p_level):
  def handle():
    l_data = log_request_response(False)
    l_val  = json.dumps(l_data, indent=2)
    for c_line in l_val.split("\n"):
      logger.log(p_level, p_module, c_line)
  return handle


def response_logger(p_module, p_level):
  def handle():
    l_data = log_request_response(True)
    l_val  = json.dumps(l_data, indent=2)
    for c_line in l_val.split("\n"):
      logger.log(p_level, p_module, c_line)
  return handle
