# -*- coding: utf-8
#------------------------------------------------------------------#
"""
.. contents::


Introduction
============

What is XTD ?
-------------

XTD is a library that provides a very high levels set of tools designed
to efficiently develop industrial-level python softwares.


Features
--------

* Static application

  * Unified command line & file configuration
  * Ready to use logging facility
  * Crash-persistent memory data
  * Statistic measurements and output

* Web application

  * Everything included in static application
  * Ready to use web server (cherrypy based)
  * HTTP api to access

    * logs
    * statistics
    * persistent parameters


Compatibility
-------------

.. warning:: Python 3.x


Installation
------------

..  code-block:: bash

 sudo pip3 install xtd


Get Started
===========


Basic Application
-----------------

XTD is designed to develop your software by inheriting the main
:py:class:`~xtd.core.application.Application` object.


Example :

..  literalinclude:: _static/base.py
     :language: python
     :linenos:


Input options
-------------

XTD provides a way to declare and read command-line and file configuration
options in a unified way. An option:

  * is registered with an unique ``name`` and belongs to a ``section``
  * is attached to zero-or-more ``checks`` that will validate input values



Command-line & File config
^^^^^^^^^^^^^^^^^^^^^^^^^^

User can provides values to options in 3 different ways :

  * from internal default value
  * from command line with ``--<section>-<name> VALUE`` option
  * from program's json configuration file with ``{"<section>": {"<name>": VALUE}}``

When multiple values are available, they are taken with the following order of priority
(from lowest to highest) :

  1. registered default value
  2. value in configuration file
  3. value on command-line


Registering options
^^^^^^^^^^^^^^^^^^^

Arguments are registered with the
:py:meth:`~xtd.core.config.manager.ConfigManager.register` and
:py:meth:`~xtd.core.config.manager.ConfigManager.register_section` methods
of the :py:class:`~xtd.core.config.manager.ConfigManager` (singleton) object

This :py:class:`~xtd.core.config.manager.ConfigManager` is accessible via the
:py:meth:`~xtd.core.application.Application.config` method of your
:py:class:`~xtd.core.application.Application` or directly from the singleton.

.. note::
   Full option documentation available at :class:`~xtd.core.config.manager.Option`

   Standard check functions :mod:`~xtd.core.config.checkers`


The following code:

..  literalinclude:: _static/options.py
  :language: python
  :linenos:
  :emphasize-lines: 10-26


Produces :


..  literalinclude:: _static/options_output.txt
  :linenos:
  :emphasize-lines: 11-13, 19-20


Reading options
^^^^^^^^^^^^^^^

Nothing simpler than reading option values.

From your :py:class:`~xtd.core.application.Application` object:

.. code-block:: python

   import xtd.core.application

   class MyApp(xtd.core.application.Application):
     def process(self):
       l_inputDir   = self.config().get("input", "directory")
       l_count      = self.config().get("input", "count")
       l_outputFile = self.config().get("output", "file")


Or, from anywhere in your code :

.. code-block:: python

   from xtd.core import config

   def my_function(self):
     l_inputDir   = config.get("input", "directory")
     l_count      = config.get("input", "count")
     l_outputFile = config.get("output", "file")



.. note:: The :py:meth:`xtd.core.application.Application.initialize` method
   has to be called before you attempt to read options values.





Logging
-------

Features
^^^^^^^^

* standard python logging module compliant

* ``logger.<level>(<module>, <message>)`` primitives in addition to the standard
  ``logging.getLogger(<module>).<level>(<message>)`` functions

* rich default configuration including:

  * standard :py:class:`~logging.handlers.SysLogHandler` bound to ``/dev/log``
    socket

  * standard :py:class:`~logging.handlers.RotatingFileHandler` bound to `./out.log`

  * standard :py:class:`~logging.StreamHandler` bound to `sys.stdout`
    This particular handler is setup with a special Formatter
    :py:class:`~xtd.core.logger.formatter.LocationFormatter` who
    **pads** fields to help with vertical reading and **colorizes** record fields
    depending on their value








Configuration
^^^^^^^^^^^^^

By default, :py:class:`~xtd.core.application.Application` defines two unified
options that changes the logging behavior:

* ``--log-config``: full logging configuration in json format. Details about
  configuration format is available in object
  :py:class:`~xtd.core.logger.manager.LogManager`

* ``--log-override``: partial logging configuration that will be merged on
  top of full configuration. This option respect the same format as the full
  format except that you may only specify parts. This is useful when you
  want to override the log level for a specific module on the command line
  while the rest of the configuration is in the configuration file

.. note:: Even we use command line options, keep in mind that they always have their
  configuration file equivalent


Example:

.. code-block:: bash

  $ # activate log-level 10 (debug) for module "a.b.c"
  $ python myapp.py --log-override='{"handler" : {"a.b.c" : { "level" : 10 } } }'


Demo
^^^^

.. image:: _static/option_log.png


Persistent data
---------------

.. todo:: some doc

Statistics
----------

.. todo:: some doc


"""

__project__      = "xtd"
__description__  = "High level library to quickly build strong python apps"
__version__      = "0.6.0"
__copyright__    = "GPL 3"
__author__       = "Xavier MARCELET <xavier@marcelet.com>"
__url__          = "https://github.com/psycofdj/xtdpy"
__download_url__ = "https://github.com/psycofdj/xtdpy/tarball/%s" % __version__
__keywords__     = ['xtd', 'python', 'library', 'high-level']
__classifiers__  = [
  "Development Status :: 2 - Pre-Alpha",
  "Environment :: Console",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
  "Operating System :: Unix",
  "Programming Language :: Python :: 2",
  "Programming Language :: Python :: 3",
  "Topic :: Software Development :: Libraries :: Python Modules"
]



#------------------------------------------------------------------#

# Local Variables:
# ispell-local-dictionary: "american"
# End:

#  LocalWords:  cherrypy
