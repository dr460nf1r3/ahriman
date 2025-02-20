#
# Copyright (c) 2021-2023 ahriman team.
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
# pylint: disable=too-many-lines
import datetime
import io
import itertools
import logging
import os
import re
import requests
import selectors
import subprocess

from collections.abc import Callable, Generator, Iterable
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from pwd import getpwuid
from typing import Any, IO, TypeVar

from ahriman.core.exceptions import OptionError, UnsafeRunError
from ahriman.models.repository_paths import RepositoryPaths


__all__ = [
    "check_output",
    "check_user",
    "dataclass_view",
    "enum_values",
    "exception_response_text",
    "extract_user",
    "filter_json",
    "full_version",
    "package_like",
    "parse_version",
    "partition",
    "pretty_datetime",
    "pretty_size",
    "safe_filename",
    "srcinfo_property",
    "srcinfo_property_list",
    "trim_package",
    "utcnow",
    "walk",
]


T = TypeVar("T")


def check_output(*args: str, exception: Exception | None = None, cwd: Path | None = None, input_data: str | None = None,
                 logger: logging.Logger | None = None, user: int | None = None,
                 environment: dict[str, str] | None = None) -> str:
    """
    subprocess wrapper

    Args:
        *args(str): command line arguments
        exception(Exception | None, optional): exception which has to be reraised instead of default subprocess
            exception (Default value = None)
        cwd(Path | None, optional): current working directory (Default value = None)
        input_data(str | None, optional): data which will be written to command stdin (Default value = None)
        logger(logging.Logger | None, optional): logger to log command result if required (Default value = None)
        user(int | None, optional): run process as specified user (Default value = None)
        environment(dict[str, str] | None, optional): optional environment variables if any (Default value = None)

    Returns:
        str: command output

    Raises:
        subprocess.CalledProcessError: if subprocess ended with status code different from 0 and no exception supplied

    Examples:
        Simply call the function::

            >>> check_output("echo", "hello world")

        The more complicated calls which include result logging and input data are also possible::

            >>> import logging
            >>>
            >>> logger = logging.getLogger()
            >>> check_output("python", "-c", "greeting = input('say hello: '); print(); print(greeting)",
            >>>              input_data="hello world", logger=logger)

        An additional argument ``exception`` can be supplied in order to override the default exception::

            >>> check_output("false", exception=RuntimeError("An exception occurred"))
    """
    # hack for IO[str] handle
    def get_io(proc: subprocess.Popen[str], channel_name: str) -> IO[str]:
        channel: IO[str] | None = getattr(proc, channel_name, None)
        return channel if channel is not None else io.StringIO()

    # wrapper around selectors polling
    def poll(sel: selectors.BaseSelector) -> Generator[str, None, None]:
        for key, _ in sel.select():  # we don't need to check mask here because we have only subscribed on reading
            line = key.fileobj.readline()  # type: ignore[union-attr]
            if not line:  # in case of empty line we remove selector as there is no data here anymore
                sel.unregister(key.fileobj)
                continue
            line = line.rstrip()

            if logger is not None:
                logger.debug(line)

            if key.data == "stdout":
                yield line  # yield only stdout data

    environment = environment or {}
    if user is not None:
        environment["HOME"] = getpwuid(user).pw_dir
    with subprocess.Popen(args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          user=user, env=environment, text=True, encoding="utf8", bufsize=1) as process:
        if input_data is not None:
            input_channel = get_io(process, "stdin")
            input_channel.write(input_data)
            input_channel.close()

        selector = selectors.DefaultSelector()
        selector.register(get_io(process, "stdout"), selectors.EVENT_READ, data="stdout")
        selector.register(get_io(process, "stderr"), selectors.EVENT_READ, data="stderr")

        result: list[str] = []
        while selector.get_map():  # while there are unread selectors, keep reading
            result.extend(poll(selector))

        process.terminate()  # make sure that process is terminated
        status_code = process.wait()
        if status_code != 0:
            if exception is not None:
                raise exception
            raise subprocess.CalledProcessError(status_code, process.args)

        return "\n".join(result).rstrip("\n")  # remove newline at the end of any


