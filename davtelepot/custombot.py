"""Subclass of third party telepot.aio.Bot, providing the following features.

- It prevents hitting Telegram flood limits by waiting
    between text and photo messages.
- It provides command, parser, button and other decorators to associate
    common Telegram actions with custom handlers.
- It supports multiple bots running in the same script
    and allows communications between them
    as well as complete independency from each other.
- Each bot is associated with a sqlite database
    using dataset, a third party library.

Please note that you need Python3.5+ to run async code
Check requirements.txt for third party dependencies.
"""

# Standard library modules
import asyncio
import datetime
import io
import logging
import os

# Third party modules
import dataset
import telepot
import telepot.aio

# Project modules
from davteutil.utilities import (
    Gettable, escape_html_chars, get_cleaned_text, line_drawing_unordered_list,
    make_lines_of_buttons, markdown_check, MyOD, pick_most_similar_from_list,
    remove_html_tags, sleep_until
)


def split_text_gracefully(text, limit, parse_mode):
    r"""Split text if it hits telegram limits for text messages.

    Split at `\n` if possible.
    Add a `[...]` at the end and beginning of split messages,
    with proper code markdown.
    """
    text = text.split("\n")[::-1]
    result = []
    while len(text) > 0:
        temp = []
        while len(text) > 0 and len("\n".join(temp + [text[-1]])) < limit:
            temp.append(text.pop())
        if len(temp) == 0:
            temp.append(text[-1][:limit])
            text[-1] = text[-1][limit:]
        result.append("\n".join(temp))
    if len(result) > 1:
        for i in range(1, len(result)):
            result[i] = "{tag[0]}[...]{tag[1]}\n{text}".format(
                tag=(
                    ('`', '`') if parse_mode == 'Markdown'
                    else ('<code>', '</code>') if parse_mode.lower() == 'html'
                    else ('', '')
                ),
                text=result[i]
            )
            result[i-1] = "{text}\n{tag[0]}[...]{tag[1]}".format(
                tag=(
                    ('`', '`') if parse_mode == 'Markdown'
                    else ('<code>', '</code>') if parse_mode.lower() == 'html'
                    else ('', '')
                ),
                text=result[i-1]
            )
    return result


def make_inline_query_answer(answer):
    """Return an article-type answer to inline query.

    Takes either a string or a dictionary and returns a list.
    """
    if type(answer) is str:
        answer = dict(
            type='article',
            id=0,
            title=remove_html_tags(answer),
            input_message_content=dict(
                message_text=answer,
                parse_mode='HTML'
            )
        )
    if type(answer) is dict:
        answer = [answer]
    return answer


