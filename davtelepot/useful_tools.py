"""General purpose functions for Telegram bots."""

# Standard library
import ast
import asyncio
import datetime
import json
import logging
import operator
import re

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
        value=' // ',
        symbol='//',
        order='A2',
    )
    buttons['%'] = dict(
        value=' % ',
        symbol='mod',
        order='A3',
    )
    buttons['_'] = dict(
        value='_',
        symbol='MR',
        order='B5',
    )
    buttons[0] = dict(
        value='0',
        symbol='0',
        order='E1',
    )
    buttons[1] = dict(
        value='1',
        symbol='1',
        order='D1',
    )
    buttons[2] = dict(
        value='2',
        symbol='2',
        order='D2',
    )
    buttons[3] = dict(
        value='3',
        symbol='3',
        order='D3',
    )
    buttons[4] = dict(
        value='4',
        symbol='4',
        order='C1',
    )
    buttons[5] = dict(
        value='5',
        symbol='5',
        order='C2',
    )
    buttons[6] = dict(
        value='6',
        symbol='6',
        order='C3',
    )
    buttons[7] = dict(
        value='7',
        symbol='7',
        order='B1',
    )
    buttons[8] = dict(
        value='8',
        symbol='8',
        order='B2',
    )
    buttons[9] = dict(
        value='9',
        symbol='9',
        order='B3',
    )
    buttons['+'] = dict(
        value=' + ',
        symbol='+',
        order='B4',
    )
    buttons['-'] = dict(
        value=' - ',
        symbol='-',
        order='C4',
    )
    buttons['*'] = dict(
        value=' * ',
        symbol='*',
        order='D4',
    )
    buttons['/'] = dict(
        value=' / ',
        symbol='/',
        order='E4',
    )
    buttons['.'] = dict(
        value='.',
        symbol='.',
        order='E2',
    )
    buttons['thousands'] = dict(
        value='000',
        symbol='000',
        order='E3',
    )
    buttons['end'] = dict(
        value='\n',
        symbol='✅',
        order='F1',
    )
    buttons['del'] = dict(
        value='del',
        symbol='⬅️',
        order='E5',
    )
    buttons['('] = dict(
        value='(',
        symbol='(️',
        order='A4',
    )
    buttons[')'] = dict(
        value=')',
        symbol=')️',
        order='A5',
    )
    buttons['info'] = dict(
        value='info',
        symbol='ℹ️️',
        order='C5',
    )

    buttons['parser'] = dict(
        value='parser',
        symbol='💬️',
        order='D5',
    )

    return buttons


def get_operators() -> dict:
    def multiply(a, b):
        """Call operator.mul only if a and b are small enough."""
        if abs(max(a, b)) > 10 ** 21:
            raise Exception("Numbers were too large!")
        return operator.mul(a, b)

    def power(a, b):
        """Call operator.pow only if a and b are small enough."""
        if abs(a) > 1000 or abs(b) > 100:
            raise Exception("Numbers were too large!")
        return operator.pow(a, b)

    return {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: multiply,
        ast.Div: operator.truediv,
        ast.Pow: power,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod
    }


calc_buttons = get_calc_buttons()
operators = get_operators()

operators_spacer = re.compile(r"([\d()_])\s*([+\-*%]|/{1,2})\s*([\d()_])")
spaced_operators = r"\1 \2 \3"
operators_space_remover = re.compile(r"([\d()_])\s*(\*\*)\s*([\d()_])")
non_spaced_operators = r"\1\2\3"
multiple_newlines_regex = re.compile(r"[\n|\r][\n|\s]{2,}")
multiple_spaces_regex = re.compile(r"[^\S\n\r]{2,}")
parentheses_regex_list = [
    {'pattern': re.compile(r"[^\S\n\r]*(\()[^\S\n\r]*([\d_])"),
     'replace': r" \1\2"},
    {'pattern': re.compile(r"([\d_])[^\S\n\r]*(\))"),
     'replace': r"\1\2"}
]


