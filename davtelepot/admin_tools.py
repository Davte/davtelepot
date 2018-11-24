"""Administration tools for telegram bots.

Usage:
```
import davtelepot
my_bot = davtelepot.Bot.get('my_token', 'my_database.db')
davtelepot.admin_tools.init(my_bot)
```
"""

# Third party modules
from davteutil.utilities import (
    get_cleaned_text, get_user, escape_html_chars, extract,
    line_drawing_unordered_list, make_button, make_inline_keyboard,
    remove_html_tags
)


TALK_MESSAGES = dict(
    confirm_user_button=dict(
        en='Talk to {u}?',
        it='Parla con {u}?'
    ),
    confirm_user_text=dict(
        en='Do you want to talk to {u}?',
        it='Vuoi parlare con {u}?'
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
    # key=dict(
    #     en='',
    #     it='',
    # ),
)


def get_talk_panel(text, bot):
    """Return text and reply markup of talk panel.

    Get 'user_id' as string, username as string or void string for main menu.
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
                        """.format(
                            username=text
                        )
                    )
                )
    if len(users) == 0:
        text = (
            bot.get_message('talk', 'user_not_found', update=update)
        ).format(
            q=escape_html_chars(
                remove_html_tags(text)
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
    elif len(users) == 1:
        user = users[0]
        text = (
            bot.get_message(
                'talk', 'confirm_user_text',
                update=update
            )
        ).format(
            u=get_user(user)
        )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    (
                        bot.get_message(
                            'talk', 'confirm_user_button',
                            update=update
                        )
                    ).format(
                        u=get_user(user)
                    )
                )
            ],
            1
        )
    else:
        text = "{header}\n\n{u}".format(
            header=bot.get_message(
                'talk', 'select_user',
                update=update
            ),
            u=line_drawing_unordered_list(
                [
                    get_user(user)
                    for user in users
                ]
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
                for user in users
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
    text, reply_markup = get_talk_panel(text, bot)
    return


async def _talk_button(update, bot):
    telegram_id = update['from']['id']
    command, *arguments = extract(update['data'], '///').split('|')
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
        with botd.db as db:
            for session in db.query(
                """SELECT *
                FROM talking_sessions
                WHERE NOT cancelled
                """
            ):
                pass  # Set cutom_parser

    @bot.command(command='/talk', aliases=[], show_in_keyboard=False,
                 descr="Choose a user and forward messages to each other.",
                 auth='admin')
    async def talk_command(update):
        return await _talk_command(update, bot)

    @bot.button(data='talk:///', auth='admin')
    async def talk_button(update):
        return await _talk_button(update, bot)
    return
