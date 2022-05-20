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
import aiohttp_jinja2

from typing import Any, Dict

from ahriman.core.auth.helpers import authorized_userid
from ahriman.models.user_access import UserAccess
from ahriman.web.views.base import BaseView


class IndexView(BaseView):
    """
    root view

    It uses jinja2 templates for report generation, the following variables are allowed:

        * auth - authorization descriptor, required
            * control - HTML to insert for login control, HTML string, required
            * enabled - whether authorization is enabled by configuration or not, boolean, required
            * username - authenticated username if any, string, null means not authenticated
        * index_url - url to the repository index, string, optional
        * repository - repository name, string, required

    Attributes:
        GET_PERMISSION(UserAccess): (class attribute) get permissions of self
        HEAD_PERMISSION(UserAccess): (class attribute) head permissions of self
    """

    GET_PERMISSION = HEAD_PERMISSION = UserAccess.Unauthorized

    @aiohttp_jinja2.template("build-status.jinja2")
    async def get(self) -> Dict[str, Any]:
        """
        process get request. No parameters supported here

        Returns:
            Dict[str, Any]: parameters for jinja template
        """
        auth_username = await authorized_userid(self.request)
        auth = {
            "control": self.validator.auth_control,
            "enabled": self.validator.enabled,
            "username": auth_username,
        }

        return {
            "auth": auth,
            "index_url": self.configuration.get("web", "index_url", fallback=None),
            "repository": self.service.repository.name,
        }
