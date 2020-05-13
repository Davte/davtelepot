"""Provide authorization levels to bot functions."""

# Standard library modules
from collections import OrderedDict
from typing import Callable, List, Union

# Project modules
from .bot import Bot
from .messages import default_authorization_messages
from .utilities import (
    Confirmator, get_cleaned_text, get_user, make_button, make_inline_keyboard
)

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


class Role:
    """Authorization level for users of a bot."""

    roles = OrderedDict()
    default_role_code = 100

    def __init__(self, code: int, name: str, symbol: str,
                 singular: str, plural: str,
                 can_appoint: List[int], can_be_appointed_by: List[int]):
        """Instantiate Role object.

        code : int
            The higher the code, the less privileges are connected to that
                role. Use 0 for banned users.
        name : str
            Short name for role.
        symbol : str
            Emoji used to represent role.
        singular : str
            Singular full name of role.
        plural : str
            Plural full name of role.
        can_appoint : list of int
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
    def code(self) -> int:
        """Return code."""
        return self._code

    @property
    def name(self) -> str:
        """Return name."""
        return self._name

    @property
    def symbol(self) -> str:
        """Return symbol."""
        return self._symbol

    @property
    def singular(self) -> str:
        """Return singular."""
        return self._singular

    @property
    def plural(self) -> str:
        """Return plural."""
        return self._plural

    @property
    def can_appoint(self) -> List[int]:
        """Return can_appoint."""
        return self._can_appoint

    @property
    def can_be_appointed_by(self) -> List[int]:
        """Return roles whom this role can be appointed by."""
        return self._can_be_appointed_by

    @classmethod
    def get_by_role_id(cls, role_id=100) -> 'Role':
        """Given a `role_id`, return the corresponding `Role` instance."""
        for code, role in cls.roles.items():
            if code == role_id:
                return role
        raise IndexError(f"Unknown role id: {role_id}")

    @classmethod
    def get_role_by_name(cls, name='everybody') -> 'Role':
        """Given a `name`, return the corresponding `Role` instance."""
        for role in cls.roles.values():
            if role.name == name:
                return role
        raise IndexError(f"Unknown role name: {name}")

    @classmethod
    def get_user_role(cls,
                      user_record: OrderedDict = None,
                      user_role_id: int = None) -> 'Role':
        """Given a `user_record`, return its `Role`.

        `role_id` may be passed as keyword argument or as user_record.
        """
        if user_role_id is None:
            if isinstance(user_record, dict) and 'privileges' in user_record:
                user_role_id = user_record['privileges']
            elif type(user_record) is int:
                user_role_id = user_record
        if type(user_role_id) is not int:
            for code, role in cls.roles.items():
                if role.name == user_role_id:
                    user_role_id = code
                    break
            else:
                user_role_id = cls.default_role_code
        return cls.get_by_role_id(role_id=user_role_id)

    @classmethod
    def set_default_role_code(cls, role: int) -> None:
        """Set class default role code.

        It will be returned if a specific role code cannot be evaluated.
        """
        cls.default_role_code = role

    @classmethod
    def get_user_role_text(cls,
                           user_record: OrderedDict,
                           user_role: 'Role' = None) -> str:
        """
        Get a string to describe the role of a user.

        @param user_record: record of table `users` about the user; it must
            contain at least a [username | last_name | first_name] and a
            telegram identifier.
        @param user_role: Role instance about user permissions.
        @return: String to describe the role of a user, like this:
            ```
            👤 LinkedUsername
            🔑 Admin ⚜️
            ```
        """
        if user_role is None:
            user_role = cls.get_user_role(user_record=user_record)
        return (
            f"""👤 {get_user(record=user_record)}\n"""
            f"🔑 <i>{user_role.singular.capitalize()}</i> {user_role.symbol}"
        )

    @classmethod
    def get_user_role_buttons(cls,
                              user_record: OrderedDict,
                              admin_record: OrderedDict,
                              user_role: 'Role' = None,
                              admin_role: 'Role' = None) -> List[dict]:
        """ Return buttons to edit user permissions.
        @param user_record: record of table `users` about the user; it must
            contain at least a [username | last_name | first_name] and a
            telegram identifier.
        @param admin_record: record of table `users` about the admin; it must
            contain at least a [username | last_name | first_name] and a
            telegram identifier.
        @param user_role: Role instance about user permissions.
        @param admin_role: Role instance about admin permissions.
        @return: list of `InlineKeyboardButton`s.
        """
        if admin_role is None:
            admin_role = cls.get_user_role(user_record=admin_record)
        if user_role is None:
            user_role = cls.get_user_role(user_record=user_record)
        return [
            make_button(
                f"{role.symbol} {role.singular.capitalize()}",
                prefix='auth:///',
                data=['set', user_record['id'], code]
            )
            for code, role in cls.roles.items()
            if (admin_role > user_role
                and code in admin_role.can_appoint
                and code != user_role.code)
        ]

    @classmethod
    def get_user_role_text_and_buttons(cls,
                                       user_record: OrderedDict,
                                       admin_record: OrderedDict):
        """Get text and buttons for user role panel."""
        admin_role = cls.get_user_role(user_record=admin_record)
        user_role = cls.get_user_role(user_record=user_record)
        text = cls.get_user_role_text(user_record=user_record,
                                      user_role=user_role)
        buttons = cls.get_user_role_buttons(user_record=user_record,
                                            user_role=user_role,
                                            admin_record=admin_record,
                                            admin_role=admin_role)
        return text, buttons

    def __eq__(self, other: 'Role'):
        """Return True if self is equal to other."""
        return self.code == other.code

    def __gt__(self, other: 'Role'):
        """Return True if self can appoint other."""
        return (
                (
                        self.code < other.code
                        or other.code == 0
                )
                and self.code in other.can_be_appointed_by
        )

    def __ge__(self, other: 'Role'):
        """Return True if self >= other."""
        return self.__gt__(other) or self.__eq__(other)

    def __lt__(self, other: 'Role'):
        """Return True if self can not appoint other."""
        return not self.__ge__(other)

    def __le__(self, other: 'Role'):
        """Return True if self is superior or equal to other."""
        return not self.__gt__(other)

    def __ne__(self, other: 'Role'):
        """Return True if self is not equal to other."""
        return not self.__eq__(other)

    def __str__(self):
        """Return human-readable description of role."""
        return f"<Role object: {self.symbol} {self.singular.capitalize()}>"


def get_authorization_function(bot: Bot):
    """Take a `bot` and return its authorization_function."""

    def is_authorized(update, user_record=None, authorization_level=2):
        """Return True if user role is at least at `authorization_level`."""
        if user_record is None:
            if (
                    isinstance(update, dict)
                    and 'from' in update
                    and isinstance(update['from'], dict)
                    and 'id' in update['from']
            ):
                user_record = bot.db['users'].find_one(
                    telegram_id=update['from']['id']
                )
        user_role = bot.Role.get_user_role(user_record=user_record)
        if user_role.code == 0:
            return False
        needed_role = bot.Role.get_user_role(user_role_id=authorization_level)
        if needed_role.code < user_role.code:
            return False
        return True

    return is_authorized


async def _authorization_command(bot: Bot,
                                 update: dict,
                                 user_record: OrderedDict,
                                 mode: str = 'auth'):
    db = bot.db
    text = get_cleaned_text(bot=bot, update=update, replace=[mode])
    reply_markup = None
    admin_record = user_record.copy()
    user_record = None
    admin_role = bot.Role.get_user_role(user_record=admin_record)
    result = bot.get_message(
        'authorization', 'auth_command', 'unhandled_case',
        update=update, user_record=admin_record
    )
    if not text:  # No text provided: command must be used in reply
        if 'reply_to_message' not in update:  # No text and not in reply
            result = bot.get_message(
                'authorization', 'auth_command', 'instructions',
                update=update, user_record=admin_record,
                command=mode
            )
        else:  # No text, command used in reply to another message
            update = update['reply_to_message']
            # Forwarded message: get both the user who forwarded and the original author
            if ('forward_from' in update
                    and update['from']['id'] != update['forward_from']['id']):
                user_record = list(
                    db['users'].find(
                        telegram_id=[update['from']['id'],
                                     update['forward_from']['id']]
                    )
                )
            else:  # Otherwise: get the author of the message
                user_record = db['users'].find_one(
                    telegram_id=update['from']['id']
                )
    else:  # Get users matching the input text
        user_record = list(
            db.query(
                "SELECT * "
                "FROM users "
                "WHERE COALESCE("
                "   first_name || last_name || username,"
                "   last_name || username,"
                "   first_name || username,"
                "   username,"
                "   first_name || last_name,"
                "   last_name,"
                "   first_name"
                f") LIKE '%{text}%'"
            )
        )
        if len(user_record) == 1:
            user_record = user_record[0]
    if user_record is None:  # If query was not provided and user cannot be found
        result = bot.get_message(
            'authorization', 'auth_command', 'unknown_user',
            update=update, user_record=admin_record
        )
    elif type(user_record) is list and len(user_record) > 1:  # If many users match
        result = bot.get_message(
            'authorization', 'auth_command', 'choose_user',
            update=update, user_record=admin_record,
            n=len(user_record)
        )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    f"👤 {get_user(user, link_profile=False)}",
                    prefix='auth:///',
                    data=['show', user['id']]
                )
                for user in user_record[:30]
            ],
            3
        )
    elif type(user_record) is list and len(user_record) == 0:  # If query was provided but no user matches
        result = bot.get_message(
            'authorization', 'auth_command', 'no_match',
            update=update, user_record=admin_record,
        )
    elif isinstance(user_record, dict):  # If 1 user matches
        # Ban user if admin can do it
        user_role = bot.Role.get_user_role(user_record=user_record)
        if mode == 'ban' and admin_role > user_role:
            user_record['privileges'] = 0
            db['users'].update(
                user_record,
                ['id']
            )
        # Show user panel (text and buttons) to edit user permissions
        result, buttons = bot.Role.get_user_role_text_and_buttons(
            user_record=user_record,
            admin_record=admin_record
        )
        reply_markup = make_inline_keyboard(buttons, 1)
    return dict(
        text=result,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def _authorization_button(bot: Bot,
                                update: dict,
                                user_record: OrderedDict,
                                data: Union[str, List[Union[int, str]]]):
    if len(data) == 0:
        data = ['']
    command, *arguments = data
    user_id = user_record['telegram_id']
    if len(arguments) > 0:
        other_user_id = arguments[0]
    else:
        other_user_id = None
    result, text, reply_markup = '', '', None
    db = bot.db
    if command in ['show']:
        other_user_record = db['users'].find_one(id=other_user_id)
        text, buttons = bot.Role.get_user_role_text_and_buttons(
            user_record=other_user_record,
            admin_record=user_record
        )
        reply_markup = make_inline_keyboard(buttons, 1)
    elif command in ['set'] and len(arguments) > 1:
        other_user_id, new_privileges, *_ = arguments
        if not Confirmator.get(
                key=f'{user_id}_set_{other_user_id}',
                confirm_timedelta=5
        ).confirm:
            return bot.get_message(
                'authorization', 'auth_button', 'confirm',
                update=update, user_record=user_record,
            )
        other_user_record = db['users'].find_one(id=other_user_id)
        user_role = bot.Role.get_user_role(user_record=user_record)
        other_user_role = bot.Role.get_user_role(user_record=other_user_record)
        if other_user_role.code == new_privileges:
            return bot.get_message(
                'authorization', 'auth_button', 'no_change',
                update=update, user_record=user_record
            )
        if not user_role > other_user_role:
            text = bot.get_message(
                'authorization', 'auth_button', 'permission_denied', 'user',
                update=update, user_record=user_record
            )
            reply_markup = make_inline_keyboard(
                [
                    make_button(
                        bot.get_message(
                            'authorization', 'auth_button', 'back_to_user',
                            update=update, user_record=user_record
                        ),
                        prefix='auth:///',
                        data=['show', other_user_id]
                    )
                ],
                1
            )
        elif new_privileges not in user_role.can_appoint:
            text = bot.get_message(
                'authorization', 'auth_button', 'permission_denied', 'role',
                update=update, user_record=user_record
            )
            reply_markup = make_inline_keyboard(
                [
                    make_button(
                        bot.get_message(
                            'authorization', 'auth_button', 'back_to_user',
                            update=update, user_record=user_record
                        ),
                        prefix='auth:///',
                        data=['show', other_user_id]
                    )
                ],
                1
            )
        else:
            db['users'].update(
                dict(
                    id=other_user_id,
                    privileges=new_privileges
                ),
                ['id']
            )
            other_user_record = db['users'].find_one(id=other_user_id)
            result = bot.get_message(
                'authorization', 'auth_button', 'appointed',
                update=update, user_record=user_record
            )
            text, buttons = bot.Role.get_user_role_text_and_buttons(
                user_record=other_user_record,
                admin_record=user_record
            )
            reply_markup = make_inline_keyboard(buttons, 1)
    if text:
        return dict(
            text=result,
            edit=dict(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        )
    return result


def default_get_administrators_function(bot: Bot):
    return list(
        bot.db['users'].find(privileges=[1, 2])
    )


def init(telegram_bot: Bot,
         roles: Union[list, OrderedDict] = None,
         authorization_messages=None,
         get_administrators_function: Callable[[object],
                                               list] = None):
    """Set bot roles and assign role-related commands.

    Pass an OrderedDict of `roles` to get them set.
    """

    class _Role(Role):
        roles = OrderedDict()

    telegram_bot.set_role_class(_Role)
    if roles is None:
        roles = DEFAULT_ROLES
    # Cast roles to OrderedDict
    if isinstance(roles, list):
        roles = OrderedDict(
            (i, element)
            for i, element in enumerate(roles)
        )
    if not isinstance(roles, OrderedDict):
        raise TypeError("`roles` shall be a OrderedDict!")
    for code, role in roles.items():
        if 'code' not in role:
            role['code'] = code
        telegram_bot.Role(**role)

    telegram_bot.set_authorization_function(
        get_authorization_function(telegram_bot)
    )
    get_administrators_function = (get_administrators_function
                                   or default_get_administrators_function)
    telegram_bot.set_get_administrator_function(get_administrators_function)
    authorization_messages = (authorization_messages
                              or default_authorization_messages)
    telegram_bot.messages['authorization'] = authorization_messages

    @telegram_bot.command(command='/auth', aliases=[], show_in_keyboard=False,
                          description=(
                                  authorization_messages['auth_command']['description']
                          ),
                          authorization_level='moderator')
    async def authorization_command(bot, update, user_record):
        return await _authorization_command(bot, update, user_record)

    @telegram_bot.button('auth:///',
                         description=authorization_messages['auth_button']['description'],
                         separator='|',
                         authorization_level='moderator')
    async def authorization_button(bot, update, user_record, data):
        return await _authorization_button(bot, update, user_record, data)

    @telegram_bot.command('/ban', aliases=[], show_in_keyboard=False,
                          description=authorization_messages['ban_command']['description'],
                          authorization_level='moderator')
    async def ban_command(bot, update, user_record):
        return await _authorization_command(bot, update, user_record, mode='ban')
