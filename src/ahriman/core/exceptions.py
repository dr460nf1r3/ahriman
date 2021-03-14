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
from typing import Any


class BuildFailed(Exception):
    '''
    base exception for failed builds
    '''

    def __init__(self, package: str) -> None:
        '''
        default constructor
        :param package: package base raised exception
        '''
        Exception.__init__(self, f'Package {package} build failed, check logs for details')


class DuplicateRun(Exception):
    '''
    exception which will be raised if there is another application instance
    '''

    def __init__(self) -> None:
        '''
        default constructor
        '''
        Exception.__init__(self, 'Another application instance is run')


class InitializeException(Exception):
    '''
    base service initialization exception
    '''

    def __init__(self) -> None:
        '''
        default constructor
        '''
        Exception.__init__(self, 'Could not load service')


class InvalidOption(Exception):
    '''
    exception which will be raised on configuration errors
    '''

    def __init__(self, value: Any) -> None:
        '''
        default constructor
        :param value: option value
        '''
        Exception.__init__(self, f'Invalid or unknown option value `{value}`')


class InvalidPackageInfo(Exception):
    '''
    exception which will be raised on package load errors
    '''

    def __init__(self, details: Any) -> None:
        '''
        default constructor
        :param details: error details
        '''
        Exception.__init__(self, f'There are errors during reading package information: `{details}`')


class ReportFailed(Exception):
    '''
    report generation exception
    '''

    def __init__(self) -> None:
        '''
        default constructor
        '''
        Exception.__init__(self, 'Report failed')


class SyncFailed(Exception):
    '''
    remote synchronization exception
    '''

    def __init__(self) -> None:
        '''
        default constructor
        '''
        Exception.__init__(self, 'Sync failed')
