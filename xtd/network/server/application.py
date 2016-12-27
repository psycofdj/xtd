# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import json
import sys
import cherrypy

from xtd.core                 import logger, config
from xtd.core.config          import checkers
from xtd.core.application     import Application

from .log                   import LogPage
from .counter               import CounterPage
from .config                import ConfigPage
from .param                 import ParamPage
from .manager               import ServerManager


#------------------------------------------------------------------#

class ServerApplication(Application):
  def __init__(self, p_name = sys.argv[0]):
    super(ServerApplication, self).__init__(p_name)

    self.config().register_section("http", "Server Settings", [{
      "name"        : "listen",
      "default"     : "tcp://localhost:8080",
      "description" : "bind server to given socket",
      "checks"      : config.checkers.is_socket(p_schemes=["tcp", "unix"])
    },{
      "name"        : "threads",
      "default"     : 10,
      "description" : "allocate VAL number of work threads",
      "checks"      : config.checkers.is_int(p_min=1)
    },{
      "name"        : "daemonize",
      "default"     : False,
      "description" : "daemonize process at startup"
    },{
      "name"        : "pid-file",
      "default"     : "/tmp/%s.pid",
      "description" : "daemon pid file"
    },{
      "name"        : "admin-password",
      "default"     : None,
      "valued"      : True,
      "description" : "Administrator password for write access to admin web interfaces"
    },{
      "name"        : "tls",
      "default"     : False,
      "description" : "Enable TLS of http server",
      "checks"      : checkers.is_bool()
    },{
      "name"        : "tlscacert",
      "default"     : None,
      "valued"      : True,
      "description" : "TLS CA-Certificate file"
    },{
      "name"        : "tlscert",
      "default"     : None,
      "valued"      : True,
      "description" : "TLS Certificate file"
    },{
      "name"        : "tlskey",
      "default"     : None,
      "valued"      : True,
      "description" : "TLS key file"
    }])

  def _initialize_server(self):
    l_password = config.get("http", "admin-password")
    l_socket   = config.get("http", "listen")
    l_threads  = config.get("http", "threads")

    l_credentials = None
    if l_password:
      l_credentials = { "admin" : l_password }

    ServerManager.initialize(__name__)

    l_tls    = config.get("http", "tls")
    l_cacert = config.get("http", "tlscacert")
    l_cert   = config.get("http", "tlscert")
    l_key    = config.get("http", "tlskey")
    ServerManager.listen(l_socket, l_threads, l_tls, l_cacert, l_cert, l_key)
    ServerManager.mount(self,          "/",              {}, __name__)
    ServerManager.mount(ConfigPage(),  "/admin/config",  {}, __name__)
    ServerManager.mount(CounterPage(), "/admin/counter", {}, __name__)

    l_paramPage = ParamPage(l_credentials)
    ServerManager.mount(l_paramPage,   "/admin/params",   {
      "/write" : {
        'tools.auth_basic.on': True,
        'tools.auth_basic.realm': 'localhost',
        'tools.auth_basic.checkpassword': l_paramPage.check_password
      }
    }, __name__)

    l_logPage = LogPage(l_credentials)
    ServerManager.mount(l_logPage,   "/admin/log",   {
      "/write" : {
        'tools.auth_basic.on': True,
        'tools.auth_basic.realm': 'localhost',
        'tools.auth_basic.checkpassword': l_logPage.check_password
      }
    }, __name__)

    ServerManager.subscribe("exit", super().stop, 100)

  @cherrypy.expose
  @cherrypy.tools.json_out()
  #pylint: disable=unused-argument
  def default(self, *p_args, **p_kwds):
    l_reqinfo = {
      "method"  : cherrypy.request.method,
      "path"    : cherrypy.request.path_info,
      "params"  : cherrypy.request.params,
      "headers" : cherrypy.request.headers
    }
    logger.error(self.m_name, "unhandled request : %s", json.dumps(l_reqinfo))
    cherrypy.response.status = 500
    return {
      "error" : "unhandled request",
      "request" : l_reqinfo
    }

  @staticmethod
  def _check_config():
    l_useTLS = config.get("http", "tls")
    if l_useTLS:
      l_values = [ "tlscacert", "tlscert", "tlskey" ]
      for c_key in l_values:
        l_val = config.get("http", c_key)
        config.set("http", c_key, checkers.is_file("http", c_key, l_val, p_read=True))

  def initialize(self):
    super(ServerApplication, self).initialize()
    self._check_config()
    self._initialize_server()


  def start(self):
    super(ServerApplication, self).start()
    ServerManager.start()

  def join(self):
    ServerManager.join()
    super(ServerApplication, self).join()

  def stop(self):
    super(ServerApplication, self).stop()
    ServerManager.stop()

  def process(self):
    return 0, False
