"""Provide a simple Bot object, mirroring Telegram API methods.

camelCase methods mirror API directly, while snake_case ones act as middlewares
    someway.
"""

# Standard library modules
import asyncio
import logging

# Third party modules
import aiohttp
from aiohttp import web

# Project modules
from utilities import get_secure_key

# Do not log aiohttp `INFO` and `DEBUG` levels
logging.getLogger('aiohttp').setLevel(logging.WARNING)


class TelegramError(Exception):
    """Telegram API exceptions class."""

    def __init__(self, error_code=0, description=None, ok=False):
        """Get an error response and return corresponding Exception."""
        self._code = error_code
        if description is None:
            self._description = 'Generic error'
        else:
            self._description = description
        super().__init__(self.description)

    @property
    def code(self):
        """Telegram error code."""
        return self._code

    @property
    def description(self):
        """Human-readable description of error."""
        return f"Error {self.code}: {self._description}"


class TelegramBot(object):
    """Provide python method having the same signature as Telegram API methods.

    All mirrored methods are camelCase.
    """

    loop = asyncio.get_event_loop()
    app = web.Application(loop=loop)
    sessions_timeouts = {
        'getUpdates': dict(
            timeout=35,
            close=False
        ),
        'sendMessage': dict(
            timeout=20,
            close=False
        )
    }

    def __init__(self, token):
        """Set bot token and store HTTP sessions."""
        self._token = token
        self.sessions = dict()

    @property
    def token(self):
        """Telegram API bot token."""
        return self._token

    @staticmethod
    def check_telegram_api_json(response):
        """Take a json Telegram response, check it and return its content.

        Example of well-formed json Telegram responses:
        {
            "ok": False,
            "error_code": 401,
            "description": "Unauthorized"
        }
        {
            "ok": True,
            "result": ...
        }
        """
        assert 'ok' in response, (
            "All Telegram API responses have an `ok` field."
        )
        if not response['ok']:
            raise TelegramError(**response)
        return response['result']

    @staticmethod
    def adapt_parameters(parameters, exclude=[]):
        """Build a aiohttp.FormData object from given `paramters`.

        Exclude `self`, empty values and parameters in `exclude` list.
        Cast integers to string to avoid TypeError during json serialization.
        """
        exclude.append('self')
        data = aiohttp.FormData()
        for key, value in parameters.items():
            if not (key in exclude or value is None):
                if type(value) is int:
                    value = str(value)
                data.add_field(key, value)
        return data

    def get_session(self, api_method):
        """According to API method, return proper session and information.

        Return a tuple (session, session_must_be_closed)
        session : aiohttp.ClientSession
            Client session with proper timeout
        session_must_be_closed : bool
            True if session must be closed after being used once
        """
        cls = self.__class__
        if api_method in cls.sessions_timeouts:
            if api_method not in self.sessions:
                self.sessions[api_method] = aiohttp.ClientSession(
                    loop=cls.loop,
                    timeout=aiohttp.ClientTimeout(
                        total=cls.sessions_timeouts[api_method]['timeout']
                    )
                )
            session = self.sessions[api_method]
            session_must_be_closed = cls.sessions_timeouts[api_method]['close']
        else:
            session = aiohttp.ClientSession(
                loop=cls.loop,
                timeout=aiohttp.ClientTimeout(total=None)
            )
            session_must_be_closed = True
        return session, session_must_be_closed

    async def api_request(self, method, parameters={}, exclude=[]):
        """Return the result of a Telegram bot API request, or an Exception.

        Opened sessions will be used more than one time (if appropriate) and
            will be closed on `Bot.app.cleanup`.
        Result may be a Telegram API json response, None, or Exception.
        """
        response_object = None
        session, session_must_be_closed = self.get_session(method)
        parameters = self.adapt_parameters(parameters, exclude=exclude)
        try:
            async with session.post(
                "https://api.telegram.org/bot"
                f"{self.token}/{method}",
                data=parameters
            ) as response:
                try:
                    response_object = self.check_telegram_api_json(
                        await response.json()  # Telegram returns json objects
                    )
                except TelegramError as e:
                    logging.error(f"{e}")
                    return e
                except Exception as e:
                    logging.error(f"{e}", exc_info=True)
                    return e
        except asyncio.TimeoutError as e:
            logging.info(f"{e}: {method} API call timed out")
        finally:
            if session_must_be_closed:
                await session.close()
        return response_object

    async def getMe(self):
        """Get basic information about the bot in form of a User object.

        Useful to test `self.token`.
        See https://core.telegram.org/bots/api#getme for details.
        """
        return await self.api_request(
            'getMe',
        )

    async def getUpdates(self, offset, timeout, limit, allowed_updates):
        """Get a list of updates starting from `offset`.

        If there are no updates, keep the request hanging until `timeout`.
        If there are more than `limit` updates, retrieve them in packs of
            `limit`.
        Allowed update types (empty list to allow all).
        See https://core.telegram.org/bots/api#getupdates for details.
        """
        return await self.api_request(
            method='getUpdates',
            parameters=locals()
        )

    async def setWebhook(self, url=None, certificate=None,
                         max_connections=None, allowed_updates=None):
        """Set or remove a webhook. Telegram will post to `url` new updates.

        See https://core.telegram.org/bots/api#setwebhook for details.
        """
        if url is None:
            url = self.webhook_url
        if allowed_updates is None:
            allowed_updates = self.allowed_updates
        if max_connections is None:
            max_connections = self.max_connections
        if certificate is None:
            certificate = self.certificate
        if type(certificate) is str:
            try:
                certificate = open(certificate, 'r')
            except FileNotFoundError as e:
                logging.error(f"{e}")
                certificate = None
        certificate = dict(
            file=certificate
        )
        return await self.api_request(
            'setWebhook',
            parameters=locals()
        )

    async def deleteWebhook(self):
        """Remove webhook integration and switch back to getUpdate.

        See https://core.telegram.org/bots/api#deletewebhook for details.
        """
        return await self.api_request(
            'deleteWebhook',
        )

    async def getWebhookInfo(self):
        """Get current webhook status.

        See https://core.telegram.org/bots/api#getwebhookinfo for details.
        """
        return await self.api_request(
            'getWebhookInfo',
        )

    async def sendMessage(self, chat_id, text,
                          parse_mode=None,
                          disable_web_page_preview=None,
                          disable_notification=None,
                          reply_to_message_id=None,
                          reply_markup=None):
        """Send a text message. On success, return it.

        See https://core.telegram.org/bots/api#sendmessage for details.
        """
        return await self.api_request(
            'sendMessage',
            parameters=locals()
        )

    async def forwardMessage(self, chat_id, from_chat_id, message_id,
                             disable_notification=None):
        """Forward a message.

        See https://core.telegram.org/bots/api#forwardmessage for details.
        """
        return await self.api_request(
            'forwardMessage',
            parameters=locals()
        )

    async def sendPhoto(self, chat_id, photo,
                        caption=None,
                        parse_mode=None,
                        disable_notification=None,
                        reply_to_message_id=None,
                        reply_markup=None):
        """Send a photo from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendphoto for details.
        """
        return await self.api_request(
            'sendPhoto',
            parameters=locals()
        )

    async def sendAudio(self, chat_id, audio,
                        caption=None,
                        parse_mode=None,
                        duration=None,
                        performer=None,
                        title=None,
                        thumb=None,
                        disable_notification=None,
                        reply_to_message_id=None,
                        reply_markup=None):
        """Send an audio file from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendaudio for details.
        """
        return await self.api_request(
            'sendAudio',
            parameters=locals()
        )

    async def sendDocument(self, chat_id, document,
                           thumb=None,
                           caption=None,
                           parse_mode=None,
                           disable_notification=None,
                           reply_to_message_id=None,
                           reply_markup=None):
        """Send a document from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#senddocument for details.
        """
        return await self.api_request(
            'sendDocument',
            parameters=locals()
        )

    async def sendVideo(self, chat_id, video,
                        duration=None,
                        width=None,
                        height=None,
                        thumb=None,
                        caption=None,
                        parse_mode=None,
                        supports_streaming=None,
                        disable_notification=None,
                        reply_to_message_id=None,
                        reply_markup=None):
        """Send a video from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendvideo for details.
        """
        return await self.api_request(
            'sendVideo',
            parameters=locals()
        )

    async def sendAnimation(self, chat_id, animation,
                            duration=None,
                            width=None,
                            height=None,
                            thumb=None,
                            caption=None,
                            parse_mode=None,
                            disable_notification=None,
                            reply_to_message_id=None,
                            reply_markup=None):
        """Send animation files (GIF or H.264/MPEG-4 AVC video without sound).

        See https://core.telegram.org/bots/api#sendanimation for details.
        """
        return await self.api_request(
            'method_name',
            parameters=locals()
        )

    async def method_name(
        self, chat_id, reply_to_message_id=None, reply_markup=None
    ):
        """method_name.

        See https://core.telegram.org/bots/api#method_name for details.
        """
        return await self.api_request(
            'method_name',
            parameters=locals()
        )


