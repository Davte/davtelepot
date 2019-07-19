"""WARNING: this is only a legacy module.

For newer versions use `administration_tools.py`.

----------
Administration tools for telegram bots.

Usage:
```
import davtelepot
my_bot = davtelepot.Bot.get('my_token', 'my_database.db')
davtelepot.admin_tools.init(my_bot)
```
"""

# Third party modules
from davtelepot.utilities import (
    async_wrapper, Confirmator, get_cleaned_text, get_user, escape_html_chars,
    extract, line_drawing_unordered_list, make_button, make_inline_keyboard,
    remove_html_tags
)


TALK_MESSAGES = dict(
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
            user_record = db['users'].find_one(
                id=session_record['user']
            )
        await end_session(
            bot=bot,
            user_record=user_record,
            admin_record=admin_record
        )
    else:
        bot.set_individual_text_message_handler(
            await async_wrapper(
                _forward_to,
                bot=bot,
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


def get_talk_panel(update, bot, text=''):
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
                        """SELECT *
                        FROM users
                        WHERE COALESCE(
                            first_name || last_name || username,
                            last_name || username,
                            first_name || username,
                            username,
                            first_name || last_name,
                            last_name,
                            first_name
                        ) LIKE '%{username}%'
                        ORDER BY LOWER(
                            COALESCE(
                                first_name || last_name || username,
                                last_name || username,
                                first_name || username,
                                username,
                                first_name || last_name,
                                last_name,
                                first_name
                            )
                        )
                        LIMIT 26
                        """.format(
                            username=text
                        )
                    )
                )
    if len(text) == 0:
        text = (
            bot.get_message(
                'talk',
                'help_text',
                update=update,
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
                        update=update
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
                        update=update
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
                update=update
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


async def _talk_command(update, bot):
    text = get_cleaned_text(
        update,
        bot,
        ['talk']
    )
    text, reply_markup = get_talk_panel(update, bot, text)
    return dict(
        text=text,
        parse_mode='HTML',
        reply_markup=reply_markup,
    )


async def start_session(bot, user_record, admin_record):
    """Start talking session between user and admin.

    Register session in database, so it gets loaded before message_loop starts.
    Send a notification both to admin and user, set custom parsers and return.
    """
    with bot.db as db:
        db['talking_sessions'].insert(
            dict(
                user=user_record['id'],
                admin=admin_record['id'],
                cancelled=0
            )
        )
    await bot.send_message(
        chat_id=user_record['telegram_id'],
        text=bot.get_message(
            'talk', 'user_warning',
            user_record=user_record,
            u=get_user(admin_record)
        )
    )
    await bot.send_message(
        chat_id=admin_record['telegram_id'],
        text=bot.get_message(
            'talk', 'admin_warning',
            user_record=admin_record,
            u=get_user(user_record)
        ),
        reply_markup=make_inline_keyboard(
            [
                make_button(
                    bot.get_message(
                        'talk', 'stop',
                        user_record=admin_record
                    ),
                    prefix='talk:///',
                    data=['stop', user_record['id']]
                )
            ]
        )
    )
    bot.set_individual_text_message_handler(
        await async_wrapper(
            _forward_to,
            bot=bot,
            sender=user_record['telegram_id'],
            addressee=admin_record['telegram_id'],
            is_admin=False
        ),
        user_record['telegram_id']
    )
    bot.set_individual_text_message_handler(
        await async_wrapper(
            _forward_to,
            bot=bot,
            sender=admin_record['telegram_id'],
            addressee=user_record['telegram_id'],
            is_admin=True
        ),
        admin_record['telegram_id']
    )
    return


async def end_session(bot, user_record, admin_record):
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
        chat_id=user_record['telegram_id'],
        text=bot.get_message(
            'talk', 'user_session_ended',
            user_record=user_record,
            u=get_user(admin_record)
        )
    )
    await bot.send_message(
        chat_id=admin_record['telegram_id'],
        text=bot.get_message(
            'talk', 'admin_session_ended',
            user_record=admin_record,
            u=get_user(user_record)
        ),
    )
    for record in (admin_record, user_record, ):
        bot.remove_individual_text_message_handler(record['telegram_id'])
    return


async def _talk_button(update, bot):
    telegram_id = update['from']['id']
    command, *arguments = extract(update['data'], '///').split('|')
    result, text, reply_markup = '', '', None
    if command == 'search':
        bot.set_individual_text_message_handler(
            await async_wrapper(
                _talk_command,
                bot=bot
            ),
            update
        )
        text = bot.get_message(
            'talk', 'instructions',
            update=update
        )
        reply_markup = None
    elif command == 'select':
        if (
            len(arguments) < 1
            or not arguments[0].isnumeric()
        ):
            result = "Errore!"
        else:
            with bot.db as db:
                user_record = db['users'].find_one(
                    id=int(arguments[0])
                )
                admin_record = db['users'].find_one(
                    telegram_id=telegram_id
                )
            await start_session(
                bot,
                user_record=user_record,
                admin_record=admin_record
            )
    elif command == 'stop':
        if (
            len(arguments) < 1
            or not arguments[0].isnumeric()
        ):
            result = "Errore!"
        elif not Confirmator.get('stop_bots').confirm(telegram_id):
            result = bot.get_message(
                'talk', 'end_session',
                update=update,
            )
        else:
            with bot.db as db:
                user_record = db['users'].find_one(
                    id=int(arguments[0])
                )
                admin_record = db['users'].find_one(
                    telegram_id=telegram_id
                )
            await end_session(
                bot,
                user_record=user_record,
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


def init(bot):
    """Assign parsers, commands, buttons and queries to given `bot`."""
    if not hasattr(bot, 'messages'):
        bot.messages = dict()
    bot.messages['talk'] = TALK_MESSAGES
    with bot.db as db:
        if 'talking_sessions' not in db.tables:
            db['talking_sessions'].insert(
                dict(
                    user=0,
                    admin=0,
                    cancelled=1
                )
            )

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
                        user_record=db['users'].find_one(
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
                    user_record=session['user_record'],
                    admin_record=session['admin_record']
                )

    @bot.command(command='/talk', aliases=[], show_in_keyboard=False,
                 descr="Choose a user and forward messages to each other.",
                 auth='admin')
    async def talk_command(update):
        return await _talk_command(update, bot)

    @bot.button(data='talk:///', auth='admin')
    async def talk_button(update):
        return await _talk_button(update, bot)
    return
