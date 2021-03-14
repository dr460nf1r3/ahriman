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
import subprocess

from logging import Logger
from typing import Optional


def check_output(*args: str, exception: Optional[Exception],
                 cwd: Optional[str] = None, stderr: int = subprocess.STDOUT,
                 logger: Optional[Logger] = None) -> str:
    '''
    subprocess wrapper
    :param args: command line arguments
    :param exception: exception which has to be reraised instead of default subprocess exception
    :param cwd: current working directory
    :param stderr: standard error output mode
    :param logger: logger to log command result if required
    :return: command output
    '''
    try:
        result = subprocess.check_output(args, cwd=cwd, stderr=stderr).decode('utf8').strip()
        if logger is not None:
            for line in result.splitlines():
                logger.debug(line)
    except subprocess.CalledProcessError as e:
        if e.output is not None and logger is not None:
            for line in e.output.decode('utf8').splitlines():
                logger.debug(line)
        raise exception or e
    return result


def package_like(filename: str) -> bool:
    '''
    check if file looks like package
    :param filename: name of file to check
    :return: True in case if name contains `.pkg.` and not signature, False otherwise
    '''
    return '.pkg.' in filename and not filename.endswith('.sig')
