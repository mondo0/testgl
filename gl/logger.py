# -*- coding: utf-8 -*-


"""Custom logger class."""

import logging
import os
import tempfile
from logging.config import dictConfig

# Define the logging configuration
LOGGING_CFG = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s -- %(levelname)s -- %(message)s'
        },
        'short': {
            'format': '%(levelname)s: %(message)s'
        },
        'free': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            # http://stackoverflow.com/questions/847850/cross-platform-way-of-getting-temp-directory-in-python
            'filename': os.path.join(tempfile.gettempdir(), 'glances.log')
        },
        'console': {
            'level': 'CRITICAL',
            'class': 'logging.StreamHandler',
            'formatter': 'free'
        }
    },
    'loggers': {
        'debug': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
        'verbose': {
            'handlers': ['file', 'console'],
            'level': 'INFO'
        },
        'standard': {
            'handlers': ['file'],
            'level': 'INFO'
        },
        'requests': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
        },
        'elasticsearch': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
        },
        'elasticsearch.trace': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
        },
    }
}


def tempfile_name():
    """Return the tempfile name (full path)."""
    ret = os.path.join(tempfile.gettempdir(), 'glances.log')
    if os.access(ret, os.F_OK):
        os.remove(ret)
    if os.access(ret, os.F_OK) and not os.access(ret, os.W_OK):
        print("WARNING: Couldn't write to log file {} (Permission denied)".format(ret))
        ret = tempfile.mkstemp(prefix='glances', suffix='.log', text=True)
        print("Create a new log file: {}".format(ret[1]))
        return ret[1]

    return ret


def gl_logger():
    """Build and return the logger."""
    temp_path = tempfile_name()
    _logger = logging.getLogger()
    LOGGING_CFG['handlers']['file']['filename'] = temp_path
    dictConfig(LOGGING_CFG)

    return _logger

logger = gl_logger()
