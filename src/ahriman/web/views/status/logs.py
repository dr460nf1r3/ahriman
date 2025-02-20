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
import aiohttp_apispec  # type: ignore[import]

from aiohttp.web import HTTPBadRequest, HTTPNoContent, HTTPNotFound, Response, json_response

from ahriman.core.exceptions import UnknownPackageError
from ahriman.models.log_record_id import LogRecordId
from ahriman.models.user_access import UserAccess
from ahriman.web.schemas import AuthSchema, ErrorSchema, LogSchema, LogsSchema, PackageNameSchema
from ahriman.web.views.base import BaseView


class LogsView(BaseView):
    """
    package logs web view

    Attributes:
        DELETE_PERMISSION(UserAccess): (class attribute) delete permissions of self
        GET_PERMISSION(UserAccess): (class attribute) get permissions of self
        POST_PERMISSION(UserAccess): (class attribute) post permissions of self
    """

    DELETE_PERMISSION = POST_PERMISSION = UserAccess.Full
    GET_PERMISSION = UserAccess.Reporter

    @aiohttp_apispec.docs(
        tags=["Packages"],
        summary="Delete package logs",
        description="Delete all logs which belong to the specified package",
        responses={
            204: {"description": "Success response"},
            401: {"description": "Authorization required", "schema": ErrorSchema},
            403: {"description": "Access is forbidden", "schema": ErrorSchema},
            500: {"description": "Internal server error", "schema": ErrorSchema},
        },
        security=[{"token": [DELETE_PERMISSION]}],
    )
    @aiohttp_apispec.cookies_schema(AuthSchema)
    @aiohttp_apispec.match_info_schema(PackageNameSchema)
    async def delete(self) -> None:
        """
        delete package logs

        Raises:
            HTTPNoContent: on success response
        """
        package_base = self.request.match_info["package"]
        self.service.remove_logs(package_base, None)

        raise HTTPNoContent()

    @aiohttp_apispec.docs(
        tags=["Packages"],
        summary="Get package logs",
        description="Retrieve all package logs and the last package status",
        responses={
            200: {"description": "Success response", "schema": LogsSchema},
            401: {"description": "Authorization required", "schema": ErrorSchema},
            403: {"description": "Access is forbidden", "schema": ErrorSchema},
            404: {"description": "Package base is unknown", "schema": ErrorSchema},
            500: {"description": "Internal server error", "schema": ErrorSchema},
        },
        security=[{"token": [GET_PERMISSION]}],
    )
    @aiohttp_apispec.cookies_schema(AuthSchema)
    @aiohttp_apispec.match_info_schema(PackageNameSchema)
    async def get(self) -> Response:
        """
        get last package logs

        Returns:
            Response: 200 with package logs on success

        Raises:
            HTTPNotFound: if package base is unknown
        """
        package_base = self.request.match_info["package"]

        try:
            _, status = self.service.get(package_base)
        except UnknownPackageError:
            raise HTTPNotFound()
        logs = self.service.get_logs(package_base)

        response = {
            "package_base": package_base,
            "status": status.view(),
            "logs": logs
        }
        return json_response(response)

    @aiohttp_apispec.docs(
        tags=["Packages"],
        summary="Add package logs",
        description="Insert new package log record",
        responses={
            204: {"description": "Success response"},
            400: {"description": "Bad data is supplied", "schema": ErrorSchema},
            401: {"description": "Authorization required", "schema": ErrorSchema},
            403: {"description": "Access is forbidden", "schema": ErrorSchema},
            500: {"description": "Internal server error", "schema": ErrorSchema},
        },
        security=[{"token": [POST_PERMISSION]}],
    )
    @aiohttp_apispec.cookies_schema(AuthSchema)
    @aiohttp_apispec.match_info_schema(PackageNameSchema)
    @aiohttp_apispec.json_schema(LogSchema)
    async def post(self) -> None:
        """
        create new package log record

        Raises:
            HTTPBadRequest: if bad data is supplied
            HTTPNoContent: in case of success response
        """
        package_base = self.request.match_info["package"]
        data = await self.extract_data()

        try:
            created = data["created"]
            record = data["message"]
            process_id = data["process_id"]
        except Exception as e:
            raise HTTPBadRequest(reason=str(e))

        self.service.update_logs(LogRecordId(package_base, process_id), created, record)

        raise HTTPNoContent()
