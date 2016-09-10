# -*- coding: utf-8 -*-

from pbsystemd.helpers import SystemdSetupHelper

__author__ = 'Eric Pascual'

SERVICE_NAME = 'nros-bus'


def install_service():
    if not SystemdSetupHelper(SERVICE_NAME).install_service():
        print("already installed")


def remove_service():
    if not SystemdSetupHelper(SERVICE_NAME).remove_service():
        print("not installed")
