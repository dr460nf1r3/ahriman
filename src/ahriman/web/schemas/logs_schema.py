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
from marshmallow import Schema, fields

from ahriman.web.schemas.status_schema import StatusSchema


class LogsSchema(Schema):
    """
    response package logs schema
    """

    package_base = fields.String(required=True, metadata={
        "description": "Package base name",
        "example": "ahriman",
    })
    status = fields.Nested(StatusSchema(), required=True, metadata={
        "description": "Last package status",
    })
    logs = fields.String(required=True, metadata={
        "description": "Full package log from the last build",
    })
