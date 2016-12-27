# -*- coding: utf-8
# pylint: disable=protected-access
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import json
import logging
import tempfile
import shutil
import os
import unittest2 as unittest

from httmock import urlmatch, HTTMock

from xtd.core.stat.handler import BaseHandler, DiskHandler
from xtd.core.stat.handler import HttpHandler, LoggingHandler
from xtd.core.stat.counter import Int32
from xtd.core.error import XtdError

#------------------------------------------------------------------#


class BaseHandlerTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(BaseHandlerTest, self).__init__(*p_args, **p_kwds)

  def test_write(self):
    l_val = BaseHandler("toto")
    with self.assertRaises(NotImplementedError):
      l_val.write({})

  def test_work(self):
    l_val = BaseHandler("toto")
    with self.assertRaises(NotImplementedError):
      l_val.write({})


class DiskHandlerTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(DiskHandlerTest, self).__init__(*p_args, **p_kwds)

  def test__create_dir(self):
    l_dir      = tempfile.mkdtemp()
    l_adminDir = l_dir + "/a/b/c"

    DiskHandler(l_adminDir)
    self.assertTrue(os.path.isdir(l_adminDir))
    self.assertTrue(os.access(l_adminDir, (os.X_OK | os.R_OK | os.W_OK)))

    with self.assertRaises(XtdError):
      DiskHandler("/perm_denied")

    DiskHandler("/tmp")
    shutil.rmtree(l_dir)

  def _check_file(self, p_path, p_content = None):
    l_status = None
    try:
      l_file = open(p_path, "r")
      if p_content is not None:
        l_content = "".join(l_file.readlines())
        self.assertEqual(p_content, l_content)
      l_file.close()
    except (FileNotFoundError, IOError) as l_error:
      l_status = str(l_error)

    if l_status is not None:
      self.fail("unable to open file '%s' : %s" % (p_path, l_status))

  def test__write_item(self):
    l_dir = tempfile.mkdtemp()
    l_obj = DiskHandler(l_dir)

    l_obj._write_item("a.b.c", "d.e", 20)
    self._check_file(l_dir + "/a/b/c/d.e", "20")

    with self.assertLogs(logging.getLogger("xtd.core.stat.handler.DiskHandler")):
      l_obj._write_item("a.b.c", "../../../../../d.e", 20)

    l_obj = DiskHandler("/etc/")
    with self.assertRaises(XtdError):
      l_obj._write_item("a.b.c", "d.e", 20)

    shutil.rmtree(l_dir)


  def test_write(self):
    l_dir = tempfile.mkdtemp()

    DiskHandler(l_dir).write({
      "a.b.c" : [ Int32("toto", 20), Int32("titi", 100) ],
      "a.b"   : [ Int32("toto", 55)                     ]
    })

    self._check_file(l_dir + "/a/b/c/toto", "20")
    self._check_file(l_dir + "/a/b/c/titi", "100")
    self._check_file(l_dir + "/a/b/toto",   "55")

    shutil.rmtree(l_dir)


class HttpHandlerTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(HttpHandlerTest, self).__init__(*p_args, **p_kwds)

  @urlmatch(netloc="localhost")
  def _handle_req(self, p_url, p_request):
    self.assertEqual(p_request.method, "POST")
    self.assertEqual(p_request.headers["Content-Type"], "application/json")
    l_json = json.loads(p_request.body)
    self.assertDictEqual(l_json, {
      "a.b.c" : {
        "toto" : 20,
        "titi" : 100
      },
      "a.b" : {
        "toto" : 55,
        "c.d" : 106
      }
    })
    return {'status_code': 200}

  @urlmatch(netloc="localhost")
  def _make_error(self, p_url, p_request):
    return {'status_code': 500}

  @urlmatch(netloc="localhost")
  def _unknown(self, p_url, p_request):
    return {'status_code': 200}

  def test_write(self):
    with HTTMock(self._handle_req):
      HttpHandler("http://localhost/json").write({
        "a.b.c" : [ Int32("toto", 20), Int32("titi", 100) ],
        "a.b"   : [ Int32("toto", 55), Int32("c.d",  106) ]
      })

    with HTTMock(self._make_error):
      l_logger = logging.getLogger("xtd.core.stat.handler.HttpHandler")
      with self.assertLogs(l_logger, level="ERROR") as l_logs:
        HttpHandler("http://localhost/json").write({
          "a.b.c" : [ Int32("toto", 20), Int32("titi", 100) ],
          "a.b"   : [ Int32("toto", 55), Int32("c.d",  106) ]
        })



class LoggingHandlerTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(LoggingHandlerTest, self).__init__(*p_args, **p_kwds)

  @urlmatch(netloc="localhost")
  def _handle_req(self, p_url, p_request):
    self.assertEqual(p_request.method, "POST")
    self.assertEqual(p_request.headers["Content-Type"], "application/json")
    l_json = json.loads(p_request.body)
    self.assertDictEqual(l_json, {
      "a.b.c" : {
        "toto" : 20,
        "titi" : 100
      },
      "a.b" : {
        "toto" : 55,
        "c.d" : 106
      }
    })
    return {'status_code': 200}

  def test_write(self):
    with self.assertLogs("logger", "INFO") as l_data:
      LoggingHandler("logger").write({
        "a.b.c" : [ Int32("toto", 20), Int32("titi", 100) ],
        "a.b"   : [ Int32("toto", 55), Int32("c.d",  106) ]
      })
      self.assertEqual(len(l_data.records), 4)

# Local Variables:
# ispell-local-dictionary: "american"
# End:
