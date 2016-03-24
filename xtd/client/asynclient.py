# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import json
import urllib.parse
import io
import pycurl

from ..core import logger

#------------------------------------------------------------------#

class HTTPRequest:
  def __init__(self, p_url, p_method = None, p_headers = {}, p_data = None, p_agent = "xtd/pucyrl"):
    self.m_method  = self._guess_method(p_method, p_data)
    self.m_url     = p_url
    self.m_headers = p_headers
    self.m_data    = p_data
    self.m_agent   = p_agent

  def _guess_method(self, p_method, p_data):
    if not p_method:
      p_method = "GET"
      if p_data:
        p_method = "POST"
    return p_method

class JsonHTTPRequest(HTTPRequest):
  def __init__(self, p_url, p_method = None, p_headers = {}, p_data = None, p_agent = "xtd/pucyrl"):
    p_headers["Content-Type"] = "application/json; charset=utf-8"
    p_data = json.dumps(p_data)
    super().__init__(p_url, p_method, p_headers, p_data, p_agent)


class TCPResponse:
  def __init__(self):
    self.m_error = "uninitialized response"

  def has_error(self):
    return self.m_error != ""

class HTTPResponse(TCPResponse):
  def __init__(self, p_client):
    super().__init__()
    self.m_error       = p_client.m_handle.errstr()
    self.m_data        = None
    self.m_rawdata     = p_client.m_data.getvalue()
    self.m_headers     = p_client.m_headers
    self.m_status_code = p_client.m_handle.getinfo(pycurl.RESPONSE_CODE)
    self.m_mimetype    = "text/plain"
    self.m_encoding    = "iso-8859-1"
    for c_key, c_val in p_kwds.items():
      setattr(self, "m_" + c_key, c_val)
    self._read()

  def _read_ctype(self, p_headers):
    l_encoding = self.m_encoding
    l_mime     = self.m_mimetype
    l_ctype    = p_headers.get("content-type", "")
    l_parts    = l_ctype.split(";", 1)
    l_mime     = l_parts[0].strip()
    if len(l_parts) == 2:
      l_charset = l_parts[1].strip()
      if l_charset.startswith("charset="):
        l_encoding = l_charset[8:]
    return l_mime, l_encoding

  def _read(self):
    self.m_mimetype, self.m_encoding = self._read_ctype(self.m_headers)
    self.m_data    = self.m_rawdata.decode(self.m_encoding)
    if self.m_mimetype == "application/json":
      try:
        self.m_data = json.loads(self.m_data)
      except Exception as l_error:
        self.m_error = str(l_error)

  def has_error(self):
    return self.m_error != ""

  def __getattr__(self, p_name):
    return getattr(self, "m_" + p_name)

class AsyncCurlClient:
  def __init__(self, p_request, p_timeoutMs = 1000, p_curlOpts = {}):
    if type(p_request) == type(""):
      p_request = HTTPRequest(p_url=p_request)
    self.m_request         = p_request
    self.m_timeoutMs       = p_timeoutMs
    self.m_opts            = p_curlOpts
    self.m_response        = None
    self.m_handle          = None
    self.m_data            = None
    self.m_headers         = None
    self.m_handle          = pycurl.Curl()

    self.cleanup()
    self._init_opt()
    self._init_url()
    self._init_method()
    self._init_headers()

    self.m_handle.setopt(pycurl.USERAGENT,      self.m_request.m_agent)
    self.m_handle.setopt(pycurl.HEADERFUNCTION, self._read_header)
    if self.m_timeoutMs:
      self.m_handle.setopt(pycurl.TIMEOUT_MS, self.m_timeoutMs)
    self.m_handle.setopt(pycurl.FOLLOWLOCATION, True)

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.close()

  def cleanup(self):
    self.m_data     = io.BytesIO()
    self.m_headers  = {}
    self.m_response = TCPResponse()
    self.m_handle.setopt(pycurl.WRITEFUNCTION,  self.m_data.write)

  def unix_socket(self, p_path):
    l_value = p_path
    if "unix://" in l_value:
      l_value = l_value[7:]
    self.m_handle.setopt(pycurl.UNIX_SOCKET_PATH, l_value)

  def options(self, p_opts):
    try:
      for c_opt, c_val in p_opts.items():
        self.m_handle.setopt(c_opt, c_val)
    except pycurl.error as l_error:
      logger.error(__name__, "unable to set option '%s' to value '%s'", c_opt, str(c_val))
      raise BaseException(__name__, "unable to set option '%s' to value '%s'" % (c_opt, str(c_val)))

  def _read_header(self, p_line):
    # HTTP standard header encoding
    l_line = p_line.decode("iso-8859-1")
    if not ":" in l_line:
      return
    l_name, l_value = l_line.split(":", 1)
    l_name  = l_name.lower().strip()
    l_value = l_value.strip()
    self.m_headers[l_name] = l_value

  def _init_opt(self):
    try:
      for c_opt, c_val in self.m_opts.items():
        self.m_handle.setopt(c_opt, c_val)
    except pycurl.error as l_error:
      logger.error(__name__, "unable to set option '%s' to value '%s'", c_opt, str(c_val))
      raise BaseException(__name__, "unable to set option '%s' to value '%s'" % (c_opt, str(c_val)))

  def _init_method(self):
    if self.m_request.m_method == "GET":
      self.m_handle.setopt(pycurl.HTTPGET, 1)
    elif self.m_request.m_method == "PUT":
      self.m_handle.setopt(pycurl.HTTPPUT, 1)
    elif self.m_request.m_method == "POST":
      if self.m_request.m_data:
        l_data = self.m_request.m_data
        self.m_handle.setopt(pycurl.POSTFIELDS, l_data)
    elif self.m_request.m_method == "HEAD":
      self.m_handle.setopt(pycurl.NOBODY, 1)
    elif self.m_request.m_method == "DELETE":
      self.m_handle.setopt(pycurl.CUSTOMREQUEST, "DELETE")

  def _init_url(self):
    self.m_handle.setopt(pycurl.URL, self.m_request.m_url)

  def _init_headers(self):
    l_headers = [ "%s: %s" % (x,y) for x,y in self.m_request.m_headers.items() ]
    self.m_handle.setopt(pycurl.HTTPHEADER, l_headers)

  def handle(self):
    return self.m_handle

  def request(self):
    return self.m_request

  def response(self):
    return self.m_response

  def read_response(self):
    self.m_response = HTTPResponse(self)

  def send(self, p_retry = 0):
    l_retry = p_retry
    while l_retry >= 0:
      self.cleanup()

      try:
        self.m_handle.perform()
        self.read_response()
      except pycurl.error as l_error:
        if l_error.args[0] == 28:
          logger.warning(__name__, "timeout on request '%s' : %s", self.m_request.m_url, l_error.args[1])
          self.m_response.m_error = l_error.args[1]
          return False
      if not self.response().has_error():
        return True
      logger.info(__name__, "error on request '%s' (left %d retries left) : %s", self.m_request.m_url, l_retry, self.response().error)
      l_retry -= 1
    logger.error(__name__, "error on request '%s' : %s", self.m_request.m_url, self.response().error)
    return True

  def close(self):
    self.m_handle.close()

