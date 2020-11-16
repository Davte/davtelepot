"""This module provides a python mirror for Telegram bot API.

All methods and parameters are the same as the original json API.
A simple aiohttp asynchronous web client is used to make requests.
"""

# Standard library modules
import asyncio
import datetime
import io
import json
import logging

from typing import Dict, Union, List, IO

# Third party modules
import aiohttp
import aiohttp.web


class TelegramError(Exception):
    """Telegram API exceptions class."""

    # noinspection PyUnusedLocal
    def __init__(self, error_code=0, description=None, ok=False,
                 *args, **kwargs):
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


class ChatPermissions(dict):
    """Actions that a non-administrator user is allowed to take in a chat."""
    def __init__(self,
                 can_send_messages: bool = True,
                 can_send_media_messages: bool = True,
                 can_send_polls: bool = True,
                 can_send_other_messages: bool = True,
                 can_add_web_page_previews: bool = True,
                 can_change_info: bool = True,
                 can_invite_users: bool = True,
                 can_pin_messages: bool = True):
        super().__init__(self)
        self['can_send_messages'] = can_send_messages
        self['can_send_media_messages'] = can_send_media_messages
        self['can_send_polls'] = can_send_polls
        self['can_send_other_messages'] = can_send_other_messages
        self['can_add_web_page_previews'] = can_add_web_page_previews
        self['can_change_info'] = can_change_info
        self['can_invite_users'] = can_invite_users
        self['can_pin_messages'] = can_pin_messages


class Command(dict):
    def __init__(self,
                 command: str = None,
                 description: str = None):
        super().__init__(self)
        self['command'] = command
        self['description'] = description


