"""Administration tools for telegram bots.

Usage:
```
import davtelepot
my_bot = davtelepot.bot.Bot(token='my_token', database_url='my_database.db')
davtelepot.admin_tools.init(my_bot)
```
"""

# Standard library modules
import asyncio
import datetime
import json
import logging
import re
import types

from collections import OrderedDict
from typing import Union, List, Tuple

# Third party modules
from sqlalchemy.exc import ResourceClosedError

# Project modules
from . import messages
from .bot import Bot
from .utilities import (
    async_wrapper, CachedPage, Confirmator, extract, get_cleaned_text,
    get_user, escape_html_chars, line_drawing_unordered_list, make_button,
    make_inline_keyboard, remove_html_tags, send_part_of_text_file,
    send_csv_file, make_lines_of_buttons
)

# Use this parameter in SQL `LIMIT x OFFSET y` clauses
rows_number_limit = 10

command_description_parser = re.compile(r'(?P<command>\w+)(\s?-\s?(?P<description>.*))?')


async def _forward_to(update,
                      bot: Bot,
                      sender,
                      addressee,
                      is_admin=False):
    if update['text'].lower() in ['stop'] and is_admin:
        with bot.db as db:
            admin_record = db['users'].find_one(
                telegram_id=sender
            )
            session_record = db['talking_sessions'].find_one(
                admin=admin_record['id'],
                cancelled=0
            )
            other_user_record = db['users'].find_one(
                id=session_record['user']
            )
        await end_session(
            bot=bot,
            other_user_record=other_user_record,
            admin_record=admin_record
        )
    else:
        bot.set_individual_text_message_handler(
            await async_wrapper(
                _forward_to,
                sender=sender,
                addressee=addressee,
                is_admin=is_admin
            ),
            sender
        )
        await bot.forward_message(
            chat_id=addressee,
            update=update
        )
    return


def get_talk_panel(bot: Bot,
                   update,
                   user_record=None,
                   text: str = ''):
    """Return text and reply markup of talk panel.

    `text` may be:
    - `user_id` as string
    - `username` as string
    - `''` (empty string) for main menu (default)
    """
    users = []
    if len(text):
        with bot.db as db:
            if text.isnumeric():
                users = list(
                    db['users'].find(id=int(text))
                )
            else:
                users = list(
                    db.query(
                        "SELECT * "
                        "FROM users "
                        "WHERE COALESCE( "
                        "    first_name || last_name || username, "
                        "    last_name || username, "
                        "    first_name || username, "
                        "    username, "
                        "    first_name || last_name, "
                        "    last_name, "
                        "    first_name "
                        f") LIKE '%{text}%' "
                        "ORDER BY LOWER( "
                        "    COALESCE( "
                        "        first_name || last_name || username, "
                        "        last_name || username, "
                        "        first_name || username, "
                        "        username, "
                        "        first_name || last_name, "
                        "        last_name, "
                        "        first_name "
                        "    ) "
                        ") "
                        "LIMIT 26"
                    )
                )
    if len(text) == 0:
        text = (
            bot.get_message(
                'talk',
                'help_text',
                update=update,
                user_record=user_record,
                q=escape_html_chars(
                    remove_html_tags(text)
                )
            )
        )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    bot.get_message(
                        'talk', 'search_button',
                        update=update, user_record=user_record
                    ),
                    prefix='talk:///',
                    data=['search']
                )
            ],
            1
        )
    elif len(users) == 0:
        text = (
            bot.get_message(
                'talk',
                'user_not_found',
                update=update,
                user_record=user_record,
                q=escape_html_chars(
                    remove_html_tags(text)
                )
            )
        )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    bot.get_message(
                        'talk', 'search_button',
                        update=update, user_record=user_record
                    ),
                    prefix='talk:///',
                    data=['search']
                )
            ],
            1
        )
    else:
        text = "{header}\n\n{u}{etc}".format(
            header=bot.get_message(
                'talk', 'select_user',
                update=update, user_record=user_record
            ),
            u=line_drawing_unordered_list(
                [
                    get_user(user)
                    for user in users[:25]
                ]
            ),
            etc=(
                '\n\n[...]'
                if len(users) > 25
                else ''
            )
        )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    '👤 {u}'.format(
                        u=get_user(
                            {
                                key: val
                                for key, val in user.items()
                                if key in ('first_name',
                                           'last_name',
                                           'username')
                            }
                        )
                    ),
                    prefix='talk:///',
                    data=[
                        'select',
                        user['id']
                    ]
                )
                for user in users[:25]
            ],
            2
        )
    return text, reply_markup


async def _talk_command(bot: Bot,
                        update,
                        user_record):
    text = get_cleaned_text(
        update,
        bot,
        ['talk']
    )
    text, reply_markup = get_talk_panel(bot=bot, update=update,
                                        user_record=user_record, text=text)
    return dict(
        text=text,
        parse_mode='HTML',
        reply_markup=reply_markup,
    )


async def start_session(bot: Bot,
                        other_user_record,
                        admin_record):
    """Start talking session between user and admin.

    Register session in database, so it gets loaded before message_loop starts.
    Send a notification both to admin and user, set custom parsers and return.
    """
    with bot.db as db:
        db['talking_sessions'].insert(
            dict(
                user=other_user_record['id'],
                admin=admin_record['id'],
                cancelled=0
            )
        )
    await bot.send_message(
        chat_id=other_user_record['telegram_id'],
        text=bot.get_message(
            'talk', 'user_warning',
            user_record=other_user_record,
            u=get_user(admin_record)
        )
    )
    await bot.send_message(
        chat_id=admin_record['telegram_id'],
        text=bot.get_message(
            'talk', 'admin_warning',
            user_record=admin_record,
            u=get_user(other_user_record)
        ),
        reply_markup=make_inline_keyboard(
            [
                make_button(
                    bot.get_message(
                        'talk', 'stop',
                        user_record=admin_record
                    ),
                    prefix='talk:///',
                    data=['stop', other_user_record['id']]
                )
            ]
        )
    )
    bot.set_individual_text_message_handler(
        await async_wrapper(
            _forward_to,
            sender=other_user_record['telegram_id'],
            addressee=admin_record['telegram_id'],
            is_admin=False
        ),
        other_user_record['telegram_id']
    )
    bot.set_individual_text_message_handler(
        await async_wrapper(
            _forward_to,
            sender=admin_record['telegram_id'],
            addressee=other_user_record['telegram_id'],
            is_admin=True
        ),
        admin_record['telegram_id']
    )
    return


