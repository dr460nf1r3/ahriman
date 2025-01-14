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
import argparse

from pathlib import Path
from pwd import getpwuid

from ahriman.application.application import Application
from ahriman.application.handlers import Handler
from ahriman.core.configuration import Configuration
from ahriman.models.repository_paths import RepositoryPaths
from ahriman.models.user import User


class Setup(Handler):
    """
    setup handler

    Attributes:
        ARCHBUILD_COMMAND_PATH(Path): (class attribute) default devtools command
        MIRRORLIST_PATH(Path): (class attribute) path to pacman default mirrorlist (used by multilib repository)
        SUDOERS_DIR_PATH(Path): (class attribute) path to sudoers.d includes directory
    """

    ALLOW_AUTO_ARCHITECTURE_RUN = False

    ARCHBUILD_COMMAND_PATH = Path("/usr") / "bin" / "archbuild"
    MIRRORLIST_PATH = Path("/etc") / "pacman.d" / "mirrorlist"
    SUDOERS_DIR_PATH = Path("/etc") / "sudoers.d"

    @classmethod
    def run(cls, args: argparse.Namespace, architecture: str, configuration: Configuration, *, report: bool) -> None:
        """
        callback for command line

        Args:
            args(argparse.Namespace): command line args
            architecture(str): repository architecture
            configuration(Configuration): configuration instance
            report(bool): force enable or disable reporting
        """
        Setup.configuration_create_ahriman(args, architecture, args.repository, configuration)
        configuration.reload()

        application = Application(architecture, configuration, report=report)

        Setup.configuration_create_makepkg(args.packager, args.makeflags_jobs, application.repository.paths)
        Setup.executable_create(application.repository.paths, args.build_command, architecture)
        Setup.configuration_create_devtools(args.build_command, architecture, args.from_configuration, args.mirror,
                                            args.multilib, args.repository, application.repository.paths)
        Setup.configuration_create_sudo(application.repository.paths, args.build_command, architecture)

        application.repository.repo.init()
        # lazy database sync
        application.repository.pacman.handle  # pylint: disable=pointless-statement

    @staticmethod
    def build_command(root: Path, prefix: str, architecture: str) -> Path:
        """
        generate build command name

        Args:
            root(Path): root directory for the build command (must be root of the repository)
            prefix(str): command prefix in {prefix}-{architecture}-build
            architecture(str): repository architecture

        Returns:
            Path: valid devtools command name
        """
        return root / f"{prefix}-{architecture}-build"

    @staticmethod
    def configuration_create_ahriman(args: argparse.Namespace, architecture: str, repository: str,
                                     root: Configuration) -> None:
        """
        create service specific configuration

        Args:
            args(argparse.Namespace): command line args
            architecture(str): repository architecture
            repository(str): repository name
            root(Configuration): root configuration instance
        """
        configuration = Configuration()

        section = Configuration.section_name("build", architecture)
        build_command = Setup.build_command(root.repository_paths.root, args.build_command, architecture)
        configuration.set_option(section, "build_command", str(build_command))
        configuration.set_option("repository", "name", repository)
        if args.build_as_user is not None:
            configuration.set_option(section, "makechrootpkg_flags", f"-U {args.build_as_user}")

        section = Configuration.section_name("alpm", architecture)
        if args.mirror is not None:
            configuration.set_option(section, "mirror", args.mirror)
        if not args.multilib:
            repositories = filter(lambda r: r != "multilib", root.getlist("alpm", "repositories"))
            configuration.set_option(section, "repositories", " ".join(repositories))

        section = Configuration.section_name("sign", architecture)
        if args.sign_key is not None:
            configuration.set_option(section, "target", " ".join([target.name.lower() for target in args.sign_target]))
            configuration.set_option(section, "key", args.sign_key)

        section = Configuration.section_name("web", architecture)
        if args.web_port is not None:
            configuration.set_option(section, "port", str(args.web_port))
        if args.web_unix_socket is not None:
            configuration.set_option(section, "unix_socket", str(args.web_unix_socket))

        if args.generate_salt:
            configuration.set_option("auth", "salt", User.generate_password(20))

        target = root.include / "00-setup-overrides.ini"
        with target.open("w") as ahriman_configuration:
            configuration.write(ahriman_configuration)

    @staticmethod
    def configuration_create_devtools(prefix: str, architecture: str, source: Path, mirror: str | None,
                                      multilib: bool, repository: str, paths: RepositoryPaths) -> None:
        """
        create configuration for devtools based on ``source`` configuration

        Notes:
            devtools does not allow to specify the pacman configuration, thus we still have to use configuration in /usr

        Args:
            prefix(str): command prefix in {prefix}-{architecture}-build
            architecture(str): repository architecture
            source(Path): path to source configuration file
            mirror(str | None): link to package server mirror
            multilib(bool): add or do not multilib repository to the configuration
            repository(str): repository name
            paths(RepositoryPaths): repository paths instance
        """
        # allow_no_value=True is required because pacman uses boolean configuration in which just keys present
        # (e.g. NoProgressBar) which will lead to exception
        configuration = Configuration(allow_no_value=True)
        # preserve case
        # stupid mypy thinks that it is impossible
        configuration.optionxform = lambda key: key  # type: ignore[method-assign]

        # load default configuration first
        # we cannot use Include here because it will be copied to new chroot, thus no includes there
        configuration.read(source)

        # set our architecture now
        configuration.set_option("options", "Architecture", architecture)

        # add multilib
        if multilib:
            configuration.set_option("multilib", "Include", str(Setup.MIRRORLIST_PATH))

        # override Include option to Server in case if mirror option set
        if mirror is not None:
            for section in filter(lambda s: s != "options", configuration.sections()):
                if configuration.get(section, "Include", fallback=None) != str(Setup.MIRRORLIST_PATH):
                    continue
                configuration.remove_option(section, "Include")
                configuration.set_option(section, "Server", mirror)

        # add repository itself
        configuration.set_option(repository, "SigLevel", "Never")  # we don't care
        configuration.set_option(repository, "Server", f"file://{paths.repository}")

        target = source.parent / f"{prefix}-{architecture}.conf"
        with target.open("w") as devtools_configuration:
            configuration.write(devtools_configuration)

    @staticmethod
    def configuration_create_makepkg(packager: str, makeflags_jobs: bool, paths: RepositoryPaths) -> None:
        """
        create configuration for makepkg

        Args:
            packager(str): packager identifier (e.g. name, email)
            makeflags_jobs(bool): set MAKEFLAGS variable to number of cores
            paths(RepositoryPaths): repository paths instance
        """

        content = f"PACKAGER='{packager}'\n"
        if makeflags_jobs:
            content += """MAKEFLAGS="-j$(nproc)"\n"""

        uid, _ = paths.root_owner
        home_dir = Path(getpwuid(uid).pw_dir)
        (home_dir / ".makepkg.conf").write_text(content, encoding="utf8")

    @staticmethod
    def configuration_create_sudo(paths: RepositoryPaths, prefix: str, architecture: str) -> None:
        """
        create configuration to run build command with sudo without password

        Args:
            paths(RepositoryPaths): repository paths instance
            prefix(str): command prefix in {prefix}-{architecture}-build
            architecture(str): repository architecture
        """
        command = Setup.build_command(paths.root, prefix, architecture)
        sudoers_file = Setup.build_command(Setup.SUDOERS_DIR_PATH, prefix, architecture)
        sudoers_file.write_text(f"ahriman ALL=(ALL) NOPASSWD:SETENV: {command} *\n", encoding="utf8")
        sudoers_file.chmod(0o400)  # security!

    @staticmethod
    def executable_create(paths: RepositoryPaths, prefix: str, architecture: str) -> None:
        """
        create executable for the service

        Args:
            paths(RepositoryPaths): repository paths instance
            prefix(str): command prefix in {prefix}-{architecture}-build
            architecture(str): repository architecture
        """
        command = Setup.build_command(paths.root, prefix, architecture)
        command.unlink(missing_ok=True)
        command.symlink_to(Setup.ARCHBUILD_COMMAND_PATH)
        paths.chown(command)  # we would like to keep owner inside ahriman's home
