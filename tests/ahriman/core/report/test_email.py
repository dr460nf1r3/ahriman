import pytest

from pytest_mock import MockerFixture

from ahriman.core.configuration import Configuration
from ahriman.core.report.email import Email
from ahriman.models.package import Package
from ahriman.models.result import Result


def test_send(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must send an email with attachment
    """
    smtp_mock = mocker.patch("smtplib.SMTP")

    report = Email("x86_64", configuration, "email")
    report._send("a text", {"attachment.html": "an attachment"})
    smtp_mock.return_value.starttls.assert_not_called()
    smtp_mock.return_value.login.assert_not_called()
    smtp_mock.return_value.sendmail.assert_called_once_with(report.sender, report.receivers, pytest.helpers.anyvar(int))
    smtp_mock.return_value.quit.assert_called_once_with()


def test_send_auth(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must send an email with attachment with auth
    """
    configuration.set_option("email", "user", "username")
    configuration.set_option("email", "password", "password")
    smtp_mock = mocker.patch("smtplib.SMTP")

    report = Email("x86_64", configuration, "email")
    report._send("a text", {"attachment.html": "an attachment"})
    smtp_mock.return_value.login.assert_called_once_with(report.user, report.password)


def test_send_auth_no_password(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must send an email with attachment without auth if no password supplied
    """
    configuration.set_option("email", "user", "username")
    smtp_mock = mocker.patch("smtplib.SMTP")

    report = Email("x86_64", configuration, "email")
    report._send("a text", {"attachment.html": "an attachment"})
    smtp_mock.return_value.login.assert_not_called()


def test_send_auth_no_user(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must send an email with attachment without auth if no user supplied
    """
    configuration.set_option("email", "password", "password")
    smtp_mock = mocker.patch("smtplib.SMTP")

    report = Email("x86_64", configuration, "email")
    report._send("a text", {"attachment.html": "an attachment"})
    smtp_mock.return_value.login.assert_not_called()


def test_send_ssl_tls(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must send an email with attachment with ssl/tls
    """
    configuration.set_option("email", "ssl", "ssl")
    smtp_mock = mocker.patch("smtplib.SMTP_SSL")

    report = Email("x86_64", configuration, "email")
    report._send("a text", {"attachment.html": "an attachment"})
    smtp_mock.return_value.starttls.assert_not_called()
    smtp_mock.return_value.login.assert_not_called()
    smtp_mock.return_value.sendmail.assert_called_once_with(report.sender, report.receivers, pytest.helpers.anyvar(int))
    smtp_mock.return_value.quit.assert_called_once_with()


def test_send_starttls(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must send an email with attachment with starttls
    """
    configuration.set_option("email", "ssl", "starttls")
    smtp_mock = mocker.patch("smtplib.SMTP")

    report = Email("x86_64", configuration, "email")
    report._send("a text", {"attachment.html": "an attachment"})
    smtp_mock.return_value.starttls.assert_called_once_with()


def test_generate(configuration: Configuration, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must generate report
    """
    send_mock = mocker.patch("ahriman.core.report.email.Email._send")

    report = Email("x86_64", configuration, "email")
    report.generate([package_ahriman], Result())
    send_mock.assert_called_once_with(pytest.helpers.anyvar(int), {})


def test_generate_with_built(configuration: Configuration, package_ahriman: Package, result: Result,
                             mocker: MockerFixture) -> None:
    """
    must generate report with built packages
    """
    send_mock = mocker.patch("ahriman.core.report.email.Email._send")

    report = Email("x86_64", configuration, "email")
    report.generate([package_ahriman], result)
    send_mock.assert_called_once_with(pytest.helpers.anyvar(int), {})


def test_generate_with_built_and_full_path(
        configuration: Configuration,
        package_ahriman: Package,
        result: Result,
        mocker: MockerFixture) -> None:
    """
    must generate report with built packages and full packages lists
    """
    send_mock = mocker.patch("ahriman.core.report.email.Email._send")

    report = Email("x86_64", configuration, "email")
    report.full_template_path = report.template_path
    report.generate([package_ahriman], result)
    send_mock.assert_called_once_with(pytest.helpers.anyvar(int), pytest.helpers.anyvar(int))


def test_generate_no_empty(configuration: Configuration, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must not generate report with built packages if no_empty_report is set
    """
    configuration.set_option("email", "no_empty_report", "yes")
    send_mock = mocker.patch("ahriman.core.report.email.Email._send")

    report = Email("x86_64", configuration, "email")
    report.generate([package_ahriman], Result())
    send_mock.assert_not_called()


def test_generate_no_empty_with_built(configuration: Configuration, package_ahriman: Package, result: Result,
                                      mocker: MockerFixture) -> None:
    """
    must generate report with built packages if no_empty_report is set
    """
    configuration.set_option("email", "no_empty_report", "yes")
    send_mock = mocker.patch("ahriman.core.report.email.Email._send")

    report = Email("x86_64", configuration, "email")
    report.generate([package_ahriman], result)
    send_mock.assert_called_once_with(pytest.helpers.anyvar(int), {})
