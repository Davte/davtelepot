"""Make a self-consistent bot help section."""

# Project modules
from .bot import Bot
from .messages import default_help_messages
from .utilities import (
    get_cleaned_text, make_inline_keyboard,
    make_lines_of_buttons, make_button,
    recursive_dictionary_update
)


def get_commands_description(bot: Bot, update, user_record):
    """Get a string description of `bot` commands.

    Show only commands available for `update` sender.
    """
    user_role = bot.Role.get_user_role(
        user_record=user_record
    )
    commands = {}
    for command, details in bot.commands.items():
        if 'description' not in details or not details['description']:
            continue
        if 'authorization_level' not in details:
            continue
        command_role = bot.Role.get_role_by_name(details['authorization_level'])
        if command_role.code < user_role.code:
            continue
        if command_role.code not in commands:
            commands[command_role.code] = []
        commands[command_role.code].append(
            "/{command}{authorization_level}: {description}".format(
                command=bot.get_message(
                    messages=details['language_labelled_commands'],
                    default_message=command,
                    user_record=user_record, update=update
                ),
                authorization_level=(
                    f" <i>[{command_role.plural}]</i>"
                    if command_role.code != bot.Role.default_role_code
                    else ""
                ),
                description=bot.get_message(
                    'commands', command, 'description',
                    user_record=user_record, update=update,
                    default_message=(
                        details['description']
                        if type(details['description']) is str
                        else ''
                    )
                )
            )
        )
    return "\n".join(
        [
            command
            for role, commands in sorted(
                commands.items(),
                key=(lambda x: -x[0])
            )
            for command in sorted(
                commands
            )
        ]
    )
    #     [
    #         "/{command}{authorization_level}: {description}".format(
    #             command=command,
    #             authorization_level=(
    #                 ""
    #                 if 1
    #                 else ""
    #             ),
    #             description=bot.get_message(
    #                 'commands', command, 'description',
    #                 user_record=user_record, update=update,
    #                 default_message=(
    #                     details['description']
    #                     if type(details['description']) is str
    #                     else ''
    #                 )
    #             )
    #         )
    #         if 'description' in details and details['description']
    #         and user_role.code <= bot.Role.get_user_role(
    #             user_role_id=details['authorization_level']
    #         ).code
    #     ]
    # )


def _make_button(text=None, callback_data='',
                 prefix='help:///', delimiter='|', data=None):
    return make_button(text=text, callback_data=callback_data,
                       prefix=prefix, delimiter=delimiter, data=data)


def get_back_to_help_menu_keyboard(bot, update, user_record):
    """Return a keyboard to let user come back to help menu."""
    return make_inline_keyboard(
        [
            _make_button(
                text=bot.get_message(
                    'help', 'help_command', 'back_to_help_menu',
                    update=update, user_record=user_record
                ),
                data=['menu']
            )
        ],
        1
    )


def get_help_buttons(bot, update, user_record):
    """Get `bot` help menu inline keyboard.

    Show only buttons available for `update` sender.
    """
    user_role = bot.Role.get_user_role(
        user_record=user_record
    )
    buttons_list = [
        _make_button(
            text=bot.get_message(
                'help_sections', section['name'], 'label',
                update=update, user_record=user_record,
            ),
            data=['section', name]
        )
        for name, section in bot.messages['help_sections'].items()
        if 'authorization_level' in section
           and user_role.code <= bot.Role.get_user_role(
            user_role_id=section['authorization_level']
        ).code
    ]
    return dict(
        inline_keyboard=(
            make_lines_of_buttons(buttons_list, 3)
            + make_lines_of_buttons(
                [
                    _make_button(
                        text=bot.get_message(
                            'help', 'commands_button_label',
                            update=update, user_record=user_record,
                        ),
                        data=['commands']
                    )
                ],
                1
            )
        )
    )


async def _help_command(bot, update, user_record):
    if not bot.authorization_function(update=update,
                                      authorization_level='everybody'):
        return bot.get_message(
            'help', 'help_command', 'access_denied_message',
            update=update, user_record=user_record
        )
    reply_markup = get_help_buttons(bot, update, user_record)
    return dict(
        text=bot.get_message(
            'help', 'help_command', 'text',
            update=update, user_record=user_record,
            bot=bot
        ),
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def _help_button(bot, update, user_record, data):
    result, text, reply_markup = '', '', None
    if data[0] == 'commands':
        text = bot.get_message(
            'help', 'help_command', 'header',
            update=update, user_record=user_record,
            bot=bot,
            commands=get_commands_description(bot, update, user_record)
        )
        reply_markup = get_back_to_help_menu_keyboard(
            bot=bot, update=update, user_record=user_record
        )
    elif data[0] == 'menu':
        text = bot.get_message(
            'help', 'help_command', 'text',
            update=update, user_record=user_record,
            bot=bot
        )
        reply_markup = get_help_buttons(bot, update, user_record)
    elif (
            data[0] == 'section'
            and len(data) > 1
            and data[1] in bot.messages['help_sections']
    ):
        section = bot.messages['help_sections'][data[1]]
        if bot.authorization_function(
                update=update,
                authorization_level=section['authorization_level']
        ):
            text = (
                "<b>{label}</b>\n\n"
                "{description}"
            ).format(
                label=bot.get_message(
                    'help_sections', section['name'], 'label',
                    update=update, user_record=user_record,
                ),
                description=bot.get_message(
                    'help_sections', section['name'], 'description',
                    update=update, user_record=user_record,
                    bot=bot
                ),
            )
        else:
            text = bot.authorization_denied_message
        reply_markup = get_back_to_help_menu_keyboard(
            bot=bot, update=update, user_record=user_record
        )
    if text or reply_markup:
        return dict(
            text=result,
            edit=dict(
                text=text,
                parse_mode='HTML',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        )
    return result


async def _start_command(bot, update, user_record):
    text = get_cleaned_text(update=update, bot=bot, replace=['start'])
    if not text:
        return await _help_command(bot, update, user_record)
    update['text'] = text
    await bot.text_message_handler(
        update=update,
        user_record=None
    )
    return


def init(telegram_bot: Bot, help_messages: dict = None):
    """Assign parsers, commands, buttons and queries to given `bot`."""
    if help_messages is None:
        help_messages = default_help_messages
    else:
        help_messages = recursive_dictionary_update(
            default_help_messages.copy(),
            help_messages.copy()
        )
    telegram_bot.messages['help'] = help_messages

    @telegram_bot.command("/start", authorization_level='everybody')
    async def start_command(bot, update, user_record):
        return await _start_command(bot, update, user_record)

    @telegram_bot.command(command='/help', aliases=['00help'],
                          reply_keyboard_button=help_messages['help_command'][
                              'reply_keyboard_button'],
                          show_in_keyboard=True,
                          description=help_messages['help_command']['description'],
                          authorization_level='everybody')
    async def help_command(bot, update, user_record):
        return await _help_command(bot, update, user_record)

    @telegram_bot.button(prefix='help:///', separator='|',
                         authorization_level='everybody')
    async def help_button(bot, update, user_record, data):
        return await _help_button(bot, update, user_record, data)
