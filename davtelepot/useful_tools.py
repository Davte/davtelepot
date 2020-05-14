"""General purpose functions for Telegram bots."""

# Standard library
from collections import OrderedDict

# Project modules
from .bot import Bot
from .messages import default_useful_tools_messages
from .utilities import recursive_dictionary_update


async def _length_command(bot: Bot, update: dict, user_record: OrderedDict):
    if 'reply_to_message' not in update:
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

    @telegram_bot.command(
        command='/length',
        aliases=None,
        reply_keyboard_button=None,
        show_in_keyboard=False,
        **{
            key: val
            for key, val in useful_tools_messages['length_command'].items()
            if key in ('description', 'help_section', 'language_labelled_commands')
        },
        authorization_level='everybody'
    )
    async def length_command(bot, update, user_record):
        return await _length_command(bot=bot, update=update, user_record=user_record)