def check_user(paths: RepositoryPaths, *, unsafe: bool) -> None:
    """
    check if current user is the owner of the root

    Args:
        paths(RepositoryPaths): repository paths object
        unsafe(bool): if set no user check will be performed before path creation

    Raises:
        UnsafeRun: if root uid differs from current uid and check is enabled

    Examples:
        Simply run function with arguments::

            >>> check_user(paths, unsafe=False)
    """
    if not paths.root.exists():
        return  # no directory found, skip check
    if unsafe:
        return  # unsafe flag is enabled, no check performed
    current_uid = os.getuid()
    root_uid, _ = paths.root_owner
    if current_uid != root_uid:
        raise UnsafeRunError(current_uid, root_uid)


def dataclass_view(instance: Any) -> dict[str, Any]:
    """
    convert dataclass instance to json object

    Args:
        instance(Any): dataclass instance

    Returns:
        dict[str, Any]: json representation of the dataclass with empty field removed
    """
    return asdict(instance, dict_factory=lambda fields: {key: value for key, value in fields if value is not None})


def enum_values(enum: type[Enum]) -> list[str]:
    """
    generate list of enumeration values from the source

    Args:
        enum(type[Enum]): source enumeration class

    Returns:
        list[str]: available enumeration values as string
    """
    return [str(key.value) for key in enum]  # explicit str conversion for typing


def exception_response_text(exception: requests.exceptions.RequestException) -> str:
    """
    safe response exception text generation

    Args:
        exception(requests.exceptions.RequestException): exception raised

    Returns:
        str: text of the response if it is not None and empty string otherwise
    """
    result: str = exception.response.text if exception.response is not None else ""
    return result


def extract_user() -> str | None:
    """
    extract user from system environment

    Returns:
        str | None: SUDO_USER in case if set and USER otherwise. It can return None in case if environment has been
    cleared before application start
    """
    return os.getenv("SUDO_USER") or os.getenv("DOAS_USER") or os.getenv("USER")


def filter_json(source: dict[str, Any], known_fields: Iterable[str]) -> dict[str, Any]:
    """
    filter json object by fields used for json-to-object conversion

    Args:
        source(dict[str, Any]): raw json object
        known_fields(Iterable[str]): list of fields which have to be known for the target object

    Returns:
        dict[str, Any]: json object without unknown and empty fields

    Examples:
        This wrapper is mainly used for the dataclasses, thus the flow must be something like this::

            >>> from dataclasses import fields
            >>> from ahriman.models.package import Package
            >>>
            >>> known_fields = [pair.name for pair in fields(Package)]
            >>> properties = filter_json(dump, known_fields)
            >>> package = Package(**properties)
    """
    return {key: value for key, value in source.items() if key in known_fields and value is not None}


def full_version(epoch: str | int | None, pkgver: str, pkgrel: str) -> str:
    """
    generate full version from components

    Args:
        epoch(str | int | None): package epoch if any
        pkgver(str): package version
        pkgrel(str): package release version (arch linux specific)

    Returns:
        str: generated version
    """
    prefix = f"{epoch}:" if epoch else ""
    return f"{prefix}{pkgver}-{pkgrel}"


def package_like(filename: Path) -> bool:
    """
    check if file looks like package

    Args:
        filename(Path): name of file to check

    Returns:
        bool: True in case if name contains ``.pkg.`` and not signature, False otherwise
    """
    name = filename.name
    return ".pkg." in name and not name.endswith(".sig")


def parse_version(version: str) -> tuple[str | None, str, str]:
    """
    parse version and returns its components

    Args:
        version(str): full version string

    Returns:
        tuple[str | None, str, str]: epoch if any, pkgver and pkgrel variables
    """
    if ":" in version:
        epoch, version = version.split(":", maxsplit=1)
    else:
        epoch = None
    pkgver, pkgrel = version.rsplit("-", maxsplit=1)

    return epoch, pkgver, pkgrel


def partition(source: list[T], predicate: Callable[[T], bool]) -> tuple[list[T], list[T]]:
    """
    partition list into two based on predicate, based on https://docs.python.org/dev/library/itertools.html#itertools-recipes

    Args:
        source(list[T]): source list to be partitioned
        predicate(Callable[[T], bool]): filter function

    Returns:
        tuple[list[T], list[T]]: two lists, first is which ``predicate`` is ``True``, second is ``False``
    """
    first_iter, second_iter = itertools.tee(source)
    return list(filter(predicate, first_iter)), list(itertools.filterfalse(predicate, second_iter))


