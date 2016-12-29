# -*- coding: utf-8
#------------------------------------------------------------------#
from __future__ import print_function

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

try:
  from urlparse import urlunparse
except ImportError:
  from urllib.parse import urlunparse


import json
import io

# pylint: disable=import-error
import pycurl

from xtd.core       import logger
from xtd.core.tools import url
from xtd.core.error import XtdError

#------------------------------------------------------------------#

#pylint: disable=line-too-long
CURL_ERRORS = {
  "1"  : "Unsupported protocol. This build of curl has no support for this protocol.",
  "2"  : "Failed to initialize.",
  "3"  : "URL malformed. The syntax was not correct.",
  "4"  : "A feature or option that was needed to perform the desired request was not enabled or was explicitly disabled at build-time. To make curl able to do this, you probably need another build of libcurl!",
  "5"  : "Couldn't resolve proxy. The given proxy host could not be resolved.",
  "6"  : "Couldn't resolve host. The given remote host was not resolved.",
  "7"  : "Failed to connect to host.",
  "8"  : "FTP weird server reply. The server sent data curl couldn't parse.",
  "9"  : "FTP access denied. The server denied login or denied access to the particular resource or directory you wanted to reach. Most often you tried to change to a directory that doesn't exist on the server.",
  "11" : "FTP weird PASS reply. Curl couldn't parse the reply sent to the PASS request.",
  "13" : "FTP weird PASV reply, Curl couldn't parse the reply sent to the PASV request.",
  "14" : "FTP weird 227 format. Curl couldn't parse the 227-line the server sent.",
  "15" : "FTP can't get host. Couldn't resolve the host IP we got in the 227-line.",
  "17" : "FTP couldn't set binary. Couldn't change transfer method to binary.",
  "18" : "Partial file. Only a part of the file was transferred.",
  "19" : "FTP couldn't download/access the given file, the RETR (or similar) command failed.",
  "21" : "FTP quote error. A quote command returned error from the server.",
  "22" : "HTTP page not retrieved. The requested url was not found or returned another error with the HTTP error code being 400 or above. This return code only appears if -f, --fail is used.",
  "23" : "Write error. Curl couldn't write data to a local filesystem or similar.",
  "25" : "FTP couldn't STOR file. The server denied the STOR operation, used for FTP uploading.",
  "26" : "Read error. Various reading problems.",
  "27" : "Out of memory. A memory allocation request failed.",
  "28" : "Operation timeout. The specified time-out period was reached according to the conditions.",
  "30" : "FTP PORT failed. The PORT command failed. Not all FTP servers support the PORT command, try doing a transfer using PASV instead!",
  "31" : "FTP couldn't use REST. The REST command failed. This command is used for resumed FTP transfers.",
  "33" : "HTTP range error. The range 'command' didn't work.",
  "34" : "HTTP post error. Internal post-request generation error.",
  "35" : "SSL connect error. The SSL handshaking failed.",
  "36" : "FTP bad download resume. Couldn't continue an earlier aborted download.",
  "37" : "FILE couldn't read file. Failed to open the file. Permissions?",
  "38" : "LDAP cannot bind. LDAP bind operation failed.",
  "39" : "LDAP search failed.",
  "41" : "Function not found. A required LDAP function was not found.",
  "42" : "Aborted by callback. An application told curl to abort the operation.",
  "43" : "Internal error. A function was called with a bad parameter.",
  "45" : "Interface error. A specified outgoing interface could not be used.",
  "47" : "Too many redirects. When following redirects, curl hit the maximum amount.",
  "48" : "Unknown option specified to libcurl. This indicates that you passed a weird option to curl that was passed on to libcurl and rejected. Read up in the manual!",
  "49" : "Malformed telnet option.",
  "51" : "The peer's SSL certificate or SSH MD5 fingerprint was not OK.",
  "52" : "The server didn't reply anything, which here is considered an error.",
  "53" : "SSL crypto engine not found.",
  "54" : "Cannot set SSL crypto engine as default.",
  "55" : "Failed sending network data.",
  "56" : "Failure in receiving network data.",
  "58" : "Problem with the local certificate.",
  "59" : "Couldn't use specified SSL cipher.",
  "60" : "Peer certificate cannot be authenticated with known CA certificates.",
  "61" : "Unrecognized transfer encoding.",
  "62" : "Invalid LDAP URL.",
  "63" : "Maximum file size exceeded.",
  "64" : "Requested FTP SSL level failed.",
  "65" : "Sending the data requires a rewind that failed.",
  "66" : "Failed to initialise SSL Engine.",
  "67" : "The user name, password, or similar was not accepted and curl failed to log in.",
  "68" : "File not found on TFTP server.",
  "69" : "Permission problem on TFTP server.",
  "70" : "Out of disk space on TFTP server.",
  "71" : "Illegal TFTP operation.",
  "72" : "Unknown TFTP transfer ID.",
  "73" : "File already exists (TFTP).",
  "74" : "No such user (TFTP).",
  "75" : "Character conversion failed.",
  "76" : "Character conversion functions required.",
  "77" : "Problem with reading the SSL CA cert (path? access rights?).",
  "78" : "The resource referenced in the URL does not exist.",
  "79" : "An unspecified error occurred during the SSH session.",
  "80" : "Failed to shut down the SSL connection.",
  "82" : "Could not load CRL file, missing or wrong format (added in 7.19.0).",
  "83" : "Issuer check failed (added in 7.19.0).",
  "84" : "The FTP PRET command failed",
  "85" : "RTSP: mismatch of CSeq numbers",
  "86" : "RTSP: mismatch of Session Identifiers",
  "87" : "unable to parse FTP file list",
  "88" : "FTP chunk callback reported error",
  "89" : "No connection available, the session will be queued",
  "90" : "SSL public key does not matched pinned public key"
}