class AsyncCurlMultiClient:
  def __init__(self, p_timeoutMs = 1000, p_curlMOpts = {}):
    self.m_opts      = p_curlMOpts
    self.m_handle    = pycurl.CurlMulti()
    self.m_clients   = []
    self.m_timeoutMs = p_timeoutMs
    self._init_opt()

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.close()

  def add_request(self, p_request):
    l_client = AsyncCurlClient(p_request, p_timeoutMs=self.m_timeoutMs)
    return self.add_client(l_client)

  def add_client(self, p_client):
    if not issubclass(p_client.__class__, AsyncCurlClient):
      logger.error(__name__, "cannot add request, must be instance of AsyncCurlClient")
      return False
    self.m_clients += [ p_client ]
    return p_client

  def _init_opt(self):
    try:
      for c_opt, c_val in self.m_opts.items():
        self.m_handle.setopt(c_opt, c_val)
    except pycurl.error as l_error:
      logger.error(__name__, "unable to set option '%s' to value '%s'", c_opt, str(c_val))
      raise BaseException(__name__, "unable to set option '%s' to value '%s'" % (c_opt, str(c_val)))

  def close(self):
    for c_client in self.m_clients:
      c_client.close()
    self.m_handle.close()

  def clients(self, p_ok = True, p_ko = True):
    if p_ok and p_ko:
      l_list = self.m_clients
    elif p_ok:
      l_list = [ x for x in self.m_clients if not x.response().has_error() ]
    else:
      l_list = [ x for x in self.m_clients if x.response().has_error() ]
    return l_list

  def send(self, p_retry = 0):
    for c_client in self.m_clients:
      self.m_handle.add_handle(c_client.m_handle)

    l_list  = self.m_clients
    l_retry = p_retry
    while l_retry >= 0:
      l_status  = True
      l_valids  = [ x for x in l_list if not x.response().has_error() ]
      l_clients = [ x for x in l_list if x.response().has_error()     ]
      l_num     = len(l_clients)

      for c_client in l_valids:
        self.m_handle.remove_handle(c_client.m_handle)

      for c_client in l_clients:
        c_client.cleanup()

      while l_num:
        l_status = self.m_handle.select(0.1)
        if l_status == -1:
          continue
        while True:
          l_ret, l_num = self.m_handle.perform()
          if l_ret != pycurl.E_CALL_MULTI_PERFORM:
            break
        if not self.should_continue():
          break

      for c_client in l_clients:
        c_client.read_response()
        if c_client.response().has_error():
          l_status = False
          logger.info(__name__, "error on request '%s' (left %d retries left) : %s", c_client.m_request.m_url, l_retry, c_client.response().error)

      if l_status:
        return True
      l_list   = l_clients
      l_retry -= 1

    logger.error(__name__, "error on request '%s' : %s", c_client.m_request.m_url, c_client.response().error)
    return False

  def should_continue(self):
    return True

if __name__ == "__main__":
  l_multi = AsyncCurlMultiClient(p_retry=4)
  l_req1 = l_multi.add_request("http://localhost:8889/")
  l_req2 = l_multi.add_request("http://www.google.fr/")
  l_res  = l_multi.send()
  print(str(l_res))
  print(str(l_req1.response().error))
  print(str(l_req2.response().status_code))
  l_multi.close()