async def end_session(bot: Bot,
                      other_user_record,
                      admin_record):
    """End talking session between user and admin.

    Cancel session in database, so it will not be loaded anymore.
    Send a notification both to admin and user, clear custom parsers
        and return.
    """
    with bot.db as db:
        db['talking_sessions'].update(
            dict(
                admin=admin_record['id'],
                cancelled=1
            ),
            ['admin']
        )
    await bot.send_message(
        chat_id=other_user_record['telegram_id'],
        text=bot.get_message(
            'talk', 'user_session_ended',
            user_record=other_user_record,
            u=get_user(admin_record)
        )
    )
    await bot.send_message(
        chat_id=admin_record['telegram_id'],
        text=bot.get_message(
            'talk', 'admin_session_ended',
            user_record=admin_record,
            u=get_user(other_user_record)
        ),
    )
    for record in (admin_record, other_user_record,):
        bot.remove_individual_text_message_handler(record['telegram_id'])
    return


async def _talk_button(bot: Bot,
                       update,
                       user_record,
                       data):
    telegram_id = user_record['telegram_id']
    command, *arguments = data
    result, text, reply_markup = '', '', None
    if command == 'search':
        bot.set_individual_text_message_handler(
            await async_wrapper(
                _talk_command,
            ),
            update
        )
        text = bot.get_message(
            'talk', 'instructions',
            update=update, user_record=user_record
        )
        reply_markup = None
    elif command == 'select':
        if (
                len(arguments) < 1
                or type(arguments[0]) is not int
        ):
            result = "Errore!"
        else:
            with bot.db as db:
                other_user_record = db['users'].find_one(
                    id=arguments[0]
                )
                admin_record = db['users'].find_one(
                    telegram_id=telegram_id
                )
            await start_session(
                bot,
                other_user_record=other_user_record,
                admin_record=admin_record
            )
    elif command == 'stop':
        if (
                len(arguments) < 1
                or type(arguments[0]) is not int
        ):
            result = "Errore!"
        elif not Confirmator.get('stop_bots').confirm(telegram_id):
            result = bot.get_message(
                'talk', 'end_session',
                update=update, user_record=user_record
            )
        else:
            with bot.db as db:
                other_user_record = db['users'].find_one(
                    id=arguments[0]
                )
                admin_record = db['users'].find_one(
                    telegram_id=telegram_id
                )
            await end_session(
                bot,
                other_user_record=other_user_record,
                admin_record=admin_record
            )
            text = "Session ended."
            reply_markup = None
    if text:
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


async def _restart_command(bot: Bot,
                           update,
                           user_record):
    with bot.db as db:
        db['restart_messages'].insert(
            dict(
                text=bot.get_message(
                    'admin', 'restart_command', 'restart_completed_message',
                    update=update, user_record=user_record
                ),
                chat_id=update['chat']['id'],
                parse_mode='HTML',
                reply_to_message_id=update['message_id'],
                sent=None
            )
        )
    await bot.reply(
        update=update,
        text=bot.get_message(
            'admin', 'restart_command', 'restart_scheduled_message',
            update=update, user_record=user_record
        )
    )
    bot.__class__.stop(message='=== RESTART ===', final_state=65)
    return


