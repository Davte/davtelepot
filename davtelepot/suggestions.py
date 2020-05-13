"""Receive structured suggestions from bot users."""

# Standard library modules
import asyncio
import datetime

# Third party modules
import davtelepot

# Project modules
from .messages import default_suggestion_messages
from .utilities import (
    async_wrapper, get_cleaned_text, make_button,
    make_inline_keyboard, send_csv_file
)


async def _handle_suggestion_message(bot: davtelepot.bot.Bot, update, user_record, try_no=1,
                                     suggestion_prefixes=None):
    if suggestion_prefixes is None:
        suggestion_prefixes = []
    suggestion_prefixes = [prefix.strip('/') for prefix in suggestion_prefixes]
    user_id = user_record['id']
    telegram_id = user_record['telegram_id']
    text = get_cleaned_text(
        update,
        bot,
        suggestion_prefixes
    )
    text = text.strip(' /')[:1500]
    if not text:
        if try_no < 2:
            bot.set_individual_text_message_handler(
                await async_wrapper(
                    _handle_suggestion_message,
                    bot=bot,
                    update=update,
                    user_record=user_record,
                    try_no=(try_no + 1),
                    suggestion_prefixes=suggestion_prefixes
                ),
                user_id=telegram_id
            )
            return dict(
                chat_id=telegram_id,
                reply_markup=dict(
                    force_reply=True
                ),
                text=bot.get_message(
                    'suggestions', 'suggestions_command', 'prompt_text',
                    update=update, user_record=user_record
                )
            )
        return bot.get_message(
            'suggestions', 'suggestions_command', 'invalid_suggestion',
            update=update, user_record=user_record
        )
    if text.lower() in [
        cancel_message
        for language in bot.messages['suggestions']['suggestions_command']['cancel_messages'].values()
        for cancel_message in language
    ]:
        return bot.get_message(
            'suggestions', 'suggestions_command', 'operation_cancelled',
            update=update, user_record=user_record
        )
    created = datetime.datetime.now()
    with bot.db as db:
        db['suggestions'].insert(
            dict(
                user_id=user_id,
                suggestion=text,
                created=created
            ),
            ensure=True
        )
        suggestion_id = db['suggestions'].find_one(
            user_id=user_id,
            created=created
        )['id']
    text = bot.get_message(
        'suggestions', 'suggestions_command', 'entered_suggestion', 'text',
        suggestion=text,
        update=update, user_record=user_record
    )
    reply_markup = make_inline_keyboard(
        [
            make_button(
                bot.get_message(
                    'suggestions', 'suggestions_command', 'entered_suggestion', 'buttons', 'send',
                    update=update, user_record=user_record
                ),
                prefix='suggest:///',
                delimiter='|',
                data=['confirm', suggestion_id]
            ),
            make_button(
                bot.get_message(
                    'suggestions', 'suggestions_command', 'entered_suggestion', 'buttons', 'cancel',
                    update=update, user_record=user_record
                ),
                prefix='suggest:///',
                delimiter='|',
                data=['cancel']
            )
        ]
    )
    return dict(
        chat_id=telegram_id,
        text=text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def _suggestions_button(bot: davtelepot.bot.Bot, update, user_record, data):
    command = data[0]
    user_id = update['from']['id']
    result, text, reply_markup = '', '', None
    if command in ['new']:
        bot.set_individual_text_message_handler(
            _handle_suggestion_message,
            user_id=user_id
        )
        asyncio.ensure_future(
            bot.send_message(
                chat_id=user_id,
                reply_markup=dict(
                    force_reply=True
                ),
                text=bot.get_message(
                    'suggestions', 'suggestions_command', 'prompt_text',
                    update=update, user_record=user_record
                )
            )
        )
        result = bot.get_message(
            'suggestions', 'suggestions_command', 'prompt_popup',
            update=update, user_record=user_record
        )
    elif command in ['cancel']:
        result = text = bot.get_message(
            'suggestions', 'suggestions_command', 'operation_cancelled',
            update=update, user_record=user_record
        )
        reply_markup = None
    elif command in ['confirm'] and len(data) > 1:
        suggestion_id = data[1]
        when = datetime.datetime.now()
        with bot.db as db:
            registered_user = db['users'].find_one(telegram_id=user_id)
            db['suggestions'].update(
                dict(
                    id=suggestion_id,
                    sent=when
                ),
                ['id'],
                ensure=True
            )
            suggestion_text = db['suggestions'].find_one(
                id=suggestion_id
            )['suggestion']
        suggestion_message = bot.get_message(
            'suggestions', 'suggestions_command', 'received_suggestion', 'text',
            user=bot.Role.get_user_role_text(user_record=registered_user),
            suggestion=suggestion_text,
            bot=bot,
            update=update, user_record=user_record,
        )
        for admin in bot.administrators:
            when += datetime.timedelta(seconds=1)
            asyncio.ensure_future(
                bot.send_message(
                    chat_id=admin['telegram_id'],
                    text=suggestion_message,
                    parse_mode='HTML'
                )
            )
        reply_markup = make_inline_keyboard(
            [
                make_button(
                    text=bot.get_message(
                        'suggestions', 'suggestions_command', 'received_suggestion', 'buttons', 'new',
                        bot=bot,
                        update=update, user_record=user_record,
                    ),
                    prefix='suggest:///',
                    delimiter='|',
                    data=['new']
                )
            ],
            1
        )
        result = bot.get_message(
            'suggestions', 'suggestions_command', 'suggestion_sent', 'popup',
            suggestion=suggestion_text, bot=bot,
            update=update, user_record=user_record,
        )
        text = bot.get_message(
            'suggestions', 'suggestions_command', 'suggestion_sent', 'text',
            suggestion=suggestion_text, bot=bot,
            update=update, user_record=user_record,
        )
    if text:
        return dict(
            text=result,
            edit=dict(
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        )
    return result


async def _see_suggestions(bot: davtelepot.bot.Bot, update, user_record):
    chat_id = update['from']['id']
    query = (
        "SELECT u.username, u.privileges, s.created, s.sent, s.suggestion "
        "FROM suggestions s "
        "LEFT JOIN users u "
        "ON u.id = s.user_id "
        "ORDER BY s.created"
    )
    await send_csv_file(
        bot=bot,
        chat_id=chat_id,
        query=query,
        caption=bot.get_message(
            'suggestions', 'suggestions_button', 'file_caption',
            user_record=user_record, update=update
        ),
        file_name=bot.get_message(
            'suggestions', 'suggestions_button', 'file_name',
            user_record=user_record, update=update
        ),
        update=update,
        user_record=user_record
    )


def init(telegram_bot: davtelepot.bot.Bot, suggestion_messages=None):
    """Set suggestion handling for `bot`."""
    if suggestion_messages is None:
        suggestion_messages = default_suggestion_messages
    telegram_bot.messages['suggestions'] = suggestion_messages
    suggestion_prefixes = (
        list(suggestion_messages['suggestions_command']['reply_keyboard_button'].values())
        + [suggestion_messages['suggestions_command']['command']]
        + suggestion_messages['suggestions_command']['aliases']
    )

    db = telegram_bot.db
    types = db.types
    if 'suggestions' not in db.tables:
        table = db.create_table(
            table_name='suggestions'
        )
        table.create_column(
            'user_id',
            types.integer
        )
        table.create_column(
            'suggestion',
            types.text
        )
        table.create_column(
            'created',
            types.datetime
        )
        table.create_column(
            'sent',
            types.datetime
        )

    @telegram_bot.command(command=suggestion_messages['suggestions_command']['command'],
                          aliases=suggestion_messages['suggestions_command']['aliases'],
                          reply_keyboard_button=(
                                  suggestion_messages['suggestions_command']['reply_keyboard_button']
                          ),
                          show_in_keyboard=True,
                          description=suggestion_messages['suggestions_command']['description'],
                          authorization_level='everybody')
    async def suggestions_command(bot, update, user_record):
        return await _handle_suggestion_message(
            bot=bot,
            update=update,
            user_record=user_record,
            try_no=1,
            suggestion_prefixes=suggestion_prefixes
        )

    @telegram_bot.button(prefix='suggest:///', separator='|',
                         authorization_level='everybody')
    async def suggestions_button(bot, update, user_record, data):
        return await _suggestions_button(
            bot=bot, update=update,
            user_record=user_record, data=data
        )

    @telegram_bot.command(command=suggestion_messages['see_suggestions']['command'],
                          aliases=suggestion_messages['see_suggestions']['aliases'],
                          description=(
                                  suggestion_messages['see_suggestions']['description']
                          ),
                          authorization_level='admin')
    async def see_suggestions(bot, update, user_record):
        return await _see_suggestions(bot, update, user_record)
