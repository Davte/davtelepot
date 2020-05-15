"""General purpose functions for Telegram bots."""

# Standard library
import datetime
import json

from collections import OrderedDict

# Project modules
from .api import TelegramError
from .bot import Bot
from .messages import default_useful_tools_messages
from .utilities import (get_cleaned_text, get_user, make_button,
                        make_inline_keyboard, recursive_dictionary_update, )


calc_buttons = OrderedDict()
calc_buttons[0] = dict(
    value=0,
    symbol='0️⃣',
    order=13
)
calc_buttons[1] = dict(
    value=1,
    symbol='1️⃣',
    order=9
)
calc_buttons[2] = dict(
    value=2,
    symbol='2️⃣',
    order=10
)
calc_buttons[3] = dict(
    value=3,
    symbol='3️⃣',
    order=11
)
calc_buttons[4] = dict(
    value=4,
    symbol='4️⃣',
    order=5
)
calc_buttons[5] = dict(
    value=5,
    symbol='5️⃣',
    order=6
)
calc_buttons[6] = dict(
    value=6,
    symbol='6️⃣',
    order=7
)
calc_buttons[7] = dict(
    value=7,
    symbol='7️⃣',
    order=1
)
calc_buttons[8] = dict(
    value=8,
    symbol='8️⃣',
    order=2
)
calc_buttons[9] = dict(
    value=9,
    symbol='9️⃣',
    order=3
)
calc_buttons['plus'] = dict(
    value='+',
    symbol='➕️',
    order=4
)
calc_buttons['minus'] = dict(
    value='-',
    symbol='➖',
    order=8
)
calc_buttons['times'] = dict(
    value='*',
    symbol='✖️',
    order=12
)
calc_buttons['divided'] = dict(
    value='/',
    symbol='➗',
    order=16
)
calc_buttons['point'] = dict(
    value='.',
    symbol='.',
    order=14
)
calc_buttons['enter'] = dict(
    value='\n',
    symbol='↩',
    order=15
)


def get_calculator_keyboard():
    return make_inline_keyboard(
        [
            make_button(
                text=button['symbol'],
                prefix='calc:///',
                delimiter='|',
                data=[button['value']]
            )
            for button in sorted(calc_buttons.values(), key=lambda b: b['order'])
        ],
        4
    )


async def _calculate_command(bot: Bot,
                             update: dict,
                             language: str,
                             command_name: str = 'calc'):
    reply_markup = None
    if 'reply_to_message' in update:
        update = update['reply_to_message']
    command_aliases = [command_name]
    if command_name in bot.commands:
        command_aliases += list(
            bot.commands[command_name]['language_labelled_commands'].values()
        ) + bot.commands[command_name]['aliases']
    text = get_cleaned_text(bot=bot,
                            update=update,
                            replace=command_aliases)
    if not text:
        text = bot.get_message(
            'useful_tools', 'calculate_command', 'instructions',
            language=language
        )
        reply_markup = get_calculator_keyboard()
    else:
        text = 'pass'
    await bot.send_message(text=text,
                           update=update,
                           reply_markup=reply_markup)


async def _length_command(bot: Bot, update: dict, user_record: OrderedDict):
    message_text = get_cleaned_text(
        update=update,
        bot=bot,
        replace=[
            alias
            for alias in bot.messages[
                'useful_tools'
            ][
                'length_command'
            ][
                'language_labelled_commands'
            ].values()
        ]
    )
    if message_text:
        text = bot.get_message(
            'useful_tools', 'length_command', 'result',
            user_record=user_record, update=update,
            n=len(message_text)
        )
    elif 'reply_to_message' not in update:
        text = bot.get_message(
            'useful_tools', 'length_command', 'instructions',
            user_record=user_record, update=update
        )
    else:
        text = bot.get_message(
            'useful_tools', 'length_command', 'result',
            user_record=user_record, update=update,
            n=len(update['reply_to_message']['text'])
        )
        update = update['reply_to_message']
    reply_to_message_id = update['message_id']
    return dict(
        chat_id=update['chat']['id'],
        text=text,
        parse_mode='HTML',
        reply_to_message_id=reply_to_message_id
    )


async def _message_info_command(bot: Bot, update: dict, language: str):
    """Provide information about selected update.

    Selected update: the message `update` is sent in reply to. If `update` is
        not a reply to anything, it gets selected.
    The update containing the command, if sent in reply, is deleted.
    """
    if 'reply_to_message' in update:
        selected_update = update['reply_to_message']
    else:
        selected_update = update
    await bot.send_message(
        text=bot.get_message(
            'useful_tools', 'info_command', 'result',
            language=language,
            info=json.dumps(selected_update, indent=2)
        ),
        update=update,
        reply_to_message_id=selected_update['message_id'],
    )
    if selected_update != update:
        try:
            await bot.delete_message(update=update)
        except TelegramError:
            pass


