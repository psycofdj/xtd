#!/usr/bin/env python

import json
import pickle
import os
import sys

l_path = os.path.realpath(os.path.dirname(__file__))
os.chdir(os.path.dirname(l_path))
sys.path.insert(0, ".")

l_classes = 0
l_members = 0
l_funcs   = 0

with open("docs/_build/coverage/undoc.pickle", "rb") as l_file:
  l_data = pickle.load(l_file)
  for c_module, c_entity in l_data[0].items():
    for c_class, c_methods in c_entity["classes"].items():
      l_count = len(c_methods)
      if l_count:
        l_members += l_count
      else:
        l_classes += 1
    l_funcs += len(c_entity["funcs"])

print(json.dumps({
  "classes" : l_classes,
  "members" : l_members,
  "funcs"   : l_funcs
}))