async def _stop_command(bot: Bot,
                        update,
                        user_record):
    text = bot.get_message(
        'admin', 'stop_command', 'text',
        update=update, user_record=user_record
    )
    reply_markup = make_inline_keyboard(
        [
            make_button(
                text=bot.get_message(
                    'admin', 'stop_button', 'stop_text',
                    update=update, user_record=user_record
                ),
                prefix='stop:///',
                data=['stop']
            ),
            make_button(
                text=bot.get_message(
                    'admin', 'stop_button', 'cancel',
                    update=update, user_record=user_record
                ),
                prefix='stop:///',
                data=['cancel']
            )
        ],
        1
    )
    return dict(
        text=text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def stop_bots(bot: Bot):
    """Stop bots in `bot` class."""
    await asyncio.sleep(2)
    bot.__class__.stop(message='=== STOP ===', final_state=0)
    return


async def _stop_button(bot: Bot,
                       update,
                       user_record,
                       data: List[Union[int, str]]):
    result, text, reply_markup = '', '', None
    telegram_id = user_record['telegram_id']
    command = data[0] if len(data) > 0 else 'None'
    if command == 'stop':
        if not Confirmator.get('stop_bots').confirm(telegram_id):
            return bot.get_message(
                'admin', 'stop_button', 'confirm',
                update=update, user_record=user_record
            )
        text = bot.get_message(
            'admin', 'stop_button', 'stopping',
            update=update, user_record=user_record
        )
        result = text
        # Do not stop bots immediately, otherwise callback query
        # will never be answered
        asyncio.ensure_future(stop_bots(bot))
    elif command == 'cancel':
        text = bot.get_message(
            'admin', 'stop_button', 'cancelled',
            update=update, user_record=user_record
        )
        result = text
    if text:
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


async def _send_bot_database(bot: Bot, user_record: OrderedDict, language: str):
    if not all(
            [
                bot.db_url.endswith('.db'),
                bot.db_url.startswith('sqlite:///')
            ]
    ):
        return bot.get_message(
            'admin', 'db_command', 'not_sqlite',
            language=language,
            db_type=bot.db_url.partition(':///')[0]
        )
    sent_update = await bot.send_document(
        chat_id=user_record['telegram_id'],
        document_path=extract(bot.db.url, starter='sqlite:///'),
        caption=bot.get_message(
            'admin', 'db_command', 'file_caption',
            language=language
        )
    )
    return bot.get_message(
        'admin', 'db_command',
        ('error' if isinstance(sent_update, Exception) else 'db_sent'),
        language=language
    )


async def _query_command(bot, update, user_record):
    query = get_cleaned_text(
        update,
        bot,
        ['query', ]
    )
    query_id = None
    if len(query) == 0:
        return bot.get_message(
            'admin', 'query_command', 'help',
            update=update, user_record=user_record
        )
    try:
        with bot.db as db:
            record = db.query(query)
            try:
                record = list(record)
            except ResourceClosedError:
                record = bot.get_message(
                    'admin', 'query_command', 'no_iterable',
                    update=update, user_record=user_record
                )
            query_id = db['queries'].upsert(
                dict(
                    query=query
                ),
                ['query']
            )
            if query_id is True:
                query_id = db['queries'].find_one(
                    query=query
                )['id']
        result = json.dumps(record, indent=2)
        if len(result) > 500:
            result = (
                f"{result[:200]}\n"  # First 200 characters
                f"[...]\n"  # Interruption symbol
                f"{result[-200:]}"  # Last 200 characters
            )
    except Exception as e:
        result = "{first_line}\n{e}".format(
            first_line=bot.get_message(
                'admin', 'query_command', 'exception',
                update=update, user_record=user_record
            ),
            e=e
        )
    result = (
            "<b>{first_line}</b>\n".format(
                first_line=bot.get_message(
                    'admin', 'query_command', 'result',
                    update=update, user_record=user_record
                )
            )
            + f"<code>{query}</code>\n\n"
              f"{result}"
    )
    if query_id:
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    text='CSV',
                    prefix='db_query:///',
                    data=['csv', query_id]
                )
            ],
            1
        )
    else:
        reply_markup = None
    return dict(
        chat_id=update['chat']['id'],
        text=result,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def _query_button(bot, update, user_record, data):
    result, text, reply_markup = '', '', None
    command = data[0] if len(data) else 'default'
    error_message = bot.get_message(
        'admin', 'query_button', 'error',
        user_record=user_record, update=update
    )
    if command == 'csv':
        if not len(data) > 1:
            return error_message
        if len(data) > 1:
            with bot.db as db:
                query_record = db['queries'].find_one(id=data[1])
                if query_record is None or 'query' not in query_record:
                    return error_message
            await send_csv_file(
                bot=bot,
                chat_id=update['from']['id'],
                query=query_record['query'],
                file_name=bot.get_message(
                    'admin', 'query_button', 'file_name',
                    user_record=user_record, update=update
                ),
                update=update,
                user_record=user_record
            )
    if text:
        return dict(
            text=result,
            edit=dict(
                text=text,
                reply_markup=reply_markup
            )
        )
    return result


async def _log_command(bot, update, user_record):
    if bot.log_file_path is None:
        return bot.get_message(
            'admin', 'log_command', 'no_log',
            update=update, user_record=user_record
        )
    # Always send log file in private chat
    chat_id = update['from']['id']
    text = get_cleaned_text(update, bot, ['log'])
    reversed_ = 'r' not in text
    text = text.strip('r')
    if text.isnumeric():
        limit = int(text)
    else:
        limit = 100
    if limit is None:
        sent = await bot.send_document(
            chat_id=chat_id,
            document_path=bot.log_file_path,
            caption=bot.get_message(
                'admin', 'log_command', 'here_is_log_file',
                update=update, user_record=user_record
            )
        )
    else:
        sent = await send_part_of_text_file(
            bot=bot,
            update=update,
            user_record=user_record,
            chat_id=chat_id,
            file_path=bot.log_file_path,
            file_name=bot.log_file_name,
            caption=bot.get_message(
                'admin', 'log_command', (
                    'log_file_last_lines'
                    if reversed_
                    else 'log_file_first_lines'
                ),
                update=update, user_record=user_record,
                lines=limit
            ),
            reversed_=reversed_,
            limit=limit
        )
    if isinstance(sent, Exception):
        return bot.get_message(
            'admin', 'log_command', 'sending_failure',
            update=update, user_record=user_record,
            e=sent
        )
    return


async def _errors_command(bot, update, user_record):
    # Always send errors log file in private chat
    chat_id = update['from']['id']
    if bot.errors_file_path is None:
        return bot.get_message(
            'admin', 'errors_command', 'no_log',
            update=update, user_record=user_record
        )
    await bot.sendChatAction(chat_id=chat_id, action='upload_document')
    try:
        # Check that error log is not empty
        with open(bot.errors_file_path, 'r') as errors_file:
            for _ in errors_file:
                break
            else:
                return bot.get_message(
                    'admin', 'errors_command', 'empty_log',
                    update=update, user_record=user_record
                )
        # Send error log
        sent = await bot.send_document(
            # Always send log file in private chat
            chat_id=chat_id,
            document_path=bot.errors_file_path,
            caption=bot.get_message(
                'admin', 'errors_command', 'here_is_log_file',
                update=update, user_record=user_record
            )
        )
        # Reset error log
        with open(bot.errors_file_path, 'w') as errors_file:
            errors_file.write('')
    except Exception as e:
        sent = e
    # Notify failure
    if isinstance(sent, Exception):
        return bot.get_message(
            'admin', 'errors_command', 'sending_failure',
            update=update, user_record=user_record,
            e=sent
        )
    return


async def _maintenance_command(bot, update, user_record):
    maintenance_message = get_cleaned_text(update, bot, ['maintenance'])
    if maintenance_message.startswith('{'):
        maintenance_message = json.loads(maintenance_message)
    maintenance_status = bot.change_maintenance_status(
        maintenance_message=maintenance_message
    )
    if maintenance_status:
        return bot.get_message(
            'admin', 'maintenance_command', 'maintenance_started',
            update=update, user_record=user_record,
            message=bot.maintenance_message
        )
    return bot.get_message(
        'admin', 'maintenance_command', 'maintenance_ended',
        update=update, user_record=user_record
    )


def get_maintenance_exception_criterion(bot, allowed_command):
    """Get a criterion to allow a type of updates during maintenance.

    `bot` : davtelepot.bot.Bot() instance
    `allowed_command` : str (command to be allowed during maintenance)
    """

    def criterion(update):
        if 'message' in update:
            update = update['message']
        if 'text' not in update:
            return False
        text = get_cleaned_text(update, bot, [])
        if (
                'from' not in update
                or 'id' not in update['from']
        ):
            return False
        with bot.db as db:
            user_record = db['users'].find_one(
                telegram_id=update['from']['id']
            )
        if not bot.authorization_function(
                update=update,
                user_record=user_record,
                authorization_level=2
        ):
            return False
        return text == allowed_command.strip('/')

    return criterion


async def get_last_commit():
    """Get last commit hash and davtelepot version."""
    try:
        _subprocess = await asyncio.create_subprocess_exec(
            'git', 'rev-parse', 'HEAD',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await _subprocess.communicate()
        last_commit = stdout.decode().strip()
    except Exception as e:
        last_commit = f"{e}"
    if last_commit.startswith("fatal: not a git repository"):
        last_commit = "-"
    return last_commit


async def get_new_versions(bot: Bot,
                           notification_interval: datetime.timedelta = None) -> dict:
    """Get new versions of packages in bot.packages.

    Result: {"name": {"current": "0.1", "new": "0.2"}}
    """
    if notification_interval is None:
        notification_interval = datetime.timedelta(seconds=0)
    news = dict()
    for package in bot.packages:
        package_web_page = CachedPage.get(
            f'https://pypi.python.org/pypi/{package.__name__}/json',
            cache_time=2,
            mode='json'
        )
        web_page = await package_web_page.get_page()
        if web_page is None or isinstance(web_page, Exception):
            logging.error(f"Cannot get updates for {package.__name__}, "
                          "skipping...")
            continue
        new_version = web_page['info']['version']
        current_version = package.__version__
        notification_record = bot.db['updates_notifications'].find_one(
            package=package.__name__,
            order_by=['-id'],
            _limit=1
        )
        if (
                new_version != current_version
                and (notification_record is None
                     or notification_record['notified_at']
                     < datetime.datetime.now() - notification_interval)
        ):
            news[package.__name__] = {
                'current': current_version,
                'new': new_version
            }
    return news


async def _version_command(bot: Bot, update: dict,
                           user_record: OrderedDict, language: str):
    last_commit = await get_last_commit()
    text = bot.get_message(
        'admin', 'version_command', 'header',
        last_commit=last_commit,
        update=update, user_record=user_record
    ) + '\n\n'
    text += '\n'.join(
        f"<b>{package.__name__}</b>: "
        f"<code>{package.__version__}</code>"
        for package in bot.packages
    )
    temporary_message = await bot.send_message(
        text=text + '\n\n' + bot.get_message(
            'admin', 'version_command', 'checking_for_updates',
            language=language
        ),
        update=update,
        send_default_keyboard=False
    )
    news = await get_new_versions(bot=bot)
    if not news:
        text += '\n\n' + bot.get_message(
            'admin', 'version_command', 'all_packages_updated',
            language=language
        )
    else:
        text += '\n\n' + bot.get_message(
            'admin', 'updates_available', 'header',
            user_record=user_record
        ) + '\n\n'
        text += '\n'.join(
            f"<b>{package}</b>: "
            f"<code>{versions['current']}</code> —> "
            f"<code>{versions['new']}</code>"
            for package, versions in news.items()
        )
    await bot.edit_message_text(
        text=text,
        update=temporary_message
    )


async def notify_new_version(bot: Bot):
    """Notify `bot` administrators about new versions.

    Notify admins when last commit and/or davtelepot version change.
    """
    last_commit = await get_last_commit()
    old_record = bot.db['version_history'].find_one(
        order_by=['-id']
    )
    current_versions = {
        f"{package.__name__}_version": package.__version__
        for package in bot.packages
    }
    current_versions['last_commit'] = last_commit
    if old_record is None:
        old_record = dict(
            updated_at=datetime.datetime.min,
        )
    for name in current_versions.keys():
        if name not in old_record:
            old_record[name] = None
    if any(
            old_record[name] != current_version
            for name, current_version in current_versions.items()
    ):
        bot.db['version_history'].insert(
            dict(
                updated_at=datetime.datetime.now(),
                **current_versions
            )
        )
        for admin in bot.administrators:
            text = bot.get_message(
                'admin', 'new_version', 'title',
                user_record=admin
            ) + '\n\n'
            if last_commit != old_record['last_commit']:
                text += bot.get_message(
                    'admin', 'new_version', 'last_commit',
                    old_record=old_record,
                    new_record=current_versions,
                    user_record=admin
                ) + '\n\n'
            text += '\n'.join(
                f"<b>{name[:-len('_version')]}</b>: "
                f"<code>{old_record[name]}</code> —> "
                f"<code>{current_version}</code>"
                for name, current_version in current_versions.items()
                if name not in ('last_commit', )
                and current_version != old_record[name]
            )
            await bot.send_message(
                chat_id=admin['telegram_id'],
                disable_notification=True,
                text=text
            )
    return


async def get_package_updates(bot: Bot,
                              monitoring_interval: Union[
                                  int, datetime.timedelta
                              ] = 60 * 60,
                              notification_interval: Union[
                                  int, datetime.timedelta
                              ] = 60 * 60 * 24):
    if isinstance(monitoring_interval, datetime.timedelta):
        monitoring_interval = monitoring_interval.total_seconds()
    if type(notification_interval) is int:
        notification_interval = datetime.timedelta(
            seconds=notification_interval
        )
    while 1:
        news = await get_new_versions(bot=bot,
                                      notification_interval=notification_interval)
        if news:
            for admin in bot.administrators:
                text = bot.get_message(
                    'admin', 'updates_available', 'header',
                    user_record=admin
                ) + '\n\n'
                text += '\n'.join(
                    f"<b>{package}</b>: "
                    f"<code>{versions['current']}</code> —> "
                    f"<code>{versions['new']}</code>"
                    for package, versions in news.items()
                )
                await bot.send_message(
                    chat_id=admin['telegram_id'],
                    disable_notification=True,
                    text=text
                )
            bot.db['updates_notifications'].insert_many(
                [
                    {
                        "package": package,
                        "version": information['new'],
                        'notified_at': datetime.datetime.now()
                    }
                    for package, information in news.items()
                ]
            )
        await asyncio.sleep(monitoring_interval)


async def _send_start_messages(bot: Bot):
    """Send restart messages at restart."""
    for restart_message in bot.db['restart_messages'].find(sent=None):
        asyncio.ensure_future(
            bot.send_message(
                **{
                    key: val
                    for key, val in restart_message.items()
                    if key in (
                        'chat_id',
                        'text',
                        'parse_mode',
                        'reply_to_message_id'
                    )
                }
            )
        )
        bot.db['restart_messages'].update(
            dict(
                sent=datetime.datetime.now(),
                id=restart_message['id']
            ),
            ['id'],
            ensure=True
        )
    return


async def _load_talking_sessions(bot: Bot):
    sessions = []
    for session in bot.db.query(
            """SELECT *
        FROM talking_sessions
        WHERE NOT cancelled
        """
    ):
        sessions.append(
            dict(
                other_user_record=bot.db['users'].find_one(
                    id=session['user']
                ),
                admin_record=bot.db['users'].find_one(
                    id=session['admin']
                ),
            )
        )
    for session in sessions:
        await start_session(
            bot=bot,
            other_user_record=session['other_user_record'],
            admin_record=session['admin_record']
        )


def get_current_commands(bot: Bot, language: str = None) -> List[dict]:
    return sorted(
        [
            {
                'command': bot.get_message(
                    messages=information['language_labelled_commands'],
                    default_message=name,
                    language=language
                ),
                'description': bot.get_message(
                    messages=information['description'],
                    language=language
                )
            }
            for name, information in bot.commands.items()
            if 'description' in information
               and information['description']
               and 'authorization_level' in information
               and information['authorization_level'] in ('registered_user', 'everybody',)
        ],
        key=(lambda c: c['command'])
    )


def get_custom_commands(bot: Bot, language: str = None) -> List[dict]:
    additional_commands = [
        {
            'command': record['command'],
            'description': record['description']
        }
        for record in bot.db['bot_father_commands'].find(
            cancelled=None,
            hidden=False
        )
    ]
    hidden_commands_names = [
        record['command']
        for record in bot.db['bot_father_commands'].find(
            cancelled=None,
            hidden=True
        )
    ]
    return sorted(
        [
            command
            for command in (get_current_commands(bot=bot, language=language)
                            + additional_commands)
            if command['command'] not in hidden_commands_names
        ],
        key=(lambda c: c['command'])
    )


async def _father_command(bot, language):
    modes = [
        {
            key: (
                bot.get_message(messages=val,
                                language=language)
                if isinstance(val, dict)
                else val
            )
            for key, val in mode.items()
        }
        for mode in bot.messages['admin']['father_command']['modes']
    ]
    text = "\n\n".join(
        [
            bot.get_message(
                'admin', 'father_command', 'title',
                language=language
            )
        ] + [
            "{m[symbol]} {m[name]}\n{m[description]}".format(m=mode)
            for mode in modes
        ]
    )
    reply_markup = make_inline_keyboard(
        [
            make_button(
                text="{m[symbol]} {m[name]}".format(m=mode),
                prefix='father:///',
                delimiter='|',
                data=[mode['id']]
            )
            for mode in modes
        ],
        2
    )
    return dict(
        text=text,
        reply_markup=reply_markup
    )


def browse_bot_father_settings_records(bot: Bot,
                                       language: str,
                                       page: int = 0) -> Tuple[str, str, dict]:
    """Return a reply keyboard to edit bot father settings records."""
    result, text, reply_markup = '', '', None
    records = list(
        bot.db['bot_father_commands'].find(
            cancelled=None,
            _limit=(rows_number_limit + 1),
            _offset=(page * rows_number_limit)
        )
    )
    for record in bot.db.query(
        "SELECT COUNT(*) AS c "
        "FROM bot_father_commands "
        "WHERE cancelled IS NULL"
    ):
        records_count = record['c']
        break
    else:
        records_count = 0
    text = bot.get_message(
        'admin', 'father_command', 'settings', 'browse_records',
        language=language,
        record_interval=((page * rows_number_limit + 1) if records else 0,
                         min((page + 1) * rows_number_limit, len(records)),
                         records_count),
        commands_list='\n'.join(
            f"{'➖' if record['hidden'] else '➕'} {record['command']}"
            for record in records[:rows_number_limit]
        )
    )
    buttons = make_lines_of_buttons(
        [
            make_button(
                text=f"{'➖' if record['hidden'] else '➕'} {record['command']}",
                prefix='father:///',
                delimiter='|',
                data=['settings', 'edit', 'select', record['id']]
            )
            for record in records[:rows_number_limit]
        ],
        3
    )
    buttons += make_lines_of_buttons(
        (
            [
                make_button(
                    text='⬅',
                    prefix='father:///',
                    delimiter='|',
                    data=['settings', 'edit', 'go', page - 1]
                )
            ]
            if page > 0
            else []
        ) + [
            make_button(
                text=bot.get_message('admin', 'father_command', 'back',
                                     language=language),
                prefix='father:///',
                delimiter='|',
                data=['settings']
            )
        ] + (
            [
                make_button(
                    text='️➡️',
                    prefix='father:///',
                    delimiter='|',
                    data=['settings', 'edit', 'go', page + 1]
                )
            ]
            if len(records) > rows_number_limit
            else []
        ),
        3
    )
    reply_markup = dict(
        inline_keyboard=buttons
    )
    return result, text, reply_markup


def get_bot_father_settings_editor(mode: str,
                                   record: OrderedDict = None):
    """Get a coroutine to edit or create a record in bot father settings table.

    Modes:
        - add
        - hide
    """
    async def bot_father_settings_editor(bot: Bot, update: dict,
                                         language: str):
        """Edit or create a record in bot father settings table."""
        nonlocal record
        if record is not None:
            record_id = record['id']
        else:
            record_id = None
        # Cancel if user used /cancel command, or remove trailing forward_slash
        input_text = update['text']
        if input_text.startswith('/'):
            if language not in bot.messages['admin']['cancel']['lower']:
                language = bot.default_language
            if input_text.lower().endswith(bot.messages['admin']['cancel']['lower'][language]):
                return bot.get_message(
                    'admin', 'cancel', 'done',
                    language=language
                )
            else:
                input_text = input_text[1:]
        if record is None:
            # Use regex compiled pattern to search for command and description
            re_search = command_description_parser.search(input_text)
            if re_search is None:
                return bot.get_message(
                    'admin', 'error', 'text',
                    language=language
                )
            re_search = re_search.groupdict()
            command = re_search['command'].lower()
            description = re_search['description']
        else:
            command = record['command']
            description = input_text
        error = None
        # A description (str 3-256) is required
        if mode in ('add', 'edit'):
            if description is None or len(description) < 3:
                error = 'missing_description'
            elif type(description) is str and len(description) > 255:
                error = 'description_too_long'
            elif mode == 'add':
                duplicate = bot.db['bot_father_commands'].find_one(
                    command=command,
                    cancelled=None
                )
                if duplicate:
                    error = 'duplicate_record'
        if error:
            text = bot.get_message(
                'admin', 'father_command', 'settings', 'modes',
                'add', 'error', error,
                language=language
            )
            reply_markup = make_inline_keyboard(
                [
                    make_button(
                        text=bot.get_message(
                            'admin', 'father_command', 'back',
                            language=language
                        ),
                        prefix='father:///',
                        delimiter='|',
                        data=['settings']
                    )
                ]
            )
        else:
            table = bot.db['bot_father_commands']
            new_record = dict(
                command=command,
                description=description,
                hidden=(mode == 'hide'),
                cancelled=None
            )
            if record_id is None:
                record_id = table.insert(
                    new_record
                )
            else:
                new_record['id'] = record_id
                table.upsert(
                    new_record,
                    ['id']
                )
            text = bot.get_message(
                'admin', 'father_command', 'settings', 'modes',
                mode, ('edit' if 'id' in new_record else 'add'), 'done',
                command=command,
                description=(description if description else '-'),
                language=language
            )
            reply_markup = make_inline_keyboard(
                [
                    make_button(
                        text=bot.get_message(
                            'admin', 'father_command', 'settings', 'modes',
                            'edit', 'button',
                            language=language
                        ),
                        prefix='father:///',
                        delimiter='|',
                        data=['settings', 'edit', 'select', record_id]
                    ), make_button(
                        text=bot.get_message(
                            'admin', 'father_command', 'back',
                            language=language
                        ),
                        prefix='father:///',
                        delimiter='|',
                        data=['settings']
                    )
                ],
                2
            )
        asyncio.ensure_future(
            bot.delete_message(update=update)
        )
        return dict(
            text=text,
            reply_markup=reply_markup
        )
    return bot_father_settings_editor


async def edit_bot_father_settings_via_message(bot: Bot,
                                               user_record: OrderedDict,
                                               language: str,
                                               mode: str,
                                               record: OrderedDict = None):
    result, text, reply_markup = '', '', None
    modes = bot.messages['admin']['father_command']['settings']['modes']
    if mode not in modes:
        result = bot.get_message(
            'admin', 'father_command', 'error',
            language=language
        )
    else:
        result = bot.get_message(
            ('add' if record is None else 'edit'), 'popup',
            messages=modes[mode],
            language=language,
            command=(record['command'] if record is not None else None)
        )
        text = bot.get_message(
            ('add' if record is None else 'edit'), 'text',
            messages=modes[mode],
            language=language,
            command=(record['command'] if record is not None else None)
        )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    text=bot.get_message(
                        'admin', 'cancel', 'button',
                        language=language,
                    ),
                    prefix='father:///',
                    delimiter='|',
                    data=['cancel']
                )
            ]
        )
        bot.set_individual_text_message_handler(
            get_bot_father_settings_editor(mode=mode, record=record),
            user_id=user_record['telegram_id'],
        )
    return result, text, reply_markup


