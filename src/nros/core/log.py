# -*- coding: utf-8 -*-

""" A couple of convenience settings and functions for using the logging facility
in a homogeneous way across applications."""

import copy

# surface logging module public definitions (do not remove although PyLint saying it is not used)
# noinspection PyUnresolvedReferences
from logging import *


_default_configuration = {
    'version': 1,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s.%(msecs).3d [%(levelname).1s] %(name)s (%(filename)s:%(lineno)d) %(message)s',
            'datefmt': '%H:%M:%S'
        },
        'brief': {
            'format': '[%(levelname).1s] %(name)s > %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'brief',
            'level': 'INFO',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'filename': '',
            'maxBytes': 1024*1024,
            'backupCount': 3
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG'
    }
}


def deep_update(d, u):
    """ Recursively update a dictionary, walking down its nested levels.
    :param dict d: dictionary to be updated
    :param dict u: dictionary containing the updates
    """
    for k, v in u.iteritems():
        if k in d and isinstance(v, dict):
            deep_update(d[k], v)
        else:
            d[k] = v


def get_logging_configuration(override=None):
    """ Returns a full logging configuration, based on the default one
    overridden with the passed one.
    :param dict override: a dictionary containing the overridden settings
    :return: the complete configuration
    :rtype: dict
    """
    cfg = copy.deepcopy(_default_configuration)
    if override:
        deep_update(cfg, override)
    return cfg


def abbrev(fqn):
    """ Given a fully qualified module name, returns an abbreviated form by replacing
    the parent full names by their initial.

    Ex: pybot.dynamixel.joints -> p.d.joints
    """
    parts = fqn.split('.')
    return '.'.join([s[0] for s in parts[:-1]] + [parts[-1]])
