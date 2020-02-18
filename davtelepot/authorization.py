"""Provide authorization levels to bot functions."""

# Standard library modules
from collections import OrderedDict

# Project modules
from .bot import Bot
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
        """Given a `role_id`, return the corresponding `Role` instance."""
        for code, role in cls.roles.items():
            if code == role_id:
                return role
        raise IndexError(f"Unknown role id: {role_id}")

    @classmethod
    def get_role_by_name(cls, name='everybody'):
        """Given a `name`, return the corresponding `Role` instance."""
        for role in cls.roles.values():
            if role.name == name:
                return role
        raise IndexError(f"Unknown role name: {name}")

    @classmethod
    def get_user_role(cls, user_record=None, user_role_id=None):
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
    def set_default_role_code(cls, role):
        """Set class default role code.

        It will be returned if a specific role code cannot be evaluated.
        """
        cls.default_role_code = role

    @classmethod
    def get_user_role_panel(cls, user_record):
        """Get text and buttons for user role panel."""
        user_role = cls.get_user_role(user_record=user_record)
        text = (
            """👤 <a href="tg://user?id={u[telegram_id]}">{u[username]}</a>\n"""
            f"🔑 <i>{user_role.singular.capitalize()}</i> {user_role.symbol}"
        ).format(
            u=user_record,
        )
        buttons = [
            make_button(
                f"{role.symbol} {role.singular.capitalize()}",
                prefix='auth:///',
                data=['set', user_record['id'], code]
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
                (
                        self.code < other.code
                        or other.code == 0
                )
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


def get_authorization_function(bot):
    """Take a `bot` and return its authorization_function."""

    def is_authorized(update, user_record=None, authorization_level=2):
        """Return True if user role is at least at `authorization_level`."""
        user_role = bot.Role.get_user_role(user_record=user_record)
        if user_role.code == 0:
            return False
        needed_role = bot.Role.get_user_role(user_role_id=authorization_level)
        if needed_role.code < user_role.code:
            return False
        return True

    return is_authorized


deafult_authorization_messages = {
    'auth_command': {
        'description': {
            'en': "Edit user permissions. To select a user, reply to "
                  "a message of theirs or write their username",
            'it': "Cambia il grado di autorizzazione di un utente "
                  "(in risposta o scrivendone lo username)"
        },
        'unhandled_case': {
            'en': "<code>Unhandled case :/</code>",
            'it': "<code>Caso non previsto :/</code>"
        },
        'instructions': {
            'en': "Reply with this command to a user or write "
                  "<code>/auth username</code> to edit their permissions.",
            'it': "Usa questo comando in risposta a un utente "
                  "oppure scrivi <code>/auth username</code> per "
                  "cambiarne il grado di autorizzazione."
        },
        'unknown_user': {
            'en': "Unknown user.",
            'it': "Utente sconosciuto."
        },
        'choose_user': {
            'en': "{n} users match your query. Please select one.",
            'it': "Ho trovato {n} utenti che soddisfano questi criteri.\n"
                  "Per procedere selezionane uno."
        },
        'no_match': {
            'en': "No user matches your query. Please try again.",
            'it': "Non ho trovato utenti che soddisfino questi criteri.\n"
                  "Prova di nuovo."
        }
    },
    'ban_command': {
        'description': {
            'en': "Reply to a user with /ban to ban them",
            'it': "Banna l'utente (da usare in risposta)"
        }
    },
    'auth_button': {
        'description': {
            'en': "Edit user permissions",
            'it': "Cambia il grado di autorizzazione di un utente"
        },
        'confirm': {
            'en': "Are you sure?",
            'it': "Sicuro sicuro?"
        },
        'back_to_user': {
            'en': "Back to user",
            'it': "Torna all'utente"
        },
        'permission_denied': {
            'user': {
                'en': "You cannot appoint this user!",
                'it': "Non hai l'autorità di modificare i permessi di questo "
                      "utente!"
            },
            'role': {
                'en': "You're not allowed to appoint someone to this role!",
                'it': "Non hai l'autorità di conferire questo permesso!"
            }
        },
        'no_change': {
            'en': "No change suggested!",
            'it': "È già così!"
        },
        'appointed': {
            'en': "Permission granted",
            'it': "Permesso conferito"
        }
    },
}


async def _authorization_command(bot, update, user_record):
    text = get_cleaned_text(bot=bot, update=update, replace=['auth'])
    reply_markup = None
    result = bot.get_message(
        'authorization', 'auth_command', 'unhandled_case',
        update=update, user_record=user_record
    )
    if not text:
        if 'reply_to_message' not in update:
            return bot.get_message(
                'authorization', 'auth_command', 'instructions',
                update=update, user_record=user_record
            )
        else:
            with bot.db as db:
                user_record = db['users'].find_one(
                    telegram_id=update['reply_to_message']['from']['id']
                )
    else:
        with bot.db as db:
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
    if user_record is None:
        result = bot.get_message(
            'authorization', 'auth_command', 'unknown_user',
            update=update, user_record=user_record
        )
    elif type(user_record) is list and len(user_record) > 1:
        result = bot.get_message(
            'authorization', 'auth_command', 'choose_user',
            update=update, user_record=user_record,
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
    elif type(user_record) is list and len(user_record) == 0:
        result = bot.get_message(
            'authorization', 'auth_command', 'no_match',
            update=update, user_record=user_record,
        )
    else:
        if type(user_record) is list:
            user_record = user_record[0]
        result, buttons = bot.Role.get_user_role_panel(user_record)
        reply_markup = make_inline_keyboard(buttons, 1)
    return dict(
        text=result,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def _authorization_button(bot, update, user_record, data):
    if len(data) == 0:
        data = ['']
    command, *arguments = data
    user_id = user_record['telegram_id']
    if len(arguments) > 0:
        other_user_id = arguments[0]
    else:
        other_user_id = None
    result, text, reply_markup = '', '', None
    if command in ['show']:
        with bot.db as db:
            other_user_record = db['users'].find_one(id=other_user_id)
        text, buttons = bot.Role.get_user_role_panel(other_user_record)
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
        with bot.db as db:
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
            with bot.db as db:
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
            text, buttons = bot.Role.get_user_role_panel(other_user_record)
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


async def _ban_command(bot, update, user_record):
    # TODO define this function!
    return


def init(telegram_bot: Bot, roles=None, authorization_messages=None):
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
    if authorization_messages is None:
        authorization_messages = deafult_authorization_messages
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
                          authorization_level='admin')
    async def ban_command(bot, update, user_record):
        return await _ban_command(bot, update, user_record)
