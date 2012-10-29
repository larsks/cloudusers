#!/usr/bin/python

import os
import sys

class ApplicationError (Exception):
    title = 'Unable to complete your request'
    reason = 'Unknown error'
    description = '''An unexpected error has occurred.  No further
    details are available.'''

    def __str__ (self):
        return '%s: %s' % (self.reason, self.description)

class ConfigurationError (ApplicationError):
    reason = 'Configuration error'
    description = '''This application is missing critical configuration
    information.  If you are repsonsible for this application, please
    consult the documentation.'''

class DebugModeDisabledError (ApplicationError):
    reason = 'Debug mode is disabled'
    description = '''You have requested a resource that is only available
    when this application is running in debug mode.  To enable debug mode,
    set `debug: True` in the application configuration file.'''

