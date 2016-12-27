# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import threading
import logging
import termcolor

#------------------------------------------------------------------#

class FieldFilter(logging.Filter):

  def __init__(self, fields=None):
    super(FieldFilter, self).__init__()
    self.m_lock   = threading.Lock()
    self.m_fields = fields
    if fields is None:
      self.m_fields = {}
    self.m_widths = { x : 0 for x in fields.keys() }
    self.m_cdiff  = {}

  def _width(self, p_record):
    l_filter = lambda x,y : y.get("pad", False) and hasattr(p_record, x)
    l_data   = { x:y for x,y in self.m_fields.items() if l_filter(x,y) }
    for c_name in l_data.keys():
      l_value = getattr(p_record, c_name)
      l_size  = len(l_value)
      self.m_widths[c_name] = max(self.m_widths[c_name], l_size)

  def _pad(self, p_record):
    l_filter = lambda x,y : y.get("pad", False) and hasattr(p_record, x)
    l_data   = { x:y for x,y in self.m_fields.items() if l_filter(x,y) }

    for c_name, c_data in l_data.items():
      l_cdiff  = self.m_cdiff.get(c_name, 0)
      l_value  = getattr(p_record, c_name)
      if c_data["pad"] == "left":
        l_width  = (int(self.m_widths[c_name]) + int(l_cdiff))
        l_format = "%%-%ds" % l_width
      elif c_data["pad"] == "right":
        l_width  = (int(self.m_widths[c_name]) + int(l_cdiff))
        l_format = "%%%ds" % l_width
      else:
        l_width  = 0
        l_format = "%s"
      l_value = l_format % l_value
      setattr(p_record, c_name, l_value)

  def _color(self, p_record):
    l_filter = lambda x,y : y.get("styles", False) and hasattr(p_record, x)
    l_data   = { x:y for x,y in self.m_fields.items() if l_filter(x,y) }
    for c_name, c_data in l_data.items():
      l_value  = getattr(p_record, c_name)
      l_rawLen = len(l_value)
      l_values = c_data.get("styles", { "default" : { "colors" : [], "attrs" : [] } })
      if l_value in l_values.keys():
        l_style = l_values[l_value]
      else:
        l_style = l_values.get("default", {})

      l_colors = l_style.get("colors", [])
      l_attrs  = l_style.get("attrs",  [])
      if l_colors or l_attrs:
        l_args = {}
        for c_color in l_colors:
          if c_color[0:3] == "on_":
            l_args["on_color"] = c_color
          else:
            l_args["color"] = c_color
        l_args["attrs"] = l_attrs

        try:
          l_newValue = termcolor.colored(l_value, **l_args)
          self.m_cdiff[c_name] = len(l_newValue) - l_rawLen
          l_value    = l_newValue
        except KeyError:
          continue
        setattr(p_record, c_name, l_value)

  def filter(self, p_record):
    with self.m_lock:
      self.m_cdiff = {}
      self._width(p_record)
      self._color(p_record)
      self._pad(p_record)
    return True
