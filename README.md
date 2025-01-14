# ArcH linux ReposItory MANager

[![tests status](https://github.com/arcan1s/ahriman/actions/workflows/run-tests.yml/badge.svg)](https://github.com/arcan1s/ahriman/actions/workflows/run-tests.yml)
[![setup status](https://github.com/arcan1s/ahriman/actions/workflows/run-setup.yml/badge.svg)](https://github.com/arcan1s/ahriman/actions/workflows/run-setup.yml)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/arcan1s/ahriman?label=docker%20image)](https://hub.docker.com/r/arcan1s/ahriman)
[![CodeFactor](https://www.codefactor.io/repository/github/arcan1s/ahriman/badge)](https://www.codefactor.io/repository/github/arcan1s/ahriman)
[![Documentation Status](https://readthedocs.org/projects/ahriman/badge/?version=latest)](https://ahriman.readthedocs.io/?badge=latest)

Wrapper for managing custom repository inspired by [repo-scripts](https://github.com/arcan1s/repo-scripts).

## Features

* Install-configure-forget manager for the very own repository.
* Multi-architecture support.
* Dependency manager.
* VCS packages support.
* Official repository support.
* Ability to patch AUR packages and even create package from local PKGBUILDs.
* Various rebuild options with ability to automatically bump package version.
* Sign support with gpg (repository, package), multiple packagers support.
* Triggers for repository updates, e.g. synchronization to remote services (rsync, s3 and github) and report generation (email, html, telegram).
* Repository status interface with optional authorization and control options:

    ![web interface](web.png)

## Installation and run

For installation details kindly refer to the [documentation](https://ahriman.readthedocs.io/en/latest/setup.html). For application commands it is possible to get information by using `--help`/`help` command or by using man page ([web version](https://ahriman.readthedocs.io/en/latest/command-line.html)).

## Configuration

Every available option is described in the [documentation](https://ahriman.readthedocs.io/en/latest/configuration.html).

The application provides reasonable defaults which allow to use it out-of-box; however additional steps (like configuring build toolchain and sudoers) are recommended and can be easily achieved by following install instructions.

## [FAQ](https://ahriman.readthedocs.io/en/latest/faq.html)

## Live demos

* [Build status page](https://ahriman-demo.arcanis.me). You can log in as `demo` user by using `demo` password. However, you will not be able to run tasks. [HTTP API documentation](https://ahriman-demo.arcanis.me/api-docs) is also available.
* [Repository index](http://repo.arcanis.me/x86_64/index.html).
* [Telegram feed](https://t.me/arcanisrepo).
