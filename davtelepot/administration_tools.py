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

# Third party modules
from davtelepot.utilities import (
    async_wrapper, Confirmator, extract, get_cleaned_text, get_user,
    escape_html_chars, line_drawing_unordered_list, make_button,
    make_inline_keyboard, remove_html_tags, send_part_of_text_file,
    send_csv_file
)
from sqlalchemy.exc import ResourceClosedError


default_talk_messages = dict(
    admin_session_ended=dict(
        en=(
            'Session with user {u} ended.'
        ),
        it=(
            'Sessione terminata con l\'utente {u}.'
        ),
    ),
    admin_warning=dict(
        en=(
            'You are now talking to {u}.\n'
            'Until you end this session, your messages will be '
            'forwarded to each other.'
        ),
        it=(
            'Sei ora connesso con {u}.\n'
            'Finché non chiuderai la connessione, i messaggi che scriverai '
            'qui saranno inoltrati a {u}, e ti inoltrerò i suoi.'
        ),
    ),
    end_session=dict(
        en=(
            'End session?'
        ),
        it=(
            'Chiudere la sessione?'
        ),
    ),
    help_text=dict(
        en='Press the button to search for user.',
        it='Premi il pulsante per scegliere un utente.'
    ),
    search_button=dict(
        en="🔍 Search for user",
        it="🔍 Cerca utente",
    ),
    select_user=dict(
        en='Which user would you like to talk to?',
        it='Con quale utente vorresti parlare?'
    ),
    user_not_found=dict(
        en=(
            "Sory, but no user matches your query for\n"
            "<code>{q}</code>"
        ),
        it=(
            "Spiacente, ma nessun utente corrisponde alla ricerca per\n"
            "<code>{q}</code>"
        ),
    ),
    instructions=dict(
        en=(
            'Write a part of name, surname or username of the user you want '
            'to talk to.'
        ),
        it=(
            'Scrivi una parte del nome, cognome o username dell\'utente con '
            'cui vuoi parlare.'
        ),
    ),
    stop=dict(
        en=(
            'End session'
        ),
        it=(
            'Termina la sessione'
        ),
    ),
    user_session_ended=dict(
        en=(
            'Session with admin {u} ended.'
        ),
        it=(
            'Sessione terminata con l\'amministratore {u}.'
        ),
    ),
    user_warning=dict(
        en=(
            '{u}, admin of this bot, wants to talk to you.\n'
            'Until this session is ended by {u}, your messages will be '
            'forwarded to each other.'
        ),
        it=(
            '{u}, amministratore di questo bot, vuole parlare con te.\n'
            'Finché non chiuderà la connessione, i messaggi che scriverai '
            'qui saranno inoltrati a {u}, e ti inoltrerò i suoi.'
        ),
    ),
    # key=dict(
    #     en='',
    #     it='',
    # ),
    # key=dict(
    #     en=(
    #         ''
    #     ),
    #     it=(
    #         ''
    #     ),
    # ),
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
                                if key in (
                                    'first_name',
                                    'last_name',
                                    'username'
                                )
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
    for record in (admin_record, other_user_record, ):
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


default_admin_messages = {
    'talk_command': {
        'description': {
            'en': "Choose a user and forward messages to each other",
            'it': "Scegli un utente e il bot farà da tramite inoltrando a "
                  "ognuno i messaggi dell'altro finché non terminerai la "
                  "sessione"
        }
    },
    'restart_command': {
        'description': {
            'en': "Restart bots",
            'it': "Riavvia i bot"
        },
        'restart_scheduled_message': {
            'en': "Bots are being restarted, after pulling from repository.",
            'it': "I bot verranno riavviati in pochi secondi, caricando "
                  "prima le eventuali modifiche al codice."
        },
        'restart_completed_message': {
            'en': "<i>Restart was successful.</i>",
            'it': "<i>Restart avvenuto con successo.</i>"
        }
    },
    'stop_command': {
        'description': {
            'en': "Stop bots",
            'it': "Ferma i bot"
        },
        'text': {
            'en': "Are you sure you want to stop all bots?\n"
                  "To make them start again you will have to ssh-log "
                  "in server.\n\n"
                  "To restart the bots remotely use the /restart command "
                  "instead (before starting over, a <code>git pull</code> "
                  "is performed).",
            'it': "Sei sicuro di voler fermare i bot?\n"
                  "Per farli ripartire dovrai accedere al server.\n\n"
                  "Per far ripartire i bot da remoto usa invece il comando "
                  "/restart (prima di ripartire farò un "
                  "<code>git pull</code>)."
        }
    },
    'stop_button': {
        'stop_text': {
            'en': "Stop bots",
            'it': "Ferma i bot"
        },
        'cancel': {
            'en': "Cancel",
            'it': "Annulla"
        },
        'confirm': {
            'en': "Do you really want to stop all bots?",
            'it': "Vuoi davvero fermare tutti i bot?"
        },
        'stopping': {
            'en': "Stopping bots...",
            'it': "Arresto in corso..."
        },
        'cancelled': {
            'en': "Operation was cancelled",
            'it': "Operazione annullata"
        }
    },
    'db_command': {
        'description': {
            'en': "Ask for bot database via Telegram",
            'it': "Ricevi il database del bot via Telegram"
        },
        'not_sqlite': {
            'en': "Only SQLite databases may be sent via Telegram, since they "
                  "are single-file databases.\n"
                  "This bot has a `{db_type}` database.",
            'it': "Via Telegram possono essere inviati solo database SQLite, "
                  "in quanto composti di un solo file.\n"
                  "Questo bot ha invece un database `{db_type}`."
        },
        'file_caption': {
            'en': "Here is bot database.",
            'it': "Ecco il database!"
        },
        'db_sent': {
            'en': "Database sent.",
            'it': "Database inviato."
        }
    },
    'query_command': {
        'description': {
            'en': "Receive the result of a SQL query performed on bot "
                  "database",
            'it': "Ricevi il risultato di una query SQL sul database del bot"
        },
        'help': {
            'en': "Write a SQL query to be run on bot database.\n\n"
                  "<b>Example</b>\n"
                  "<code>/query SELECT * FROM users WHERE 0</code>",
            'it': "Invia una query SQL da eseguire sul database del bot.\n\n"
                  "<b>Esempio</b>\n"
                  "<code>/query SELECT * FROM users WHERE 0</code>"
        },
        'no_iterable': {
            'en': "No result to show was returned",
            'it': "La query non ha restituito risultati da mostrare"
        },
        'exception': {
            'en': "The query threw this error:",
            'it': "La query ha dato questo errore:"
        },
        'result': {
            'en': "Query result",
            'it': "Risultato della query"
        }
    },
    'select_command': {
        'description': {
            'en': "Receive the result of a SELECT query performed on bot "
                  "database",
            'it': "Ricevi il risultato di una query SQL di tipo SELECT "
                  "sul database del bot"
        }
    },
    'query_button': {
        'error': {
            'en': "Error!",
            'it': "Errore!"
        },
        'file_name': {
            'en': "Query result.csv",
            'it': "Risultato della query.csv"
        },
        'empty_file': {
            'en': "No result to show.",
            'it': "Nessun risultato da mostrare."
        }
    },
    'log_command': {
        'description': {
            'en': "Receive bot log file, if set",
            'it': "Ricevi il file di log del bot, se impostato"
        },
        'no_log': {
            'en': "Sorry but no log file is set.\n"
                  "To set it, use `bot.set_log_file_name` instance method or "
                  "`Bot.set_class_log_file_name` class method.",
            'it': "Spiacente ma il file di log non è stato impostato.\n"
                  "Per impostarlo, usa il metodo d'istanza "
                  "`bot.set_log_file_name` o il metodo di classe"
                  "`Bot.set_class_log_file_name`."
        },
        'sending_failure': {
            'en': "Sending log file failed!\n\n"
                  "<b>Error:</b>\n"
                  "<code>{e}</code>",
            'it': "Inviio del messaggio di log fallito!\n\n"
                  "<b>Errore:</b>\n"
                  "<code>{e}</code>"
        },
        'here_is_log_file': {
            'en': "Here is the complete log file.",
            'it': "Ecco il file di log completo."
        },
        'log_file_first_lines': {
            'en': "Here are the first {lines} lines of the log file.",
            'it': "Ecco le prime {lines} righe del file di log."
        },
        'log_file_last_lines': {
            'en': "Here are the last {lines} lines of the log file.\n"
                  "Newer lines are at the top of the file.",
            'it': "Ecco le ultime {lines} righe del file di log.\n"
                  "L'ordine è cronologico, con i messaggi nuovi in alto."
        }
    },
    'errors_command': {
        'description': {
            'en': "Receive bot error log file, if set",
            'it': "Ricevi il file di log degli errori del bot, se impostato"
        },
        'no_log': {
            'en': "Sorry but no errors log file is set.\n"
                  "To set it, use `bot.set_errors_file_name` instance method"
                  "or `Bot.set_class_errors_file_name` class method.",
            'it': "Spiacente ma il file di log degli errori non è stato "
                  "impostato.\n"
                  "Per impostarlo, usa il metodo d'istanza "
                  "`bot.set_errors_file_name` o il metodo di classe"
                  "`Bot.set_class_errors_file_name`."
        },
        'empty_log': {
            'en': "Congratulations! Errors log is empty!",
            'it': "Congratulazioni! Il log degli errori è vuoto!"
        },
        'sending_failure': {
            'en': "Sending errors log file failed!\n\n"
                  "<b>Error:</b>\n"
                  "<code>{e}</code>",
            'it': "Inviio del messaggio di log degli errori fallito!\n\n"
                  "<b>Errore:</b>\n"
                  "<code>{e}</code>"
        },
        'here_is_log_file': {
            'en': "Here is the complete errors log file.",
            'it': "Ecco il file di log degli errori completo."
        },
        'log_file_first_lines': {
            'en': "Here are the first {lines} lines of the errors log file.",
            'it': "Ecco le prime {lines} righe del file di log degli errori."
        },
        'log_file_last_lines': {
            'en': "Here are the last {lines} lines of the errors log file.\n"
                  "Newer lines are at the top of the file.",
            'it': "Ecco le ultime {lines} righe del file di log degli "
                  "errori.\n"
                  "L'ordine è cronologico, con i messaggi nuovi in alto."
        }
    },
    'maintenance_command': {
        'description': {
            'en': "Put the bot under maintenance",
            'it': "Metti il bot in manutenzione"
        },
        'maintenance_started': {
            'en': "<i>Bot has just been put under maintenance!</i>\n\n"
                  "Until further notice, it will reply to users "
                  "with the following message:\n\n"
                  "{message}",
            'it': "<i>Il bot è stato messo in manutenzione!</i>\n\n"
                  "Fino a nuovo ordine, risponderà a tutti i comandi con il "
                  "seguente messaggio\n\n"
                  "{message}"
        },
        'maintenance_ended': {
            'en': "<i>Maintenance ended!</i>",
            'it': "<i>Manutenzione terminata!</i>"
        }
    }
}


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
            for line in errors_file:
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
    maintenance_status = bot.change_maintenance_status(
        maintenance_message=get_cleaned_text(update, bot, ['maintenance'])
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


def init(bot, talk_messages=None, admin_messages=None):
    """Assign parsers, commands, buttons and queries to given `bot`."""
    if talk_messages is None:
        talk_messages = default_talk_messages
    bot.messages['talk'] = talk_messages
    if admin_messages is None:
        admin_messages = default_admin_messages
    bot.messages['admin'] = admin_messages
    with bot.db as db:
        if 'talking_sessions' not in db.tables:
            db['talking_sessions'].insert(
                dict(
                    user=0,
                    admin=0,
                    cancelled=1
                )
            )

    allowed_during_maintenance = [
        get_maintenance_exception_criterion(bot, command)
        for command in ['stop', 'restart', 'maintenance']
    ]

    @bot.additional_task(when='BEFORE')
    async def load_talking_sessions():
        sessions = []
        with bot.db as db:
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
                    bot=bot,
                    other_user_record=session['other_user_record'],
                    admin_record=session['admin_record']
                )

    @bot.command(command='/talk', aliases=[], show_in_keyboard=False,
                 description=admin_messages['talk_command']['description'],
                 authorization_level='admin')
    async def talk_command(bot, update, user_record):
        return await _talk_command(bot, update, user_record)

    @bot.button(prefix='talk:///', separator='|', authorization_level='admin')
    async def talk_button(bot, update, user_record, data):
        return await _talk_button(bot, update, user_record, data)

    @bot.command(command='/restart', aliases=[], show_in_keyboard=False,
                 description=admin_messages['restart_command']['description'],
                 authorization_level='admin')
    async def restart_command(bot, update, user_record):
        return await _restart_command(bot, update, user_record)

    @bot.additional_task('BEFORE')
    async def send_restart_messages():
        """Send restart messages at restart."""
        with bot.db as db:
            for restart_message in db['restart_messages'].find(sent=None):
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
                db['restart_messages'].update(
                    dict(
                        sent=datetime.datetime.now(),
                        id=restart_message['id']
                    ),
                    ['id'],
                    ensure=True
                )
        return

    @bot.command(command='/stop', aliases=[], show_in_keyboard=False,
                 description=admin_messages['stop_command']['description'],
                 authorization_level='admin')
    async def stop_command(bot, update, user_record):
        return await _stop_command(bot, update, user_record)

    @bot.button(prefix='stop:///', separator='|',
                description=admin_messages['stop_command']['description'],
                authorization_level='admin')
    async def stop_button(bot, update, user_record, data):
        return await _stop_button(bot, update, user_record, data)

    @bot.command(command='/db', aliases=[], show_in_keyboard=False,
                 description=admin_messages['db_command']['description'],
                 authorization_level='admin')
    async def send_bot_database(bot, update, user_record):
        return await _send_bot_database(bot, update, user_record)

    @bot.command(command='/query', aliases=[], show_in_keyboard=False,
                 description=admin_messages['query_command']['description'],
                 authorization_level='admin')
    async def query_command(bot, update, user_record):
        return await _query_command(bot, update, user_record)

    @bot.command(command='/select', aliases=[], show_in_keyboard=False,
                 description=admin_messages['select_command']['description'],
                 authorization_level='admin')
    async def select_command(bot, update, user_record):
        return await _query_command(bot, update, user_record)

    @bot.button(prefix='db_query:///', separator='|',
                description=admin_messages['query_command']['description'],
                authorization_level='admin')
    async def query_button(bot, update, user_record, data):
        return await _query_button(bot, update, user_record, data)

    @bot.command(command='/log', aliases=[], show_in_keyboard=False,
                 description=admin_messages['log_command']['description'],
                 authorization_level='admin')
    async def log_command(bot, update, user_record):
        return await _log_command(bot, update, user_record)

    @bot.command(command='/errors', aliases=[], show_in_keyboard=False,
                 description=admin_messages['errors_command']['description'],
                 authorization_level='admin')
    async def errors_command(bot, update, user_record):
        return await _errors_command(bot, update, user_record)

    for exception in allowed_during_maintenance:
        bot.allow_during_maintenance(exception)

    @bot.command(command='/maintenance', aliases=[], show_in_keyboard=False,
                 description=admin_messages[
                    'maintenance_command']['description'],
                 authorization_level='admin')
    async def maintenance_command(bot, update, user_record):
        return await _maintenance_command(bot, update, user_record)
