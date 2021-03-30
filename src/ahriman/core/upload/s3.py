#
# Copyright (c) 2021 ahriman team.
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
from pathlib import Path

from ahriman.core.configuration import Configuration
from ahriman.core.upload.upload import Upload
from ahriman.core.util import check_output


class S3(Upload):
    """
    aws-cli wrapper
    :ivar bucket: full bucket name
    :ivar command: command arguments for sync
    """

    _check_output = check_output

    def __init__(self, architecture: str, configuration: Configuration) -> None:
        """
        default constructor
        :param architecture: repository architecture
        :param configuration: configuration instance
        """
        Upload.__init__(self, architecture, configuration)
        self.bucket = configuration.get("s3", "bucket")
        self.command = configuration.getlist("s3", "command")

    def sync(self, path: Path) -> None:
        """
        sync data to remote server
        :param path: local path to sync
        """
        # TODO rewrite to boto, but it is bullshit
        S3._check_output(*self.command, str(path), self.bucket, exception=None, logger=self.logger)
