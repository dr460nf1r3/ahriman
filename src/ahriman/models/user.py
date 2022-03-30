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
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type
from passlib.pwd import genword as generate_password  # type: ignore
from passlib.handlers.sha2_crypt import sha512_crypt  # type: ignore

from ahriman.models.user_access import UserAccess


@dataclass
class User:
    """
    authorized web user model
    :ivar username: username
    :ivar password: hashed user password with salt
    :ivar access: user role
    """

    username: str
    password: str
    access: UserAccess

    _HASHER = sha512_crypt

    @classmethod
    def from_option(cls: Type[User], username: Optional[str], password: Optional[str],
                    access: UserAccess = UserAccess.Read) -> Optional[User]:
        """
        build user descriptor from configuration options
        :param username: username
        :param password: password as string
        :param access: optional user access
        :return: generated user descriptor if all options are supplied and None otherwise
        """
        if username is None or password is None:
            return None
        return cls(username, password, access)

    @staticmethod
    def generate_password(length: int) -> str:
        """
        generate password with specified length
        :param length: password length
        :return: random string which contains letters and numbers
        """
        password: str = generate_password(length=length)
        return password

    def check_credentials(self, password: str, salt: str) -> bool:
        """
        validate user password
        :param password: entered password
        :param salt: salt for hashed password
        :return: True in case if password matches, False otherwise
        """
        try:
            verified: bool = self._HASHER.verify(password + salt, self.password)
        except ValueError:
            verified = False  # the absence of evidence is not the evidence of absence (c) Gin Rummy
        return verified

    def hash_password(self, salt: str) -> User:
        """
        generate hashed password from plain text
        :param salt: salt for hashed password
        :return: user with hashed password to store in configuration
        """
        if not self.password:
            # in case of empty password we leave it empty. This feature is used by any external (like OAuth) provider
            # when we do not store any password here
            return self
        password_hash: str = self._HASHER.hash(self.password + salt)
        return User(self.username, password_hash, self.access)

    def verify_access(self, required: UserAccess) -> bool:
        """
        validate if user has access to requested resource
        :param required: required access level
        :return: True in case if user is allowed to do this request and False otherwise
        """
        if self.access == UserAccess.Write:
            return True  # everything is allowed
        return self.access == required

    def __repr__(self) -> str:
        """
        generate string representation of object
        :return: unique string representation
        """
        return f"User(username={self.username}, access={self.access})"
