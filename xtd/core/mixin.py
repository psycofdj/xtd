# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

class Singleton(type):
  ms_instances = {}
  def __call__(cls, *p_args, **p_kwargs):
    if cls not in cls.ms_instances:
      cls.ms_instances[cls] = super(Singleton, cls).__call__(*p_args, **p_kwargs)
    return cls.ms_instances[cls]

  @classmethod
  def reset(mcs, p_item):
    if p_item in mcs.ms_instances:
      del mcs.ms_instances[p_item]

#------------------------------------------------------------------#
