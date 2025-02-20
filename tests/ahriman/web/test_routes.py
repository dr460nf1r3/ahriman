from aiohttp.web import Application

from ahriman.core.configuration import Configuration
from ahriman.web.routes import setup_routes


def test_setup_routes(application: Application, configuration: Configuration) -> None:
    """
    must generate non-empty list of routes
    """
    setup_routes(application, configuration.getpath("web", "static_path"))
    assert application.router.routes()
