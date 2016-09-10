#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Convenience functions and definitions, avoiding to deal directly with D-Bus binding at application level.

``import *`` can be done without risk, since exported symbols are restricted by the ``__all__`` definition.
"""

import os
import signal
import subprocess

from dbus.bus import BusConnection
from dbus import Interface

__author__ = 'Eric Pascual'

__all__ = [
    'dbus_init',
    'start_session_bus', 'stop_session_bus', 'session_bus_is_running', 'get_bus_config',
    'bus_monitor',
    'get_bus', 'get_remote_bus',
    'get_node_proxy', 'get_node_interface',
    'connect_to_interface_signal'
]

DBUS_ENV_FILE = '/tmp/nros-session-bus'


def dbus_init():
    """ D-Bus environment initialization.

    Must be called before doing anything related to D-Bus.

    :return: the D-Bus mainloop, to be started by its :py:meth:`run` method when ready
    :rtype: glib.MainLoop
    """
    import dbus.mainloop.glib
    import gobject

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    gobject.threads_init()
    dbus.mainloop.glib.threads_init()

    return gobject.MainLoop()


def start_session_bus(logger=None):
    is_running = session_bus_is_running()
    if not is_running:
        if logger:
            logger.info('starting nROS bus...')
        error = subprocess.call("dbus-launch --sh-syntax > " + DBUS_ENV_FILE, shell=True)
        if error:
            # ensure no env file is left around
            try:
                os.remove(DBUS_ENV_FILE)
            except OSError:
                pass
            raise Exception("dbus-launch failed with rc=%d" % error)

    return get_bus_config(), is_running


def stop_session_bus():
    if session_bus_is_running():
        d = get_bus_config()
        pid = d['DBUS_SESSION_BUS_PID']
        os.kill(int(pid), signal.SIGTERM)
        os.remove(DBUS_ENV_FILE)


def session_bus_is_running():
    return os.path.exists(DBUS_ENV_FILE)


def get_bus_config():
    d = {}
    for line in [line for line in file(DBUS_ENV_FILE) if '=' in line]:
        var, value = line.split('=', 1)
        d[var] = value.strip().strip(';').strip("'")
    return d


def bus_monitor():
    if session_bus_is_running():
        d = get_bus_config()
        error = subprocess.call("dbus-monitor --address %s" % d['DBUS_SESSION_BUS_ADDRESS'], shell=True)
        if error:
            raise Exception("dbus-monitor failed with rc=%d" % error)


def get_bus(address_or_type=BusConnection.TYPE_SESSION):
    """ Returns a given bus, either from the local system or from a remote one, thanks to D-Bus TCP support.

    The parameter is used the same way as in D-Bus class :py:class:`BusConnection`. Refer to original
    documentation for details.

    :param address_or_type: request bus identification
    :return: the requested bus
    :rtype: BusConnection
    """
    os.environ.update(get_bus_config())
    return BusConnection(address_or_type)


def get_remote_bus(host, port):
    """ Returns a bus exposed by a remote host.

    This is a convenience wrapper of the :py:class:`BusConnection` create, building the bus address
    for a TCP connection.

    :param str host: host name or IP
    :param int port: port on which the remote host is listening
    :return: the requested bus
    :rtype: BusConnection
    """
    return BusConnection("tcp:host=%s,port=%d" % (host, port))


def get_node_proxy(bus, node_name, object_path='/'):
    """ Returns a proxy for an object inside a given node.

    Refer to D-Bus :py:meth:`det_object` method documentation for details.

    :param BusConnection bus: the bus on which is connected the node containing the object
    :param str node_name: the node name
    :param str object_path: the path of the object inside the node (default : "/")
    :return: the requested proxy
    :rtype: :py:class:`dbus.proxies.ProxyObject`
    """
    return bus.get_object(node_name, object_path)


def get_node_interface(proxy, interface_name):
    """ Returns a given interface from a proxy object implementing it.

    :param ProxyObject proxy: the proxy object implementing the interface
    :param str interface_name: the name of the interface
    :return: the requested interface
    :rtype: :py:class:`dbus.proxies.Interface`
    """
    return Interface(proxy, dbus_interface=interface_name)


def connect_to_interface_signal(interface, signal_name, callback, **keywords):
    """ Connect a handler to a signal defined by an interface.

    :param Interface interface: the interface defining the signal
    :param str signal_name: the name of the signal
    :param callable callback: a callable with the same signature as the signal
    :param keywords: refer to :py:meth:`ProxyObject.connect_to_signal` method documentation
    """
    interface.connect_to_signal(signal_name, callback, **keywords)
