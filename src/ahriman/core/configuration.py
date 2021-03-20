#
# Copyright (c) 2021 Evgenii Alekseev.
#
# This file is part of ahriman
# (see https://github.com/arcan1s/ahriman).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import annotations

import configparser
import logging
import os

from logging.config import fileConfig
from typing import Dict, List, Optional, Type


class Configuration(configparser.RawConfigParser):
    '''
    extension for built-in configuration parser
    :ivar path: path to root configuration file
    :cvar ARCHITECTURE_SPECIFIC_SECTIONS: known sections which can be architecture specific (required by dump)
    :cvar DEFAULT_LOG_FORMAT: default log format (in case of fallback)
    :cvar DEFAULT_LOG_LEVEL: default log level (in case of fallback)
    :cvar STATIC_SECTIONS: known sections which are not architecture specific (required by dump)
    '''

    DEFAULT_LOG_FORMAT = '[%(levelname)s %(asctime)s] [%(filename)s:%(lineno)d] [%(funcName)s]: %(message)s'
    DEFAULT_LOG_LEVEL = logging.DEBUG

    STATIC_SECTIONS = ['alpm', 'report', 'repository', 'settings', 'upload']
    ARCHITECTURE_SPECIFIC_SECTIONS = ['build', 'html', 'rsync', 's3', 'sign', 'web']

    def __init__(self) -> None:
        '''
        default constructor. In the most cases must not be called directly
        '''
        configparser.RawConfigParser.__init__(self, allow_no_value=True)
        self.path: Optional[str] = None

    @property
    def include(self) -> str:
        '''
        :return: path to directory with configuration includes
        '''
        return self.get('settings', 'include')

    @classmethod
    def from_path(cls: Type[Configuration], path: str, logfile: bool) -> Configuration:
        '''
        constructor with full object initialization
        :param path: path to root configuration file
        :param logfile: use log file to output messages
        :return: configuration instance
        '''
        config = cls()
        config.load(path)
        config.load_logging(logfile)
        return config

    def dump(self, architecture: str) -> Dict[str, Dict[str, str]]:
        '''
        dump configuration to dictionary
        :param architecture: repository architecture
        :return: configuration dump for specific architecture
        '''
        result: Dict[str, Dict[str, str]] = {}
        for section in Configuration.STATIC_SECTIONS:
            if not self.has_section(section):
                continue
            result[section] = dict(self[section])
        for group in Configuration.ARCHITECTURE_SPECIFIC_SECTIONS:
            section = self.get_section_name(group, architecture)
            if not self.has_section(section):
                continue
            result[section] = dict(self[section])

        return result

    def getlist(self, section: str, key: str) -> List[str]:
        '''
        get space separated string list option
        :param section: section name
        :param key: key name
        :return: list of string if option is set, empty list otherwise
        '''
        raw = self.get(section, key, fallback=None)
        if not raw:  # empty string or none
            return []
        return raw.split()

    def get_section_name(self, prefix: str, suffix: str) -> str:
        '''
        check if there is `prefix`_`suffix` section and return it on success. Return `prefix` otherwise
        :param prefix: section name prefix
        :param suffix: section name suffix (e.g. architecture name)
        :return: found section name
        '''
        probe = f'{prefix}_{suffix}'
        return probe if self.has_section(probe) else prefix

    def load(self, path: str) -> None:
        '''
        fully load configuration
        :param path: path to root configuration file
        '''
        self.path = path
        self.read(self.path)
        self.load_includes()

    def load_includes(self) -> None:
        '''
        load configuration includes
        '''
        try:
            for conf in filter(lambda p: p.endswith('.ini'), sorted(os.listdir(self.include))):
                self.read(os.path.join(self.include, conf))
        except (FileNotFoundError, configparser.NoOptionError):
            pass

    def load_logging(self, logfile: bool) -> None:
        '''
        setup logging settings from configuration
        :param logfile: use log file to output messages
        '''
        def file_logger() -> None:
            try:
                fileConfig(self.get('settings', 'logging'))
            except PermissionError:
                console_logger()
                logging.error('could not create logfile, fallback to stderr', exc_info=True)

        def console_logger() -> None:
            logging.basicConfig(filename=None, format=Configuration.DEFAULT_LOG_FORMAT,
                                level=Configuration.DEFAULT_LOG_LEVEL)

        if logfile:
            file_logger()
        else:
            console_logger()
