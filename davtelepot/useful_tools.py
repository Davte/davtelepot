"""General purpose functions for Telegram bots."""

# Standard library
import json

from collections import OrderedDict

# Project modules
from .api import TelegramError
from .bot import Bot
from .messages import default_useful_tools_messages
from .utilities import get_cleaned_text, recursive_dictionary_update


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


async def _ping_command(bot: Bot, update: dict):
    """Return `pong` only in private chat."""
    chat_id = bot.get_chat_id(update=update)
    if chat_id < 0:
        return
    return "<i>Pong!</i>"


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