class Bot(TelegramBot):
    """Simple Bot object, providing methods corresponding to Telegram bot API.

    Multiple Bot() instances may be run together, along with a aiohttp web app.
    """

    bots = []
    runner = None
    local_host = 'localhost'
    port = 3000
    final_state = 0

    def __init__(
        self, token, hostname='', certificate=None, max_connections=40,
        allowed_updates=[]
    ):
        """Init a bot instance.

        token : str
            Telegram bot API token.
        hostname : str
            Domain (or public IP address) for webhooks.
        certificate : str
            Path to domain certificate.
        max_connections : int (1 - 100)
            Maximum number of HTTPS connections allowed.
        allowed_updates : List(str)
            Allowed update types (empty list to allow all).
        """
        self.__class__.bots.append(self)
        super().__init__(token)
        self._offset = 0
        self._hostname = hostname
        self._certificate = certificate
        self._max_connections = max_connections
        self._allowed_updates = allowed_updates
        self._session_token = get_secure_key(length=10)
        self._name = None
        self._telegram_id = None
        return

    @property
    def hostname(self):
        """Hostname for the webhook URL.

        It must be a public domain or IP address. Port may be specified.
        A custom webhook url, including bot token and a random token, will be
        generated for Telegram to post new updates.
        """
        return self._hostname

    @property
    def webhook_url(self):
        """URL where Telegram servers should post new updates.

        It must be a public domain name or IP address. Port may be specified.
        """
        if not self.hostname:
            return ''
        return (
            f"{self.hostname}/webhook/{self.token}_{self.session_token}/"
        )

    @property
    def webhook_local_address(self):
        """Local address where Telegram updates are routed by revers proxy."""
        return (
            f"/webhook/{self.token}_{self.session_token}/"
        )

    @property
    def certificate(self):
        """Public certificate for `webhook_url`.

        May be self-signed
        """
        return self._certificate

    @property
    def max_connections(self):
        """Maximum number of simultaneous HTTPS connections allowed.

        Telegram will open as many connections as possible to boost bot’s
            throughput, lower values limit the load on bot‘s server.
        """
        return self._max_connections

    @property
    def allowed_updates(self):
        """List of update types to be retrieved.

        Empty list to allow all updates.
        """
        return self._allowed_updates

    @property
    def name(self):
        """Bot name."""
        return self._name

    @property
    def telegram_id(self):
        """Telegram id of this bot."""
        return self._telegram_id

    @property
    def session_token(self):
        """Return a token generated with the current instantiation."""
        return self._session_token

    @property
    def offset(self):
        """Return last update id.

        Useful to ignore repeated updates and restore original update order.
        """
        return self._offset

    async def webhook_feeder(self, request):
        """Handle incoming HTTP `request`s.

        Get data, feed webhook and return and OK message.
        """
        update = await request.json()
        asyncio.ensure_future(
            self.route_update(update)
        )
        return web.Response(
            body='OK'.encode('utf-8')
        )

    async def get_me(self):
        """Get bot information.

        Restart bots if bot can't be got.
        """
        try:
            me = await self.getMe()
            if isinstance(me, Exception):
                raise me
            elif me is None:
                raise Exception('getMe returned None')
            self._name = me["username"]
            self._telegram_id = me['id']
        except Exception as e:
            logging.error(
                f"Information about bot with token {self.token} could not "
                f"be got. Restarting in 5 minutes...\n\n"
                f"Error information:\n{e}"
            )
            await asyncio.sleep(5*60)
            self.__class__.stop(
                65,
                f"Information about bot with token {self.token} could not "
                "be got. Restarting..."
            )

    def setup(self):
        """Make bot ask for updates and handle responses."""
        if not self.webhook_url:
            asyncio.ensure_future(self.get_updates())
        else:
            asyncio.ensure_future(self.set_webhook())
            self.__class__.app.router.add_route(
                'POST', self.webhook_local_address, self.webhook_feeder
            )

    async def close_sessions(self):
        """Close open sessions."""
        for session_name, session in self.sessions.items():
            await session.close()

    async def set_webhook(self, url=None, certificate=None,
                          max_connections=None, allowed_updates=None):
        """Set a webhook if token is valid."""
        # Return if token is invalid
        await self.get_me()
        if self.name is None:
            return
        webhook_was_set = await self.setWebhook(
            url=url, certificate=certificate, max_connections=max_connections,
            allowed_updates=allowed_updates
        )  # `setWebhook` API method returns `True` on success
        webhook_information = await self.getWebhookInfo()
        if webhook_was_set:
            logging.info(
                f"Webhook was set correctly.\n"
                f"Webhook information: {webhook_information}"
            )
        else:
            logging.error(
                f"Failed to set webhook!\n"
                f"Webhook information: {webhook_information}"
            )

    async def get_updates(self, timeout=30, limit=100, allowed_updates=None,
                          error_cooldown=10):
        """Get updates using long polling.

        timeout : int
            Timeout set for Telegram servers. Make sure that connection timeout
            is greater than `timeout`.
        limit : int (1 - 100)
            Max number of updates to be retrieved.
        allowed_updates : List(str)
            List of update types to be retrieved.
            Empty list to allow all updates.
            None to fallback to class default.
        """
        # Return if token is invalid
        await self.get_me()
        if self.name is None:
            return
        # Set custom list of allowed updates or fallback to class default list
        if allowed_updates is None:
            allowed_updates = self.allowed_updates
        await self.deleteWebhook()  # Remove eventually active webhook
        update = None  # Do not update offset if no update is received
        while True:
            updates = await self.getUpdates(
                offset=self._offset,
                timeout=timeout,
                limit=limit,
                allowed_updates=allowed_updates
            )
            if updates is None:
                continue
            elif isinstance(updates, TelegramError):
                logging.error(
                    f"Waiting {error_cooldown} seconds before trying again..."
                )
                await asyncio.sleep(error_cooldown)
                continue
            for update in updates:
                asyncio.ensure_future(self.route_update(update))
            if update is not None:
                self._offset = update['update_id'] + 1

    async def route_update(self, update):
        """Pass `update` to proper method.

        Work in progress: at the moment the update gets simply printed.
        """
        print(update)
        await self.sendMessage(
            chat_id=update['message']['chat']['id'],
            text="Ciaone!"
        )
        with open('rrr.txt', 'r') as _file:
            await self.sendDocument(
                chat_id=update['message']['chat']['id'],
                document=_file,
                caption="Prova!"
            )
        return

    @classmethod
    async def start_app(cls):
        """Start running `aiohttp.web.Application`.

        It will route webhook-received updates and other custom paths.
        """
        assert cls.local_host is not None, "Invalid local host"
        assert cls.port is not None, "Invalid port"
        cls.runner = web.AppRunner(cls.app)
        await cls.runner.setup()
        cls.server = web.TCPSite(cls.runner, cls.local_host, cls.port)
        await cls.server.start()
        logging.info(f"App running at http://{cls.local_host}:{cls.port}")

    @classmethod
    async def stop_app(cls):
        """Close bot sessions and cleanup."""
        for bot in cls.bots:
            await bot.close_sessions()
        await cls.runner.cleanup()

    @classmethod
    def stop(cls, message, final_state=0):
        """Log a final `message`, stop loop and set exiting `code`.

        All bots and the web app will be terminated gracefully.
        The final state may be retrieved to get information about what stopped
            the bots.
        """
        logging.info(message)
        cls.final_state = final_state
        cls.loop.stop()
        return

    @classmethod
    def run(cls, local_host=None, port=None):
        """Run aiohttp web app and all Bot instances.

        Each bot will receive updates via long polling or webhook according to
            its initialization parameters.
        A single aiohttp.web.Application instance will be run (cls.app) on
            local_host:port and it may serve custom-defined routes as well.
        """
        if local_host is not None:
            cls.local_host = local_host
        if port is not None:
            cls.port = port
        for bot in cls.bots:
            bot.setup()
        asyncio.ensure_future(cls.start_app())
        try:
            cls.loop.run_forever()
        except KeyboardInterrupt:
            logging.info("Stopped by KeyboardInterrupt")
        except Exception as e:
            logging.error(f"{e}", exc_info=True)
        finally:
            cls.loop.run_until_complete(cls.stop_app())
        return cls.final_state
