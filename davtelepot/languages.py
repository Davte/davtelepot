"""Bot support for multiple languages."""

# Standard library modules
import logging

# Project modules
from .utilities import extract


class MultiLanguageObject(object):
    """Make bot inherit from this class to make it support multiple languages.

    Call MultiLanguage().get_message(
        field1, field2, ...,
        update, user_record, language,
        format_kwarg1, format_kwarg2, ...
    ) to get the corresponding message in the selected language.
    """

    def __init__(self):
        """Instantiate MultiLanguage object, setting self.messages."""
        self.messages = dict()

    def get_message(self, *fields, update=dict(), user_record=dict(),
                    language=None, **format_kwargs):
        """Given a list of strings (`fields`), return proper message.

        Language will be selected in this order:
        - `language` parameter
        - `user_record['selected_language_code']`: language selected by user
        - `update['language_code']`: language of incoming telegram update
        - Fallback to English if none of the above fits

        `format_kwargs` will be passed to format function on the result.
        """
        # Choose language
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
        if language is None:
            language = 'en'
        # Find result for `language`
        result = self.messages
        for field in fields:
            if field not in result:
                logging.error(
                    "Please define self.message{f}".format(
                        f=''.join(
                            '[\'{field}\']'.format(
                                field=field
                            )
                            for field in fields
                        )
                    )
                )
                return "Invalid message!"
            result = result[field]
        if language not in result:
            # For specific languages, try generic ones
            language = extract(
                language,
                ender='-'
            )
            if language not in result:
                language = 'en'
                if language not in result:
                    logging.error(
                        "Please define self.message{f}['en']".format(
                            f=''.join(
                                '[\'{field}\']'.format(
                                    field=field
                                )
                                for field in fields
                            )
                        )
                    )
                    return "Invalid message!"
        return result[language].format(
            **format_kwargs
        )