async def _father_button(bot: Bot, user_record: OrderedDict,
                         language: str, data: list):
    """Handle BotFather button.

    Operational modes
    - main: back to main page (see _father_command)
    - get: show commands stored by @BotFather
    - set: edit commands stored by @BotFather
    """
    result, text, reply_markup = '', '', None
    command, *data = data
    if command == 'cancel':
        bot.remove_individual_text_message_handler(user_id=user_record['telegram_id'])
        result = text = bot.get_message(
            'admin', 'cancel', 'done',
            language=language
        )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    text=bot.get_message('admin', 'father_command', 'back',
                                         language=language),
                    prefix='father:///',
                    delimiter='|',
                    data=['main']
                )
            ]
        )
    elif command == 'del':
        if not Confirmator.get('del_bot_father_commands',
                               confirm_timedelta=3
                               ).confirm(user_record['id']):
            return bot.get_message(
                'admin', 'confirm',
                language=language
            )
        stored_commands = await bot.getMyCommands()
        if not len(stored_commands):
            text = bot.get_message(
                'admin', 'father_command', 'del', 'no_change',
                language=language
            )
        else:
            if isinstance(
                    await bot.setMyCommands([]),
                    Exception
            ):
                text = bot.get_message(
                    'admin', 'father_command', 'del', 'error',
                    language=language
                )
            else:
                text = bot.get_message(
                    'admin', 'father_command', 'del', 'done',
                    language=language
                )
                reply_markup = make_inline_keyboard(
                    [
                        make_button(
                            text=bot.get_message('admin', 'father_command', 'back',
                                                 language=language),
                            prefix='father:///',
                            delimiter='|',
                            data=['main']
                        )
                    ]
                )
    elif command == 'get':
        commands = await bot.getMyCommands()
        if len(commands) == 0:
            commands = bot.get_message(
                'admin', 'father_command', 'get', 'empty',
                language=language,
                commands=commands
            )
        else:
            commands = '<code>' + '\n'.join(
                "{c[command]} - {c[description]}".format(c=command)
                for command in commands
            ) + '</code>'
        text = bot.get_message(
            'admin', 'father_command', 'get', 'panel',
            language=language,
            commands=commands
        )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    text=bot.get_message('admin', 'father_command', 'back',
                                         language=language),
                    prefix='father:///',
                    delimiter='|',
                    data=['main']
                )
            ]
        )
    elif command == 'main':
        return dict(
            text='',
            edit=(await _father_command(bot=bot, language=language))
        )
    elif command == 'set':
        stored_commands = await bot.getMyCommands()
        current_commands = get_custom_commands(bot=bot, language=language)
        if len(data) > 0 and data[0] == 'confirm':
            if not Confirmator.get('set_bot_father_commands',
                                   confirm_timedelta=3
                                   ).confirm(user_record['id']):
                return bot.get_message(
                    'admin', 'confirm',
                    language=language
                )
            if stored_commands == current_commands:
                text = bot.get_message(
                    'admin', 'father_command', 'set', 'no_change',
                    language=language
                )
            else:
                if isinstance(
                        await bot.setMyCommands(current_commands),
                        Exception
                ):
                    text = bot.get_message(
                        'admin', 'father_command', 'set', 'error',
                        language=language
                    )
                else:
                    text = bot.get_message(
                        'admin', 'father_command', 'set', 'done',
                        language=language
                    )
            reply_markup = make_inline_keyboard(
                [
                    make_button(
                        text=bot.get_message('admin', 'father_command', 'back',
                                             language=language),
                        prefix='father:///',
                        delimiter='|',
                        data=['main']
                    )
                ]
            )
        else:
            stored_commands_names = [c['command'] for c in stored_commands]
            current_commands_names = [c['command'] for c in current_commands]
            # Show preview of new, edited and removed commands
            # See 'legend' in bot.messages['admin']['father_command']['set']
            text = bot.get_message(
                    'admin', 'father_command', 'set', 'header',
                    language=language
            ) + '\n\n' + '\n\n'.join([
                '\n'.join(
                    ('✅ ' if c in stored_commands
                     else '☑️ ' if c['command'] not in stored_commands_names
                     else '✏️') + c['command']
                    for c in current_commands
                ),
                '\n'.join(
                    f'❌ {command}'
                    for command in stored_commands_names
                    if command not in current_commands_names
                ),
                bot.get_message(
                    'admin', 'father_command', 'set', 'legend',
                    language=language
                )
            ])
            reply_markup = make_inline_keyboard(
                [
                    make_button(
                        text=bot.get_message('admin', 'father_command', 'set',
                                             'button',
                                             language=language),
                        prefix='father:///',
                        delimiter='|',
                        data=['set', 'confirm']
                    )
                ] + [
                    make_button(
                        text=bot.get_message('admin', 'father_command', 'back',
                                             language=language),
                        prefix='father:///',
                        delimiter='|',
                        data=['main']
                    )
                ],
                1
            )
    elif command == 'settings':
        if len(data) == 0:
            additional_commands = '\n'.join(
                f"{record['command']} - {record['description']}"
                for record in bot.db['bot_father_commands'].find(
                    cancelled=None,
                    hidden=False
                )
            )
            if not additional_commands:
                additional_commands = '-'
            hidden_commands = '\n'.join(
                f"{record['command']}"
                for record in bot.db['bot_father_commands'].find(
                    cancelled=None,
                    hidden=True
                )
            )
            if not hidden_commands:
                hidden_commands = '-'
            text = bot.get_message(
                'admin', 'father_command', 'settings', 'panel',
                language=language,
                additional_commands=additional_commands,
                hidden_commands=hidden_commands
            )
            modes = bot.messages['admin']['father_command']['settings']['modes']
            reply_markup = make_inline_keyboard(
                [
                    make_button(
                        text=modes[code]['symbol'] + ' ' + bot.get_message(
                            messages=modes[code]['name'],
                            language=language
                        ),
                        prefix='father:///',
                        delimiter='|',
                        data=['settings', code]
                    )
                    for code, mode in modes.items()
                ] + [
                    make_button(
                        text=bot.get_message('admin', 'father_command', 'back',
                                             language=language),
                        prefix='father:///',
                        delimiter='|',
                        data=['main']
                    )
                ],
                2
            )
        elif data[0] in ('add', 'hide', ):
            result, text, reply_markup = await edit_bot_father_settings_via_message(
                bot=bot,
                user_record=user_record,
                language=language,
                mode=data[0]
            )
        elif data[0] == 'edit':
            if len(data) > 2 and data[1] == 'select':
                selected_record = bot.db['bot_father_commands'].find_one(id=data[2])
                if selected_record is None:
                    return bot.get_message(
                        'admin', 'error',
                        language=language
                    )
                if len(data) == 3:
                    text = bot.get_message(
                        'admin', 'father_command', 'settings',
                        'modes', 'edit', 'panel', 'text',
                        language=language,
                        command=selected_record['command'],
                        description=selected_record['description'],
                    )
                    reply_markup = make_inline_keyboard(
                        [
                            make_button(
                                text=bot.get_message(
                                    'admin', 'father_command', 'settings',
                                    'modes', 'edit', 'panel',
                                    'edit_description', 'button',
                                    language=language,
                                ),
                                prefix='father:///',
                                delimiter='|',
                                data=['settings', 'edit', 'select',
                                      selected_record['id'], 'edit_descr']
                            ),
                            make_button(
                                text=bot.get_message(
                                    'admin', 'father_command', 'settings',
                                    'modes', 'edit', 'panel',
                                    'delete', 'button',
                                    language=language,
                                ),
                                prefix='father:///',
                                delimiter='|',
                                data=['settings', 'edit', 'select',
                                      selected_record['id'], 'del']
                            ),
                            make_button(
                                text=bot.get_message(
                                    'admin', 'father_command', 'back',
                                    language=language,
                                ),
                                prefix='father:///',
                                delimiter='|',
                                data=['settings', 'edit']
                            )
                        ],
                        2
                    )
                elif len(data) > 3 and data[3] == 'edit_descr':
                    result, text, reply_markup = await edit_bot_father_settings_via_message(
                        bot=bot,
                        user_record=user_record,
                        language=language,
                        mode=data[0],
                        record=selected_record
                    )
                elif len(data) > 3 and data[3] == 'del':
                    if not Confirmator.get('set_bot_father_commands',
                                           confirm_timedelta=3
                                           ).confirm(user_record['id']):
                        result = bot.get_message(
                            'admin', 'confirm',
                            language=language
                        )
                    else:
                        bot.db['bot_father_commands'].update(
                            dict(
                                id=selected_record['id'],
                                cancelled=True
                            ),
                            ['id']
                        )
                        result = bot.get_message(
                            'admin', 'father_command', 'settings',
                            'modes', 'edit', 'panel', 'delete',
                            'done', 'popup',
                            language=language
                        )
                        text = bot.get_message(
                            'admin', 'father_command', 'settings',
                            'modes', 'edit', 'panel', 'delete',
                            'done', 'text',
                            language=language
                        )
                        reply_markup = make_inline_keyboard(
                            [
                                make_button(
                                    text=bot.get_message(
                                        'admin', 'father_command',
                                        'back',
                                        language=language
                                    ),
                                    prefix='father:///',
                                    delimiter='|',
                                    data=['settings']
                                )
                            ],
                            1
                        )
            elif len(data) == 1 or data[1] == 'go':
                result, text, reply_markup = browse_bot_father_settings_records(
                    bot=bot,
                    language=language,
                    page=(data[2] if len(data) > 2 else 0)
                )
    if text:
        return dict(
            text=result,
            edit=dict(
                text=text,
                reply_markup=reply_markup
            )
        )
    return result