# This class needs to mirror Telegram API, so camelCase method are needed
# noinspection PyPep8Naming
class TelegramBot:
    """Provide python method having the same signature as Telegram API methods.

    All mirrored methods are camelCase.
    """

    loop = asyncio.get_event_loop()
    app = aiohttp.web.Application()
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
    _absolute_cooldown_timedelta = datetime.timedelta(seconds=1/30)
    _per_chat_cooldown_timedelta = datetime.timedelta(seconds=1)
    _allowed_messages_per_group_per_minute = 20

    def __init__(self, token):
        """Set bot token and store HTTP sessions."""
        self._token = token
        self.sessions = dict()
        self._flood_wait = 0
        # Each `telegram_id` key has a list of `datetime.datetime` as value
        self.last_sending_time = {
            'absolute': (
                datetime.datetime.now()
                - self.absolute_cooldown_timedelta
            ),
            0: []
        }

    @property
    def token(self):
        """Telegram API bot token."""
        return self._token

    @property
    def flood_wait(self):
        """Seconds to wait before next API requests."""
        return self._flood_wait

    @property
    def absolute_cooldown_timedelta(self):
        """Return time delta to wait between messages (any chat).

        Return class value (all bots have the same limits).
        """
        return self.__class__._absolute_cooldown_timedelta

    @property
    def per_chat_cooldown_timedelta(self):
        """Return time delta to wait between messages in a chat.

        Return class value (all bots have the same limits).
        """
        return self.__class__._per_chat_cooldown_timedelta

    @property
    def longest_cooldown_timedelta(self):
        """Return the longest cooldown timedelta.

        Updates sent more than `longest_cooldown_timedelta` ago will be
            forgotten.
        """
        return datetime.timedelta(minutes=1)

    @property
    def allowed_messages_per_group_per_minute(self):
        """Return maximum number of messages allowed in a group per minute.

        Group, supergroup and channels are considered.
        Return class value (all bots have the same limits).
        """
        return self.__class__._allowed_messages_per_group_per_minute

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
    def adapt_parameters(parameters, exclude=None):
        """Build a aiohttp.FormData object from given `parameters`.

        Exclude `self`, empty values and parameters in `exclude` list.
        Cast integers to string to avoid TypeError during json serialization.
        """
        if exclude is None:
            exclude = []
        exclude.append('self')
        # quote_fields=False, otherwise some file names cause troubles
        data = aiohttp.FormData(quote_fields=False)
        for key, value in parameters.items():
            if not (key in exclude or value is None):
                if (
                    type(value) in (int, list,)
                    or (type(value) is dict and 'file' not in value)
                ):
                    value = json.dumps(value, separators=(',', ':'))
                data.add_field(key, value)
        return data

    @staticmethod
    def prepare_file_object(file: Union[str, IO, dict, None]
                            ) -> Union[Dict[str, IO], None]:
        if type(file) is str:
            try:
                file = open(file, 'r')
            except FileNotFoundError as e:
                logging.error(f"{e}")
                file = None
        if isinstance(file, io.IOBase):
            file = dict(file=file)
        return file

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

    def set_flood_wait(self, flood_wait):
        """Wait `flood_wait` seconds before next request."""
        self._flood_wait = flood_wait

    async def prevent_flooding(self, chat_id):
        """Await until request may be sent safely.

        Telegram flood control won't allow too many API requests in a small
            period.
        Exact limits are unknown, but less than 30 total private chat messages
            per second, less than 1 private message per chat and less than 20
            group chat messages per chat per minute should be safe.
        """
        now = datetime.datetime.now
        if type(chat_id) is int and chat_id > 0:
            while (
                now() < (
                    self.last_sending_time['absolute']
                    + self.absolute_cooldown_timedelta
                )
            ) or (
                chat_id in self.last_sending_time
                and (
                    now() < (
                        self.last_sending_time[chat_id]
                        + self.per_chat_cooldown_timedelta
                    )
                )
            ):
                await asyncio.sleep(
                    self.absolute_cooldown_timedelta.seconds
                )
            self.last_sending_time[chat_id] = now()
        else:
            while (
                now() < (
                    self.last_sending_time['absolute']
                    + self.absolute_cooldown_timedelta
                )
            ) or (
                chat_id in self.last_sending_time
                and len(
                    [
                        sending_datetime
                        for sending_datetime in self.last_sending_time[chat_id]
                        if sending_datetime >= (
                            now()
                            - datetime.timedelta(minutes=1)
                        )
                    ]
                ) >= self.allowed_messages_per_group_per_minute
            ) or (
                chat_id in self.last_sending_time
                and len(self.last_sending_time[chat_id]) > 0
                and now() < (
                    self.last_sending_time[chat_id][-1]
                    + self.per_chat_cooldown_timedelta
                )
            ):
                await asyncio.sleep(0.5)
            if chat_id not in self.last_sending_time:
                self.last_sending_time[chat_id] = []
            self.last_sending_time[chat_id].append(now())
            self.last_sending_time[chat_id] = [
                sending_datetime
                for sending_datetime in self.last_sending_time[chat_id]
                if sending_datetime >= (
                    now()
                    - self.longest_cooldown_timedelta
                )
            ]
        self.last_sending_time['absolute'] = now()
        return

    async def api_request(self, method, parameters=None, exclude=None):
        """Return the result of a Telegram bot API request, or an Exception.

        Opened sessions will be used more than one time (if appropriate) and
            will be closed on `Bot.app.cleanup`.
        Result may be a Telegram API json response, None, or Exception.
        """
        if exclude is None:
            exclude = []
        if parameters is None:
            parameters = {}
        response_object = None
        session, session_must_be_closed = self.get_session(method)
        # Prevent Telegram flood control for all methods having a `chat_id`
        if 'chat_id' in parameters:
            await self.prevent_flooding(parameters['chat_id'])
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
                    logging.error(f"API error response - {e}")
                    if e.code == 420:  # Flood error!
                        try:
                            flood_wait = int(
                                e.description.split('_')[-1]
                            ) + 30
                        except Exception as e:
                            logging.error(f"{e}")
                            flood_wait = 5*60
                        logging.critical(
                            "Telegram antiflood control triggered!\n"
                            f"Wait {flood_wait} seconds before making another "
                            "request"
                        )
                        self.set_flood_wait(flood_wait)
                    response_object = e
                except Exception as e:
                    logging.error(f"{e}", exc_info=True)
                    response_object = e
        except asyncio.TimeoutError as e:
            logging.info(f"{e}: {method} API call timed out")
        except Exception as e:
            logging.info(f"Unexpected exception:\n{e}")
            response_object = e
        finally:
            if session_must_be_closed and not session.closed:
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

    async def getUpdates(self, offset: int = None,
                         limit: int = None,
                         timeout: int = None,
                         allowed_updates: List[str] = None):
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

    async def setWebhook(self, url: str,
                         certificate: Union[str, IO] = None,
                         ip_address: str = None,
                         max_connections: int = None,
                         allowed_updates: List[str] = None,
                         drop_pending_updates: bool = None):
        """Set or remove a webhook. Telegram will post to `url` new updates.

        See https://core.telegram.org/bots/api#setwebhook for details.
        """
        certificate = self.prepare_file_object(certificate)
        result = await self.api_request(
            'setWebhook',
            parameters=locals()
        )
        if type(certificate) is dict:  # Close certificate file, if it was open
            certificate['file'].close()
        return result

    async def deleteWebhook(self, drop_pending_updates: bool = None):
        """Remove webhook integration and switch back to getUpdate.

        See https://core.telegram.org/bots/api#deletewebhook for details.
        """
        return await self.api_request(
            'deleteWebhook',
            parameters=locals()
        )

    async def getWebhookInfo(self):
        """Get current webhook status.

        See https://core.telegram.org/bots/api#getwebhookinfo for details.
        """
        return await self.api_request(
            'getWebhookInfo',
        )

    async def sendMessage(self, chat_id: Union[int, str], text: str,
                          parse_mode: str = None,
                          entities: List[dict] = None,
                          disable_web_page_preview: bool = None,
                          disable_notification: bool = None,
                          reply_to_message_id: int = None,
                          allow_sending_without_reply: bool = None,
                          reply_markup=None):
        """Send a text message. On success, return it.

        See https://core.telegram.org/bots/api#sendmessage for details.
        """
        return await self.api_request(
            'sendMessage',
            parameters=locals()
        )

    async def forwardMessage(self, chat_id: Union[int, str],
                             from_chat_id: Union[int, str],
                             message_id: int,
                             disable_notification: bool = None):
        """Forward a message.

        See https://core.telegram.org/bots/api#forwardmessage for details.
        """
        return await self.api_request(
            'forwardMessage',
            parameters=locals()
        )

    async def sendPhoto(self, chat_id: Union[int, str], photo,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        disable_notification: bool = None,
                        reply_to_message_id: int = None,
                        allow_sending_without_reply: bool = None,
                        reply_markup=None):
        """Send a photo from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendphoto for details.
        """
        return await self.api_request(
            'sendPhoto',
            parameters=locals()
        )

    async def sendAudio(self, chat_id: Union[int, str], audio,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        duration: int = None,
                        performer: str = None,
                        title: str = None,
                        thumb=None,
                        disable_notification: bool = None,
                        reply_to_message_id: int = None,
                        allow_sending_without_reply: bool = None,
                        reply_markup=None):
        """Send an audio file from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendaudio for details.
        """
        return await self.api_request(
            'sendAudio',
            parameters=locals()
        )

    async def sendDocument(self, chat_id: Union[int, str], document,
                           thumb=None,
                           caption: str = None,
                           parse_mode: str = None,
                           caption_entities: List[dict] = None,
                           disable_content_type_detection: bool = None,
                           disable_notification: bool = None,
                           reply_to_message_id: int = None,
                           allow_sending_without_reply: bool = None,
                           reply_markup=None):
        """Send a document from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#senddocument for details.
        """
        return await self.api_request(
            'sendDocument',
            parameters=locals()
        )

    async def sendVideo(self, chat_id: Union[int, str], video,
                        duration: int = None,
                        width: int = None,
                        height: int = None,
                        thumb=None,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        supports_streaming: bool = None,
                        disable_notification: bool = None,
                        reply_to_message_id: int = None,
                        allow_sending_without_reply: bool = None,
                        reply_markup=None):
        """Send a video from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendvideo for details.
        """
        return await self.api_request(
            'sendVideo',
            parameters=locals()
        )

    async def sendAnimation(self, chat_id: Union[int, str], animation,
                            duration: int = None,
                            width: int = None,
                            height: int = None,
                            thumb=None,
                            caption: str = None,
                            parse_mode: str = None,
                            caption_entities: List[dict] = None,
                            disable_notification: bool = None,
                            reply_to_message_id: int = None,
                            allow_sending_without_reply: bool = None,
                            reply_markup=None):
        """Send animation files (GIF or H.264/MPEG-4 AVC video without sound).

        See https://core.telegram.org/bots/api#sendanimation for details.
        """
        return await self.api_request(
            'sendAnimation',
            parameters=locals()
        )

    async def sendVoice(self, chat_id: Union[int, str], voice,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        duration: int = None,
                        disable_notification: bool = None,
                        reply_to_message_id: int = None,
                        allow_sending_without_reply: bool = None,
                        reply_markup=None):
        """Send an audio file to be displayed as playable voice message.

        `voice` must be in an .ogg file encoded with OPUS.
        See https://core.telegram.org/bots/api#sendvoice for details.
        """
        return await self.api_request(
            'sendVoice',
            parameters=locals()
        )

    async def sendVideoNote(self, chat_id: Union[int, str], video_note,
                            duration: int = None,
                            length: int = None,
                            thumb=None,
                            disable_notification: bool = None,
                            reply_to_message_id: int = None,
                            allow_sending_without_reply: bool = None,
                            reply_markup=None):
        """Send a rounded square mp4 video message of up to 1 minute long.

        See https://core.telegram.org/bots/api#sendvideonote for details.
        """
        return await self.api_request(
            'sendVideoNote',
            parameters=locals()
        )

    async def sendMediaGroup(self, chat_id: Union[int, str], media: list,
                             disable_notification: bool = None,
                             reply_to_message_id: int = None,
                             allow_sending_without_reply: bool = None):
        """Send a group of photos or videos as an album.

        `media` must be a list of `InputMediaPhoto` and/or `InputMediaVideo`
            objects.
        See https://core.telegram.org/bots/api#sendmediagroup for details.
        """
        return await self.api_request(
            'sendMediaGroup',
            parameters=locals()
        )

    async def sendLocation(self, chat_id: Union[int, str],
                           latitude: float, longitude: float,
                           horizontal_accuracy: float = None,
                           live_period=None,
                           heading: int = None,
                           proximity_alert_radius: int = None,
                           disable_notification: bool = None,
                           reply_to_message_id: int = None,
                           allow_sending_without_reply: bool = None,
                           reply_markup=None):
        """Send a point on the map. May be kept updated for a `live_period`.

        See https://core.telegram.org/bots/api#sendlocation for details.
        """
        if horizontal_accuracy:  # Horizontal accuracy: 0-1500 m [float].
            horizontal_accuracy = max(0.0, min(horizontal_accuracy, 1500.0))
        if live_period:
            live_period = max(60, min(live_period, 86400))
        if heading:  # Direction in which the user is moving, 1-360°
            heading = max(1, min(heading, 360))
        if proximity_alert_radius:  # Distance 1-100000 m
            proximity_alert_radius = max(1, min(proximity_alert_radius, 100000))
        return await self.api_request(
            'sendLocation',
            parameters=locals()
        )

    async def editMessageLiveLocation(self, latitude: float, longitude: float,
                                      chat_id: Union[int, str] = None,
                                      message_id: int = None,
                                      inline_message_id: str = None,
                                      horizontal_accuracy: float = None,
                                      heading: int = None,
                                      proximity_alert_radius: int = None,
                                      reply_markup=None):
        """Edit live location messages.

        A location can be edited until its live_period expires or editing is
            explicitly disabled by a call to stopMessageLiveLocation.
        The message to be edited may be identified through `inline_message_id`
            OR the couple (`chat_id`, `message_id`).
        See https://core.telegram.org/bots/api#editmessagelivelocation
            for details.
        """
        if inline_message_id is None and (chat_id is None or message_id is None):
            logging.error("Invalid target chat!")
        if horizontal_accuracy:  # Horizontal accuracy: 0-1500 m [float].
            horizontal_accuracy = max(0.0, min(horizontal_accuracy, 1500.0))
        if heading:  # Direction in which the user is moving, 1-360°
            heading = max(1, min(heading, 360))
        if proximity_alert_radius:  # Distance 1-100000 m
            proximity_alert_radius = max(1, min(proximity_alert_radius, 100000))
        return await self.api_request(
            'editMessageLiveLocation',
            parameters=locals()
        )

    async def stopMessageLiveLocation(self,
                                      chat_id: Union[int, str] = None,
                                      message_id: int = None,
                                      inline_message_id: int = None,
                                      reply_markup=None):
        """Stop updating a live location message before live_period expires.

        The position to be stopped may be identified through
            `inline_message_id` OR the couple (`chat_id`, `message_id`).
        `reply_markup` type may be only `InlineKeyboardMarkup`.
        See https://core.telegram.org/bots/api#stopmessagelivelocation
            for details.
        """
        return await self.api_request(
            'stopMessageLiveLocation',
            parameters=locals()
        )

    async def sendVenue(self, chat_id: Union[int, str],
                        latitude: float, longitude: float,
                        title: str, address: str,
                        foursquare_id: str = None,
                        foursquare_type: str = None,
                        google_place_id: str = None,
                        google_place_type: str = None,
                        disable_notification: bool = None,
                        reply_to_message_id: int = None,
                        allow_sending_without_reply: bool = None,
                        reply_markup=None):
        """Send information about a venue.

        Integrated with FourSquare.
        See https://core.telegram.org/bots/api#sendvenue for details.
        """
        return await self.api_request(
            'sendVenue',
            parameters=locals()
        )

    async def sendContact(self, chat_id: Union[int, str],
                          phone_number: str,
                          first_name: str,
                          last_name: str = None,
                          vcard: str = None,
                          disable_notification: bool = None,
                          reply_to_message_id: int = None,
                          allow_sending_without_reply: bool = None,
                          reply_markup=None):
        """Send a phone contact.

        See https://core.telegram.org/bots/api#sendcontact for details.
        """
        return await self.api_request(
            'sendContact',
            parameters=locals()
        )

    async def sendPoll(self,
                       chat_id: Union[int, str],
                       question: str,
                       options: List[str],
                       is_anonymous: bool = True,
                       type_: str = 'regular',
                       allows_multiple_answers: bool = False,
                       correct_option_id: int = None,
                       explanation: str = None,
                       explanation_parse_mode: str = None,
                       explanation_entities: List[dict] = None,
                       open_period: int = None,
                       close_date: Union[int, datetime.datetime] = None,
                       is_closed: bool = None,
                       disable_notification: bool = None,
                       allow_sending_without_reply: bool = None,
                       reply_to_message_id: int = None,
                       reply_markup=None):
        """Send a native poll in a group, a supergroup or channel.

        See https://core.telegram.org/bots/api#sendpoll for details.

        close_date: Unix timestamp; 5-600 seconds from now.
        open_period (overwrites close_date): seconds (integer), 5-600.
        """
        if open_period is not None:
            close_date = None
            open_period = min(max(5, open_period), 600)
        elif isinstance(close_date, datetime.datetime):
            now = datetime.datetime.now()
            close_date = min(
                max(
                    now + datetime.timedelta(seconds=5),
                    close_date
                ), now + datetime.timedelta(seconds=600)
            )
            close_date = int(close_date.timestamp())
        # To avoid shadowing `type`, this workaround is required
        parameters = locals().copy()
        parameters['type'] = parameters['type_']
        del parameters['type_']
        return await self.api_request(
            'sendPoll',
            parameters=parameters
        )

    async def sendChatAction(self, chat_id: Union[int, str], action):
        """Fake a typing status or similar.

        See https://core.telegram.org/bots/api#sendchataction for details.
        """
        return await self.api_request(
            'sendChatAction',
            parameters=locals()
        )

    async def getUserProfilePhotos(self, user_id,
                                   offset=None,
                                   limit=None,):
        """Get a list of profile pictures for a user.

        See https://core.telegram.org/bots/api#getuserprofilephotos
            for details.
        """
        return await self.api_request(
            'getUserProfilePhotos',
            parameters=locals()
        )

    async def getFile(self, file_id):
        """Get basic info about a file and prepare it for downloading.

        For the moment, bots can download files of up to
            20MB in size.
        On success, a File object is returned. The file can then be downloaded
            via the link https://api.telegram.org/file/bot<token>/<file_path>,
            where <file_path> is taken from the response.

        See https://core.telegram.org/bots/api#getfile for details.
        """
        return await self.api_request(
            'getFile',
            parameters=locals()
        )

    async def kickChatMember(self, chat_id: Union[int, str], user_id,
                             until_date=None):
        """Kick a user from a group, a supergroup or a channel.

        In the case of supergroups and channels, the user will not be able to
            return to the group on their own using invite links, etc., unless
            unbanned first.
        Note: In regular groups (non-supergroups), this method will only work
            if the ‘All Members Are Admins’ setting is off in the target group.
            Otherwise members may only be removed by the group's creator or by
            the member that added them.
        See https://core.telegram.org/bots/api#kickchatmember for details.
        """
        return await self.api_request(
            'kickChatMember',
            parameters=locals()
        )

    async def unbanChatMember(self, chat_id: Union[int, str], user_id: int,
                              only_if_banned: bool = True):
        """Unban a previously kicked user in a supergroup or channel.

        The user will not return to the group or channel automatically, but
            will be able to join via link, etc.
        The bot must be an administrator for this to work.
        Return True on success.
        See https://core.telegram.org/bots/api#unbanchatmember for details.

        If `only_if_banned` is set to False, regular users will be kicked from
            chat upon call of this method on them.
        """
        return await self.api_request(
            'unbanChatMember',
            parameters=locals()
        )

    async def restrictChatMember(self, chat_id: Union[int, str], user_id: int,
                                 permissions: Dict[str, bool],
                                 until_date: Union[datetime.datetime, int] = None):
        """Restrict a user in a supergroup.

        The bot must be an administrator in the supergroup for this to work
            and must have the appropriate admin rights.
            Pass True for all boolean parameters to lift restrictions from a
            user.
        Return True on success.
        See https://core.telegram.org/bots/api#restrictchatmember for details.

        until_date must be a Unix timestamp.
        """
        if isinstance(until_date, datetime.datetime):
            until_date = int(until_date.timestamp())
        return await self.api_request(
            'restrictChatMember',
            parameters=locals()
        )

    async def promoteChatMember(self, chat_id: Union[int, str], user_id: int,
                                is_anonymous: bool = None,
                                can_change_info: bool = None,
                                can_post_messages: bool = None,
                                can_edit_messages: bool = None,
                                can_delete_messages: bool = None,
                                can_invite_users: bool = None,
                                can_restrict_members: bool = None,
                                can_pin_messages: bool = None,
                                can_promote_members: bool = None):
        """Promote or demote a user in a supergroup or a channel.

        The bot must be an administrator in the chat for this to work and must
            have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user.
        Return True on success.
        See https://core.telegram.org/bots/api#promotechatmember for details.
        """
        return await self.api_request(
            'promoteChatMember',
            parameters=locals()
        )

    async def exportChatInviteLink(self, chat_id: Union[int, str]):
        """Generate a new invite link for a chat and revoke any active link.

        The bot must be an administrator in the chat for this to work and must
            have the appropriate admin rights.
        Return the new invite link as String on success.
        NOTE: to get the current invite link, use `getChat` method.
        See https://core.telegram.org/bots/api#exportchatinvitelink
            for details.
        """
        return await self.api_request(
            'exportChatInviteLink',
            parameters=locals()
        )

    async def setChatPhoto(self, chat_id: Union[int, str], photo):
        """Set a new profile photo for the chat.

        Photos can't be changed for private chats.
        `photo` must be an input file (file_id and urls are not allowed).
        The bot must be an administrator in the chat for this to work and must
            have the appropriate admin rights.
        Return True on success.
        See https://core.telegram.org/bots/api#setchatphoto for details.
        """
        return await self.api_request(
            'setChatPhoto',
            parameters=locals()
        )

    async def deleteChatPhoto(self, chat_id: Union[int, str]):
        """Delete a chat photo.

        Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must
            have the appropriate admin rights.
        Return True on success.
        See https://core.telegram.org/bots/api#deletechatphoto for details.
        """
        return await self.api_request(
            'deleteChatPhoto',
            parameters=locals()
        )

    async def setChatTitle(self, chat_id: Union[int, str], title):
        """Change the title of a chat.

        Titles can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must
            have the appropriate admin rights.
        Return True on success.
        See https://core.telegram.org/bots/api#setchattitle for details.
        """
        return await self.api_request(
            'setChatTitle',
            parameters=locals()
        )

    async def setChatDescription(self, chat_id: Union[int, str], description):
        """Change the description of a supergroup or a channel.

        The bot must be an administrator in the chat for this to work and must
            have the appropriate admin rights.
        Return True on success.
        See https://core.telegram.org/bots/api#setchatdescription for details.
        """
        return await self.api_request(
            'setChatDescription',
            parameters=locals()
        )

    async def pinChatMessage(self, chat_id: Union[int, str], message_id,
                             disable_notification: bool = None):
        """Pin a message in a group, a supergroup, or a channel.

        The bot must be an administrator in the chat for this to work and must
            have the ‘can_pin_messages’ admin right in the supergroup or
            ‘can_edit_messages’ admin right in the channel.
        Return True on success.
        See https://core.telegram.org/bots/api#pinchatmessage for details.
        """
        return await self.api_request(
            'pinChatMessage',
            parameters=locals()
        )

    async def unpinChatMessage(self, chat_id: Union[int, str],
                               message_id: int = None):
        """Unpin a message in a group, a supergroup, or a channel.

        The bot must be an administrator in the chat for this to work and must
            have the ‘can_pin_messages’ admin right in the supergroup or
            ‘can_edit_messages’ admin right in the channel.
        Return True on success.
        See https://core.telegram.org/bots/api#unpinchatmessage for details.
        """
        return await self.api_request(
            'unpinChatMessage',
            parameters=locals()
        )

    async def leaveChat(self, chat_id: Union[int, str]):
        """Make the bot leave a group, supergroup or channel.

        Return True on success.
        See https://core.telegram.org/bots/api#leavechat for details.
        """
        return await self.api_request(
            'leaveChat',
            parameters=locals()
        )

    async def getChat(self, chat_id: Union[int, str]):
        """Get up to date information about the chat.

        Return a Chat object on success.
        See https://core.telegram.org/bots/api#getchat for details.
        """
        return await self.api_request(
            'getChat',
            parameters=locals()
        )

    async def getChatAdministrators(self, chat_id: Union[int, str]):
        """Get a list of administrators in a chat.

        On success, return an Array of ChatMember objects that contains
            information about all chat administrators except other bots.
        If the chat is a group or a supergroup and no administrators were
            appointed, only the creator will be returned.

        See https://core.telegram.org/bots/api#getchatadministrators
            for details.
        """
        return await self.api_request(
            'getChatAdministrators',
            parameters=locals()
        )

    async def getChatMembersCount(self, chat_id: Union[int, str]):
        """Get the number of members in a chat.

        Returns Int on success.
        See https://core.telegram.org/bots/api#getchatmemberscount for details.
        """
        return await self.api_request(
            'getChatMembersCount',
            parameters=locals()
        )

    async def getChatMember(self, chat_id: Union[int, str], user_id):
        """Get information about a member of a chat.

        Returns a ChatMember object on success.
        See https://core.telegram.org/bots/api#getchatmember for details.
        """
        return await self.api_request(
            'getChatMember',
            parameters=locals()
        )

    async def setChatStickerSet(self, chat_id: Union[int, str], sticker_set_name):
        """Set a new group sticker set for a supergroup.

        The bot must be an administrator in the chat for this to work and must
            have the appropriate admin rights.
        Use the field `can_set_sticker_set` optionally returned in getChat
            requests to check if the bot can use this method.
        Returns True on success.
        See https://core.telegram.org/bots/api#setchatstickerset for details.
        """
        return await self.api_request(
            'setChatStickerSet',
            parameters=locals()
        )

    async def deleteChatStickerSet(self, chat_id: Union[int, str]):
        """Delete a group sticker set from a supergroup.

        The bot must be an administrator in the chat for this to work and must
            have the appropriate admin rights.
        Use the field `can_set_sticker_set` optionally returned in getChat
            requests to check if the bot can use this method.
        Returns True on success.
        See https://core.telegram.org/bots/api#deletechatstickerset for
            details.
        """
        return await self.api_request(
            'deleteChatStickerSet',
            parameters=locals()
        )

    async def answerCallbackQuery(self, callback_query_id,
                                  text=None,
                                  show_alert=None,
                                  url=None,
                                  cache_time=None):
        """Send answers to callback queries sent from inline keyboards.

        The answer will be displayed to the user as a notification at the top
            of the chat screen or as an alert.
        On success, True is returned.
        See https://core.telegram.org/bots/api#answercallbackquery for details.
        """
        return await self.api_request(
            'answerCallbackQuery',
            parameters=locals()
        )

    async def editMessageText(self, text: str,
                              chat_id: Union[int, str] = None,
                              message_id: int = None,
                              inline_message_id: str = None,
                              parse_mode: str = None,
                              entities: List[dict] = None,
                              disable_web_page_preview: bool = None,
                              reply_markup=None):
        """Edit text and game messages.

        On success, if edited message is sent by the bot, the edited Message
            is returned, otherwise True is returned.
        See https://core.telegram.org/bots/api#editmessagetext for details.
        """
        return await self.api_request(
            'editMessageText',
            parameters=locals()
        )

    async def editMessageCaption(self,
                                 chat_id: Union[int, str] = None,
                                 message_id: int = None,
                                 inline_message_id: str = None,
                                 caption: str = None,
                                 parse_mode: str = None,
                                 caption_entities: List[dict] = None,
                                 reply_markup=None):
        """Edit captions of messages.

        On success, if edited message is sent by the bot, the edited Message is
            returned, otherwise True is returned.
        See https://core.telegram.org/bots/api#editmessagecaption for details.
        """
        return await self.api_request(
            'editMessageCaption',
            parameters=locals()
        )

    async def editMessageMedia(self,
                               chat_id: Union[int, str] = None,
                               message_id: int = None,
                               inline_message_id: str = None,
                               media=None,
                               reply_markup=None):
        """Edit animation, audio, document, photo, or video messages.

        If a message is a part of a message album, then it can be edited only
            to a photo or a video. Otherwise, message type can be changed
            arbitrarily.
        When inline message is edited, new file can't be uploaded.
        Use previously uploaded file via its file_id or specify a URL.
        On success, if the edited message was sent by the bot, the edited
            Message is returned, otherwise True is returned.
        See https://core.telegram.org/bots/api#editmessagemedia for details.
        """
        return await self.api_request(
            'editMessageMedia',
            parameters=locals()
        )

    async def editMessageReplyMarkup(self,
                                     chat_id: Union[int, str] = None,
                                     message_id: int = None,
                                     inline_message_id: str = None,
                                     reply_markup=None):
        """Edit only the reply markup of messages.

        On success, if edited message is sent by the bot, the edited Message is
            returned, otherwise True is returned.
        See https://core.telegram.org/bots/api#editmessagereplymarkup for
            details.
        """
        return await self.api_request(
            'editMessageReplyMarkup',
            parameters=locals()
        )

    async def stopPoll(self, chat_id: Union[int, str], message_id,
                       reply_markup=None):
        """Stop a poll which was sent by the bot.

        On success, the stopped Poll with the final results is returned.
        `reply_markup` type may be only `InlineKeyboardMarkup`.
        See https://core.telegram.org/bots/api#stoppoll for details.
        """
        return await self.api_request(
            'stopPoll',
            parameters=locals()
        )

    async def deleteMessage(self, chat_id: Union[int, str], message_id):
        """Delete a message, including service messages.

            - A message can only be deleted if it was sent less than 48 hours
                ago.
            - Bots can delete outgoing messages in private chats, groups, and
                supergroups.
            - Bots can delete incoming messages in private chats.
            - Bots granted can_post_messages permissions can delete outgoing
                messages in channels.
            - If the bot is an administrator of a group, it can delete any
                message there.
            - If the bot has can_delete_messages permission in a supergroup or
                a channel, it can delete any message there.
            Returns True on success.

        See https://core.telegram.org/bots/api#deletemessage for details.
        """
        return await self.api_request(
            'deleteMessage',
            parameters=locals()
        )

    async def sendSticker(self, chat_id: Union[int, str],
                          sticker: Union[str, dict, IO],
                          disable_notification: bool = None,
                          reply_to_message_id: int = None,
                          allow_sending_without_reply: bool = None,
                          reply_markup=None):
        """Send `.webp` stickers.

        On success, the sent Message is returned.
        See https://core.telegram.org/bots/api#sendsticker for details.
        """
        sticker = self.prepare_file_object(sticker)
        if sticker is None:
            logging.error("Invalid sticker provided!")
            return
        result = await self.api_request(
            'sendSticker',
            parameters=locals()
        )
        if type(sticker) is dict:  # Close sticker file, if it was open
            sticker['file'].close()
        return result

    async def getStickerSet(self, name):
        """Get a sticker set.

        On success, a StickerSet object is returned.
        See https://core.telegram.org/bots/api#getstickerset for details.
        """
        return await self.api_request(
            'getStickerSet',
            parameters=locals()
        )

    async def uploadStickerFile(self, user_id, png_sticker):
        """Upload a .png file as a sticker.

        Use it later via `createNewStickerSet` and `addStickerToSet` methods
            (can be used multiple times).
        Return the uploaded File on success.
        `png_sticker` must be a *.png image up to 512 kilobytes in size,
            dimensions must not exceed 512px, and either width or height must
            be exactly 512px.
        See https://core.telegram.org/bots/api#uploadstickerfile for details.
        """
        return await self.api_request(
            'uploadStickerFile',
            parameters=locals()
        )

    async def createNewStickerSet(self, user_id: int, name: str, title: str,
                                  emojis: str,
                                  png_sticker: Union[str, dict, IO] = None,
                                  tgs_sticker: Union[str, dict, IO] = None,
                                  contains_masks: bool = None,
                                  mask_position: dict = None):
        """Create new sticker set owned by a user.

        The bot will be able to edit the created sticker set.
        Returns True on success.
        See https://core.telegram.org/bots/api#createnewstickerset for details.
        """
        png_sticker = self.prepare_file_object(png_sticker)
        tgs_sticker = self.prepare_file_object(tgs_sticker)
        if png_sticker is None and tgs_sticker is None:
            logging.error("Invalid sticker provided!")
            return
        result = await self.api_request(
            'createNewStickerSet',
            parameters=locals()
        )
        if type(png_sticker) is dict:  # Close png_sticker file, if it was open
            png_sticker['file'].close()
        if type(tgs_sticker) is dict:  # Close tgs_sticker file, if it was open
            tgs_sticker['file'].close()
        return result

    async def addStickerToSet(self, user_id: int, name: str,
                              emojis: str,
                              png_sticker: Union[str, dict, IO] = None,
                              tgs_sticker: Union[str, dict, IO] = None,
                              mask_position: dict = None):
        """Add a new sticker to a set created by the bot.

        Returns True on success.
        See https://core.telegram.org/bots/api#addstickertoset for details.
        """
        png_sticker = self.prepare_file_object(png_sticker)
        tgs_sticker = self.prepare_file_object(tgs_sticker)
        if png_sticker is None and tgs_sticker is None:
            logging.error("Invalid sticker provided!")
            return
        result = await self.api_request(
            'addStickerToSet',
            parameters=locals()
        )
        if type(png_sticker) is dict:  # Close png_sticker file, if it was open
            png_sticker['file'].close()
        if type(tgs_sticker) is dict:  # Close tgs_sticker file, if it was open
            tgs_sticker['file'].close()
        return result

    async def setStickerPositionInSet(self, sticker, position):
        """Move a sticker in a set created by the bot to a specific position .

        Position is 0-based.
        Returns True on success.
        See https://core.telegram.org/bots/api#setstickerpositioninset for
            details.
        """
        return await self.api_request(
            'setStickerPositionInSet',
            parameters=locals()
        )

    async def deleteStickerFromSet(self, sticker):
        """Delete a sticker from a set created by the bot.

        Returns True on success.
        See https://core.telegram.org/bots/api#deletestickerfromset for
            details.
        """
        return await self.api_request(
            'deleteStickerFromSet',
            parameters=locals()
        )

    async def answerInlineQuery(self, inline_query_id, results,
                                cache_time=None,
                                is_personal=None,
                                next_offset=None,
                                switch_pm_text=None,
                                switch_pm_parameter=None):
        """Send answers to an inline query.

        On success, True is returned.
        No more than 50 results per query are allowed.
        See https://core.telegram.org/bots/api#answerinlinequery for details.
        """
        return await self.api_request(
            'answerInlineQuery',
            parameters=locals()
        )

    async def sendInvoice(self, chat_id: int, title: str, description: str,
                          payload: str, provider_token: str,
                          start_parameter: str, currency: str, prices: List[dict],
                          provider_data: str = None,
                          photo_url: str = None,
                          photo_size: int = None,
                          photo_width: int = None,
                          photo_height: int = None,
                          need_name: bool = None,
                          need_phone_number: bool = None,
                          need_email: bool = None,
                          need_shipping_address: bool = None,
                          send_phone_number_to_provider: bool = None,
                          send_email_to_provider: bool = None,
                          is_flexible: bool = None,
                          disable_notification: bool = None,
                          reply_to_message_id: int = None,
                          allow_sending_without_reply: bool = None,
                          reply_markup=None):
        """Send an invoice.

        On success, the sent Message is returned.
        See https://core.telegram.org/bots/api#sendinvoice for details.
        """
        return await self.api_request(
            'sendInvoice',
            parameters=locals()
        )

    async def answerShippingQuery(self, shipping_query_id, ok,
                                  shipping_options=None,
                                  error_message=None):
        """Reply to shipping queries.

        On success, True is returned.
        If you sent an invoice requesting a shipping address and the parameter
            is_flexible was specified, the Bot API will send an Update with a
            shipping_query field to the bot.
        See https://core.telegram.org/bots/api#answershippingquery for details.
        """
        return await self.api_request(
            'answerShippingQuery',
            parameters=locals()
        )

    async def answerPreCheckoutQuery(self, pre_checkout_query_id, ok,
                                     error_message=None):
        """Respond to pre-checkout queries.

        Once the user has confirmed their payment and shipping details, the Bot
            API sends the final confirmation in the form of an Update with the
            field pre_checkout_query.
        On success, True is returned.
        Note: The Bot API must receive an answer within 10 seconds after the
            pre-checkout query was sent.
        See https://core.telegram.org/bots/api#answerprecheckoutquery for
            details.
        """
        return await self.api_request(
            'answerPreCheckoutQuery',
            parameters=locals()
        )

    async def setPassportDataErrors(self, user_id, errors):
        """Refuse a Telegram Passport element with `errors`.

        Inform a user that some of the Telegram Passport elements they provided
            contains errors.
        The user will not be able to re-submit their Passport to you until the
            errors are fixed (the contents of the field for which you returned
            the error must change).
        Returns True on success.
        Use this if the data submitted by the user doesn't satisfy the
            standards your service requires for any reason.
            For example, if a birthday date seems invalid, a submitted document
            is blurry, a scan shows evidence of tampering, etc.
        Supply some details in the error message to make sure the user knows
            how to correct the issues.
        See https://core.telegram.org/bots/api#setpassportdataerrors for
            details.
        """
        return await self.api_request(
            'setPassportDataErrors',
            parameters=locals()
        )

    async def sendGame(self, chat_id: Union[int, str], game_short_name,
                       disable_notification: bool = None,
                       reply_to_message_id: int = None,
                       reply_markup=None,
                       allow_sending_without_reply: bool = None):
        """Send a game.

        On success, the sent Message is returned.
        See https://core.telegram.org/bots/api#sendgame for
            details.
        """
        return await self.api_request(
            'sendGame',
            parameters=locals()
        )

    async def setGameScore(self, user_id: int, score: int,
                           force: bool = None,
                           disable_edit_message: bool = None,
                           chat_id: Union[int, str] = None,
                           message_id: int = None,
                           inline_message_id: str = None):
        """Set the score of the specified user in a game.

        On success, if the message was sent by the bot, returns the edited
            Message, otherwise returns True.
        Returns an error, if the new score is not greater than the user's
            current score in the chat and force is False.
        See https://core.telegram.org/bots/api#setgamescore for
            details.
        """
        return await self.api_request(
            'setGameScore',
            parameters=locals()
        )

    async def getGameHighScores(self, user_id,
                                chat_id: Union[int, str] = None,
                                message_id: int = None,
                                inline_message_id: str = None):
        """Get data for high score tables.

        Will return the score of the specified user and several of his
            neighbors in a game.
        On success, returns an Array of GameHighScore objects.
        This method will currently return scores for the target user, plus two
            of his closest neighbors on each side. Will also return the top
            three users if the user and his neighbors are not among them.
            Please note that this behavior is subject to change.
        See https://core.telegram.org/bots/api#getgamehighscores for
            details.
        """
        return await self.api_request(
            'getGameHighScores',
            parameters=locals()
        )

    async def sendDice(self,
                       chat_id: Union[int, str] = None,
                       emoji: str = None,
                       disable_notification: bool = None,
                       reply_to_message_id: int = None,
                       allow_sending_without_reply: bool = None,
                       reply_markup=None):
        """Send a dice.

        Use this method to send a dice, which will have a random value from 1
            to 6.
        On success, the sent Message is returned.
        (Yes, we're aware of the “proper” singular of die. But it's awkward,
            and we decided to help it change. One dice at a time!)
        See https://core.telegram.org/bots/api#senddice for
            details.
        """
        return await self.api_request(
            'sendDice',
            parameters=locals()
        )

    async def setChatAdministratorCustomTitle(self,
                                              chat_id: Union[int, str] = None,
                                              user_id: int = None,
                                              custom_title: str = None):
        """Set a custom title for an administrator.

        Use this method to set a custom title for an administrator in a
            supergroup promoted by the bot.
        Returns True on success.
        See https://core.telegram.org/bots/api#setchatadministratorcustomtitle
            for details.
        """
        return await self.api_request(
            'setChatAdministratorCustomTitle',
            parameters=locals()
        )

    async def setChatPermissions(self,
                                 chat_id: Union[int, str] = None,
                                 permissions: Union[ChatPermissions,
                                                    dict] = None):
        """Set default chat permissions for all members.

        Use this method to set default chat permissions for all members.
        The bot must be an administrator in the group or a supergroup for this
            to work and must have the can_restrict_members admin rights.
        Returns True on success.
        See https://core.telegram.org/bots/api#setchatpermissions for details.
        """
        return await self.api_request(
            'setChatPermissions',
            parameters=locals()
        )

    async def setMyCommands(self, commands: List[Union[Command, dict]]):
        """Change the list of the bot's commands.

        Use this method to change the list of the bot's commands.
        Returns True on success.
        See https://core.telegram.org/bots/api#setmycommands for details.
        """
        return await self.api_request(
            'setMyCommands',
            parameters=locals()
        )

    async def getMyCommands(self):
        """Get the current list of the bot's commands.

        Use this method to get the current list of the bot's commands.
        Requires no parameters.
        Returns Array of BotCommand on success.
        See https://core.telegram.org/bots/api#getmycommands for details.
        """
        return await self.api_request(
            'getMyCommands',
            parameters=locals()
        )

    async def setStickerSetThumb(self,
                                 name: str = None,
                                 user_id: int = None,
                                 thumb=None):
        """Set the thumbnail of a sticker set.

        Use this method to set the thumbnail of a sticker set.
        Animated thumbnails can be set for animated sticker sets only.
        Returns True on success.
        See https://core.telegram.org/bots/api#setstickersetthumb for details.
        """
        return await self.api_request(
            'setStickerSetThumb',
            parameters=locals()
        )

    async def logOut(self):
        """Log out from the cloud Bot API server.

        Use this method to log out from the cloud Bot API server
        before launching the bot locally.
        You must log out the bot before running it locally, otherwise there
        is no guarantee that the bot will receive updates.
        After a successful call, you can immediately log in on a local server,
        but will not be able to log in back to the cloud Bot API server
        for 10 minutes.
        Returns True on success. Requires no parameters.
        See https://core.telegram.org/bots/api#logout for details.
        """
        return await self.api_request(
            'logOut',
            parameters=locals()
        )

    async def close(self):
        """Close bot instance in local server.

        Use this method to close the bot instance before moving it from one
        local server to another.
        You need to delete the webhook before calling this method to ensure
        that the bot isn't launched again after server restart.
        The method will return error 429 in the first 10 minutes after the
        bot is launched. Returns True on success.
        Requires no parameters.
        See https://core.telegram.org/bots/api#close for details.
        """
        return await self.api_request(
            'close',
            parameters=locals()
        )

    async def copyMessage(self, chat_id: Union[int, str],
                          from_chat_id: Union[int, str],
                          message_id: int,
                          caption: str = None,
                          parse_mode: str = None,
                          caption_entities: list = None,
                          disable_notification: bool = None,
                          reply_to_message_id: int = None,
                          allow_sending_without_reply: bool = None,
                          reply_markup=None):
        """Use this method to copy messages of any kind.

        The method is analogous to the method forwardMessages, but the copied
        message doesn't have a link to the original message.
        Returns the MessageId of the sent message on success.
        See https://core.telegram.org/bots/api#copymessage for details.
        """
        return await self.api_request(
            'copyMessage',
            parameters=locals()
        )

    async def unpinAllChatMessages(self, chat_id: Union[int, str]):
        """Use this method to clear the list of pinned messages in a chat.

        If the chat is not a private chat, the bot must be an administrator
        in the chat for this to work and must have the 'can_pin_messages'
        admin right in a supergroup or 'can_edit_messages' admin right in a
        channel.
        Returns True on success.
        See https://core.telegram.org/bots/api#unpinallchatmessages for details.
        """
        return await self.api_request(
            'unpinAllChatMessages',
            parameters=locals()
        )
