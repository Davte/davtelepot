"""Bot support for multiple languages."""

# Standard library modules
import asyncio
from collections import OrderedDict
import logging

# Project modules
from .messages import default_language_messages
from .utilities import extract, make_button, make_inline_keyboard


class MultiLanguageObject(object):
    """Make bot inherit from this class to make it support multiple languages.

    Call MultiLanguageObject().get_message(
        field1, field2, ...,
        update, user_record, language,
        format_kwarg1, format_kwarg2, ...
    ) to get the corresponding message in the selected language.
    """

    def __init__(self, *args,
                 messages=None,
                 default_language='en',
                 missing_message="Invalid message!",
                 supported_languages=None,
                 **kwargs):
        """Instantiate MultiLanguageObject, setting its attributes."""
        if messages is None:
            messages = dict()
        self.messages = messages
        self._default_language = default_language
        self._missing_message = missing_message
        if supported_languages is None:
            supported_languages = OrderedDict(
                {
                    self.default_language: OrderedDict(
                        name=self.default_language,
                        flag=''
                    )
                }
            )
        self._supported_languages = supported_languages

    @property
    def default_language(self):
        """Return default language."""
        return self._default_language

    def set_default_language(self, language):
        """Set default language."""
        self._default_language = language

    @property
    def missing_message(self):
        """Return this message when a proper message can not be found."""
        return self._missing_message

    def set_missing_message(self, message):
        """Set message to be returned where a proper one can not be found."""
        self._missing_message = message

    @property
    def supported_languages(self):
        """Return dict of supported languages.

        If it is not set, return default language only without flag.
        """
        return self._supported_languages

    def add_supported_languages(self, languages):
        """Add some `languages` to supported languages.

        Example
        ```python
        languages = {
            'en': {
                'flag': '🇬🇧',
                'name': 'English'
            },
            'it': {
                'flag': '🇮🇹',
                'name': 'Italiano'
            }
        }
        ```
        """
        assert type(languages) is dict, "Supported languages must be in a dict"
        if len(languages) == 0:
            return
        if self._supported_languages is None:
            self._supported_languages = dict()
        self._supported_languages.update(languages)

    def get_language(self, update=None, user_record=None, language=None):
        """Get language.

        Language will be the first non-null value of this list:
        - `language` parameter
        - `user_record['selected_language_code']`: language selected by user
        - `update['language_code']`: language of incoming telegram update
        - Fallback to default language if none of the above fits
        """
        if user_record is None:
            user_record = dict()
        if update is None:
            update = dict()
        if (
            language is None
            and 'selected_language_code' in user_record
        ):
            language = user_record['selected_language_code']
        if (
            language is None
            and 'from' in update
            and 'language_code' in update['from']
        ):
            language = update['from']['language_code']
        return language or self.default_language

    def get_message(self, *fields, update=None, user_record=None,
                    default_message=None, language=None, messages=None, **format_kwargs):
        """Given a list of strings (`fields`), return proper message.

        Language will be determined by `get_language` method.
        `format_kwargs` will be passed to format function on the result.
        """
        # Choose language
        if update is None:
            update = dict()
        if user_record is None:
            user_record = dict()
        language = self.get_language(
            update=update,
            user_record=user_record,
            language=language
        )
        # Find result for `language`
        result = messages or self.messages
        for field in fields:
            if field not in result:
                if not default_message:
                    logging.debug(
                        "Please define self.message{f}".format(
                            f=''.join(
                                '[\'{field}\']'.format(
                                    field=field
                                )
                                for field in fields
                            )
                        )
                    )
                return default_message or self.missing_message
            result = result[field]
        if language not in result:
            # For specific languages, try generic ones
            language = language.partition('-')[0]
            if language not in result:
                language = 'en'
                if language not in result:
                    if not default_message:
                        logging.debug(
                            "Please define self.message{f}['en']".format(
                                f=''.join(
                                    '[\'{field}\']'.format(
                                        field=field
                                    )
                                    for field in fields
                                )
                            )
                        )
                    return default_message or self.missing_message
        if type(result) is str:
            return result
        return result[language].format(
            **format_kwargs
        )


