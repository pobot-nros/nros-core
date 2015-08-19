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
import json

import dbus.mainloop.glib
import dbus.service
import gobject

from nros.core import cli
from nros.core import log


DEFAULT_SERVICE_OBJECT_PATH = '/'


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
    - DBus main loop
    - :py:meth:`shutdown`

    Sub-class implementing real nodes will most of the time override the following methods :

    ``configure``

        It is the place to create instances of classes in charge of doing the real job, based
        on what is specified in the configuration data.

    ``prepare_node``

        At this point, everybody is on the stage, at the right position to start the play. This
        is the place to put everything in its initial state.

    ``setup_dbus_environment``

        Everybody is now up and running, and it is time to bind them to D-Bus by creating and
        preparing the required service objects.

    ``shutdown``

        The place for stopping all the worker processes which have been involved until now and doing
        the final housekeeping. At this point the D-Bus mechanisms are no more active.
    """
    _logger = None
    _node = None
    _loop = None
    _verbose = False
    _debug = False

    @classmethod
    def add_arguments_to_parser(cls, parser):
        """ Command line parser customization.

        Override this method to add arguments to the parser already initialized with common
        ones, using :meth:`ArgumentParser.add_argument` standard method.

        The default method is empty, so that you don't need to call `super` in your version.
        But it is wiser to do it anyway, in case some process would be added here in the future.

        Arguments included by default to the parser are:

        - ``-n``, ``--name`` : the name of the node **(required)**
        - ``-C``, ``--config`` : the node configuration file path **(required)**
        - ``--logger-config`` : the logging configuration file path
        - ``--verbose`` : verbose logs
        - ``--debug`` : debug mode activation

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

    def configure(self, cfg_file):
        """ Override this method to process the configuration of the node.

        Since the base method is empty, there is no need to invoke ``super``.

        :param file cfg_file: a read-only opened file located at the path specified by
            then command line `-C/--config` argument if any. It will be None if the option is not used.
        """

    def _get_cfg_dict(self, cfg):
        """ Helper method for sub-classes for pre-processing the configuration data passed to
        the node during its initialization step.

        If the parameter is already a dictionary, it is supposed to be the expected configuration data,
        and it is returned unchanged.

        :param cfg: a dictionary, or a file or the path of the file containing the configuration data in JSON format
        :return: the configuration data as a dictionary (empty if no configuration data provided).
        :rtype: dict
        :raises: ValuerError if JSON data are not valid
        :raises: TypeError if the parameter is of any of the accepted types
        """
        if not cfg:
            return {}

        if isinstance(cfg, dict):
            return cfg

        elif isinstance(cfg, file):
            return json.load(cfg)

        elif isinstance(cfg, basestring):
            return json.load(file(cfg, 'rt'))

        else:
            raise TypeError(self.logged_message('unsupported configuration data type'))

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

        Since the default implementation of ``prepare_node`` does nothing,
        you don't need to invoke ``super`` in the overridden version.
        """

    def setup_dbus_environment(self, bus_name):
        """ Called as the first step of the run phase, just before entering the run loop.

        The execution context has been validated, and the node is connected to the D-Bus hub.

        Since the default implementation of ``setup_dbus_environment`` does nothing,
        you don't need to invoke ``super`` in the overridden version.

        :param :py:class:`dbus.service.BusName` bus_name: the well known name used for this node
        """

    def shutdown(self):
        """ Called during the terminate phase, just before the loop `quit()` is called.

        Override to perform cleanup to be done while the loop is still alive, such as
        housekeeping of service objects.

        Since the default implementation of ``shutdown`` does nothing,
        you don't need to invoke ``super`` in the overridden version.
        """

    def __init__(self, name):
        """ To extend the initialization process, override the :py:meth:`init_node()` method
        instead of :py:meth:`__init__`.

        Nodes can be named to easily distinguish them. If not, a default name will be generated,
        built with the concrete class name and the process id.

        :param str name: the name of the node. (optional)
        """
        if not name:
            name = 'nros.%s-%d' % (self.__class__.__name__, os.getpid())

        self._logger.info("initializing node '%s'" % name)
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

    BANNER_WIDTH = 60

    @classmethod
    def main(cls):
        """ The main line of the node.

        Invoke it in the main part of the node script, like this :

        >>> if __name__ == '__main__':
        >>>     MyNode.main()
        """
        args = cls._process_command_line()

        cls._logger = cls._setup_logging(args.log_cfg)
        cls._logger.info(' NODE STARTED '.center(cls.BANNER_WIDTH, '-'))
        cls._logger.info('pid=%d', os.getpid())

        cls._init_dbus()

        cls._node = node = cls(name=getattr(args, 'name', None))
        node._verbose = args.verbose
        node._debug = args.debug
        try:
            node.configure(args.config)
        except Exception as e:
            cls.die(e)

        node.prepare_node()

        cls._logger.info('connecting to D-Bus as %s', node.name)
        bus_name = dbus.service.BusName(node.name, bus=dbus.SessionBus())
        node.setup_dbus_environment(bus_name)

        signal.signal(signal.SIGTERM, cls._sigterm_handler)

        try:
            cls._logger.info('starting loop')
            cls._loop.run()
            cls._logger.info('loop exited')

        except KeyboardInterrupt:
            cls._logger.info(" keyboard interrupt or SIGINT caught ".center(cls.BANNER_WIDTH, '!'))
            node.terminate()

        cls._logger.info(' TERMINATED '.center(cls.BANNER_WIDTH, '-'))

    @classmethod
    def die(cls, msg, exit_code=1):
        cls._logger.error(msg)
        cls._logger.error(' ABORTED '.center(cls.BANNER_WIDTH, '-'))
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
            help='node name (default: nros.%s-<pid>)' % cls.__name__
        )
        parser.add_argument(
            '-C', '--config',
            dest='config',
            type=file,
            help='configuration file path (default: %(default)s)'
        )
        parser.add_argument(
            '--logger-config',
            dest='log_cfg',
            type=file,
            help='logging customisation (default: %(default)s)'
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
        log_dir = '/var/log/nros' if os.getuid() == 0 else os.path.expanduser('~/.nros/log')
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