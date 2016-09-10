# -*- coding: utf-8 -*-

import pbsystemd.helpers

__author__ = 'Eric Pascual'

SERVICE_NAME = 'nros-bus'


def install_service():
    pbsystemd.helpers.install_service(SERVICE_NAME, __name__)


def remove_service():
    pbsystemd.helpers.remove_service(SERVICE_NAME, __name__)