#------------------------------------------------------------------#

class HTTPRequest(object):
  def __init__(self, p_url, p_method=None, p_headers=None, p_data=None, p_agent="xtd/pucyrl"):
    self.m_method  = self._guess_method(p_method, p_data)
    self.m_url     = p_url
    self.m_data    = p_data
    self.m_agent   = p_agent
    self.m_headers = p_headers
    if p_headers is None:
      self.m_headers = {}

  @staticmethod
  def _guess_method(p_method, p_data):
    if not p_method:
      p_method = "GET"
      if p_data:
        p_method = "POST"
    return p_method

class JsonHTTPRequest(HTTPRequest):
  def __init__(self, p_url, p_method=None, p_headers=None, p_data=None, p_agent="xtd/pucyrl"):
    if p_headers is None:
      p_headers = {}
    p_headers["Content-Type"] = "application/json; charset=utf-8"
    p_data = json.dumps(p_data)
    super(JsonHTTPRequest, self).__init__(p_url, p_method, p_headers, p_data, p_agent)


class TCPResponse(object):
  def __init__(self):
    self.m_error = "uninitialized response"

  def has_error(self):
    return self.m_error != ""

class HTTPResponse(TCPResponse):
  def __init__(self, p_client):
    super(HTTPResponse, self).__init__()
    self.m_error       = p_client.m_handle.errstr()
    self.m_data        = None
    self.m_rawdata     = p_client.m_data.getvalue()
    self.m_headers     = p_client.m_headers
    self.m_statusCode  = p_client.m_handle.getinfo(pycurl.RESPONSE_CODE)
    self.m_mimetype    = "text/plain"
    self.m_encoding    = "iso-8859-1"
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

  def has_error(self):
    return self.m_error != ""



