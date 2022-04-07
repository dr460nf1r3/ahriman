#
# Copyright (c) 2021-2022 ahriman team.
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
import datetime
import os
import requests
import shutil
import subprocess
import tempfile

from contextlib import contextmanager
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Union

from ahriman.core.exceptions import InvalidOption, UnsafeRun
from ahriman.models.repository_paths import RepositoryPaths


def check_output(*args: str, exception: Optional[Exception], cwd: Optional[Path] = None,
                 input_data: Optional[str] = None, logger: Optional[Logger] = None, user: Optional[int] = None) -> str:
    """
    subprocess wrapper
    :param args: command line arguments
    :param exception: exception which has to be reraised instead of default subprocess exception
    :param cwd: current working directory
    :param input_data: data which will be written to command stdin
    :param logger: logger to log command result if required
    :param user: run process as specified user
    :return: command output
    """
    def log(single: str) -> None:
        if logger is not None:
            logger.debug(single)

    # FIXME additional workaround for linter and type check which do not know that user arg is supported
    # pylint: disable=unexpected-keyword-arg
    with subprocess.Popen(args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          user=user, text=True, encoding="utf8", bufsize=1) as process:  # type: ignore
        if input_data is not None:
            process.stdin.write(input_data)
            process.stdin.close()

        # read stdout and append to output result
        result: List[str] = []
        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            if not line:  # skip empty lines
                continue
            result.append(line)
            log(line)

        # read stderr and write info to logs
        for line in iter(process.stderr.readline, ""):
            log(line.strip())

        process.terminate()  # make sure that process is terminated
        status_code = process.wait()
        if status_code != 0:
            if exception is not None:
                raise exception
            raise subprocess.CalledProcessError(status_code, process.args)

        return "\n".join(result)


def check_user(paths: RepositoryPaths, unsafe: bool) -> None:
    """
    check if current user is the owner of the root
    :param paths: repository paths object
    :param unsafe: if set no user check will be performed before path creation
    """
    if not paths.root.exists():
        return  # no directory found, skip check
    if unsafe:
        return  # unsafe flag is enabled, no check performed
    current_uid = os.getuid()
    root_uid, _ = paths.root_owner
    if current_uid != root_uid:
        raise UnsafeRun(current_uid, root_uid)


def exception_response_text(exception: requests.exceptions.HTTPError) -> str:
    """
    safe response exception text generation
    :param exception: exception raised
    :return: text of the response if it is not None and empty string otherwise
    """
    result: str = exception.response.text if exception.response is not None else ""
    return result


def filter_json(source: Dict[str, Any], known_fields: Iterable[str]) -> Dict[str, Any]:
    """
    filter json object by fields used for json-to-object conversion
    :param source: raw json object
    :param known_fields: list of fields which have to be known for the target object
    :return: json object without unknown and empty fields
    """
    return {key: value for key, value in source.items() if key in known_fields and value is not None}


def full_version(epoch: Union[str, int, None], pkgver: str, pkgrel: str) -> str:
    """
    generate full version from components
    :param epoch: package epoch if any
    :param pkgver: package version
    :param pkgrel: package release version (arch linux specific)
    :return: generated version
    """
    prefix = f"{epoch}:" if epoch else ""
    return f"{prefix}{pkgver}-{pkgrel}"


def package_like(filename: Path) -> bool:
    """
    check if file looks like package
    :param filename: name of file to check
    :return: True in case if name contains `.pkg.` and not signature, False otherwise
    """
    name = filename.name
    return ".pkg." in name and not name.endswith(".sig")


def pretty_datetime(timestamp: Optional[Union[datetime.datetime, float, int]]) -> str:
    """
    convert datetime object to string
    :param timestamp: datetime to convert
    :return: pretty printable datetime as string
    """
    if timestamp is None:
        return ""
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.datetime.utcfromtimestamp(timestamp)
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def pretty_size(size: Optional[float], level: int = 0) -> str:
    """
    convert size to string
    :param size: size to convert
    :param level: represents current units, 0 is B, 1 is KiB etc
    :return: pretty printable size as string
    """
    def str_level() -> str:
        if level == 0:
            return "B"
        if level == 1:
            return "KiB"
        if level == 2:
            return "MiB"
        if level == 3:
            return "GiB"
        raise InvalidOption(level)  # must never happen actually

    if size is None:
        return ""
    if size < 1024 or level >= 3:
        return f"{size:.1f} {str_level()}"
    return pretty_size(size / 1024, level + 1)


@contextmanager
def tmpdir() -> Generator[Path, None, None]:
    """
    wrapper for tempfile to remove directory after all
    :return: path to the created directory
    """
    path = Path(tempfile.mkdtemp())
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def walk(directory_path: Path) -> Generator[Path, None, None]:
    """
    list all file paths in given directory
    Credits to https://stackoverflow.com/a/64915960
    :param directory_path: root directory path
    :return: all found files in given directory with full path
    """
    for element in directory_path.iterdir():
        if element.is_dir():
            yield from walk(element)
            continue
        yield element
