#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This module includes the definitions of the base types used to define a
nROS node.

The nROS node is the building block for nROS applications. Each node runs as
a separate process and is intended to handle a specific functionality of the
system. It can be for instance a driver for a specific piece of hardware
attached to a USB port, a on-the-fly image processing, an AI task,...

Nodes use D-Bus to communicate, by publishing messages, subscribing to messages or
calling methods from other nodes.
"""

__author__ = 'Eric Pascual'

import signal
import logging.config
import sys
import os

import dbus.mainloop.glib
import dbus.service
import gobject

from pybot_core import cli, log
from pybot_dynamixel import DmxlError


class NROSNode(object):
    """ Base class for implementing a nROS node.

    It defines the main line of the node execution, which is supposed to be called in the
    node script 'main' part, using something like this :

    >>> if __name__ == '__main__':
    >>>     MyNode.main()

    The various stages of the execution can be defined or customized by overriding the
    following methods:

    - :py:meth:`add_arguments_to_parser`
    - :py:meth:`get_get_mainloop`
    - :py:meth:`init_node`
    - :py:meth:`configure`
    - :py:meth:`prepare_node`
    - :py:meth:`setup_dbus_environment`
    - :py:meth:`shutdown`
    """
    _logger = None
    _node = None
    _loop = None

    @classmethod
    def add_arguments_to_parser(cls, parser):
        """ Command line parser customization.

        Override this method to add arguments to the parser already initialized with common
        ones, using :meth:`ArgumentParser.add_argument` standard method.
        
        Arguments included by default to the parser are:
         
        - ``-n``, ``--name`` : the name of the node **(required)**
        - ``-C``, ``--config`` : the node configuration file path **(required)**
        - ``--logger-config`` : the logging configuration file path

        :param ArgumentParser parser: the argument parser
        """

    @classmethod
    def get_mainloop(cls):
        """ Override this method to use another event loop than the default one.

        Should not be needed most of the time, apart if the node is part of a GUI application.
        """
        return gobject.MainLoop()

    def init_node(self):
        """ Called in ``__init__`` method, just after core initializations have been made.

        Override this method to add specific process to the default ``__init__`` method instead
        of overriding it. Since the default implementation of ``init_node`` does nothing,
        you don't need to invoke ``super`` in the overridden version.
        """

    def configure(self, cfg):
        """ Override this method to process the configuration of the node.

        :param dict cfg: the node configuration as a dictionary
        """

    # def is_ready(self):
    #     """ Invoked at the beginning of :meth:`run()` process.
    #
    #     Override it to insert specific checks to be performed before going into run mode.
    #     :return: True if run process can be started, False to abort it
    #     """
    #     return True

    def prepare_node(self):
        """ Prepare the node to be run.

        Last pre-flight checks should take place here.
        """

    def setup_dbus_environment(self, connection):
        """ Called as the first step of the run phase, just before entering the run loop.

        The execution context has been validated, and the node is connected to the D-Bus hub.

        :param connection: the node connection to the D-Bus hub
        """

    def shutdown(self):
        """ Called during the terminate phase, just before the loop `quit()` is called.

        Override to perform cleanup to be done while the loop is still alive, such as
        housekeeping of service objects.
        """

    def __init__(self, name):
        """ To extend the initialization process, override the :py:meth:`init_node()` method
        instead of :py:meth:`__init__`.

        :param name: the name of the node
        """
        self._logger.info('initialiazing node %s' % name)
        self.name = name
        self.init_node()

    def terminate(self):
        """ Invoke this method to trigger the node termination stage.

        Kill signals are automatically handled to trigger the node termination stage.
        """
        self._logger.info('terminate called')
        self.shutdown()
        self._loop.quit()

    def logged_message(self, msg):
        """ An helper method which "tee" a message to the logger.

        Common usage is when raising an exception, for shortening the resulting code:

        >>> raise ValueError(self.logged_message("Houston we have a problem"))

        :param str msg: the message to be logged
        :return: the message
        """
        self._logger.error(msg)
        return msg


    @classmethod
    def main(cls):
        """ The main line of the node.

        Invoke it in the main part of the node script, like this :

        >>> if __name__ == '__main__':
        >>>     MyNode.main()
        """
        args = cls._process_command_line()

        cls._logger = cls._setup_logging(args.log_cfg)
        cls._logger.info('--------------------- STARTING ---------------------')
        cls._logger.info('pid=%d', os.getpid())

        cls._init_dbus()

        cls._node = node = cls(name=args.name)
        try:
            node.configure(args.config)
        except DmxlError as e:
            cls.die(e)

        node.prepare_node()

        connection = dbus.service.BusName('org.pobot.nros.' + node.name, bus=dbus.SessionBus())
        node.setup_dbus_environment(connection)

        signal.signal(signal.SIGTERM, cls._sigterm_handler)

        try:
            cls._logger.info('starting loop')
            cls._loop.run()
            cls._logger.info('loop exited')

        except KeyboardInterrupt:
            cls._logger.info("!!! keyboard interrupt or SIGINT caught !!!")
            node.terminate()

        cls._logger.info('-------------------- TERMINATED --------------------')

    @classmethod
    def die(cls, msg, exit_code=1):
        cls._logger.error(msg)
        cls._logger.error('--------------------- ABORTED ----------------------')
        sys.exit(exit_code)


    @classmethod
    def _sigterm_handler(cls, signum, frame):
        cls._logger.info('!!! SIGTERM caught !!!')
        cls._node.terminate()

    @classmethod
    def _process_command_line(cls):
        parser = cli.get_argument_parser()
        parser.add_argument(
            '-n', '--name',
            dest='name',
            required=True,
            help='node name'
        )
        parser.add_argument(
            '-C', '--config',
            dest='config',
            required=True,
            type=file,
            help='configuration file path'
        )
        parser.add_argument(
            '--logger-config',
            dest='log_cfg',
            type=file,
            help='logging customisation'
        )

        cls.add_arguments_to_parser(parser)

        return parser.parse_args()

    @classmethod
    def _init_dbus(cls):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        gobject.threads_init()
        dbus.mainloop.glib.threads_init()
        cls._loop = cls.get_mainloop()

    @classmethod
    def _setup_logging(cls, cfg_path):
        log_name = os.path.splitext(os.path.basename(sys.argv[0]))[0] + '.log'
        log_dir = '/var/log/nros' if os.getuid() == 0 else os.path.expanduser('~/.nros')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, log_name)

        logging_cfg = {
            'handlers': {
                'file': {
                    'filename': log_path
                }
            }
        }
        if cfg_path:
            import json
            cfg = json.load(cfg_path)
            log.deep_update(logging_cfg, cfg)

        logging.config.dictConfig(log.get_logging_configuration(logging_cfg))
        logger = logging.getLogger(cls.__name__)

        return logger
