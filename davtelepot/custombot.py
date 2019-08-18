"""WARNING: this is only a legacy module, written for backward compatibility.

For newer versions use `bot.py`.
This module used to rely on third party `telepot` library by Nick Lee
    (@Nickoala).
The `telepot` repository was archived in may 2019 and will no longer be listed
    in requirements. To run legacy code, install telepot manually.
    `pip install telepot`

Subclass of third party telepot.aio.Bot, providing the following features.

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
from collections import OrderedDict
import datetime
import inspect
import logging
import os

# Third party modules
import davtelepot.bot

# Project modules
from .utilities import (
    get_secure_key, extract, sleep_until
)


class Bot(davtelepot.bot.Bot):
    """Legacy adapter for backward compatibility.

    Old description:
    telepot.aio.Bot (async Telegram bot framework) convenient subclass.

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

    def __init__(self, token, db_name=None, **kwargs):
        """Instantiate Bot instance, given a token and a db name."""
        davtelepot.bot.Bot.__init__(
            self,
            token=token,
            database_url=db_name,
            **kwargs
        )
        self.message_handlers['pinned_message'] = self.handle_pinned_message
        self.message_handlers['photo'] = self.handle_photo_message
        self.message_handlers['location'] = self.handle_location
        self.custom_photo_parsers = dict()
        self.custom_location_parsers = dict()
        self.to_be_obscured = []
        self.to_be_destroyed = []
        self.chat_actions = dict(
            pinned=OrderedDict()
        )

    @property
    def unauthorized_message(self):
        """Return this if user is unauthorized to make a request.

        This property is deprecated: use `authorization_denied_message`
            instead.
        """
        return self.authorization_denied_message

    @property
    def maintenance(self):
        """Check whether bot is under maintenance.

        This property is deprecated: use `under_maintenance` instead.
        """
        return self.under_maintenance

    @classmethod
    def set_class_unauthorized_message(csl, unauthorized_message):
        """Set class unauthorized message.

        This method is deprecated: use `set_class_authorization_denied_message`
            instead.
        """
        return csl.set_class_authorization_denied_message(unauthorized_message)

    def set_unauthorized_message(self, unauthorized_message):
        """Set instance unauthorized message.

        This method is deprecated: use `set_authorization_denied_message`
            instead.
        """
        return self.set_authorization_denied_message(unauthorized_message)

    def set_authorization_function(self, authorization_function):
        """Set a custom authorization_function.

        It should evaluate True if user is authorized to perform a specific
            action and False otherwise.
        It should take update and role and return a Boolean.
        Default authorization_function always evaluates True.
        """
        def _authorization_function(update, authorization_level,
                                    user_record=None):
            privileges = authorization_level  # noqa: W0612, this variable
            #                                   is used by locals()
            return authorization_function(
                **{
                    name: argument
                    for name, argument in locals().items()
                    if name in inspect.signature(
                        authorization_function
                    ).parameters
                }
            )
        self.authorization_function = _authorization_function

    def set_maintenance(self, maintenance_message):
        """Put the bot under maintenance or end it.

        This method is deprecated: use `change_maintenance_status` instead.
        """
        bot_in_maintenance = self.change_maintenance_status(
            maintenance_message=maintenance_message
        )
        if bot_in_maintenance:
            return (
                "<i>Bot has just been put under maintenance!</i>\n\n"
                "Until further notice, it will reply to users "
                "with the following message:\n\n{}"
            ).format(
                self.maintenance_message
            )
        return "<i>Maintenance ended!</i>"

    def set_get_chat_id_function(self, get_chat_id_function):
        """Set a custom get_chat_id function.

        This method is deprecated: use `set_chat_id_getter` instead.
        """
        return self.set_chat_id_getter(get_chat_id_function)

    async def on_chat_message(self, update, user_record=None):
        """Handle text message.

        This method is deprecated: use `text_message_handler` instead.
        """
        return await self.text_message_handler(
            update=update,
            user_record=user_record
        )

    def set_inline_result_handler(self, user_id, result_id, func):
        """Associate a `func` with a `result_id` for `user_id`.

        This method is deprecated: use `set_chosen_inline_result_handler`
            instead.
        """
        if not asyncio.iscoroutinefunction(func):
            async def _func(update):
                return func(update)
        else:
            _func = func
        return self.set_chosen_inline_result_handler(
            user_id=user_id,
            result_id=result_id,
            handler=_func
        )

    async def handle_pinned_message(self, update, user_record=None):
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

    async def handle_photo_message(self, update, user_record=None):
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

    async def handle_location(self, *args, **kwargs):
        """Handle location sent by user.

        This method is deprecated: use `location_message_handler` instead.
        """
        return await super().location_message_handler(*args, **kwargs)

    def set_custom_parser(self, parser, update=None, user=None):
        """Set a custom parser for the user.

        This method is deprecated: use `set_individual_text_message_handler`
            instead.
        """
        return self.set_individual_text_message_handler(
            handler=parser,
            update=update,
            user_id=user
        )

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

    def set_custom_location_parser(self, parser, update=None, user=None):
        """Set a custom location parser for the user.

        Any location chat update coming from the user will be handled by
        this custom parser instead of default parsers.
        Custom location parsers last one single use, but their handler can
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
        self.custom_location_parsers[user] = parser
        return

    def command(self, command, aliases=None, show_in_keyboard=False,
                reply_keyboard_button=None, descr="", auth='admin',
                description=None,
                help_section=None,
                authorization_level=None):
        """Define a bot command.

        `descr` and `auth` parameters are deprecated: use `description` and
            `authorization_level` instead.
        """
        authorization_level = authorization_level or auth
        description = description or descr
        return super().command(
            command=command,
            aliases=aliases,
            reply_keyboard_button=reply_keyboard_button,
            show_in_keyboard=show_in_keyboard,
            description=description,
            help_section=help_section,
            authorization_level=authorization_level
        )

    def parser(self, condition, descr='', auth='admin', argument='text',
               description=None,
               authorization_level=None):
        """Define a message parser.

        `descr` and `auth` parameters are deprecated: use `description` and
            `authorization_level` instead.
        """
        authorization_level = authorization_level or auth
        description = description or descr
        return super().parser(
            condition=condition,
            description=description,
            authorization_level=authorization_level,
            argument=argument
        )

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

    def button(self, data=None, descr='', auth='admin',
               authorization_level=None, prefix=None, description=None,
               separator=None):
        """Define a bot button.

        `descr` and `auth` parameters are deprecated: use `description` and
            `authorization_level` instead.
        `data` parameter renamed `prefix`.
        """
        authorization_level = authorization_level or auth
        description = description or descr
        prefix = prefix or data
        return super().button(
            prefix=prefix,
            separator=separator,
            description=description,
            authorization_level=authorization_level,
        )

    def query(self, condition, descr='', auth='admin', description=None,
              authorization_level=None):
        """Define an inline query.

        `descr` and `auth` parameters are deprecated: use `description` and
            `authorization_level` instead.
        """
        authorization_level = authorization_level or auth
        description = description or descr
        return super().query(
            condition=condition,
            description=description,
            authorization_level=authorization_level,
        )

    async def edit_message(self, update, *args, **kwargs):
        """Edit given update with given *args and **kwargs.

        This method is deprecated: use `edit_message_text` instead.
        """
        return await self.edit_message_text(
            *args,
            update=update,
            **kwargs
        )

    async def send_message(self, answer=dict(), chat_id=None, text='',
                           parse_mode="HTML", disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None,
                           reply_markup=None, update=dict(),
                           reply_to_update=False, send_default_keyboard=True):
        """Send a message.

        This method is deprecated: use `super().send_message` instead.
        """
        if update is None:
            update = dict()
        parameters = dict()
        for parameter, value in locals().items():
            if parameter in ['self', 'answer', 'parameters', '__class__']:
                continue
            if parameter in answer:
                parameters[parameter] = answer[parameter]
            else:
                parameters[parameter] = value
        if type(parameters['chat_id']) is dict:
            parameters['update'] = parameters['chat_id']
            del parameters['chat_id']
        return await super().send_message(**parameters)

    async def send_photo(self, chat_id=None, answer=dict(),
                         photo=None, caption='', parse_mode='HTML',
                         disable_notification=None, reply_to_message_id=None,
                         reply_markup=None, use_stored=True,
                         second_chance=False, use_stored_file_id=None,
                         update=dict(), reply_to_update=False,
                         send_default_keyboard=True):
        """Send a photo.

        This method is deprecated: use `super().send_photo` instead.
        """
        if update is None:
            update = dict()
        if use_stored is not None:
            use_stored_file_id = use_stored
        parameters = dict()
        for parameter, value in locals().items():
            if parameter in ['self', 'answer', 'parameters', '__class__',
                             'second_chance', 'use_stored']:
                continue
            if parameter in answer:
                parameters[parameter] = answer[parameter]
            else:
                parameters[parameter] = value
        if type(parameters['chat_id']) is dict:
            parameters['update'] = parameters['chat_id']
            del parameters['chat_id']
        return await super().send_photo(**parameters)

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
        await sleep_until(when)
        try:
            await self.editMessageCaption(
                inline_message_id=inline_message_id,
                text="Time over"
            )
        except Exception:
            try:
                await self.editMessageText(
                    inline_message_id=inline_message_id,
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

    async def save_picture(self, update, file_name=None, path='img/',
                           extension='jpg'):
        """Store `update` picture as `path`/`file_name`.`extension`."""
        if not path.endswith('/'):
            path = '{p}/'.format(
                p=path
            )
        if not os.path.isdir(path):
            path = '{path}/img/'.format(
                path=self.path
            )
        if file_name is None:
            file_name = get_secure_key(length=6)
        if file_name.endswith('.'):
            file_name = file_name[:-1]
        complete_file_name = '{path}{name}.{ext}'.format(
            path=self.path,
            name=file_name,
            ext=extension
        )
        while os.path.isfile(complete_file_name):
            file_name += get_secure_key(length=1)
            complete_file_name = '{path}{name}.{ext}'.format(
                path=self.path,
                name=file_name,
                ext=extension
            )
        try:
            await self.download_file(
                update['photo'][-1]['file_id'],
                complete_file_name
            )
        except Exception as e:
            return dict(
                result=1,  # Error
                file_name=None,
                error=e
            )
        return dict(
            result=0,  # Success
            file_name=complete_file_name,
            error=None
        )

    def stop_bots(self):
        """Exit script with code 0.

        This method is deprecated: use `Bot.stop` instead.
        """
        self.__class__.stop(
            message=f"Stopping bots via bot `@{self.name}` method.",
            final_state=0
        )

    def restart_bots(self):
        """Restart the script exiting with code 65.

        This method is deprecated: use `Bot.stop` instead.
        """
        self.__class__.stop(
            message=f"Restarting bots via bot `@{self.name}` method.",
            final_state=65
        )

    async def delete_and_obscure_messages(self):
        """Run after stop, before the script exits.

        Await final tasks, obscure and delete pending messages,
            log current operation (stop/restart).
        """
        for message in self.to_be_destroyed:
            try:
                await self.delete_message(message)
            except Exception as e:
                logging.error(
                    "Couldn't delete message\n{}\n\n{}".format(
                        message,
                        e
                    )
                )
        for inline_message_id in self.to_be_obscured:
            try:
                await self.editMessageCaption(
                    inline_message_id,
                    text="Time over"
                )
            except Exception:
                try:
                    await self.editMessageText(
                        inline_message_id=inline_message_id,
                        text="Time over"
                    )
                except Exception as e:
                    logging.error(
                        "Couldn't obscure message\n{}\n\n{}".format(
                            inline_message_id,
                            e
                        )
                    )

    @classmethod
    def run(cls, loop=None, *args, **kwargs):
        """Call this method to run the async bots.

        This method is deprecated: use `super(Bot, cls).run` instead.
        `loop` must not be determined outside that method.
        """
        for bot in cls.bots:
            bot.additional_task('AFTER')(bot.delete_and_obscure_messages)
        return super(Bot, cls).run(*args, **kwargs)
