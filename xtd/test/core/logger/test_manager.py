# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import logging
import unittest2 as unittest

from xtd.core        import logger
from xtd.core.logger import manager
from xtd.core        import error
from xtd.core        import mixin

#------------------------------------------------------------------#

class Rec(object):
  def __init__(self):
    pass

#------------------------------------------------------------------#

class LogManagerTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(LogManagerTest, self).__init__(*p_args, **p_kwds)

  def setUp(self):
    mixin.Singleton.reset(manager.LogManager)
    self.m_obj = manager.LogManager()

  def test_add_formatter(self):
    l_formatter = logging.Formatter()
    self.m_obj.add_formatter("f1", l_formatter)
    self.m_obj.add_formatter("f2", l_formatter)
    with self.assertRaises(error.XtdError):
      self.m_obj.add_formatter("f2", l_formatter)

  def test_get_formatter(self):
    l_f1 = logging.Formatter()
    l_f2 = logging.Formatter()
    self.m_obj.add_formatter("f1", l_f1)
    self.m_obj.add_formatter("f2", l_f2)
    self.assertEqual(l_f1, self.m_obj.get_formatter("f1"))
    self.assertEqual(l_f2, self.m_obj.get_formatter("f2"))
    self.assertNotEqual(self.m_obj.get_formatter("f2"), self.m_obj.get_formatter("f1"))
    with self.assertRaises(error.XtdError):
      self.m_obj.get_formatter("unknown")

  def test_add_filter(self):
    l_filter = logging.Filter()
    self.m_obj.add_filter("f1", l_filter)
    self.m_obj.add_filter("f2", l_filter)
    with self.assertRaises(error.XtdError):
      self.m_obj.add_filter("f2", l_filter)

  def test_get_filter(self):
    l_f1 = logging.Filter()
    l_f2 = logging.Filter()
    self.m_obj.add_filter("f1", l_f1)
    self.m_obj.add_filter("f2", l_f2)
    self.assertEqual(l_f1, self.m_obj.get_filter("f1"))
    self.assertEqual(l_f2, self.m_obj.get_filter("f2"))
    self.assertNotEqual(self.m_obj.get_filter("f2"), self.m_obj.get_filter("f1"))
    with self.assertRaises(error.XtdError):
      self.m_obj.get_filter("unknown")

  def test_add_handler(self):
    l_handler = logging.Handler()
    self.m_obj.add_handler("h1", l_handler)
    self.m_obj.add_handler("h2", l_handler)
    with self.assertRaises(error.XtdError):
      self.m_obj.add_handler("h2", l_handler)

  def test_get_handler(self):
    l_f1 = logging.Handler()
    l_f2 = logging.Handler()
    self.m_obj.add_handler("h1", l_f1)
    self.m_obj.add_handler("h2", l_f2)
    self.assertEqual(l_f1, self.m_obj.get_handler("h1"))
    self.assertEqual(l_f2, self.m_obj.get_handler("h2"))
    self.assertNotEqual(self.m_obj.get_handler("h2"), self.m_obj.get_handler("h1"))
    with self.assertRaises(error.XtdError):
      self.m_obj.get_handler("unknown")

  def test__get_class(self):
    l_class = self.m_obj._get_class("object", { "class" : "logging.handlers.WatchedFileHandler" })
    self.assertEqual(l_class, logging.handlers.WatchedFileHandler)
    l_class = self.m_obj._get_class("object", { "class" : "logging.StreamHandler" })
    self.assertEqual(l_class, logging.StreamHandler)
    with self.assertRaises(error.XtdError):
      l_class = self.m_obj._get_class("object", { "class" : "logging.DoesNotExistsClass" })
    with self.assertRaises(error.XtdError):
      l_class = self.m_obj._get_class("object", { "class" : "doesnotexistsmodule.Class" })
    with self.assertRaises(error.XtdError):
      l_class = self.m_obj._get_class("object", { "class" : "unkown.module.class" })

  def test_load_config(self):
    self.m_obj.load_config()
    self.assertEqual(self.m_obj.m_config, manager.DEFAULT_CONFIG)
    self.m_obj.load_config(None)
    self.assertEqual(self.m_obj.m_config, manager.DEFAULT_CONFIG)
    self.m_obj.load_config({})
    self.assertEqual(self.m_obj.m_config, manager.DEFAULT_CONFIG)

    l_conf = {
      "loggers" : {
        "root" : { "a" : 2 }
      }
    }
    self.m_obj.load_config(l_conf)
    self.assertEqual(self.m_obj.m_config, l_conf)
    self.m_obj.load_config(l_conf, {"handlers" : { "a" : 1 }})
    self.assertEqual(self.m_obj.m_config, {
      "loggers" : {
        "root" : { "a" : 2  }
      },
      "handlers" : { "a" : 1 }
    })
    self.m_obj.load_config(l_conf, {})
    self.assertEqual(self.m_obj.m_config, l_conf)
    with self.assertRaises(error.XtdError):
      self.m_obj.load_config(l_conf, list("notadict"))

  def test_load_filters_invalid(self):
    self.m_obj.load_config({ "invalid" : "conf" })
    self.m_obj._load_filters()
    self.assertEqual(self.m_obj.m_filters, {})

  def test_load_filters_onlyused(self):
    self.m_obj.load_config({
      "handlers" : {
        "root" : {
          "filters" : [ "f2" ]
        }
      },
      "filters" : {
        "f1" : {
          "class" : "logging.Filter"
        },
        "f2" : {
          "class" : "logging.Filter"
        }
      }
    })
    self.m_obj._load_filters()
    self.assertEqual(len(self.m_obj.m_filters), 1)
    self.assertEqual(list(self.m_obj.m_filters.keys())[0], "f2")

  def test_load_filters_noclass(self):
    self.m_obj.load_config({
      "handlers" : {
        "root" : {
          "filters" : [ "f2" ]
        }
      },
      "filters" : {
        "f1" : {
          "param" : "logging.Filter"
        },
        "f2" : {
          "param" : "logging.Filter"
        }
      }
    })
    with self.assertRaises(error.XtdError):
      self.m_obj._load_filters()


  def test_load_filters_error(self):
    self.m_obj.load_config({
      "handlers" : {
        "root" : {
          "filters" : [ "f2" ]
        }
      },
      "filters" : {
        "f2" : {
          "class" : "unkown.module.class"
        }
      }
    })
    with self.assertRaises(error.XtdError):
      self.m_obj._load_filters()

    self.m_obj.load_config({
      "handlers" : {
        "root" : {
          "filters" : [ "f2" ]
        }
      },
      "filters" : {
        "f2" : {
          "class" : "logging.Filter",
          "arg1" : "toto1",
          "arg2" : "toto2",
          "arg3" : "toto3"
        }
      }
    })
    with self.assertRaises(error.XtdError):
      self.m_obj._load_filters()

  def test_load_formatters_invalid(self):
    self.m_obj.load_config({ "invalid" : "conf" })
    self.m_obj._load_formatters()
    self.assertEqual(self.m_obj.m_formatters, {})

  def test_load_formatters_onlyused(self):
    # loads only used formatters
    self.m_obj.load_config({
      "handlers" : {
        "root" : {
          "formatter" : "f2"
        }
      },
      "formatters" : {
        "f1" : {
          "class" : "logging.Formatter"
        },
        "f2" : {
          "class" : "logging.Formatter"
        }
      }
    })
    self.m_obj._load_formatters()
    self.assertEqual(len(self.m_obj.m_formatters), 1)
    self.assertEqual(list(self.m_obj.m_formatters.keys())[0], "f2")

  def test_load_formatters_error(self):
    # loads only used formatters
    self.m_obj.load_config({
      "handlers" : {
        "root" : {
          "formatter" : "f2"
        }
      },
      "formatters" : {
        "f2" : {
          "class" : "unkown.module.class"
        }
      }
    })
    with self.assertRaises(error.XtdError):
      self.m_obj._load_formatters()

    self.m_obj.load_config({
      "handlers" : {
        "root" : {
          "formatter" : "f2"
        }
      },
      "formatters" : {
        "f2" : {
          "class" : "logging.Formatter",
          "arg1" : "toto1",
          "arg2" : "toto2",
          "arg3" : "toto3"
        }
      }
    })
    with self.assertRaises(error.XtdError):
      self.m_obj._load_formatters()


  # ------------------------------------------------------------------------- #

  def test_load_handlers_invalid(self):
    self.m_obj.load_config({ "invalid" : "conf" })
    self.m_obj._load_handlers()
    self.assertEqual(self.m_obj.m_handlers, {})

  def test_load_handlers_nodefaultformat(self):
    self.m_obj.load_config({
      "loggers" : {
        "root" : {
          "handlers" : ["h2"]
        }
      },
      "handlers" : {
        "h1" : {
          "class" : "logging.Handler"
        },
        "h2" : {
          "class" : "logging.Handler"
        }
      }
    })
    with self.assertRaises(error.XtdError):
      self.m_obj._load_handlers()

    self.m_obj.load_config({
      "loggers" : {
        "root" : {
          "handlers" : ["h2"]
        }
      },
      "formatters" : {
        "default" : {
          "class" : "logging.Formatter"
        }
      },
      "handlers" : {
        "h1" : {
          "class" : "logging.Handler"
        },
        "h2" : {
          "class" : "logging.Handler"
        }
      }
    })
    self.m_obj._load_formatters()
    self.m_obj._load_handlers()
    self.assertEqual(len(self.m_obj.m_handlers), 1)
    self.assertEqual(list(self.m_obj.m_handlers.keys())[0], "h2")

  def test_load_handlers_onlyused(self):
    self.m_obj.load_config({
      "loggers" : {
        "root" : {
          "handlers" : ["h2"]
        }
      },
      "formatters" : {
        "default" : {
          "class" : "logging.Formatter"
        }
      },
      "handlers" : {
        "h1" : {
          "class" : "logging.Handler"
        },
        "h2" : {
          "class" : "logging.Handler"
        }
      }
    })
    self.m_obj._load_formatters()
    self.m_obj._load_handlers()
    self.assertEqual(len(self.m_obj.m_handlers), 1)
    self.assertEqual(list(self.m_obj.m_handlers.keys())[0], "h2")

  def test_load_handlers_noclass(self):
    self.m_obj.load_config({
      "loggers" : {
        "root" : {
          "handlers" : ["h2"]
        }
      },
      "formatters" : {
        "default" : {
          "class" : "logging.Formatter"
        }
      },
      "handlers" : {
        "h2" : {
          "attrib" : "logging.Handler"
        }
      }
    })
    self.m_obj._load_formatters()
    with self.assertRaises(error.XtdError):
      self.m_obj._load_handlers()

  def test_load_handlers_error(self):
    self.m_obj.load_config({
      "loggers" : {
        "root" : {
          "handlers" : ["h2"]
        }
      },
      "formatters" : {
        "default" : {
          "class" : "logging.Formatter"
        }
      },
      "handlers" : {
        "h2" : {
          "class" : "doesnotexistmodule.class"
        }
      }
    })
    self.m_obj._load_formatters()
    with self.assertRaises(error.XtdError):
      self.m_obj._load_handlers()

    self.m_obj.load_config({
      "loggers" : {
        "root" : {
          "handlers" : ["h2"]
        }
      },
      "formatters" : {
        "default" : {
          "class" : "logging.Formatter"
        }
      },
      "handlers" : {
        "h2" : {
          "class" : "logging.Handler",
          "doesnotexit" : "value"
        }
      }
    })
    with self.assertRaises(error.XtdError):
      self.m_obj._load_handlers()




  def test_load_handlers_filter(self):
    self.m_obj.load_config({
      "loggers" : {
        "root" : {
          "handlers" : ["h2"]
        }
      },
      "formatters" : {
        "mf1" : {
          "class" : "logging.Formatter"
        }
      },
      "filters" : {
        "f1" : {
          "class" : "logging.Filter"
        }
      },
      "handlers" : {
        "h2" : {
          "class" : "logging.Handler",
          "filters" : [ "f1" ],
          "formatter" : "mf1"
        }
      }
    })
    self.m_obj._load_filters()
    self.m_obj._load_formatters()
    self.m_obj._load_handlers()
    self.assertEqual(len(self.m_obj.m_handlers),    1)
    self.assertEqual(len(self.m_obj.m_formatters),  1)
    self.assertEqual(len(self.m_obj.m_filters),     1)

  def test_load_loggers(self):
    self.m_obj.load_config({
      "loggers" : {
        "root" : {
          "handlers" : ["h2"]
        },
        "a.b.c" : {
          "handlers" : ["h2"]
        }
      },
      "formatters" : {
        "mf1" : {
          "class" : "logging.Formatter"
        }
      },
      "filters" : {
        "f1" : {
          "class" : "logging.Filter"
        }
      },
      "handlers" : {
        "h2" : {
          "class" : "logging.Handler",
          "filters" : [ "f1" ],
          "formatter" : "mf1"
        }
      }
    })
    self.m_obj._load_filters()
    self.m_obj._load_formatters()
    self.m_obj._load_handlers()
    self.m_obj._load_loggers()

  def test_initialize(self):
    l_override = {
      "loggers" : {
        "root" : {
          "handlers" : [ ],
          "level" : 20
        }
      }
    }
    self.m_obj.initialize({}, l_override)
    with self.assertLogs(logger.get()) as l_logs:
      logger.debug(__name__, "test")
      logger.info(__name__, "test")
      logger.warning(__name__, "test")
      logger.error(__name__, "test")
      logger.critical(__name__, "test")
      self.assertEqual(len(l_logs.records), 4)

  def test_dupped_record(self):
    l_override = {
      "loggers" : {
        "root" : {
          "handlers" : [  ],
          "level" : 30
        },
        "test" : {
          "handlers" : [ "h2", "h1" ],
          "level" : 30
        }
      },
      "handlers" : {
        "h2" : {
          "class" : "logging.handlers.MemoryHandler",
          "capacity" : 30,
          "filters" : [ "colored" ]
        },
        "h1" : {
          "class" : "logging.handlers.MemoryHandler",
          "capacity" : 30,
          "filters" : [ ]
        }
      }
    }
    self.m_obj.initialize({}, l_override)
    logger.error("test", "msg")
    l_h1 = self.m_obj.get_handler("h1")   
    l_h2 = self.m_obj.get_handler("h2")   
    self.assertEqual(len(l_h1.buffer), 1)
    self.assertEqual(len(l_h2.buffer), 1)
    self.assertEqual(l_h2.buffer[0].name, "\x1b[1m\x1b[31mtest\x1b[0m")
    self.assertEqual(l_h1.buffer[0].name, "test")

if __name__ == "__main__":
  unittest.main()
