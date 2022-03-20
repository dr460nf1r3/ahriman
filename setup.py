from pathlib import Path
from setuptools import setup, find_packages
from typing import Any, Dict


metadata_path = Path(__file__).resolve().parent / "src/ahriman/version.py"
metadata: Dict[str, Any] = {}
with metadata_path.open() as metadata_file:
    exec(metadata_file.read(), metadata)  # pylint: disable=exec-used


setup(
    name="ahriman",

    version=metadata["__version__"],
    zip_safe=False,

    description="ArcH Linux ReposItory MANager",

    author="ahriman team",
    author_email="",
    url="https://github.com/arcan1s/ahriman",

    license="GPL3",

    packages=find_packages("src"),
    package_dir={"": "src"},

    dependency_links=[
    ],
    install_requires=[
        "inflection",
        "passlib",
        "pyalpm",
        "requests",
        "srcinfo",
    ],
    setup_requires=[
        "pytest-runner",
    ],
    tests_require=[
        "pytest",
        "pytest-aiohttp",
        "pytest-cov",
        "pytest-helpers-namespace",
        "pytest-mock",
        "pytest-spec",
        "pytest-resource-path",
    ],

    include_package_data=True,
    scripts=[
        "package/bin/ahriman",
    ],
    data_files=[
        ("/etc", [
            "package/etc/ahriman.ini",
        ]),
        ("/etc/ahriman.ini.d", [
            "package/etc/ahriman.ini.d/logging.ini",
        ]),
        ("lib/systemd/system", [
            "package/lib/systemd/system/ahriman@.service",
            "package/lib/systemd/system/ahriman@.timer",
            "package/lib/systemd/system/ahriman-web@.service",
        ]),
        ("share/ahriman", [
            "package/share/ahriman/build-status.jinja2",
            "package/share/ahriman/email-index.jinja2",
            "package/share/ahriman/repo-index.jinja2",
        ]),
        ("share/ahriman/build-status", [
            "package/share/ahriman/build-status/login-modal.jinja2",
            "package/share/ahriman/build-status/package-actions-modals.jinja2",
            "package/share/ahriman/build-status/package-actions-script.jinja2",
        ]),
        ("share/ahriman/static", [
            "package/share/ahriman/static/favicon.ico",
        ]),
        ("share/ahriman/utils", [
            "package/share/ahriman/utils/bootstrap-scripts.jinja2",
            "package/share/ahriman/utils/style.jinja2",
        ]),
        ("share/man/man1", [
            "docs/ahriman.1",
        ])
    ],

    extras_require={
        "check": [
            "autopep8",
            "bandit",
            "mypy",
            "pylint",
        ],
        "s3": [
            "boto3",
        ],
        "test": [
            "pytest",
            "pytest-aiohttp",
            "pytest-cov",
            "pytest-helpers-namespace",
            "pytest-mock",
            "pytest-resource-path",
            "pytest-spec",
        ],
        "web": [
            "Jinja2",
            "aiohttp",
            "aiohttp_jinja2",
            "aioauth-client",
            "aiohttp_debugtoolbar",
            "aiohttp_session",
            "aiohttp_security",
            "cryptography",
        ],
    },
)