class AsyncCurlClient(object):
  def __init__(self, p_request, p_timeoutMs = 1000, p_curlOpts=None):
    if isinstance(p_request, str):
      p_request = HTTPRequest(p_url=p_request)
    self.m_request   = p_request
    self.m_timeoutMs = p_timeoutMs
    self.m_response  = None
    self.m_handle    = None
    self.m_data      = None
    self.m_headers   = None
    self.m_handle    = pycurl.Curl()
    self.m_opts      = p_curlOpts
    if p_curlOpts is None:
      self.m_opts = {}

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

  @staticmethod
  def _error_from_core(p_code):
    l_code = str(p_code)
    if l_code in CURL_ERRORS:
      return CURL_ERRORS[l_code]
    return "unknown curl curl '%s'" % l_code

  def __enter__(self):
    return self

  def __exit__(self, p_type, p_value, p_traceback):
    self.close()

  def cleanup(self):
    self.m_data     = io.BytesIO()
    self.m_headers  = {}
    self.m_response = TCPResponse()
    self.m_handle.setopt(pycurl.WRITEFUNCTION,  self.m_data.write)

  def enable_tls(self, p_cacert, p_cert, p_key):
    self.m_handle.setopt(pycurl.CAINFO,         p_cacert)
    self.m_handle.setopt(pycurl.SSLCERT,        p_cert)
    self.m_handle.setopt(pycurl.SSLKEY,         p_key)
    self.m_handle.setopt(pycurl.SSL_VERIFYPEER, True)

  def options(self, p_opts):
    try:
      for c_opt, c_val in p_opts.items():
        self.m_handle.setopt(c_opt, c_val)
    except pycurl.error:
      logger.error(__name__, "unable to set option '%s' to value '%s'", c_opt, str(c_val))
      raise XtdError(__name__, "unable to set option '%s' to value '%s'" % (c_opt, str(c_val)))

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
    except pycurl.error:
      logger.error(__name__, "unable to set option '%s' to value '%s'", c_opt, str(c_val))
      raise XtdError(__name__, "unable to set option '%s' to value '%s'" % (c_opt, str(c_val)))

  def _init_method(self):
    if self.m_request.m_method == "GET":
      self.m_handle.setopt(pycurl.HTTPGET, 1)
    elif self.m_request.m_method == "PUT":
      self.m_handle.setopt(pycurl.PUT, 1)
    elif self.m_request.m_method == "POST":
      if self.m_request.m_data:
        l_data = self.m_request.m_data
        self.m_handle.setopt(pycurl.POSTFIELDS, l_data)
      else:
        self.m_handle.setopt(pycurl.CUSTOMREQUEST, "POST")
    elif self.m_request.m_method == "HEAD":
      self.m_handle.setopt(pycurl.NOBODY, 1)
    elif self.m_request.m_method == "DELETE":
      self.m_handle.setopt(pycurl.CUSTOMREQUEST, "DELETE")

  def _init_url(self):
    l_parsed, l_unix = url.parse_unix(self.m_request.m_url)
    l_url            = urlunparse(l_parsed)
    self.m_handle.setopt(pycurl.URL, l_url)
    if l_unix:
      # pylint: disable=no-member
      self.m_handle.setopt(pycurl.UNIX_SOCKET_PATH, l_unix)

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
        l_code = l_error.args[0]
        if l_code == 28:
          logger.warning(__name__, "timeout on request '%s' : %s", self.m_request.m_url, l_error.args[1])
          self.m_response.m_error = l_error.args[1]
          return False
        else:
          self.m_response.m_error = "curl error : %s" % self._error_from_core(l_code)
      if not self.response().has_error():
        return True
      logger.info(__name__, "error on request '%s' (left %d retries left) : %s", self.m_request.m_url, l_retry, self.response().m_error)
      l_retry -= 1
    logger.error(__name__, "error on request '%s' : %s", self.m_request.m_url, self.response().m_error)
    return False

  def close(self):
    self.m_handle.close()

class AsyncCurlMultiClient(object):
  def __init__(self, p_timeoutMs=1000, p_curlMOpts=None):
    self.m_handle    = pycurl.CurlMulti()
    self.m_clients   = []
    self.m_timeoutMs = p_timeoutMs
    self.m_opts      = p_curlMOpts
    if p_curlMOpts is None:
      self.m_opts = {}

    self._init_opt()

  def __enter__(self):
    return self

  def __exit__(self, p_type, p_value, p_traceback):
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
    except pycurl.error:
      logger.error(__name__, "unable to set option '%s' to value '%s'", c_opt, str(c_val))
      raise XtdError(__name__, "unable to set option '%s' to value '%s'" % (c_opt, str(c_val)))

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

  #pylint: disable=no-self-use
  def should_continue(self):
    return True

if __name__ == "__main__":
  def test():
    l_multi = AsyncCurlMultiClient()
    l_req1 = l_multi.add_request("http://localhost:8889/")
    l_req2 = l_multi.add_request("http://www.google.fr/")
    l_res  = l_multi.send(p_retry=4)
    print(str(l_res))
    print(str(l_req1.response().m_error))
    print(str(l_req2.response().m_statusCode))
    l_multi.close()
  test()
