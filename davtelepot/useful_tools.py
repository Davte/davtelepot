"""General purpose functions for Telegram bots."""

# Standard library
import asyncio
import datetime
import json
import logging

from collections import OrderedDict
from typing import List, Union

# Project modules
from .api import TelegramError
from .bot import Bot
from .messages import default_useful_tools_messages
from .utilities import (get_cleaned_text, get_user, make_button,
                        make_inline_keyboard, recursive_dictionary_update, )


def get_calc_buttons() -> OrderedDict:
    buttons = OrderedDict()
    buttons['**'] = dict(
        value='**',
        symbol='**',
        order='A1',
    )
    buttons['//'] = dict(
        value='//',
        symbol='//',
        order='A2',
    )
    buttons['%'] = dict(
        value='%',
        symbol='mod',
        order='A3',
    )
    buttons['info'] = dict(
        value='info',
        symbol='ℹ️',
        order='A4',
    )
    buttons[0] = dict(
        value=0,
        symbol='0',
        order='E1',
    )
    buttons[1] = dict(
        value=1,
        symbol='1',
        order='D1',
    )
    buttons[2] = dict(
        value=2,
        symbol='2',
        order='D2',
    )
    buttons[3] = dict(
        value=3,
        symbol='3',
        order='D3',
    )
    buttons[4] = dict(
        value=4,
        symbol='4',
        order='C1',
    )
    buttons[5] = dict(
        value=5,
        symbol='5',
        order='C2',
    )
    buttons[6] = dict(
        value=6,
        symbol='6',
        order='C3',
    )
    buttons[7] = dict(
        value=7,
        symbol='7',
        order='B1',
    )
    buttons[8] = dict(
        value=8,
        symbol='8',
        order='B2',
    )
    buttons[9] = dict(
        value=9,
        symbol='9',
        order='B3',
    )
    buttons['+'] = dict(
        value='+',
        symbol='+',
        order='B4',
    )
    buttons['-'] = dict(
        value='-',
        symbol='-',
        order='C4',
    )
    buttons['*'] = dict(
        value='*',
        symbol='*',
        order='D4',
    )
    buttons['/'] = dict(
        value='/',
        symbol='/',
        order='E4',
    )
    buttons['.'] = dict(
        value='.',
        symbol='.',
        order='E2',
    )
    buttons['*1000'] = dict(
        value='*1000',
        symbol='000',
        order='E3',
    )
    buttons['\n'] = dict(
        value='\n',
        symbol='✅',
        order='F1',
    )
    buttons['del'] = dict(
        value='del',
        symbol='⬅️',
        order='F2',
    )
    return buttons


calc_buttons = get_calc_buttons()


def get_calculator_keyboard(additional_data: list = None):
    if additional_data is None:
        additional_data = []
    return make_inline_keyboard(
        [
            make_button(
                text=button['symbol'],
                prefix='calc:///',
                delimiter='|',
                data=[*additional_data, button['value']]
            )
            for button in sorted(calc_buttons.values(), key=lambda b: b['order'])
        ],
        4
    )


async def _calculate_button(bot: Bot,
                            update: dict,
                            user_record: OrderedDict,
                            language: str,
                            data: List[Union[int, str]]):
    text, reply_markup = '', None
    if update['from']['id'] not in bot.shared_data['calc']:
        bot.shared_data['calc'][update['from']['id']] = []
        if len(data) < 2:
            record_id = bot.db['calculations'].insert(
                dict(
                    user_id=user_record['id'],
                    created=datetime.datetime.now()
                )
            )
            data = [record_id, *data]
        else:
            record_id = data[0]
        asyncio.ensure_future(
            calculate_session(bot=bot,
                              user_telegram_id=update['from']['id'],
                              language=language,
                              data=data)
        )
        text = bot.get_message(
            'useful_tools', 'calculate_command', 'use_buttons',
            language=language
        )
        reply_markup = get_calculator_keyboard(additional_data=[record_id])
    update['data'] = data
    bot.shared_data['calc'][update['from']['id']].append(update)
    # Edit the update with the button if a new text is specified
    if not text:
        return
    return dict(
        text='',
        edit=dict(
            text=text,
            reply_markup=reply_markup
        )
    )


async def calculate_session(bot: Bot,
                            user_telegram_id: int,
                            language: str,
                            data: List[Union[int, str]]):
    queue = bot.shared_data['calc'][user_telegram_id]
    queue_len = None
    while queue_len != len(queue):
        queue_len = len(queue)
        await asyncio.sleep(2)
    last_entry = max(queue, key=lambda u: u['id'])
    # Remove user queue
    queue = queue.copy()
    del bot.shared_data['calc'][user_telegram_id]

    record = None
    text, reply_markup = '', None

    # It would be nice to do:
    # for update in sorted(queue, key=lambda u: u['id'])
    # Alas, 'id's are not progressive... Telegram's fault!
    for i, update in enumerate(queue):
        if i % 5 == 0:
            await asyncio.sleep(.1)
        data = update['data']
        if len(data) != 2:
            logging.error(f"Something went wrong: invalid data received.\n{data}")
            return
        if not text:
            record = bot.db['calculations'].find_one(
                id=data[0]
            )
            text = record['text'] or ''
            reply_markup = get_calculator_keyboard(additional_data=[record['id']])
        input_value = data[1]
        if input_value == 'del':
            pass
        elif input_value == 'info':
            pass
        elif input_value in calc_buttons:
            text = f"{text} {calc_buttons[input_value]['value']}"
        else:
            pass  # Error!
    if record:
        bot.db['calculations'].update(
            dict(
                id=record['id'],
                modified=datetime.datetime.now(),
                text=text
            ),
            ['id']
        )
    await bot.edit_message_text(
        text=text,
        update=last_entry,
        reply_markup=reply_markup
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
    telegram_bot.shared_data['calc'] = dict()

    if 'calculations' not in telegram_bot.db.tables:
        types = telegram_bot.db.types
        table = telegram_bot.db.create_table(
            table_name='calculations'
        )
        table.create_column(
            'user_id',
            types.integer
        )
        table.create_column(
            'created',
            types.datetime
        )
        table.create_column(
            'modified',
            types.datetime
        )
        table.create_column(
            'text',
            types.string
        )

    @telegram_bot.command(command='/calc',
                          aliases=None,
                          reply_keyboard_button=None,
                          show_in_keyboard=False,
                          **{key: val for key, val
                             in useful_tools_messages['calculate_command'].items()
                             if key in ('description', 'help_section',
                                        'language_labelled_commands')},
                          authorization_level='everybody')
    async def calculate_command(bot, update, language):
        return await _calculate_command(bot=bot,
                                        update=update,
                                        language=language,
                                        command_name='calc')

    @telegram_bot.button(prefix='calc:///',
                         separator='|',
                         authorization_level='everybody')
    async def calculate_button(bot, update, user_record, language, data):
        return await _calculate_button(bot=bot, user_record=user_record,
                                       update=update,
                                       language=language, data=data)

    @telegram_bot.command(command='/info',
                          aliases=None,
                          reply_keyboard_button=None,
                          show_in_keyboard=False,
                          **{key: val for key, val
                             in useful_tools_messages['info_command'].items()
                             if key in ('description', 'help_section',
                                        'language_labelled_commands')},
                          authorization_level='everybody')
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
