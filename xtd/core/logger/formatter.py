# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import logging
import termcolor

#------------------------------------------------------------------#

class FieldFormatter(logging.Formatter):
  def __init__(self, fmt, locfmt, datefmt, fields = {}):
    super().__init__(fmt, datefmt)
    self.m_fmt     = fmt
    self.m_locFmt  = locfmt
    self.m_datefmt = datefmt
    self.m_fields  = fields
    self.m_curFmt  = fmt
    for c_name, c_data in self.m_fields.items():
      c_data["size"] = 0
    self.m_fmt = self._apply_colors(self.m_fmt)

  def _apply_colors(self, p_format):
    l_fmt  = p_format
    l_data = { x:y for x,y in self.m_fields.items() if y.get("colors", None) }
    for c_name, c_data in l_data.items():
      l_args = {}
      for c_color in c_data["colors"]:
        if c_color[0:3] == "on_":
          l_args["on_color"] = c_color
        else:
          l_args["color"] = c_color
      l_args["attrs"] = c_data.get("attrs", [])
      l_origin  = "%%(%s)s" % c_name
      l_replace = termcolor.colored(l_origin, **l_args)
      l_fmt = l_fmt.replace(l_origin, l_replace)
    return l_fmt

  def _update(self):
    l_fmt  = self.m_fmt
    l_data = { x:y for x,y in self.m_fields.items() if y.get("pad", False) }
    for c_name, c_data in l_data.items():
      l_origin  = "%%(%s)s" % c_name
      if c_data["pad"] == "right":
        l_replace = "%%(%s)%ds" % (c_name, c_data["size"])
      else:
        l_replace = "%%(%s)-%ds" % (c_name, c_data["size"])
      l_fmt = l_fmt.replace(l_origin, l_replace)
    self.m_curFmt = l_fmt

  def _monitor(self, p_record):
    l_data = { x:y for x,y in self.m_fields.items() if y.get("pad", False) }
    l_changed = False
    for c_name, c_data in l_data.items():
      l_size = c_data["size"]
      c_data["size"] = max(l_size, len(getattr(p_record, c_name)))
      l_changed = l_changed or (l_size != c_data["size"])
    if l_changed:
      self._update()

  def _get_loc(self, p_record):
    return self.m_locFmt % { x : getattr(p_record, x) for x in dir(p_record) if x[0] != "_" }

  def format(self, p_record):
    self._monitor(p_record)
    l_loc = self._get_loc(p_record)
    self._style._fmt = self.m_curFmt.replace("%(location)s", l_loc)
    return super().format(p_record)
