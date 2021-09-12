from ahriman.core.auth.mapping import Mapping
from ahriman.models.user import User
from ahriman.models.user_access import UserAccess


async def test_check_credentials(mapping: Mapping, user: User) -> None:
    """
    must return true for valid credentials
    """
    current_password = user.password
    user.password = user.hash_password(mapping.salt)
    mapping._users[user.username] = user
    assert await mapping.check_credentials(user.username, current_password)
    # here password is hashed so it is invalid
    assert not await mapping.check_credentials(user.username, user.password)


async def test_check_credentials_empty(mapping: Mapping) -> None:
    """
    must reject on empty credentials
    """
    assert not await mapping.check_credentials(None, "")
    assert not await mapping.check_credentials("", None)
    assert not await mapping.check_credentials(None, None)


async def test_check_credentials_unknown(mapping: Mapping, user: User) -> None:
    """
    must reject on unknown user
    """
    assert not await mapping.check_credentials(user.username, user.password)


def test_get_user(mapping: Mapping, user: User) -> None:
    """
    must return user from storage by username
    """
    mapping._users[user.username] = user
    assert mapping.get_user(user.username) == user


def test_get_user_normalized(mapping: Mapping, user: User) -> None:
    """
    must return user from storage by username case-insensitive
    """
    mapping._users[user.username] = user
    assert mapping.get_user(user.username.upper()) == user


def test_get_user_unknown(mapping: Mapping, user: User) -> None:
    """
    must return None in case if no user found
    """
    assert mapping.get_user(user.username) is None


async def test_known_username(mapping: Mapping, user: User) -> None:
    """
    must allow only known users
    """
    mapping._users[user.username] = user
    assert await mapping.known_username(user.username)
    assert not await mapping.known_username(None)
    assert not await mapping.known_username(user.password)


async def test_verify_access(mapping: Mapping, user: User) -> None:
    """
    must verify user access
    """
    mapping._users[user.username] = user
    assert await mapping.verify_access(user.username, user.access, None)
    assert not await mapping.verify_access(user.username, UserAccess.Write, None)