async def _ping_command(bot: Bot, update: dict):
    """Return `pong` only in private chat."""
    chat_id = bot.get_chat_id(update=update)
    if chat_id < 0:
        return
    return "<i>Pong!</i>"


async def _when_command(bot: Bot, update: dict, language: str):
    reply_markup = None
    text = ''
    if 'reply_to_message' not in update:
        return bot.get_message(
            'useful_tools', 'when_command', 'instructions',
            language=language
        )
    update = update['reply_to_message']
    date = (
        datetime.datetime.fromtimestamp(update['date'])
        if 'date' in update
        else None
    )
    text += bot.get_message(
        'useful_tools', 'when_command', 'who_when',
        language=language,
        who=get_user(update['from']),
        when=date
    )
    if 'forward_date' in update:
        original_datetime = (
            datetime.datetime.fromtimestamp(update['forward_date'])
            if 'forward_from' in update
            else None
        )
        text += "\n\n" + bot.get_message(
            'useful_tools', 'when_command', 'forwarded_message',
            language=language,
            who=get_user(update['forward_from']),
            when=original_datetime
        ) + "\n"
        text += bot.get_message(
            'useful_tools', 'when_command', 'who_when',
            language=language,
            who=get_user(update['forward_from']),
            when=original_datetime
        )
    await bot.send_message(
        text=text,
        reply_markup=reply_markup,
        reply_to_message_id=update['message_id'],
        disable_notification=True,
        chat_id=update['chat']['id']
    )


def init(telegram_bot: Bot, useful_tools_messages=None):
    """Define commands for `telegram_bot`.

    You may provide customized `useful_tools_messages` that will overwrite
        `default_useful_tools_messages`. Missing entries will be kept default.
    """
    if useful_tools_messages is None:
        useful_tools_messages = dict()
    useful_tools_messages = recursive_dictionary_update(
        default_useful_tools_messages,
        useful_tools_messages
    )
    telegram_bot.messages['useful_tools'] = useful_tools_messages

    @telegram_bot.command(command='/calc',
                          aliases=None,
                          reply_keyboard_button=None,
                          show_in_keyboard=False,
                          **{key: val for key, val
                             in useful_tools_messages['calculate_command'].items()
                             if key in ('description', 'help_section',
                                        'language_labelled_commands')},
                          authorization_level='moderator')
    async def calculate_command(bot, update, language):
        return await _calculate_command(bot=bot,
                                        update=update,
                                        language=language,
                                        command_name='calc')

    @telegram_bot.command(command='/info',
                          aliases=None,
                          reply_keyboard_button=None,
                          show_in_keyboard=False,
                          **{key: val for key, val
                             in useful_tools_messages['info_command'].items()
                             if key in ('description', 'help_section',
                                        'language_labelled_commands')},
                          authorization_level='moderator')
    async def message_info_command(bot, update, language):
        return await _message_info_command(bot=bot,
                                           update=update,
                                           language=language)

    @telegram_bot.command(command='/length',
                          aliases=None,
                          reply_keyboard_button=None,
                          show_in_keyboard=False,
                          **{key: val for key, val
                             in useful_tools_messages['length_command'].items()
                             if key in ('description', 'help_section',
                                        'language_labelled_commands')},
                          authorization_level='everybody')
    async def length_command(bot, update, user_record):
        return await _length_command(bot=bot, update=update, user_record=user_record)

    @telegram_bot.command(command='/ping',
                          aliases=None,
                          reply_keyboard_button=None,
                          show_in_keyboard=False,
                          **{key: val for key, val
                             in useful_tools_messages['ping_command'].items()
                             if key in ('description', 'help_section',
                                        'language_labelled_commands')},
                          authorization_level='everybody')
    async def ping_command(bot, update):
        return await _ping_command(bot=bot, update=update)

    @telegram_bot.command(command='/when',
                          aliases=None,
                          reply_keyboard_button=None,
                          show_in_keyboard=False,
                          **{key: val for key, val
                             in useful_tools_messages['when_command'].items()
                             if key in ('description', 'help_section',
                                        'language_labelled_commands')},
                          authorization_level='everybody')
    async def when_command(bot, update, language):
        return await _when_command(bot=bot, update=update, language=language)
