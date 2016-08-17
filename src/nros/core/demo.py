#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This module provides building blocks to create simple text based nROS demos.

It uses the :py:mod:`curses` package.
"""

import curses
import argparse
import textwrap
from multiprocessing.pool import ThreadPool
import logging
import os
import tempfile

from nros.core.commons import *

__author__ = 'Eric Pascual'


class Demo(object):
    """ To implement a demo application, override this class and implement the
    following methods:

        :py:meth:`add_demo_arguments`
            (optional) to add specific CLI options

        :py:meth:`setup_logger`
            (optional) to define a customized logger

        :py:meth:`setup`
            to initialize the application and its UI

        :py:meth:`loop`
            (optional) to implement specific UI processing if any. If the
            application interacts using the keyboard, is is the place for
            defining how

        :py:meth:`terminate_ui_loop`
            (optional) to execute some UI termination code if needed

        :py:meth:`teardown`
            (optional) to execute final housekeeping if needed

    Then, define the module main sequence like this:

    >>> if __name__ == '__main__':
    >>>     MyDemo.main()

    That's all.
    """
    TITLE = 'nROS demo'
    DESCRIPTION = ''    # Short description (can be docstrings)
    USAGE = ''          # Optional usage text (can be docstrings)
    MAIN_WINDOW_SIZE = (24, 80)

    COLOR_ERROR_MESSAGE = curses.COLOR_RED
    COLOR_SUCCESS_MESSAGE = curses.COLOR_GREEN
    COLOR_DEFAULT_MESSAGE = curses.COLOR_BLUE

    @classmethod
    def add_demo_arguments(cls, parser):
        """ Application specific CLI options.

        Override this method to add application specific CLI options to the
        initialized parser.

        :param argparse.ArgumentParser parser: the initialized command line parser
        """
        pass

    @classmethod
    def setup_logger(cls):
        """ Can be overridden to configure the application logging.

        If not used (or return None) a default one is created.

        :return: the application logger or None
        :rtype: logging.Logger
        """
        return None

    def setup(self, bus, wnd_client):
        """ Initialization method to be overridden by the demo concrete class to perform
        its specific setup.

        It is invoked just before the run loop is started. Raise an exception to abort
        the application launch.

        :param Bus bus: the D-Bus bus on which we are connected
        :param wnd_client: the ncurses window reserved to the application own interface
        """
        pass

    def loop(self, event, key, logger):
        """ User interface loop callback.

        Invoked at each occurrence of the UI loop, when a keyboard input is available
        and the exit key has been tested. To be overridden by application concrete classes
        to Implement here their specific UI actions.

        This callback is invoked in the context of the UI loop thread.

        :param int event: the raw keyboard event
        :param char key: the character equivalent of the event, if any, None otherwise
        :param logging.Logger: child logger of the UI loop
        :return: True for staying in the UI loop, False to terminate it
        """
        return True

    def terminate_ui_loop(self, logger):
        """ Callback invoked at end of the UI loop.

        Can be overridden to add any application specific cleanup in the context of
        the UI loop thread and before it is terminated.

        :param logging.Logger: child logger of the UI loop
        """
        pass

    def teardown(self):
        """ Final cleanup called at the very end of the application.

        .. note::

            Invoked with ncurses context still active.
        """
        pass

    @classmethod
    def main(cls):
        """ The demo application main line.

        To be called in the main part of the script.
        """
        app_logger = cls.setup_logger()
        if not app_logger:
            # create a logger if none has been provided by the concrete class
            logger_name = cls.__name__
            app_logger = logging.getLogger(logger_name)
            handler = logging.FileHandler(os.path.join(tempfile.gettempdir(), logger_name + '.log'), mode='w')
            handler.setFormatter(logging.Formatter("[%(levelname).1s] %(name)s > %(message)s"))
            app_logger.addHandler(handler)
            app_logger.setLevel(logging.INFO)

        app_logger.info(' Starting '.center(60, '-'))

        parser = argparse.ArgumentParser(description=cls.TITLE)

        parser.add_argument(
            '-n', '--node',
            dest="node_name",
            required=True,
            help='name of the name of the node to connect to'
        )

        def host_and_port(s):
            parts = s.split(':')
            try:
                return parts[0], int(parts[1])
            except:
                raise argparse.ArgumentTypeError("expected form: <hostname_or_IP>:<port_num>")

        parser.add_argument(
            '-r', '--remote',
            dest='remote',
            type=host_and_port,
            help="host:port if connecting to a remote node"
        )

        cls.add_demo_arguments(parser)

        args = parser.parse_args()

        app_logger.info("invoked with CLI args: %s", args)

        cls.inner_width = cls.MAIN_WINDOW_SIZE[-1] - 2

        run_error = None
        _stdscr = curses.initscr()
        try:
            curses.noecho()
            curses.cbreak()
            curses.curs_set(0)
            _stdscr.keypad(1)

            try:
                curses.start_color()
                curses.use_default_colors()
                for i in range(0, curses.COLORS):
                    curses.init_pair(i, i, -1)
            except:
                pass

            app = cls(args, _stdscr, app_logger)
            try:
                app_logger.info('>>> invoking run()...')
                app.run()
                app_logger.info('normal return from run()')

            except Exception as e:
                app_logger.error('!!! unexpected error in run():')
                app_logger.exception(e)
                run_error = e

            finally:
                app_logger.info('>>> invoking teardown()...')
                app.teardown()
                app_logger.info('<<< normal return from teardown()')

        finally:
            # Set everything back to normal
            _stdscr.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

            app_logger.info(' Terminated '.center(60, '-'))

            if run_error:
                import textwrap
                print(textwrap.dedent("""
                Abnormal termination due to error:
                ---------------------------------
                %s
                ---------------------------------
                """) % str(run_error).strip())
            else:
                print('Terminated.')

    def __init__(self, args, stdscr, logger):
        self.logger = logger
        self.node_name = args.node_name
        self.remote_node = args.remote

        self.cli_args = args

        self._stdscr = stdscr
        stdscr.refresh()

        # replace the color constants to the equivalent color pairs to optimize later usage
        self.COLOR_DEFAULT_MESSAGE = curses.color_pair(self.COLOR_DEFAULT_MESSAGE)
        self.COLOR_ERROR_MESSAGE = curses.color_pair(self.COLOR_ERROR_MESSAGE)
        self.COLOR_SUCCESS_MESSAGE = curses.color_pair(self.COLOR_SUCCESS_MESSAGE)

    def run(self):
        h, w = self.MAIN_WINDOW_SIZE

        wnd_main = curses.newwin(h, w)
        wnd_main.border(0)
        wnd_main.addstr(0, 2, " " + self.TITLE + " ")

        s = " 'q': Exit "
        wnd_main.addstr(h - 1, w - len(s) - 2, s, curses.color_pair(curses.COLOR_GREEN))

        def display_text(y, x, s, attr=0):
            lines = textwrap.dedent(s).strip().split('\n')
            for line in lines:
                wnd_main.addstr(y, x, line, attr)
                y += 1
            return y

        if self.DESCRIPTION:
            y = display_text(2, 3, self.DESCRIPTION, curses.color_pair(curses.COLOR_BLUE)) + 1

        if self.USAGE:
            wnd_main.addstr(y, 3, "Usage:", curses.A_BOLD)
            y = display_text(y + 1, 7, self.USAGE) + 1

        wnd_main.refresh()

        wnd_client = wnd_main.derwin(h - y - 1, w - 2, y, 1)
        wnd_client.refresh()

        dbus_loop = dbus_init()

        # get the appropriate bus (local session or TCP remote) depending on command line arguments
        if self.remote_node:
            host, port = self.remote_node
            bus = get_remote_bus(host=host, port=port)
        else:
            bus = get_bus()

        self.logger.info('>>> invoking setup()...')
        self.setup(bus, wnd_client)
        self.logger.info('<<< normal return from setup()')

        pool = ThreadPool(processes=1)
        pool.apply_async(self.ui_loop, args=(dbus_loop,))

        self.logger.info('starting D-Bus main loop')
        dbus_loop.run()
        self.logger.info('D-Bus main loop terminated')

    def ui_loop(self, dbus_loop):
        """ The ncurses UI loop.

        Called internally and not to be used by applications or sub-classes
        """
        logger = self.logger.getChild('ui_loop')
        try:
            logger.info(' started '.center(40, '-'))
            while True:
                event = self._stdscr.getch()
                try:
                    key = chr(event)
                except ValueError:
                    key = None
                    logger.info("event=0x%x", event)
                else:
                    logger.info("event=0x%x key='%s'", event, key)
                if key in ('q', 'Q'):
                    break

                if not self.loop(event, key, logger):
                    break

            logger.info(' terminated '.center(40, '-'))

            logger.info('>>> invoking terminate()...')
            self.terminate_ui_loop(logger)
            logger.info('<<< normal return from terminate()...')

        except Exception as e:
            logger.exception(e)

        finally:
            dbus_loop.quit()

    def _display_message(self, msg, attr):
        self._stdscr.addstr(1, 1, msg[:self.inner_width].ljust(self.inner_width), attr)

    def display_error_message(self, error):
        """ Displays an error message in the status line of the window.

        The message is truncated if needed to fit in the window width. It is displayed
        with the error color, as defined by the ``COLOR_ERROR_MESSAGE`` class attribute.

        An exception can be passed, and in this case the message is built with its name
        and message text.

        :param error: either the text of the message or an exception
        :return:
        """
        if isinstance(error, Exception):
            error = "[%d] %s" % (error.__class__.__name__, error.message)

        self._display_message(error, self.COLOR_ERROR_MESSAGE)

    def display_success_message(self, msg):
        """ Displays an success message in the status line of the window.

        Uses the color defined by the ``COLOR_SUCCESS_MESSAGE`` class attribute.
        """
        self._display_message(msg, self.COLOR_SUCCESS_MESSAGE)

    def display_message(self, msg):
        """ Displays an default message in the status line of the window.

        Uses the color defined by the ``COLOR_DEFAULT_MESSAGE`` class attribute.
        """
        self._display_message(msg, self.COLOR_DEFAULT_MESSAGE)

    def beep(self):
        """ Sounds the audible alarm.
        """
        curses.beep()


if __name__ == '__main__':
    # for test only
    class TestDemo(Demo):
        TITLE = 'nROS demo framework demo'
        DESCRIPTION = """
            This lovely demo shows you...
        """
        USAGE = """
            Use key "A" to type a "A"
            Use key "Z" to type a "Z"
        """

        def setup(self, bus, wnd_client):
            wnd_client.border(0)
            h, w = wnd_client.getmaxyx()
            s = "This is my window"
            wnd_client.addstr(1, 1, s)
            wnd_client.addstr(h - 2, w - len(s) - 1, s)
            wnd_client.refresh()

    TestDemo.main()