def prettify_expression(expression):
    """Make expression cleaner to read.

    Place a single space around binary operators `+,-,*,%,/,//`, no space
        around `**`, single newlines and single spaces.
        No space after `(` or before `)`.
        No space at the beginning or ending of a line.
    """
    expression = operators_spacer.sub(spaced_operators, expression)
    expression = operators_space_remover.sub(non_spaced_operators, expression)
    for regex in parentheses_regex_list:
        expression = regex['pattern'].sub(regex['replace'], expression)
    expression = multiple_newlines_regex.sub('\n', expression)
    expression = multiple_spaces_regex.sub(' ', expression)
    expression = expression.replace('\n ', '\n')
    expression = expression.replace(' \n', '\n')
    return expression.strip(' ')


def get_calculator_keyboard(additional_data: list = None):
    if additional_data is None:
        additional_data = []
    return make_inline_keyboard(
        [
            make_button(
                text=button['symbol'],
                prefix='calc:///',
                delimiter='|',
                data=[*additional_data, code]
            )
            for code, button in sorted(calc_buttons.items(),
                                       key=lambda b: b[1]['order'])
        ],
        5
    )


async def _calculate_button(bot: Bot,
                            update: dict,
                            user_record: OrderedDict,
                            language: str,
                            data: List[Union[int, str]]):
    text, reply_markup = '', None
    if len(data) < 2:
        record_id = bot.db['calculations'].insert(
            dict(
                user_id=user_record['id'],
                created=datetime.datetime.now()
            )
        )
        data = [record_id, *data]
        text = bot.get_message(
            'useful_tools', 'calculate_command', 'use_buttons',
            language=language
        )
    else:
        record_id = data[0]
    reply_markup = get_calculator_keyboard(
        additional_data=([record_id] if record_id else None)
    )
    if record_id not in bot.shared_data['calc']:
        bot.shared_data['calc'][record_id] = []
        asyncio.ensure_future(
            calculate_session(bot=bot,
                              record_id=record_id,
                              language=language)
        )
    update['data'] = data
    if len(data) and data[-1] in ('info', 'parser'):
        command = data[-1]
        if command == 'parser':
            reply_markup = None
            bot.set_individual_text_message_handler(
                handler=wrap_calculate_command(record_id=record_id),
                user_id=user_record['telegram_id']
            )
        elif command == 'info':
            reply_markup = make_inline_keyboard(
                [
                    make_button(
                        text='Ok',
                        prefix='calc:///',
                        delimiter='|',
                        data=[record_id, 'back']
                    )
                ]
            )
        text = bot.get_message(
            'useful_tools', 'calculate_command', (
                'special_keys' if command == 'info'
                else 'message_input' if command == 'parser'
                else ''
            ),
            language=language
        )
    else:
        bot.shared_data['calc'][record_id].append(update)
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


def eval_(node):
    """Evaluate ast nodes."""
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        # noinspection PyArgumentList
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise Exception("Invalid operator")


def evaluate_expression(expr):
    """Evaluate expressions in a safe way."""
    return eval_(
        ast.parse(
            expr,
            mode='eval'
        ).body
    )


def evaluate_expressions(bot: Bot,
                         expressions: str,
                         language: str = None) -> str:
    """Evaluate a string containing lines of expressions.

    `expressions` must be a string containing one expression per line.
    """
    line_result, result = 0, []
    for line in expressions.split('\n'):
        if not line:
            continue
        try:
            line_result = evaluate_expression(
                line.replace('_', str(line_result))
            )
        except Exception as e:
            line_result = bot.get_message(
                'useful_tools', 'calculate_command', 'invalid_expression',
                language=language,
                error=e
            )
        result.append(
            f"<code>{line}</code>\n<b>= {line_result}</b>"
        )
    return '\n\n'.join(result)


