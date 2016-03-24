# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__ = "Copyright (C) 2008 Xavier"
__version__   = "0.3"

#------------------------------------------------------------------#

import sys
import datetime

#------------------------------------------------------------------#

class BaseException(Exception):
    def __init__(self, p_module, p_message):
        self.m_message = p_message
        self.m_module = p_module

    def log(self):
        raise NotImplemented

    def __str__(self):
        return "[%s] %s" % (self.m_module, self.m_message)

#------------------------------------------------------------------#

class ConfigException(BaseException):
    def __init__(self, p_message):
        BaseException.__init__(self, "config", p_message)

class ConfigValueException(ConfigException):
    def __init__(self, p_sectionName, p_optionName, p_message):
        l_message = "error with parameter '%s' of section '%s' : %s" % (p_optionName,
                                                                        p_sectionName,
                                                                        p_message)
        ConfigException.__init__(self, l_message)

class ConfigValueFileException(ConfigValueException):
    def __init__(self,
                 p_sectionName,
                 p_optionName,
                 p_fileName):
        l_message = "path '%s' does not name a file" % (p_fileName)
        ConfigValueException.__init__(self, p_sectionName, p_optionName, l_message)


class ConfigValueDirException(ConfigValueException):
    def __init__(self,
                 p_sectionName,
                 p_optionName,
                 p_fileName):
        l_message = "path '%s' does not name a directory" % (p_fileName)
        ConfigValueException.__init__(self, p_sectionName, p_optionName, l_message)


class ConfigValueDirModeException(ConfigValueException):
    def __init__(self,
                 p_sectionName,
                 p_optionName,
                 p_fileName,
                 p_read = False,
                 p_write = False,
                 p_execute = False):
        l_modeString = ""
        if p_read:
            l_modeString += "r"
        else:
            l_modeString += "-"
        if p_write:
            l_modeString += "w"
        else:
            l_modeString += "-"
        if p_execute:
            l_modeString += "x"
        else:
            l_modeString += "-"
        l_message = "could not open directory '%s' with '%s' access" % (p_fileName, l_modeString)
        ConfigValueException.__init__(self, p_sectionName, p_optionName, l_message)

class ConfigValueFileModeException(ConfigValueException):
    def __init__(self,
                 p_sectionName,
                 p_optionName,
                 p_fileName,
                 p_read = False,
                 p_write = False,
                 p_execute = False):
        l_modeString = ""
        if p_read:
            l_modeString += "r"
        else:
            l_modeString += "-"
        if p_write:
            l_modeString += "w"
        else:
            l_modeString += "-"
        if p_execute:
            l_modeString += "x"
        else:
            l_modeString += "-"
        l_message = "could not open path '%s' with '%s' access" % (p_fileName, l_modeString)
        ConfigValueException.__init__(self, p_sectionName, p_optionName, l_message)

class ConfigValueTypeException(ConfigValueException):
    INT   = "int"
    FLOAT = "float"
    BOOL  = "bool"
    def __init__(self, p_sectionName, p_optionName, p_value, p_typeName):
        l_message = "could not cast value '%s' int type '%s'" % (p_value, p_typeName)
        ConfigValueException.__init__(self, p_sectionName, p_optionName, l_message)

class ConfigValueLimitsException(ConfigValueException):
    def __init__(self, p_sectionName, p_optionName, p_value, p_minValue = None, p_maxValue = None):
        if p_minValue == None:
            p_minValue = "-inf"
        if p_maxValue == None:
            p_maxValue = "inf"
        l_message = "value out of bounds, should be %s < %s < %s" % (p_minValue,
                                                                     p_value,
                                                                     p_maxValue)
        ConfigValueException.__init__(self, p_sectionName, p_optionName, l_message)


class ConfigValueEnumException(ConfigValueException):
    def __init__(self, p_sectionName, p_optionName, p_value, p_authorizedValues):
        l_message = "value '%s' must be one of the following '%s'" % (p_value, str(p_authorizedValues))
        ConfigValueException.__init__(self, p_sectionName, p_optionName, l_message)
