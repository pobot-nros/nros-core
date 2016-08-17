# -*- coding: utf-8 -*-

import os

from nros.core.node import start_session_bus, session_bus_is_running, stop_session_bus, get_bus_config, bus_monitor

__author__ = 'Eric Pascual'

PKG_NAME = 'nros.dynamixel'

_CONFIG_DIR = os.path.join('/etc', PKG_NAME.replace('.', '/'))


def nros_bus_start():
    if session_bus_is_running():
        print('nROS bus already started.')
    else:
        print('Starting nROS bus...')
        config, _ = start_session_bus()
        nros_bus_status()

    print("Configuration :")
    nros_bus_config()


def nros_bus_stop():
    if session_bus_is_running():
        print('Stopping nROS bus...')
        stop_session_bus()
        nros_bus_status()
    else:
        print('nROS bus not started.')


def nros_bus_status():
    print('nROS bus is %s.' % ('started' if session_bus_is_running() else 'stopped'))


def nros_bus_config():
    if session_bus_is_running():
        config = get_bus_config()
        for k, v in config.iteritems():
            print("- %-25s : %s" % (k, v))

    else:
        print('nROS bus not started.')


def nros_bus_monitor():
    if session_bus_is_running():
        try:
            print('-- Starting bus monitor (Ctrl-C to end)\n')
            bus_monitor()
        except KeyboardInterrupt:
            print('\r\n-- Monitoring ended.')
        except Exception as e:
            print(e.message)

    else:
        print('nROS bus not started.')
