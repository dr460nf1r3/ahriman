from pytest_mock import MockerFixture

from ahriman.core.configuration import Configuration
from ahriman.core.gitremote import RemotePushTrigger
from ahriman.models.package import Package
from ahriman.models.result import Result


def test_on_result(configuration: Configuration, result: Result, package_ahriman: Package,
                   mocker: MockerFixture) -> None:
    """
    must push changes on result
    """
    run_mock = mocker.patch("ahriman.core.gitremote.remote_push.RemotePush.run")
    trigger = RemotePushTrigger("x86_64", configuration)

    trigger.on_result(result, [package_ahriman])
    run_mock.assert_called_once_with(result)
