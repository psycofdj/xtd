# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import unittest2 as unittest

from xtd.core.tools  import url

#------------------------------------------------------------------#


class UrlTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(UrlTest, self).__init__(*p_args, **p_kwds)

  def test_parse_unix(self):
    l_parts, l_unix = url.parse_unix("http://localhost:80/path?param=1")
    self.assertEqual(l_parts[:2], ["http", "localhost:80"])
    self.assertEqual(l_unix, None)

    l_parts, l_unix = url.parse_unix("http+unix://%2Fvar%2Frun%2Fdocker.sock/path?param=1")
    self.assertEqual(l_unix, "/var/run/docker.sock")
    self.assertEqual(l_parts[:2], ["http", "localhost"])

    l_parts, l_unix = url.parse_unix("https+unix://%2Fvar%2Frun%2Fdocker.sock/path?param=1")
    self.assertEqual(l_unix, "/var/run/docker.sock")
    self.assertEqual(l_parts[:2], ["https", "localhost"])

    l_parts, l_unix = url.parse_unix("unix:///var/run/docker.sock")
    self.assertEqual(l_unix, "/var/run/docker.sock")
    self.assertEqual(l_parts[:2], ["http", "localhost"])

  def test_unparse_unix(self):
    l_parts, l_unix = url.parse_unix("http+unix://%2Fvar%2Frun%2Fdocker.sock/path?param=1")
    self.assertEqual(l_unix, "/var/run/docker.sock")
    self.assertEqual(l_parts[:2], ["http", "localhost"])
    l_parts[2] = "/path/to/toto"
    l_url = url.unparse_unix(l_parts, l_unix)
    self.assertEqual(l_url, "http+unix://%2Fvar%2Frun%2Fdocker.sock/path/to/toto?param=1")

    l_parts, l_unix = url.parse_unix("http://localhost:80/path?param=1")
    self.assertEqual(l_parts[:2], ["http", "localhost:80"])
    self.assertEqual(l_unix, None)
    l_parts[1] = "localhost:8888"
    l_url = url.unparse_unix(l_parts, l_unix)
    self.assertEqual(l_url, "http://localhost:8888/path?param=1")


if __name__ == "__main__":
  unittest.main(module=__name__)