async def _language_command(bot, update, user_record):
    text, reply_markup = get_language_panel(
        bot=bot,
        update=update,
        user_record=user_record
    )
    return dict(
        text=text,
        reply_markup=reply_markup
    )


def get_language_panel(bot, update, user_record):
    """Get language panel for user.

    Return text and reply_markup of the message about user's language
        preferences.
    """
    text = bot.get_message(
        'language', 'language_panel', 'text',
        update=update, user_record=user_record,
    )
    text += "\n"
    if 'selected_language_code' in user_record:
        current_code = user_record['selected_language_code']
    else:
        current_code = None
    for code, language in bot.supported_languages.items():
        text += (f"\n{'✅' if code == current_code else '☑️'} "
                 f"{language['name']} {language['flag']}")
    reply_markup = make_inline_keyboard(
        [
            make_button(
                text=(
                    f"{'✅' if code == current_code else '☑️'} "
                    f"{language['name']} {language['flag']}"
                ),
                prefix='lang:///',
                delimiter='|',
                data=['set', code]
            )
            for code, language in bot.supported_languages.items()
        ],
        3
    )
    return text, reply_markup


async def _language_button(bot, update, user_record, data):
    result, text, reply_markup = '', '', None
    if len(data) > 1 and data[0] == 'set':
        # If message is already updated, do not update it
        if (
            'selected_language_code' in user_record
            and data[1] == user_record['selected_language_code']
            and data[1] in bot.supported_languages
            and bot.supported_languages[data[1]]['flag'] in extract(
                update['message']['text'],
                starter='✅',
                ender='\n'
            )
        ):
            return
        # If database-stored information is not updated, update it
        if (
            'selected_language_code' not in user_record
            or data[1] != user_record['selected_language_code']
        ):
            with bot.db as db:
                db['users'].update(
                    dict(
                        selected_language_code=data[1],
                        id=user_record['id']
                    ),
                    ['id'],
                    ensure=True
                )
                user_record['selected_language_code'] = data[1]
        if 'chat' in update['message'] and update['message']['chat']['id'] > 0:
            asyncio.ensure_future(
                bot.send_message(
                    text=bot.get_message(
                        'language', 'language_button', 'language_set',
                        update=update['message'], user_record=user_record
                    ),
                    chat_id=update['message']['chat']['id']
                )
            )
    if len(data) == 0 or data[0] in ('show', 'set'):
        text, reply_markup = get_language_panel(bot=bot, update=update, user_record=user_record)
    if text:
        return dict(
            text=result,
            edit=dict(
                text=text,
                reply_markup=reply_markup
            )
        )
    return result


def init(telegram_bot,
         language_messages=None,
         show_in_keyboard=True,
         supported_languages=None):
    """Set language support to `bot`."""
    if supported_languages is None:
        supported_languages = {}
    from .bot import Bot
    assert isinstance(telegram_bot, MultiLanguageObject), (
        "Bot must be a MultiLanguageObject subclass in order to support "
        "multiple languages."
    )
    assert isinstance(telegram_bot, Bot), (
        "Bot must be a davtelepot Bot subclass in order to support "
        "command and button decorators."
    )
    if language_messages is None:
        language_messages = default_language_messages
    telegram_bot.messages['language'] = language_messages
    telegram_bot.add_supported_languages(supported_languages)

    aliases = [
        alias
        for alias in language_messages[
            'language_command']['alias'].values()
    ]

    @telegram_bot.command(
        command='/language',
        aliases=aliases,
        reply_keyboard_button=language_messages['language_command'][
            'reply_keyboard_button'],
        show_in_keyboard=show_in_keyboard,
        description=language_messages['language_command']['description'],
        authorization_level='everybody'
    )
    async def language_command(bot, update, user_record):
        return await _language_command(bot, update, user_record)

    @telegram_bot.button(
        prefix='lang:///',
        separator='|',
        description=language_messages['language_button']['description'],
        authorization_level='everybody'
    )
    async def language_button(bot, update, user_record, data):
        return await _language_button(bot, update, user_record, data)