async def calculate_session(bot: Bot,
                            record_id: int,
                            language: str,
                            buffer_seconds: Union[int, float] = .5):
    # Wait until input ends
    queue = bot.shared_data['calc'][record_id]
    queue_len = None
    while queue_len != len(queue):
        queue_len = len(queue)
        await asyncio.sleep(buffer_seconds)
    last_entry = max(queue, key=lambda u: u['id'], default=None)
    # Delete record-associated queue
    queue = queue.copy()
    del bot.shared_data['calc'][record_id]

    record = bot.db['calculations'].find_one(
        id=record_id
    )
    old_expression = record['expression'] or ''
    if record is None:
        logging.error("Invalid record identifier!")
        return
    expression = record['expression'] or ''
    reply_markup = get_calculator_keyboard(additional_data=[record['id']])
    # Process updates in order of arrival (according to Telegram servers)
    for i, update in enumerate(sorted(queue, key=lambda u: u['update_id'])):
        if i % 5 == 0:
            await asyncio.sleep(.1)
        data = update['data']
        if len(data) != 2:
            logging.error(f"Something went wrong: invalid data received.\n{data}")
            return
        input_value = data[1]
        if input_value == 'del':
            expression = expression[:-1].strip()
        elif input_value == 'back':
            pass
        elif input_value in calc_buttons:
            expression += calc_buttons[input_value]['value']
        else:
            logging.error(f"Invalid input from calculator button: {input_value}")
    expression = prettify_expression(expression)
    if record:
        bot.db['calculations'].update(
            dict(
                id=record['id'],
                modified=datetime.datetime.now(),
                expression=expression
            ),
            ['id']
        )
    if expression:
        if expression.strip(' \n') != old_expression.strip(' \n'):
            text = bot.get_message(
                'useful_tools', 'calculate_command', 'result',
                language=language,
                expressions=evaluate_expressions(bot=bot,
                                                 expressions=expression,
                                                 language=language)
            )
        else:
            text = ''
    else:
        text = bot.get_message(
            'useful_tools', 'calculate_command', 'instructions',
            language=language
        )
    if last_entry is None or not text:
        return
    await bot.edit_message_text(
        text=text,
        update=last_entry,
        reply_markup=reply_markup
    )


def wrap_calculate_command(record_id: int = None, command_name: str = 'calc'):
    async def wrapped_calculate_command(bot: Bot,
                                        update: dict,
                                        user_record: OrderedDict,
                                        language: str,):
        return await _calculate_command(bot=bot,
                                        update=update,
                                        user_record=user_record,
                                        language=language,
                                        command_name=command_name,
                                        record_id=record_id)
    return wrapped_calculate_command


async def _calculate_command(bot: Bot,
                             update: dict,
                             user_record: OrderedDict,
                             language: str,
                             command_name: str = 'calc',
                             record_id: int = None):
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
        if record_id is None:
            record_id = bot.db['calculations'].insert(
                dict(
                    user_id=user_record['id'],
                    created=datetime.datetime.now(),
                    expression=text
                )
            )
            expression = text
        else:
            record = bot.db['calculations'].find_one(
                id=record_id
            )
            expression = f"{record['expression'] or ''}\n{text}"
        expression = prettify_expression(expression)
        bot.db['calculations'].update(
            dict(
                id=record_id,
                modified=datetime.datetime.now(),
                expression=expression
            ),
            ['id']
        )
        text = bot.get_message(
            'useful_tools', 'calculate_command', 'result',
            language=language,
            expressions=evaluate_expressions(bot=bot,
                                             expressions=expression,
                                             language=language)
        )
        reply_markup = get_calculator_keyboard(additional_data=[record_id])
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
            'expression',
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
    async def calculate_command(bot, update, user_record, language):
        return await _calculate_command(bot=bot,
                                        update=update,
                                        user_record=user_record,
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