def pretty_datetime(timestamp: datetime.datetime | float | int | None) -> str:
    """
    convert datetime object to string

    Args:
        timestamp(datetime.datetime | float | int | None): datetime to convert

    Returns:
        str: pretty printable datetime as string
    """
    if timestamp is None:
        return ""
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.datetime.utcfromtimestamp(timestamp)
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def pretty_size(size: float | None, level: int = 0) -> str:
    """
    convert size to string

    Args:
        size(float | None): size to convert
        level(int, optional): represents current units, 0 is B, 1 is KiB, etc (Default value = 0)

    Returns:
        str: pretty printable size as string

    Raises:
        InvalidOption: if size is more than 1TiB
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
        raise OptionError(level)  # must never happen actually

    if size is None:
        return ""
    if size < 1024 or level >= 3:
        return f"{size:.1f} {str_level()}"
    return pretty_size(size / 1024, level + 1)


def safe_filename(source: str) -> str:
    """
    convert source string to its safe representation

    Args:
        source(str): string to convert

    Returns:
        str: result string in which all unsafe characters are replaced by dash
    """
    # RFC-3986 https://datatracker.ietf.org/doc/html/rfc3986 states that unreserved characters are
    # https://datatracker.ietf.org/doc/html/rfc3986#section-2.3
    #     unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
    # however we would like to allow some gen-delims characters in filename, because those characters are used
    # as delimiter in other URI parts. The ones we allow to are:
    #     ":" - used as separator in schema and userinfo
    #     "[" and "]" - used for host part
    #     "@" - used as separator between host and userinfo
    return re.sub(r"[^A-Za-z\d\-._~:\[\]@]", "-", source)


def srcinfo_property(key: str, srcinfo: dict[str, Any], package_srcinfo: dict[str, Any], *,
                     default: Any = None) -> Any:
    """
    extract property from SRCINFO. This method extracts property from package if this property is presented in
    ``package``. Otherwise, it looks for the same property in root srcinfo. If none found, the default value will be
    returned

    Args:
        key(str): key to extract from srcinfo
        srcinfo(dict[str, Any]): root structure of SRCINFO
        package_srcinfo(dict[str, Any]): package specific SRCINFO
        default(Any, optional): the default value for the specified key (Default value = None)

    Returns:
        Any: extracted value from SRCINFO
    """
    return package_srcinfo.get(key) or srcinfo.get(key) or default


def srcinfo_property_list(key: str, srcinfo: dict[str, Any], package_srcinfo: dict[str, Any], *,
                          architecture: str | None = None) -> list[Any]:
    """
    extract list property from SRCINFO. Unlike ``srcinfo_property`` it supposes that default return value is always
    empty list. If ``architecture`` is supplied, then it will try to lookup for architecture specific values and will
    append it at the end of result

    Args:
        key(str): key to extract from srcinfo
        srcinfo(dict[str, Any]): root structure of SRCINFO
        package_srcinfo(dict[str, Any]): package specific SRCINFO
        architecture(str | None, optional): package architecture if set (Default value = None)

    Returns:
        list[Any]: list of extracted properties from SRCINFO
    """
    values: list[Any] = srcinfo_property(key, srcinfo, package_srcinfo, default=[])
    if architecture is not None:
        values.extend(srcinfo_property(f"{key}_{architecture}", srcinfo, package_srcinfo, default=[]))
    return values


def trim_package(package_name: str) -> str:
    """
    remove version bound and description from package name. Pacman allows to specify version bound (=, <=, >= etc) for
    packages in dependencies and also allows to specify description (via :); this function removes trailing parts and
    return exact package name

    Args:
        package_name(str): source package name

    Returns:
        str: package name without description or version bound
    """
    for symbol in ("<", "=", ">", ":"):
        package_name = package_name.partition(symbol)[0]
    return package_name


def utcnow() -> datetime.datetime:
    """
    get current time

    Returns:
        datetime.datetime: current time in UTC
    """
    return datetime.datetime.utcnow()


def walk(directory_path: Path) -> Generator[Path, None, None]:
    """
    list all file paths in given directory
    Credits to https://stackoverflow.com/a/64915960

    Args:
        directory_path(Path): root directory path

    Yields:
        Path: all found files in given directory with full path

    Examples:
        Since the ``pathlib`` module does not provide an alternative to ``os.walk``, this wrapper can be used instead::

            >>> from pathlib import Path
            >>>
            >>> for file_path in walk(Path.cwd()):
            >>>     print(file_path)

        Note, however, that unlike the original method, it does not yield directories.
    """
    for element in directory_path.iterdir():
        if element.is_dir():
            yield from walk(element)
            continue
        yield element