def init(telegram_bot: Bot,
         talk_messages: dict = None,
         admin_messages: dict = None,
         packages: List[types.ModuleType] = None):
    """Assign parsers, commands, buttons and queries to given `bot`."""
    if packages is None:
        packages = []
    telegram_bot.packages.extend(
        filter(lambda package: package not in telegram_bot.packages,
               packages)
    )
    asyncio.ensure_future(get_package_updates(telegram_bot))
    if talk_messages is None:
        talk_messages = messages.default_talk_messages
    telegram_bot.messages['talk'] = talk_messages
    if admin_messages is None:
        admin_messages = messages.default_admin_messages
    telegram_bot.messages['admin'] = admin_messages
    db = telegram_bot.db
    if 'bot_father_commands' not in db.tables:
        table = db.create_table(
            table_name='bot_father_commands'
        )
        table.create_column(
            'command',
            db.types.string
        )
        table.create_column(
            'description',
            db.types.string
        )
        table.create_column(
            'hidden',
            db.types.boolean
        )
        table.create_column(
            'cancelled',
            db.types.boolean
        )
    if 'talking_sessions' not in db.tables:
        table = db.create_table(
            table_name='talking_sessions'
        )
        table.create_column(
            'user',
            db.types.integer
        )
        table.create_column(
            'admin',
            db.types.integer
        )
        table.create_column(
            'cancelled',
            db.types.integer
        )
    for exception in [
        get_maintenance_exception_criterion(telegram_bot, command)
        for command in ['stop', 'restart', 'maintenance']
    ]:
        telegram_bot.allow_during_maintenance(exception)

    # Tasks to complete before starting bot
    @telegram_bot.additional_task(when='BEFORE')
    async def load_talking_sessions():
        return await _load_talking_sessions(bot=telegram_bot)

    @telegram_bot.additional_task(when='BEFORE', bot=telegram_bot)
    async def notify_version(bot):
        return await notify_new_version(bot=bot)

    @telegram_bot.additional_task('BEFORE')
    async def send_restart_messages():
        return await _send_start_messages(bot=telegram_bot)

    # Administration commands
    @telegram_bot.command(command='/db',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'db_command']['description'],
                          authorization_level='admin')
    async def send_bot_database(bot, user_record, language):
        return await _send_bot_database(bot=bot,
                                        user_record=user_record,
                                        language=language)

    @telegram_bot.command(command='/errors',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'errors_command']['description'],
                          authorization_level='admin')
    async def errors_command(bot, update, user_record):
        return await _errors_command(bot, update, user_record)

    @telegram_bot.command(command='/father',
                          aliases=[],
                          show_in_keyboard=False,
                          **{
                              key: value
                              for key, value in admin_messages['father_command'].items()
                              if key in ('description', )
                          },
                          authorization_level='admin')
    async def father_command(bot, language):
        return await _father_command(bot=bot, language=language)

    @telegram_bot.button(prefix='father:///',
                         separator='|',
                         authorization_level='admin')
    async def query_button(bot, user_record, language, data):
        return await _father_button(bot=bot,
                                    user_record=user_record,
                                    language=language,
                                    data=data)

    @telegram_bot.command(command='/log',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'log_command']['description'],
                          authorization_level='admin')
    async def log_command(bot, update, user_record):
        return await _log_command(bot, update, user_record)

    @telegram_bot.command(command='/maintenance', aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'maintenance_command']['description'],
                          authorization_level='admin')
    async def maintenance_command(bot, update, user_record):
        return await _maintenance_command(bot, update, user_record)

    @telegram_bot.command(command='/query',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'query_command']['description'],
                          authorization_level='admin')
    async def query_command(bot, update, user_record):
        return await _query_command(bot, update, user_record)

    @telegram_bot.button(prefix='db_query:///',
                         separator='|',
                         description=admin_messages[
                             'query_command']['description'],
                         authorization_level='admin')
    async def query_button(bot, update, user_record, data):
        return await _query_button(bot, update, user_record, data)

    @telegram_bot.command(command='/restart',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'restart_command']['description'],
                          authorization_level='admin')
    async def restart_command(bot, update, user_record):
        return await _restart_command(bot, update, user_record)

    @telegram_bot.command(command='/select',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'select_command']['description'],
                          authorization_level='admin')
    async def select_command(bot, update, user_record):
        return await _query_command(bot, update, user_record)

    @telegram_bot.command(command='/stop',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'stop_command']['description'],
                          authorization_level='admin')
    async def stop_command(bot, update, user_record):
        return await _stop_command(bot, update, user_record)

    @telegram_bot.button(prefix='stop:///',
                         separator='|',
                         description=admin_messages[
                             'stop_command']['description'],
                         authorization_level='admin')
    async def stop_button(bot, update, user_record, data):
        return await _stop_button(bot, update, user_record, data)

    @telegram_bot.command(command='/talk',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'talk_command']['description'],
                          authorization_level='admin')
    async def talk_command(bot, update, user_record):
        return await _talk_command(bot, update, user_record)

    @telegram_bot.button(prefix='talk:///',
                         separator='|',
                         authorization_level='admin')
    async def talk_button(bot, update, user_record, data):
        return await _talk_button(bot, update, user_record, data)

    @telegram_bot.command(command='/version',
                          aliases=[],
                          **{key: admin_messages['version_command'][key]
                             for key in ('reply_keyboard_button',
                                         'description',
                                         'help_section',)
                             },
                          show_in_keyboard=False,
                          authorization_level='admin')
    async def version_command(bot, update, user_record, language):
        return await _version_command(bot=bot,
                                      update=update,
                                      user_record=user_record,
                                      language=language)