class Bot(telepot.aio.Bot, Gettable):
    """telepot.aio.Bot (async Telegram bot framework) convenient subclass.

    === General functioning ===
    - While Bot.run() coroutine is executed, HTTP get requests are made
        to Telegram servers asking for new messages for each Bot instance.
    - Each message causes the proper Bot instance method coroutine
        to be awaited, according to its flavour (see routing_table)
        -- For example, chat messages cause `Bot().on_chat_message(message)`
            to be awaited.
    - This even-processing coroutine ensures the proper handling function
        a future and returns.
        -- That means that simpler tasks are completed before slower ones,
            since handling functions are not awaited but scheduled
            by `asyncio.ensure_future(handling_function(...))`
        -- For example, chat text messages are handled by
            `handle_text_message`, which looks for the proper function
            to elaborate the request (in bot's commands and parsers)
    - The handling function evaluates an answer, depending on the message
        content, and eventually provides a reply
        -- For example, `handle_text_message` sends its
            answer via `send_message`
    - All Bot.instances run simultaneously and faster requests
        are completed earlier.
    - All uncaught events are ignored.
    """

    instances = {}
    stop = False
    # Cooldown time between sent messages, to prevent hitting
    # Telegram flood limits
    # Current limits: 30 total messages sent per second,
    # 1 message per second per chat, 20 messages per minute per group
    COOLDOWN_TIME_ABSOLUTE = datetime.timedelta(seconds=1/30)
    COOLDOWN_TIME_PER_CHAT = datetime.timedelta(seconds=1)
    MAX_GROUP_MESSAGES_PER_MINUTE = 20
    # Max length of text field for a Telegram message (UTF-8 text)
    TELEGRAM_MESSAGES_MAX_LEN = 4096
    _path = '.'
    _unauthorized_message = None
    _unknown_command_message = None
    _maintenance_message = None
    _default_inline_query_answer = [
        dict(
            type='article',
            id=0,
            title="I cannot answer this query, sorry",
            input_message_content=dict(
                message_text="I'm sorry "
                "but I could not find an answer for your query."
            )
        )
    ]

    def __init__(self, token, db_name=None):
        """Instantiate Bot instance, given a token and a db name."""
        super().__init__(token)
        self.routing_table = {
            'chat': self.on_chat_message,
            'inline_query': self.on_inline_query,
            'chosen_inline_result': self.on_chosen_inline_result,
            'callback_query': self.on_callback_query
        }
        self.chat_message_handlers = {
            'text': self.handle_text_message,
            'pinned_message': self.handle_pinned_message,
            'photo': self.handle_photo_message
        }
        if db_name:
            self.db_url = 'sqlite:///{name}{ext}'.format(
                name=db_name,
                ext='.db' if not db_name.endswith('.db') else ''
            )
        self._unauthorized_message = None
        self.authorization_function = lambda update, authorization_level: True
        self.get_chat_id = lambda update: (
            update['message']['chat']['id']
            if 'message' in update
            else update['chat']['id']
        )
        self.commands = dict()
        self.callback_handlers = dict()
        self.inline_query_handlers = MyOD()
        self._default_inline_query_answer = None
        self.chosen_inline_result_handlers = dict()
        self.aliases = MyOD()
        self.parsers = MyOD()
        self.custom_parsers = dict()
        self.custom_photo_parsers = dict()
        self.bot_name = None
        self.default_reply_keyboard_elements = []
        self._default_keyboard = dict()
        self.run_before_loop = []
        self.run_after_loop = []
        self.to_be_obscured = []
        self.to_be_destroyed = []
        self.last_sending_time = dict(
            absolute=(
                datetime.datetime.now()
                - self.__class__.COOLDOWN_TIME_ABSOLUTE
            )
        )
        self._maintenance = False
        self._maintenance_message = None
        self.chat_actions = dict(
            pinned=MyOD()
        )

    @property
    def name(self):
        """Bot name."""
        return self.bot_name

    @property
    def path(self):
        """custombot.py file path."""
        return self.__class__._path

    @property
    def db(self):
        """Connect to bot's database.

        It must be used inside a with statement: `with bot.db as db`
        """
        if self.db_url:
            return dataset.connect(self.db_url)

    @property
    def default_keyboard(self):
        """Get the default keyboard.

        It is sent when reply_markup is left blank and chat is private.
        """
        return self._default_keyboard

    @property
    def default_inline_query_answer(self):
        """Answer to be returned if inline query returned None."""
        if self._default_inline_query_answer:
            return self._default_inline_query_answer
        return self.__class__._default_inline_query_answer

    @property
    def unauthorized_message(self):
        """Return this if user is unauthorized to make a request.

        If instance message is not set, class message is returned.
        """
        if self._unauthorized_message:
            return self._unauthorized_message
        return self.__class__._unauthorized_message

    @property
    def unknown_command_message(self):
        """Message to be returned if user sends an unknown command in private chat.

        If instance message is not set, class message is returned.
        """
        if self._unknown_command_message:
            return self._unknown_command_message
        return self.__class__._unknown_command_message

    @property
    def maintenance(self):
        """Check whether bot is under maintenance.

        While under maintenance, bot will reply with
            `self.maintenance_message` to any request, with few exceptions.
        """
        return self._maintenance

    @property
    def maintenance_message(self):
        """Message to be returned if bot is under maintenance.

        If instance message is not set, class message is returned.
        """
        if self._maintenance_message:
            return self._maintenance_message
        if self.__class__.maintenance_message:
            return self.__class__._maintenance_message
        return "Bot is currently under maintenance! Retry later please."

    @classmethod
    def set_class_path(csl, path):
        """Set class path, where files will be looked for.

        For example, if send_photo receives `photo='mypic.png'`,
            it will parse it as `'{path}/mypic.png'.format(path=self.path)`
        """
        csl._path = path

    @classmethod
    def set_class_unauthorized_message(csl, unauthorized_message):
        """Set class unauthorized message.

        It will be returned if user is unauthorized to make a request.
        """
        csl._unauthorized_message = unauthorized_message

    @classmethod
    def set_class_unknown_command_message(cls, unknown_command_message):
        """Set class unknown command message.

        It will be returned if user sends an unknown command in private chat.
        """
        cls._unknown_command_message = unknown_command_message

    @classmethod
    def set_class_maintenance_message(cls, maintenance_message):
        """Set class maintenance message.

        It will be returned if bot is under maintenance.
        """
        cls._maintenance_message = maintenance_message

    @classmethod
    def set_class_default_inline_query_answer(cls,
                                              default_inline_query_answer):
        """Set class default inline query answer.

        It will be returned if an inline query returned no answer.
        """
        cls._default_inline_query_answer = default_inline_query_answer

    def set_unauthorized_message(self, unauthorized_message):
        """Set instance unauthorized message.

        If instance message is None, default class message is used.
        """
        self._unauthorized_message = unauthorized_message

    def set_unknown_command_message(self, unknown_command_message):
        """Set instance unknown command message.

        It will be returned if user sends an unknown command in private chat.
        If instance message is None, default class message is used.
        """
        self._unknown_command_message = unknown_command_message

    def set_maintenance_message(self, maintenance_message):
        """Set instance maintenance message.

        It will be returned if bot is under maintenance.
        If instance message is None, default class message is used.
        """
        self._maintenance_message = maintenance_message

    def set_default_inline_query_answer(self, default_inline_query_answer):
        """Set a custom default_inline_query_answer.

        It will be returned when no answer is found for an inline query.
        If instance answer is None, default class answer is used.
        """
        if type(default_inline_query_answer) in (str, dict):
            default_inline_query_answer = make_inline_query_answer(
                default_inline_query_answer
            )
        if type(default_inline_query_answer) is not list:
            return 1
        self._default_inline_query_answer = default_inline_query_answer
        return 0

    def set_maintenance(self, maintenance_message):
        """Put the bot under maintenance or ends it.

        While in maintenance, bot will reply to users with maintenance_message.
        Bot will accept /coma, /stop and /restart commands from admins.
        """
        self._maintenance = not self.maintenance
        if maintenance_message:
            self.set_maintenance_message(maintenance_message)
        if self.maintenance:
            return (
                "<i>Bot has just been put under maintenance!</i>\n\n"
                "Until further notice, it will reply to users "
                "with the following message:\n\n{}"
            ).format(
                self.maintenance_message
            )
        return "<i>Maintenance ended!</i>"

    def set_authorization_function(self, authorization_function):
        """Set a custom authorization_function.

        It should evaluate True if user is authorized to perform
            a specific action and False otherwise.
        It should take update and role and return a Boolean.
        Default authorization_function always evaluates True.
        """
        self.authorization_function = authorization_function

    def set_get_chat_id_function(self, get_chat_id_function):
        """Set a custom get_chat_id function.

        It should take and update and return the chat in which
            a reply should be sent.
        For instance, a bot could reply in private to group messages
            as a default behaviour.
        Default chat_id returned is current chat id.
        """
        self.get_chat_id = get_chat_id_function

    async def avoid_flooding(self, chat_id):
        """asyncio-sleep until COOLDOWN_TIME (per_chat and absolute) has passed.

        To prevent hitting Telegram flood limits, send_message and
            send_photo await this function.
        """
        if type(chat_id) is int and chat_id > 0:
            while (
                datetime.datetime.now() < (
                    self.last_sending_time['absolute']
                    + self.__class__.COOLDOWN_TIME_ABSOLUTE
                )
            ) or (
                chat_id in self.last_sending_time
                and (
                    datetime.datetime.now() < (
                        self.last_sending_time[chat_id]
                        + self.__class__.COOLDOWN_TIME_PER_CHAT
                    )
                )
            ):
                await asyncio.sleep(
                    self.__class__.COOLDOWN_TIME_ABSOLUTE.seconds
                )
            self.last_sending_time[chat_id] = datetime.datetime.now()
        else:
            while (
                datetime.datetime.now() < (
                    self.last_sending_time['absolute']
                    + self.__class__.COOLDOWN_TIME_ABSOLUTE
                )
            ) or (
                chat_id in self.last_sending_time
                and len(
                    [
                        sending_datetime
                        for sending_datetime in self.last_sending_time[chat_id]
                        if sending_datetime >= (
                            datetime.datetime.now()
                            - datetime.timedelta(minutes=1)
                        )
                    ]
                ) >= self.__class__.MAX_GROUP_MESSAGES_PER_MINUTE
            ) or (
                chat_id in self.last_sending_time
                and len(self.last_sending_time[chat_id]) > 0
                and datetime.datetime.now() < (
                    self.last_sending_time[chat_id][-1]
                    + self.__class__.COOLDOWN_TIME_PER_CHAT
                )
            ):
                await asyncio.sleep(0.5)
            if chat_id not in self.last_sending_time:
                self.last_sending_time[chat_id] = []
            self.last_sending_time[chat_id].append(datetime.datetime.now())
            self.last_sending_time[chat_id] = [
                sending_datetime
                for sending_datetime in self.last_sending_time[chat_id]
                if sending_datetime >= (
                    datetime.datetime.now()
                    - datetime.timedelta(minutes=1)
                )
            ]
        self.last_sending_time['absolute'] = datetime.datetime.now()
        return

    async def on_inline_query(self, update):
        """Schedule handling of received inline queries.

        Notice that handling is only scheduled, not awaited.
        This means that all Bot instances may now handle other requests
            before this one is completed.
        """
        asyncio.ensure_future(self.handle_inline_query(update))
        return

    async def on_chosen_inline_result(self, update):
        """Schedule handling of received chosen inline result events.

        Notice that handling is only scheduled, not awaited.
        This means that all Bot instances may now handle other requests
            before this one is completed.
        """
        asyncio.ensure_future(self.handle_chosen_inline_result(update))
        return

    async def on_callback_query(self, update):
        """Schedule handling of received callback queries.

        A callback query is sent when users press inline keyboard buttons.
        Bad clients may send malformed or deceiving callback queries:
            never use secret keys in buttons and always check request validity!
        Notice that handling is only scheduled, not awaited.
        This means that all Bot instances may now handle other requests
            before this one is completed.
        """
        # Reject malformed updates lacking of data field
        if 'data' not in update:
            return
        asyncio.ensure_future(self.handle_callback_query(update))
        return

    async def on_chat_message(self, update):
        """Schedule handling of received chat message.

        Notice that handling is only scheduled, not awaited.
        According to update type, the corresponding handler is
            scheduled (see self.chat_message_handlers).
        This means that all Bot instances may now handle other
            requests before this one is completed.
        """
        answer = None
        content_type, chat_type, chat_id = telepot.glance(
            update,
            flavor='chat',
            long=False
        )
        if content_type in self.chat_message_handlers:
            answer = asyncio.ensure_future(
                self.chat_message_handlers[content_type](update)
            )
        else:
            answer = None
            logging.debug("Unhandled message")
        return answer

    async def handle_inline_query(self, update):
        """Handle inline query and answer it with results, or log errors."""
        query = update['query']
        answer = None
        switch_pm_text, switch_pm_parameter = None, None
        if self.maintenance:
            answer = self.maintenance_message
        else:
            for condition, handler in self.inline_query_handlers.items():
                answerer = handler['function']
                if condition(update['query']):
                    if asyncio.iscoroutinefunction(answerer):
                        answer = await answerer(update)
                    else:
                        answer = answerer(update)
                    break
            if not answer:
                answer = self.default_inline_query_answer
        if type(answer) is dict:
            if 'switch_pm_text' in answer:
                switch_pm_text = answer['switch_pm_text']
            if 'switch_pm_parameter' in answer:
                switch_pm_parameter = answer['switch_pm_parameter']
            answer = answer['answer']
        if type(answer) is str:
            answer = make_inline_query_answer(answer)
        try:
            await self.answerInlineQuery(
                update['id'],
                answer,
                cache_time=10,
                is_personal=True,
                switch_pm_text=switch_pm_text,
                switch_pm_parameter=switch_pm_parameter
            )
        except Exception as e:
            logging.info("Error answering inline query\n{}".format(e))
        return

    async def handle_chosen_inline_result(self, update):
        """When an inline query result is chosen, perform an action.

        If chosen inline result id is in self.chosen_inline_result_handlers,
            call the related function passing the update as argument.
        """
        user_id = update['from']['id'] if 'from' in update else None
        if self.maintenance:
            return
        if user_id in self.chosen_inline_result_handlers:
            result_id = update['result_id']
            handlers = self.chosen_inline_result_handlers[user_id]
            if result_id in handlers:
                func = handlers[result_id]
                if asyncio.iscoroutinefunction(func):
                    await func(update)
                else:
                    func(update)
        return

    def set_inline_result_handler(self, user_id, result_id, func):
        """Associate a func to a result_id.

        When an inline result is chosen having that id, function will
            be passed the update as argument.
        """
        if type(user_id) is dict:
            user_id = user_id['from']['id']
        assert type(user_id) is int, "user_id must be int!"
        # Query result ids are parsed as str by telegram
        result_id = str(result_id)
        assert callable(func), "func must be a callable"
        if user_id not in self.chosen_inline_result_handlers:
            self.chosen_inline_result_handlers[user_id] = {}
        self.chosen_inline_result_handlers[user_id][result_id] = func
        return

    async def handle_callback_query(self, update):
        """Answer callback queries.

        Call the callback handler associated to the query prefix.
        The answer is used to edit the source message or send new ones
            if text is longer than single message limit.
        Anyway, the query is answered, otherwise the client would hang and
            the bot would look like idle.
        """
        answer = None
        if self.maintenance:
            answer = remove_html_tags(self.maintenance_message[:45])
        else:
            data = update['data']
            for start_text, handler in self.callback_handlers.items():
                answerer = handler['function']
                if data.startswith(start_text):
                    if asyncio.iscoroutinefunction(answerer):
                        answer = await answerer(update)
                    else:
                        answer = answerer(update)
                    break
        if answer:
            if type(answer) is str:
                answer = {'text': answer}
            if type(answer) is not dict:
                return
            if 'edit' in answer:
                if 'message' in update:
                    message_identifier = telepot.message_identifier(
                        update['message']
                    )
                else:
                    message_identifier = telepot.message_identifier(update)
                edit = answer['edit']
                reply_markup = (
                    edit['reply_markup']
                    if 'reply_markup' in edit
                    else None
                )
                text = (
                    edit['text']
                    if 'text' in edit
                    else None
                )
                caption = (
                    edit['caption']
                    if 'caption' in edit
                    else None
                )
                parse_mode = (
                    edit['parse_mode']
                    if 'parse_mode' in edit
                    else None
                )
                disable_web_page_preview = (
                    edit['disable_web_page_preview']
                    if 'disable_web_page_preview' in edit
                    else None
                )
                try:
                    if 'text' in edit:
                        if (
                            len(text)
                            > self.__class__.TELEGRAM_MESSAGES_MAX_LEN - 200
                        ):
                            if 'from' in update:
                                await self.send_message(
                                    chat_id=update['from']['id'],
                                    text=text,
                                    reply_markup=reply_markup,
                                    parse_mode=parse_mode,
                                    disable_web_page_preview=(
                                        disable_web_page_preview
                                    )
                                )
                        else:
                            await self.editMessageText(
                                msg_identifier=message_identifier,
                                text=text,
                                parse_mode=parse_mode,
                                disable_web_page_preview=(
                                    disable_web_page_preview
                                ),
                                reply_markup=reply_markup
                            )
                    elif 'caption' in edit:
                        await self.editMessageCaption(
                            msg_identifier=message_identifier,
                            caption=caption,
                            reply_markup=reply_markup
                        )
                    elif 'reply_markup' in edit:
                        await self.editMessageReplyMarkup(
                            msg_identifier=message_identifier,
                            reply_markup=reply_markup
                        )
                except Exception as e:
                    logging.info("Message was not modified:\n{}".format(e))
            text = answer['text'][:180] if 'text' in answer else None
            show_alert = (
                answer['show_alert']
                if 'show_alert' in answer
                else None
            )
            cache_time = (
                answer['cache_time']
                if 'cache_time' in answer
                else None
            )
            try:
                await self.answerCallbackQuery(
                    callback_query_id=update['id'],
                    text=text,
                    show_alert=show_alert,
                    cache_time=cache_time
                )
            except telepot.exception.TelegramError as e:
                logging.error(e)
        else:
            try:
                await self.answerCallbackQuery(callback_query_id=update['id'])
            except telepot.exception.TelegramError as e:
                logging.error(e)
        return

    async def handle_text_message(self, update):
        """Answer to chat text messages.

        1) Ignore bot name (case-insensitive) and search bot custom parsers,
            commands, aliases and parsers for an answerer.
        2) Get an answer from answerer(update).
        3) Send it to the user.
        """
        answerer, answer = None, None
        # Lower text and replace only bot's tag,
        # meaning that `/command@OtherBot` will be ignored.
        text = update['text'].lower().replace(
            '@{}'.format(
                self.name.lower()
            ),
            ''
        )
        user_id = update['from']['id'] if 'from' in update else None
        if self.maintenance and not any(
            text.startswith(x)
            for x in ('/coma', '/restart')
        ):
            if update['chat']['id'] > 0:
                answer = self.maintenance_message
        elif user_id in self.custom_parsers:
            answerer = self.custom_parsers[user_id]
            del self.custom_parsers[user_id]
        elif text.startswith('/'):
            command = text.split()[0].strip(' /@')
            if command in self.commands:
                answerer = self.commands[command]['function']
            elif update['chat']['id'] > 0:
                answer = self.unknown_command_message
        else:
            # If text starts with an alias
            # Aliases are case insensitive: text and alias are both .lower()
            for alias, parser in self.aliases.items():
                if text.startswith(alias.lower()):
                    answerer = parser
                    break
            # If update matches any parser
            for check_function, parser in self.parsers.items():
                if (
                    parser['argument'] == 'text'
                    and check_function(text)
                ) or (
                    parser['argument'] == 'update'
                    and check_function(update)
                ):
                    answerer = parser['function']
                    break
        if answerer:
            if asyncio.iscoroutinefunction(answerer):
                answer = await answerer(update)
            else:
                answer = answerer(update)
        if answer:
            try:
                return await self.send_message(answer=answer, chat_id=update)
            except Exception as e:
                logging.error(
                    "Failed to process answer:\n{}".format(e),
                    exc_info=True
                )

    async def handle_pinned_message(self, update):
        """Handle pinned message chat action."""
        if self.maintenance:
            return
        answerer = None
        for criteria, handler in self.chat_actions['pinned'].items():
            if criteria(update):
                answerer = handler['function']
                break
        if answerer is None:
            return
        elif asyncio.iscoroutinefunction(answerer):
            answer = await answerer(update)
        else:
            answer = answerer(update)
        if answer:
            try:
                return await self.send_message(
                    answer=answer,
                    chat_id=update['chat']['id']
                )
            except Exception as e:
                logging.error(
                    "Failed to process answer:\n{}".format(
                        e
                    ),
                    exc_info=True
                )
        return

    async def handle_photo_message(self, update):
        """Handle photo chat message."""
        user_id = update['from']['id'] if 'from' in update else None
        answerer, answer = None, None
        if self.maintenance:
            if update['chat']['id'] > 0:
                answer = self.maintenance_message
        elif user_id in self.custom_photo_parsers:
            answerer = self.custom_photo_parsers[user_id]
            del self.custom_photo_parsers[user_id]
        if answerer:
            if asyncio.iscoroutinefunction(answerer):
                answer = await answerer(update)
            else:
                answer = answerer(update)
        if answer:
            try:
                return await self.send_message(answer=answer, chat_id=update)
            except Exception as e:
                logging.error(
                    "Failed to process answer:\n{}".format(
                        e
                    ),
                    exc_info=True
                )
        return

    def set_custom_parser(self, parser, update=None, user=None):
        """Set a custom parser for the user.

        Any chat message update coming from the user will be handled by
            this custom parser instead of default parsers (commands, aliases
            and text parsers).
        Custom parsers last one single use, but their handler can call this
            function to provide multiple tries.
        """
        if user and type(user) is int:
            pass
        elif type(update) is int:
            user = update
        elif type(user) is dict:
            user = (
                user['from']['id']
                if 'from' in user
                and 'id' in user['from']
                else None
            )
        elif not user and type(update) is dict:
            user = (
                update['from']['id']
                if 'from' in update
                and 'id' in update['from']
                else None
            )
        else:
            raise TypeError(
                'Invalid user.\nuser: {}\nupdate: {}'.format(
                    user,
                    update
                )
            )
        if not type(user) is int:
            raise TypeError(
                'User {} is not an int id'.format(
                    user
                )
            )
        if not callable(parser):
            raise TypeError(
                'Parser {} is not a callable'.format(
                    parser.__name__
                )
            )
        self.custom_parsers[user] = parser
        return

    def set_custom_photo_parser(self, parser, update=None, user=None):
        """Set a custom photo parser for the user.

        Any photo chat update coming from the user will be handled by
        this custom parser instead of default parsers.
        Custom photo parsers last one single use, but their handler can
        call this function to provide multiple tries.
        """
        if user and type(user) is int:
            pass
        elif type(update) is int:
            user = update
        elif type(user) is dict:
            user = (
                user['from']['id']
                if 'from' in user
                and 'id' in user['from']
                else None
            )
        elif not user and type(update) is dict:
            user = (
                update['from']['id']
                if 'from' in update
                and 'id' in update['from']
                else None
            )
        else:
            raise TypeError(
                'Invalid user.\nuser: {}\nupdate: {}'.format(
                    user,
                    update
                )
            )
        if not type(user) is int:
            raise TypeError(
                'User {} is not an int id'.format(
                    user
                )
            )
        if not callable(parser):
            raise TypeError(
                'Parser {} is not a callable'.format(
                    parser.__name__
                )
            )
        self.custom_photo_parsers[user] = parser
        return

    def command(self, command, aliases=None, show_in_keyboard=False,
                descr="", auth='admin'):
        """Define a bot command.

        Decorator: `@bot.command(*args)`
        When a message text starts with `/command[@bot_name]`, or with an
            alias, it gets passed to the decorated function.
        `command` is the command name (with or without /)
        `aliases` is a list of aliases
        `show_in_keyboard`, if True, makes first alias appear
            in default_keyboard
        `descr` is a description
        `auth` is the lowest authorization level needed to run the command
        """
        command = command.replace('/', '').lower()
        if not isinstance(command, str):
            raise TypeError('Command {} is not a string'.format(command))
        if aliases:
            if not isinstance(aliases, list):
                raise TypeError('Aliases is not a list: {}'.format(aliases))
            for alias in aliases:
                if not isinstance(alias, str):
                    raise TypeError('Alias {} is not a string'.format(alias))

        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                async def decorated(message):
                    logging.info(
                        "COMMAND({c}) @{n} FROM({f})".format(
                            c=command,
                            n=self.name,
                            f=(
                                message['from']
                                if 'from' in message
                                else message['chat']
                            )
                        )
                    )
                    if self.authorization_function(message, auth):
                        return await func(message)
                    return self.unauthorized_message
            else:
                def decorated(message):
                    logging.info(
                        "COMMAND({c}) @{n} FROM({f})".format(
                            c=command,
                            n=self.name,
                            f=(
                                message['from']
                                if 'from' in message
                                else message['chat']
                            )
                        )
                    )
                    if self.authorization_function(message, auth):
                        return func(message)
                    return self.unauthorized_message
            self.commands[command] = dict(
                function=decorated,
                descr=descr,
                auth=auth
            )
            if aliases:
                for alias in aliases:
                    self.aliases[alias] = decorated
                if show_in_keyboard:
                    self.default_reply_keyboard_elements.append(aliases[0])
        return decorator

    def parser(self, condition, descr='', auth='admin', argument='text'):
        """Define a message parser.

        Decorator: `@bot.parser(condition)`
        If condition evaluates True when run on a message text
            (not starting with '/'), such decorated function gets
            called on update.
        Conditions of parsers are evaluated in order; when one is True,
            others will be skipped.
        `descr` is a description
        `auth` is the lowest authorization level needed to run the command
        """
        if not callable(condition):
            raise TypeError(
                'Condition {} is not a callable'.format(
                    condition.__name__
                )
            )

        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                async def decorated(message):
                    logging.info(
                        "TEXT MATCHING CONDITION({c}) @{n} FROM({f})".format(
                            c=condition.__name__,
                            n=self.name,
                            f=(
                                message['from']
                                if 'from' in message
                                else message['chat']
                            )
                        )
                    )
                    if self.authorization_function(message, auth):
                        return await func(message)
                    return self.unauthorized_message
            else:
                def decorated(message):
                    logging.info(
                        "TEXT MATCHING CONDITION({c}) @{n} FROM({f})".format(
                            c=condition.__name__,
                            n=self.name,
                            f=(
                                message['from']
                                if 'from' in message
                                else message['chat']
                            )
                        )
                    )
                    if self.authorization_function(message, auth):
                        return func(message)
                    return self.unauthorized_message
            self.parsers[condition] = dict(
                function=decorated,
                descr=descr,
                auth=auth,
                argument=argument
            )
        return decorator

    def pinned(self, condition, descr='', auth='admin'):
        """Handle pinned messages.

        Decorator: `@bot.pinned(condition)`
        If condition evaluates True when run on a pinned_message update,
            such decorated function gets called on update.
        Conditions are evaluated in order; when one is True,
            others will be skipped.
        `descr` is a description
        `auth` is the lowest authorization level needed to run the command
        """
        if not callable(condition):
            raise TypeError(
                'Condition {c} is not a callable'.format(
                    c=condition.__name__
                )
            )

        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                async def decorated(message):
                    logging.info(
                        "PINNED MESSAGE MATCHING({c}) @{n} FROM({f})".format(
                            c=condition.__name__,
                            n=self.name,
                            f=(
                                message['from']
                                if 'from' in message
                                else message['chat']
                            )
                        )
                    )
                    if self.authorization_function(message, auth):
                        return await func(message)
                    return
            else:
                def decorated(message):
                    logging.info(
                        "PINNED MESSAGE MATCHING({c}) @{n} FROM({f})".format(
                            c=condition.__name__,
                            n=self.name,
                            f=(
                                message['from']
                                if 'from' in message
                                else message['chat']
                            )
                        )
                    )
                    if self.authorization_function(message, auth):
                        return func(message)
                    return
            self.chat_actions['pinned'][condition] = dict(
                function=decorated,
                descr=descr,
                auth=auth
            )
        return decorator

    def button(self, data, descr='', auth='admin'):
        """Define a bot button.

        Decorator: `@bot.button('example:///')`
        When a callback data text starts with <data>, it gets passed to the
            decorated function
        `descr` is a description
        `auth` is the lowest authorization level needed to run the command
        """
        if not isinstance(data, str):
            raise TypeError(
                'Inline button callback_data {d} is not a string'.format(
                    d=data
                )
            )

        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                async def decorated(message):
                    logging.info(
                        "INLINE BUTTON({d}) @{n} FROM({f})".format(
                            d=message['data'],
                            n=self.name,
                            f=(
                                message['from']
                            )
                        )
                    )
                    if self.authorization_function(message, auth):
                        return await func(message)
                    return self.unauthorized_message
            else:
                def decorated(message):
                    logging.info(
                        "INLINE BUTTON({d}) @{n} FROM({f})".format(
                            d=message['data'],
                            n=self.name,
                            f=(
                                message['from']
                            )
                        )
                    )
                    if self.authorization_function(message, auth):
                        return func(message)
                    return self.unauthorized_message
            self.callback_handlers[data] = dict(
                function=decorated,
                descr=descr,
                auth=auth
            )
        return decorator

    def query(self, condition, descr='', auth='admin'):
        """Define an inline query.

        Decorator: `@bot.query(example)`
        When an inline query matches the `condition` function,
            decorated function is called and passed the query update object
            as argument.
        `descr` is a description
        `auth` is the lowest authorization level needed to run the command
        """
        if not callable(condition):
            raise TypeError(
                'Condition {c} is not a callable'.format(
                    c=condition.__name__
                )
            )

        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                async def decorated(message):
                    logging.info(
                        "QUERY MATCHING CONDITION({c}) @{n} FROM({f})".format(
                            c=condition.__name__,
                            n=self.name,
                            f=message['from']
                        )
                    )
                    if self.authorization_function(message, auth):
                        return await func(message)
                    return self.unauthorized_message
            else:
                def decorated(message):
                    logging.info(
                        "QUERY MATCHING CONDITION({c}) @{n} FROM({f})".format(
                            c=condition.__name__,
                            n=self.name,
                            f=message['from']
                        )
                    )
                    if self.authorization_function(message, auth):
                        return func(message)
                    return self.unauthorized_message
            self.inline_query_handlers[condition] = dict(
                function=decorated,
                descr=descr,
                auth=auth
            )
        return decorator

    def additional_task(self, when='BEFORE'):
        """Add a task before or after message_loop.

        Decorator: such decorated async functions get awaited BEFORE or
            AFTER messageloop
        """
        when = when[0].lower()

        def decorator(func):
            if when == 'b':
                self.run_before_loop.append(func())
            elif when == 'a':
                self.run_after_loop.append(func())
        return decorator

    def set_default_keyboard(self, keyboard='set_default'):
        """Set a default keyboard for the bot.

        If a keyboard is not passed as argument, a default one is generated,
            based on aliases of commands.
        """
        if keyboard == 'set_default':
            btns = [
                dict(
                    text=x
                )
                for x in self.default_reply_keyboard_elements
            ]
            row_len = 2 if len(btns) < 4 else 3
            self._default_keyboard = dict(
                keyboard=make_lines_of_buttons(
                    btns,
                    row_len
                ),
                resize_keyboard=True
            )
        else:
            self._default_keyboard = keyboard
        return

    async def edit_message(self, update, *args, **kwargs):
        """Edit given update with given *args and **kwargs.

        Please note, that it is currently only possible to edit messages
        without reply_markup or with inline keyboards.
        """
        try:
            return await self.editMessageText(
                telepot.message_identifier(update),
                *args,
                **kwargs
            )
        except Exception as e:
            logging.error("{}".format(e))

    async def delete_message(self, update, *args, **kwargs):
        """Delete given update with given *args and **kwargs.

        Please note, that a bot can delete only messages sent by itself
        or sent in a group which it is administrator of.
        """
        try:
            return await self.deleteMessage(
                telepot.message_identifier(update),
                *args,
                **kwargs
            )
        except Exception as e:
            logging.error("{}".format(e))

    async def send_message(self, answer=dict(), chat_id=None, text='',
                           parse_mode="HTML", disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None,
                           reply_markup=None):
        """Send a message.

        Convenient method to call telepot.Bot(token).sendMessage
        All sendMessage **kwargs can be either **kwargs of send_message
            or key:val of answer argument.
        Messages longer than telegram limit will be split properly.
        Telegram flood limits won't be reached thanks to
            `await avoid_flooding(chat_id)`
        parse_mode will be checked and edited if necessary.
        Arguments will be checked and adapted.
        """
        if type(answer) is dict and 'chat_id' in answer:
            chat_id = answer['chat_id']
        # chat_id may simply be the update to which the bot should repy
        if type(chat_id) is dict:
            chat_id = self.get_chat_id(chat_id)
        if type(answer) is str:
            text = answer
            if (
                not reply_markup
                and chat_id > 0
                and text != self.unauthorized_message
            ):
                reply_markup = self.default_keyboard
        elif type(answer) is dict:
            if 'text' in answer:
                text = answer['text']
            if 'parse_mode' in answer:
                parse_mode = answer['parse_mode']
            if 'disable_web_page_preview' in answer:
                disable_web_page_preview = answer['disable_web_page_preview']
            if 'disable_notification' in answer:
                disable_notification = answer['disable_notification']
            if 'reply_to_message_id' in answer:
                reply_to_message_id = answer['reply_to_message_id']
            if 'reply_markup' in answer:
                reply_markup = answer['reply_markup']
            elif (
                not reply_markup
                and type(chat_id) is int
                and chat_id > 0
                and text != self.unauthorized_message
            ):
                reply_markup = self.default_keyboard
        assert type(text) is str, "Text is not a string!"
        assert (
            type(chat_id) is int
            or (type(chat_id) is str and chat_id.startswith('@'))
        ), "Invalid chat_id:\n\t\t{}".format(chat_id)
        if not text:
            return
        parse_mode = str(parse_mode)
        text_chunks = split_text_gracefully(
            text=text,
            limit=self.__class__.TELEGRAM_MESSAGES_MAX_LEN - 100,
            parse_mode=parse_mode
        )
        n = len(text_chunks)
        for text_chunk in text_chunks:
            n -= 1
            if parse_mode.lower() == "html":
                this_parse_mode = "HTML"
                # Check that all tags are well-formed
                if not markdown_check(
                    text_chunk,
                    [
                        "<", ">",
                        "code>", "bold>", "italic>",
                        "b>", "i>", "a>", "pre>"
                    ]
                ):
                    this_parse_mode = "None"
                    text_chunk = (
                        "!!![invalid markdown syntax]!!!\n\n"
                        + text_chunk
                    )
            elif parse_mode != "None":
                this_parse_mode = "Markdown"
                # Check that all markdowns are well-formed
                if not markdown_check(
                    text_chunk,
                    [
                        "*", "_", "`"
                    ]
                ):
                    this_parse_mode = "None"
                    text_chunk = (
                        "!!![invalid markdown syntax]!!!\n\n"
                        + text_chunk
                    )
            else:
                this_parse_mode = parse_mode
            this_reply_markup = reply_markup if n == 0 else None
            try:
                await self.avoid_flooding(chat_id)
                result = await self.sendMessage(
                    chat_id=chat_id,
                    text=text_chunk,
                    parse_mode=this_parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=this_reply_markup
                )
            except Exception as e:
                logging.debug(
                    e,
                    exc_info=False  # Set exc_info=True for more information
                )
                result = e
        return result

    async def send_photo(self, chat_id=None, answer={},
                         photo=None, caption='', parse_mode='HTML',
                         disable_notification=None, reply_to_message_id=None,
                         reply_markup=None, use_stored=True,
                         second_chance=False):
        """Send a photo.

        Convenient method to call telepot.Bot(token).sendPhoto
        All sendPhoto **kwargs can be either **kwargs of send_message
            or key:val of answer argument.
        Captions longer than telegram limit will be shortened gently.
        Telegram flood limits won't be reached thanks to
            `await avoid_flooding(chat_id)`
        Most arguments will be checked and adapted.
        If use_stored is set to True, the bot will store sent photo
            telegram_id and use it for faster sending next times (unless
            future errors).
        Sending photos by their file_id already stored on telegram servers
            is way faster: that's why bot stores and uses this info,
            if required.
        A second_chance is given to send photo on error.
        """
        if 'chat_id' in answer:
            chat_id = answer['chat_id']
        # chat_id may simply be the update to which the bot should repy
        if type(chat_id) is dict:
            chat_id = self.get_chat_id(chat_id)
        assert (
            type(chat_id) is int
            or (type(chat_id) is str and chat_id.startswith('@'))
        ), "Invalid chat_id:\n\t\t{}".format(chat_id)
        if 'photo' in answer:
            photo = answer['photo']
        assert photo is not None, "Null photo!"
        if 'caption' in answer:
            caption = answer['caption']
        if 'parse_mode' in answer:
            parse_mode = answer['parse_mode']
        if 'disable_notification' in answer:
            disable_notification = answer['disable_notification']
        if 'reply_to_message_id' in answer:
            reply_to_message_id = answer['reply_to_message_id']
        if 'reply_markup' in answer:
            reply_markup = answer['reply_markup']
        already_sent = False
        if type(photo) is str:
            photo_url = photo
            with self.db as db:
                already_sent = db['sent_pictures'].find_one(
                    url=photo_url,
                    errors=False
                )
            if already_sent and use_stored:
                photo = already_sent['file_id']
                already_sent = True
            else:
                already_sent = False
                if not any(photo_url.startswith(x) for x in ['http', 'www']):
                    with io.BytesIO() as buffered_picture:
                        with open(
                            "{}/{}".format(
                                self.path,
                                photo_url
                            ),
                            'rb'
                        ) as photo_file:
                            buffered_picture.write(photo_file.read())
                        photo = buffered_picture.getvalue()
        caption = escape_html_chars(caption)
        if len(caption) > 199:
            new_caption = ''
            tag = False
            tag_body = False
            count = 0
            temp = ''
            for char in caption:
                if tag and char == '>':
                    tag = False
                elif char == '<':
                    tag = True
                    tag_body = not tag_body
                elif not tag:
                    count += 1
                if count == 199:
                    break
                temp += char
                if not tag_body:
                    new_caption += temp
                    temp = ''
            caption = new_caption
        sent = None
        try:
            await self.avoid_flooding(chat_id)
            sent = await self.sendPhoto(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup
            )
            if isinstance(sent, Exception):
                raise Exception("SendingFailed")
        except Exception as e:
            logging.error(
                "Error sending photo\n{}".format(
                    e
                ),
                exc_info=False  # Set exc_info=True for more information
            )
            if already_sent:
                with self.db as db:
                    db['sent_pictures'].update(
                        dict(
                            url=photo_url,
                            errors=True
                        ),
                        ['url']
                    )
                if not second_chance:
                    logging.info("Trying again (only once)...")
                    sent = await self.send_photo(
                        chat_id=chat_id,
                        answer=answer,
                        photo=photo,
                        caption=caption,
                        parse_mode=parse_mode,
                        disable_notification=disable_notification,
                        reply_to_message_id=reply_to_message_id,
                        reply_markup=reply_markup,
                        second_chance=True
                    )
        if (
            sent is not None
            and hasattr(sent, '__getitem__')
            and 'photo' in sent
            and len(sent['photo']) > 0
            and 'file_id' in sent['photo'][0]
            and (not already_sent)
            and use_stored
        ):
            with self.db as db:
                db['sent_pictures'].insert(
                    dict(
                        url=photo_url,
                        file_id=sent['photo'][0]['file_id'],
                        errors=False
                    )
                )
        return sent

    async def send_and_destroy(self, chat_id, answer,
                               timer=60, mode='text', **kwargs):
        """Send a message or photo and delete it after `timer` seconds."""
        if mode == 'text':
            sent_message = await self.send_message(
                chat_id=chat_id,
                answer=answer,
                **kwargs
            )
        elif mode == 'pic':
            sent_message = await self.send_photo(
                chat_id=chat_id,
                answer=answer,
                **kwargs
            )
        if sent_message is None:
            return
        self.to_be_destroyed.append(sent_message)
        await asyncio.sleep(timer)
        if await self.delete_message(sent_message):
            self.to_be_destroyed.remove(sent_message)
        return

    async def wait_and_obscure(self, update, when, inline_message_id):
        """Obscure messages which can't be deleted.

        Obscure an inline_message `timer` seconds after sending it,
        by editing its text or caption.
        At the moment Telegram won't let bots delete sent inline query results.
        """
        if type(when) is int:
            when = datetime.datetime.now() + datetime.timedelta(seconds=when)
        assert type(when) is datetime.datetime, (
            "when must be a datetime instance or a number of seconds (int) "
            "to be awaited"
        )
        if 'inline_message_id' not in update:
            logging.info(
                "This inline query result owns no inline_keyboard, so it "
                "can't be modified"
            )
            return
        inline_message_id = update['inline_message_id']
        self.to_be_obscured.append(inline_message_id)
        while datetime.datetime.now() < when:
            await sleep_until(when)
        try:
            await self.editMessageCaption(
                inline_message_id,
                text="Time over"
            )
        except Exception:
            try:
                await self.editMessageText(
                    inline_message_id,
                    text="Time over"
                )
            except Exception as e:
                logging.error(
                    "Couldn't obscure message\n{}\n\n{}".format(
                        inline_message_id,
                        e
                    )
                )
        self.to_be_obscured.remove(inline_message_id)
        return

    async def get_me(self):
        """Get bot information.

        Restart bots if bot can't be got.
        """
        try:
            me = await self.getMe()
            self.bot_name = me["username"]
            self.telegram_id = me['id']
        except Exception as e:
            logging.error(
                "Could not get bot\n{e}".format(
                    e=e
                )
            )
            await asyncio.sleep(5*60)
            self.restart_bots()
            return

    async def continue_running(self):
        """Get updates.

        If bot can be got, sets name and telegram_id,
            awaits preliminary tasks and starts getting updates from telegram.
        If bot can't be got, restarts all bots in 5 minutes.
        """
        await self.get_me()
        for task in self.run_before_loop:
            await task
        self.set_default_keyboard()
        asyncio.ensure_future(
            self.message_loop(handler=self.routing_table)
        )
        return

    def stop_bots(self):
        """Exit script with code 0."""
        Bot.stop = True

    def restart_bots(self):
        """Restart the script exiting with code 65.

        Actually, you need to catch Bot.stop state when Bot.run() returns
        and handle the situation yourself.
        """
        Bot.stop = "Restart"

    @classmethod
    async def check_task(cls):
        """Await until cls.stop, then end session and return."""
        for bot in cls.instances.values():
            asyncio.ensure_future(bot.continue_running())
        while not cls.stop:
            await asyncio.sleep(10)
        return await cls.end_session()

    @classmethod
    async def end_session(cls):
        """Run after stop, before the script exits.

        Await final tasks, obscure and delete pending messages,
            log current operation (stop/restart).
        """
        for bot in cls.instances.values():
            for task in bot.run_after_loop:
                await task
            for message in bot.to_be_destroyed:
                try:
                    await bot.delete_message(message)
                except Exception as e:
                    logging.error(
                        "Couldn't delete message\n{}\n\n{}".format(
                            message,
                            e
                        )
                    )
            for inline_message_id in bot.to_be_obscured:
                try:
                    await bot.editMessageCaption(
                        inline_message_id,
                        text="Time over"
                    )
                except Exception:
                    try:
                        await bot.editMessageText(
                            inline_message_id,
                            text="Time over"
                        )
                    except Exception as e:
                        logging.error(
                            "Couldn't obscure message\n{}\n\n{}".format(
                                inline_message_id,
                                e
                            )
                        )
        if cls.stop == "Restart":
            logging.info("\n\t\t---Restart!---")
        elif cls.stop == "KeyboardInterrupt":
            logging.info("Stopped by KeyboardInterrupt.")
        else:
            logging.info("Stopped gracefully by user.")
        return

    @classmethod
    def run(cls, loop=None):
        """Call this method to run the async bots."""
        if loop is None:
            loop = asyncio.get_event_loop()
        logging.info(
            "{sep}{subjvb} STARTED{sep}".format(
                sep='-'*10,
                subjvb='BOT HAS' if len(cls.instances) == 1 else 'BOTS HAVE'
            )
        )
        try:
            loop.run_until_complete(cls.check_task())
        except KeyboardInterrupt:
            logging.info(
                (
                    "\n\t\tYour script received a KeyboardInterrupt signal, "
                    "your bot{} being stopped."
                ).format(
                    's are'
                    if len(cls.instances) > 1
                    else ' is'
                )
            )

            cls.stop = "KeyboardInterrupt"
            loop.run_until_complete(cls.end_session())
        except Exception as e:
            logging.error(
                '\nYour bot{vb} been stopped. with error \'{e}\''.format(
                    e=e,
                    vb='s have' if len(cls.instances) > 1 else ' has'
                ),
                exc_info=True
            )
        logging.info(
            "{sep}{subjvb} STOPPED{sep}".format(
                sep='-'*10,
                subjvb='BOT HAS' if len(cls.instances) == 1 else 'BOTS HAVE'
            )
        )
        return

    @classmethod
    async def _run_manual_mode(cls):
        available_bots = MyOD()
        for code, bot in enumerate(
            cls.instances.values()
        ):
            await bot.get_me()
            available_bots[code] = dict(
                bot=bot,
                code=code,
                name=bot.name
            )
        selected_bot = None
        while selected_bot is None:
            user_input = input(
                "\n=============================================\n"
                "Which bot would you like to control manually?\n"
                "Available bots:\n{}\n\n\t\t".format(
                    line_drawing_unordered_list(
                        list(
                            "{b[code]:>3} - {b[bot].name}".format(
                                b=bot,
                            )
                            for bot in available_bots.values()
                        )
                    )
                )
            )
            if (
                user_input.isnumeric()
                and int(user_input) in available_bots
            ):
                selected_bot = available_bots[int(user_input)]
            else:
                selected_bot = pick_most_similar_from_list(
                    [
                        bot['name']
                        for bot in available_bots.values()
                    ],
                    user_input
                )
                selected_bot = available_bots.get_by_key_val(
                    key='name',
                    val=selected_bot,
                    case_sensitive=False,
                    return_value=True
                )
            if selected_bot is None:
                logging.error("Invalid selection.")
                continue
            logging.info(
                "Bot `{b[name]}` selected.".format(
                    b=selected_bot
                )
            )
            exit_code = await selected_bot['bot']._run_manually()
            if exit_code == 0:
                break
        return

    @classmethod
    def run_manual_mode(cls, loop=None):
        """Run in manual mode: send messages via bots."""
        if loop is None:
            loop = asyncio.get_event_loop()
        logging.info(
            "=== MANUAL MODE STARTED ==="
        )
        try:
            loop.run_until_complete(
                cls._run_manual_mode()
            )
        except KeyboardInterrupt:
            logging.info(
                (
                    "\n\t\tYour script received a KeyboardInterrupt signal, "
                    "your bot{} being stopped."
                ).format(
                    's are' if len(cls.instances) > 1 else ' is'
                )
            )
        except Exception as e:
            logging.error(
                '\nYour bot{vb} been stopped. with error \'{e}\''.format(
                    e=e,
                    vb='s have' if len(cls.instances) > 1 else ' has'
                ),
                exc_info=True
            )
        logging.info(
            "=== MANUAL MODE STOPPED ==="
        )

    async def _run_manually(self):
        user_input = '  choose_addressee'
        while user_input:
            try:
                user_input = input(
                    "Choose an addressee."
                    "\n\t\t"
                )
            except KeyboardInterrupt:
                logging.error("Keyboard interrupt.")
                break
            logging.info(user_input)


if __name__ == '__main__':
    log_formatter = logging.Formatter(
        "%(asctime)s [%(module)-15s %(levelname)-8s]     %(message)s",
        style='%'
    )
    # Get root logger and set level to DEBUG
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    # ConsoleHandler (log to terminal)
    ConsoleHandler = logging.StreamHandler()
    ConsoleHandler.setFormatter(log_formatter)
    ConsoleHandler.setLevel(logging.DEBUG)
    # Add ConsoleHandler to root_logger
    root_logger.addHandler(ConsoleHandler)
    # from davtelepot.custombot import Bot
    # davtebot = Bot.get('335545766:AAEVvbdqy7OCG7ufxBwKVdBscdfddFF2lmk')
    # davtetest = Bot.get('279769259:AAEri-FF8AZeLz0LAi4BpPVjkQcKeOOTimo')
    # Bot.run_manual_mode()
    print('Work in progress')
