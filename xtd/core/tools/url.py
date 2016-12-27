# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#


try:
  from urlparse import urlparse
  from urlparse import urlunparse
  from urllib   import unquote_plus
  from urllib   import quote_plus
except ImportError:
  from urllib.parse import urlparse
  from urllib.parse import urlunparse
  from urllib.parse import unquote_plus
  from urllib.parse import quote_plus

#------------------------------------------------------------------#

def parse_unix(p_url):
  l_unix  = None
  l_parse = urlparse(p_url)
  l_items = list(l_parse)
  if l_items[0].endswith("+unix"):
    l_unix     = unquote_plus(l_items[1])
    l_items[0] = l_items[0][:-5]
    l_items[1] = "localhost"
  elif l_items[0].endswith("unix"):
    l_unix     = l_items[2]
    l_items[0] = "http"
    l_items[1] = "localhost"
    l_items[2] = ""
  return l_items, l_unix

def unparse_unix(p_parsed, p_unix):
  p_parsed = list(p_parsed)
  if p_unix:
    p_parsed[0] = "%s+unix" % p_parsed[0]
    p_parsed[1] = quote_plus(p_unix)
  else:
    p_parsed[0] = "http"
  return urlunparse(p_parsed)


def is_pureunix(p_url):
  return p_url.startswith("unix://")

def parse_pureunix(p_url):
  l_parse = urlparse(p_url)
  return (l_parse.scheme, l_parse.path)

def pureunix_to_unixhttp(p_url, p_https = False):
  l_scheme = "http+unix"
  if p_https:
    l_scheme = "https+unix"
  l_parse = urlparse(p_url)
  l_netloc = quote_plus(l_parse.path)
  l_items = [ l_scheme, l_netloc, "/", "", "", "" ]
  return urlunparse(l_items)
