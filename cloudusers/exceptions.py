#!/usr/bin/python

import os
import sys

class ApplicationError (Exception):
    description = 'Unknown error'

    def __str__ (self):
        return self.description

class ConfigurationError (ApplicationError):
    description = 'Configuration error'

class DebugModeDisabledError (ApplicationError):
    description = 'Debug mode is disabled')
