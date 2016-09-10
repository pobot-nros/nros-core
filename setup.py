# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='nros-core',
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    description='Core part of nROS framework',
    install_requires=['dbus-python'],
    extras_require = {
        'systemd': ['pybot-systemd']
    },
    license='LGPL',
    author='Eric Pascual',
    author_email='eric@pobot.org',
    url='http://www.pobot.org',
    download_url='https://github.com/Pobot/PyBot',
    packages=find_packages("src"),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'nros-bus-start = nros.core.entry_points:nros_bus_start',
            'nros-bus-stop = nros.core.entry_points:nros_bus_stop',
            'nros-bus-status = nros.core.entry_points:nros_bus_status',
            'nros-bus-config = nros.core.entry_points:nros_bus_config',
            'nros-bus-monitor = nros.core.entry_points:nros_bus_monitor',
            # optionals
            "nros-bus-systemd-setup = nros.core.setup.systemd:install_service [systemd]",
            "nros-bus-systemd-cleanup = nros.core.setup.systemd:remove_service [systemd]",
        ]
    },
    package_data={
        'nros.core.setup': ['pkg_data/*']
    }
)
