# -*- coding: utf-8 -*-

import sys

from pbsystemd.helpers import SystemdSetupHelper

__author__ = 'Eric Pascual'

SERVICE_NAME = 'nros-bus'


def install_service():
    try:
        if not SystemdSetupHelper(SERVICE_NAME).install_service():
            print("already installed")
    except RuntimeError as e:
        sys.exit(e.message)


def remove_service():
    try:
        if not SystemdSetupHelper(SERVICE_NAME).remove_service():
            print("not installed")
    except RuntimeError as e:
        sys.exit(e.message)
