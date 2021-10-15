from ahriman.core.configuration import Configuration
from ahriman.core.report.jinja_template import JinjaTemplate
from ahriman.models.package import Package


def test_generate(configuration: Configuration, package_ahriman: Package) -> None:
    """
    must generate html report
    """
    path = configuration.getpath("html", "template_path")
    report = JinjaTemplate("html", configuration)
    assert report.make_html([package_ahriman], path)