"""Provide authorization levels to bot functions."""

# Standard library modules
from collections import OrderedDict

# Project modules
from .utilities import make_button

DEFAULT_ROLES = OrderedDict()
DEFAULT_ROLES[0] = {
    'name': 'banned',
    'symbol': '🚫',
    'singular': 'banned',
    'plural': 'banned',
    'can_appoint': [],
    'can_be_appointed_by': [1, 2, 3]
}
DEFAULT_ROLES[1] = {
    'name': 'founder',
    'symbol': '👑',
    'singular': 'founder',
    'plural': 'founders',
    'can_appoint': [0, 1, 2, 3, 4, 5, 7, 100],
    'can_be_appointed_by': []
}
DEFAULT_ROLES[2] = {
    'name': 'admin',
    'symbol': '⚜️',
    'singular': 'administrator',
    'plural': 'administrators',
    'can_appoint': [0, 3, 4, 5, 7, 100],
    'can_be_appointed_by': [1]
}
DEFAULT_ROLES[3] = {
    'name': 'moderator',
    'symbol': '🔰',
    'singular': 'moderator',
    'plural': 'moderators',
    'can_appoint': [0, 5, 7],
    'can_be_appointed_by': [1, 2]
}
DEFAULT_ROLES[5] = {
    'name': 'user',
    'symbol': '🎫',
    'singular': 'registered user',
    'plural': 'registered users',
    'can_appoint': [],
    'can_be_appointed_by': [1, 2, 3]
}
DEFAULT_ROLES[100] = {
    'name': 'everybody',
    'symbol': '👤',
    'singular': 'common user',
    'plural': 'common users',
    'can_appoint': [],
    'can_be_appointed_by': [1, 2, 3]
}


class Role():
    """Authorization level for users of a bot."""

    roles = OrderedDict()

    def __init__(self, code, name, symbol, singular, plural,
                 can_appoint, can_be_appointed_by):
        """Instantiate Role object.

        code : int
            The higher the code, the less privileges are connected to that
                role.
            Use 0 for banned users.
        name : str
            Short name for role.
        symbol : str
            Emoji used to represent role.
        singular : str
            Singular full name of role.
        plural : str
            Plural full name of role.
        can_appoint : lsit of int
            List of role codes that this role can appoint.
        can_be_appointed_by : list of int
            List of role codes this role can be appointed by.
        """
        self._code = code
        self._name = name
        self._symbol = symbol
        self._singular = singular
        self._plural = plural
        self._can_appoint = can_appoint
        self._can_be_appointed_by = can_be_appointed_by
        self.__class__.roles[self.code] = self

    @property
    def code(self):
        """Return code."""
        return self._code

    @property
    def name(self):
        """Return name."""
        return self._name

    @property
    def symbol(self):
        """Return symbol."""
        return self._symbol

    @property
    def singular(self):
        """Return singular."""
        return self._singular

    @property
    def plural(self):
        """Return plural."""
        return self._plural

    @property
    def can_appoint(self):
        """Return can_appoint."""
        return self._can_appoint

    @property
    def can_be_appointed_by(self):
        """Return roles whom this role can be appointed by."""
        return self._can_be_appointed_by

    @classmethod
    def get_by_role_id(cls, role_id=100):
        """Give a `role_id`, return the corresponding `Role` instance."""
        for code, role in cls.roles.items():
            if code == role_id:
                return role
        raise IndexError(f"Unknown role id: {role_id}")

    @classmethod
    def get_user_role(cls, user_record=None, role_id=None):
        """Given a `user_record`, return its `Role`.

        `role_id` may be passed as keyword argument or as user_record.
        """
        if isinstance(user_record, dict) and 'privileges' in user_record:
            user_role_id = user_record['privileges']
        elif type(user_record) is int:
            user_role_id = user_record
        if type(user_role_id) is not int:
            user_role_id = 100
        return cls.get_by_role_id(role_id=role_id)

    @classmethod
    def get_user_role_panel(cls, user_record):
        """Get text and buttons for user role panel."""
        user_role = cls.get_user_role(user_record)
        text = (
            """👤 <a href="tg://user?id={u[telegram_id]}">{u[username]}</a>\n"""
            f"🔑 <i>{user_role.singular.capitalize()}</i> {user_role.symbol}"
        ).format(
            u=user_record,
        )
        buttons = [
            make_button(
                f"{role.symbol} {role.singular.capitalize()}",
                f"auth:///set|{user_record['id']}_{code}"
            )
            for code, role in cls.roles.items()
        ]
        return text, buttons

    def __eq__(self, other):
        """Return True if self is equal to other."""
        return self.code == other.code

    def __gt__(self, other):
        """Return True if self can appoint other."""
        return (
            self.code < other.code
            and self.code in other.can_be_appointed_by
        )

    def __ge__(self, other):
        """Return True if self >= other."""
        return self.__gt__(other) or self.__eq__(other)

    def __lt__(self, other):
        """Return True if self can not appoint other."""
        return not self.__ge__(other)

    def __le__(self, other):
        """Return True if self is superior or equal to other."""
        return not self.__gt__(other)

    def __ne__(self, other):
        """Return True if self is not equal to other."""
        return not self.__eq__(other)

    def __str__(self):
        """Return human-readable description of role."""
        return f"<Role object: {self.symbol} {self.singular.capitalize()}>"


def init(bot, roles=None):
    """Set bot roles and assign role-related commands.

    Pass an OrderedDict of `roles` to get them set.
    """
    class _Role(Role):
        roles = OrderedDict()

    if roles is None:
        roles = DEFAULT_ROLES
    # Cast roles to OrderedDict
    if isinstance(roles, list):
        roles = OrderedDict(
            (i, element)
            for i, element in enumerate(list)
        )
    if not isinstance(roles, OrderedDict):
        raise TypeError("`roles` shall be a OrderedDict!")
    for id, role in roles.items():
        if 'code' not in role:
            role['code'] = id
        Role(**role)
