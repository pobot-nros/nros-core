#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This module provides building blocks to create simple text based nROS demos.

It uses the :py:package:`curses` package.
"""
__author__ = 'Eric Pascual'

import curses
import argparse
import textwrap
from multiprocessing.pool import ThreadPool

from nros.core.commons import *


class Demo(object):
    TITLE = 'nROS demo'
    DESCRIPTION = ''    # Short description (can be docstrings)
    USAGE = ''          # Optional usage text (can be docstrings)
    MAIN_WINDOW_SIZE = (24, 80)

    @classmethod
    def add_demo_arguments(cls, parser):
        pass

    @classmethod
    def main(cls):
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

            app = cls(args, _stdscr)
            try:
                return app.run()
            finally:
                app.teardown()

        finally:
            # Set everything back to normal
            _stdscr.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

    def __init__(self, args, stdscr):
        self.node_name = args.node_name
        self.remote_node = args.remote

        self.cli_args = args

        self._stdscr = stdscr
        stdscr.refresh()

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

        self.setup(bus, wnd_client)

        pool = ThreadPool(processes=1)
        async_result = pool.apply_async(self.ui_loop, args=(dbus_loop,))

        dbus_loop.run()

        return async_result.get()

    def ui_loop(self, dbus_loop):
        """ The ncurses UI loop.
        """
        try:
            while True:
                event = self._stdscr.getch()
                if event == ord('q'):
                    break

                if not self.loop(event):
                    break

            self.terminate()

        finally:
            dbus_loop.quit()

    def setup(self, bus, wnd_client):
        pass

    def loop(self, event):
        return True

    def terminate(self):
        pass

    def teardown(self):
        pass


if __name__ == '__main__':
    # for test only
    class TestDemo(Demo):
        TITLE = 'nROS demo framework demo'
        DESCRIPTION = """
            This lovely demo shows you...
        """
        USAGE = """
            Use key "A" to type a "A"
            User key "Z" to type a "Z"
        """

        def setup(self, bus, wnd_client):
            wnd_client.border(0)
            h, w = wnd_client.getmaxyx()
            s = "This is my window"
            wnd_client.addstr(1, 1, s)
            wnd_client.addstr(h - 2, w - len(s) - 1, s)
            wnd_client.refresh()

    TestDemo.main()
