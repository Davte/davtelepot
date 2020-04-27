"""Administration tools for telegram bots.

Usage:
```
import davtelepot
my_bot = davtelepot.Bot.get('my_token', 'my_database.db')
davtelepot.admin_tools.init(my_bot)
```
"""

# Standard library modules
import asyncio
import datetime
import json
import logging

# Third party modules
from sqlalchemy.exc import ResourceClosedError

# Project modules
from . import bot as davtelepot_bot, messages, __version__
from .utilities import (
    async_wrapper, CachedPage, Confirmator, extract, get_cleaned_text,
    get_user, escape_html_chars, line_drawing_unordered_list, make_button,
    make_inline_keyboard, remove_html_tags, send_part_of_text_file,
    send_csv_file
)


async def _forward_to(update, bot, sender, addressee, is_admin=False):
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


def get_talk_panel(bot, update, user_record=None, text=''):
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


async def _talk_command(bot, update, user_record):
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


async def start_session(bot, other_user_record, admin_record):
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


async def end_session(bot, other_user_record, admin_record):
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


async def _talk_button(bot, update, user_record, data):
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


async def _restart_command(bot, update, user_record):
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


async def _stop_command(bot, update, user_record):
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


async def stop_bots(bot):
    """Stop bots in `bot` class."""
    await asyncio.sleep(2)
    bot.__class__.stop(message='=== STOP ===', final_state=0)
    return


async def _stop_button(bot, update, user_record, data):
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


async def _send_bot_database(bot, update, user_record):
    if not all(
            [
                bot.db_url.endswith('.db'),
                bot.db_url.startswith('sqlite:///')
            ]
    ):
        return bot.get_message(
            'admin', 'db_command', 'not_sqlite',
            update=update, user_record=user_record,
            db_type=bot.db_url.partition(':///')[0]
        )
    await bot.send_document(
        chat_id=user_record['telegram_id'],
        document_path=extract(bot.db.url, starter='sqlite:///'),
        caption=bot.get_message(
            'admin', 'db_command', 'file_caption',
            update=update, user_record=user_record
        )
    )
    return bot.get_message(
        'admin', 'db_command', 'db_sent',
        update=update, user_record=user_record
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
        if 'message' not in update:
            return False
        update = update['message']
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


async def _version_command(bot, update, user_record):
    last_commit = await get_last_commit()
    return bot.get_message(
        'admin', 'version_command', 'result',
        last_commit=last_commit,
        davtelepot_version=__version__,
        update=update, user_record=user_record
    )


async def notify_new_version(bot: davtelepot_bot):
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


async def get_package_updates(bot: davtelepot_bot,
                              monitoring_interval: int = 60 * 60):
    while 1:
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
            if new_version != current_version:
                news[package.__name__] = {
                    'current': current_version,
                    'new': new_version
                }
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
        await asyncio.sleep(monitoring_interval)


def init(telegram_bot,
         talk_messages=None,
         admin_messages=None,
         packages=None):
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
    if 'talking_sessions' not in db.tables:
        db['talking_sessions'].insert(
            dict(
                user=0,
                admin=0,
                cancelled=1
            )
        )

    allowed_during_maintenance = [
        get_maintenance_exception_criterion(telegram_bot, command)
        for command in ['stop', 'restart', 'maintenance']
    ]

    @telegram_bot.additional_task(when='BEFORE')
    async def load_talking_sessions():
        sessions = []
        for session in db.query(
                """SELECT *
            FROM talking_sessions
            WHERE NOT cancelled
            """
        ):
            sessions.append(
                dict(
                    other_user_record=db['users'].find_one(
                        id=session['user']
                    ),
                    admin_record=db['users'].find_one(
                        id=session['admin']
                    ),
                )
            )
        for session in sessions:
            await start_session(
                bot=telegram_bot,
                other_user_record=session['other_user_record'],
                admin_record=session['admin_record']
            )

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

    @telegram_bot.command(command='/restart',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'restart_command']['description'],
                          authorization_level='admin')
    async def restart_command(bot, update, user_record):
        return await _restart_command(bot, update, user_record)

    @telegram_bot.additional_task('BEFORE')
    async def send_restart_messages():
        """Send restart messages at restart."""
        for restart_message in db['restart_messages'].find(sent=None):
            asyncio.ensure_future(
                telegram_bot.send_message(
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
            db['restart_messages'].update(
                dict(
                    sent=datetime.datetime.now(),
                    id=restart_message['id']
                ),
                ['id'],
                ensure=True
            )
        return

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

    @telegram_bot.command(command='/db',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'db_command']['description'],
                          authorization_level='admin')
    async def send_bot_database(bot, update, user_record):
        return await _send_bot_database(bot, update, user_record)

    @telegram_bot.command(command='/query',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'query_command']['description'],
                          authorization_level='admin')
    async def query_command(bot, update, user_record):
        return await _query_command(bot, update, user_record)

    @telegram_bot.command(command='/select',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'select_command']['description'],
                          authorization_level='admin')
    async def select_command(bot, update, user_record):
        return await _query_command(bot, update, user_record)

    @telegram_bot.button(prefix='db_query:///',
                         separator='|',
                         description=admin_messages[
                             'query_command']['description'],
                         authorization_level='admin')
    async def query_button(bot, update, user_record, data):
        return await _query_button(bot, update, user_record, data)

    @telegram_bot.command(command='/log',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'log_command']['description'],
                          authorization_level='admin')
    async def log_command(bot, update, user_record):
        return await _log_command(bot, update, user_record)

    @telegram_bot.command(command='/errors',
                          aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'errors_command']['description'],
                          authorization_level='admin')
    async def errors_command(bot, update, user_record):
        return await _errors_command(bot, update, user_record)

    for exception in allowed_during_maintenance:
        telegram_bot.allow_during_maintenance(exception)

    @telegram_bot.command(command='/maintenance', aliases=[],
                          show_in_keyboard=False,
                          description=admin_messages[
                              'maintenance_command']['description'],
                          authorization_level='admin')
    async def maintenance_command(bot, update, user_record):
        return await _maintenance_command(bot, update, user_record)

    @telegram_bot.command(command='/version',
                          aliases=[],
                          **{key: admin_messages['version_command'][key]
                             for key in ('reply_keyboard_button',
                                         'description',
                                         'help_section',)
                             },
                          show_in_keyboard=False,
                          authorization_level='admin')
    async def version_command(bot, update, user_record):
        return await _version_command(bot=bot,
                                      update=update,
                                      user_record=user_record)

    @telegram_bot.additional_task(when='BEFORE', bot=telegram_bot)
    async def notify_version(bot):
        return await notify_new_version(bot=bot)
