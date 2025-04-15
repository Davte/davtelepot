"""This module provides a python mirror for Telegram bot API.

All methods and parameters are the same as the original json API.
A simple aiohttp asynchronous web client is used to make requests.
"""

# Standard library modules
import asyncio
import datetime
import inspect
import io
import json
import logging
import os.path

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
    """Actions that a non-administrator user is allowed to take in a chat.

    See https://core.telegram.org/bots/api#chatpermissions for details.
    """

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


class BotCommandScope(dict):
    """This object represents the scope to which bot commands are applied.

    See https://core.telegram.org/bots/api#botcommandscope for details.

    Currently, the following 7 scopes are supported:
        - BotCommandScopeDefault;
        - BotCommandScopeAllPrivateChats;
        - BotCommandScopeAllGroupChats;
        - BotCommandScopeAllChatAdministrators;
        - BotCommandScopeChat;
        - BotCommandScopeChatAdministrators;
        - BotCommandScopeChatMember.

    An algorithm described [here](https://core.telegram.org/bots/api#botcommandscope)
        is used to determine the list of commands for a particular user
        viewing the bot menu.
    """

    # noinspection PyShadowingBuiltins
    def __init__(self,
                 type: str = 'default'):
        if type not in ('default', 'all_private_chats', 'all_group_chats',
                        'all_chat_administrators', 'chat', 'chat_administrators',
                        'chat_member'):
            raise TypeError(f"Unknown bot command scope type: `{type}`.")
        super().__init__(self)
        self['type'] = type


class WebAppInfo(dict):
    """Describes a Web App.

    See https://core.telegram.org/bots/api#webappinfo for details."""

    def __init__(self,
                 url: str = None):
        super().__init__(self)
        self['url'] = url


class MenuButton(dict):
    # noinspection PyShadowingBuiltins
    def __init__(self,
                 type: str = 'default',
                 text: str = None,
                 web_app: 'WebAppInfo' = None):
        if type not in ('default', 'commands', 'web_app'):
            raise TypeError(f"Unknown menu button type: `{type}`.")
        super().__init__(self)
        self['type'] = type
        if type == 'web_app':
            self['text'] = text
            self['web_app'] = web_app


class ChatAdministratorRights(dict):
    """Represents the rights of an administrator in a chat."""

    def __init__(self,
                 is_anonymous: bool = False,
                 can_manage_chat: bool = False,
                 can_delete_messages: bool = False,
                 can_manage_video_chats: bool = False,
                 can_restrict_members: bool = False,
                 can_promote_members: bool = False,
                 can_change_info: bool = False,
                 can_invite_users: bool = False,
                 can_post_messages: bool = False,
                 can_edit_messages: bool = False,
                 can_pin_messages: bool = False,
                 can_manage_topics: bool = False,
                 can_post_stories: bool = False,
                 can_edit_stories : bool = False,
                 can_delete_stories: bool = False):
        """Represents the rights of an administrator in a chat.

        @param is_anonymous: True, if the user's presence in the chat is hidden
        @param can_manage_chat: True, if the administrator can access the chat
            event log, chat statistics, message statistics in channels, see
            channel members, see anonymous administrators in supergroups and
            ignore slow mode. Implied by any other administrator privilege
        @param can_delete_messages: True, if the administrator can delete
            messages of other users
        @param can_manage_video_chats: True, if the administrator can manage
            video chats
        @param can_restrict_members: True, if the administrator can restrict,
            ban or unban chat members
        @param can_promote_members: True, if the administrator can add new
            administrators with a subset of their own privileges or demote
            administrators that he has promoted, directly or indirectly
            (promoted by administrators that were appointed by the user)
        @param can_change_info: True, if the user is allowed to change the
            chat title, photo and other settings
        @param can_invite_users: True, if the user is allowed to invite new
            users to the chat
        @param can_post_messages: Optional. True, if the administrator can
            post in the channel; channels only
        @param can_edit_messages: Optional. True, if the administrator can
            edit messages of other users and can pin messages; channels only
        @param can_pin_messages: Optional. True, if the user is allowed to
            pin messages; groups and supergroups only
        @param can_manage_topics: Optional. True, if the user is allowed to
            create, rename, close, and reopen forum topics; supergroups only
        """
        super().__init__(self)
        self['is_anonymous'] = is_anonymous
        self['can_manage_chat'] = can_manage_chat
        self['can_delete_messages'] = can_delete_messages
        self['can_manage_video_chats'] = can_manage_video_chats
        self['can_restrict_members'] = can_restrict_members
        self['can_promote_members'] = can_promote_members
        self['can_change_info'] = can_change_info
        self['can_invite_users'] = can_invite_users
        self['can_post_messages'] = can_post_messages
        self['can_edit_messages'] = can_edit_messages
        self['can_pin_messages'] = can_pin_messages
        self['can_manage_topics'] = can_manage_topics
        self['can_post_stories'] = can_post_stories
        self['can_edit_stories'] = can_edit_stories
        self['can_delete_stories'] = can_delete_stories


class LabeledPrice(dict):
    """This object represents a portion of the price for goods or services."""
    def __init__(self, label: str, amount: int):
        """This object represents a portion of the price for goods or services.

        @param label: Portion label.
        @param amount: Price of the product in the smallest units of the
            currency (integer, not float/double).
            For example, for a price of US$ 1.45 pass amount = 145.
            See the exp parameter in currencies.json, it shows the number of
            digits past the decimal point for each currency (2 for the majority
            of currencies).
        Reference (currencies.json): https://core.telegram.org/bots/payments/currencies.json
        """
        super().__init__(self)
        self['label'] = label
        self['amount'] = amount


class InlineQueryResult(dict):
    """This object represents one result of an inline query.

    Telegram clients currently support results of the following 20 types:
        - InlineQueryResultCachedAudio;
        - InlineQueryResultCachedDocument;
        - InlineQueryResultCachedGif;
        - InlineQueryResultCachedMpeg4Gif;
        - InlineQueryResultCachedPhoto;
        - InlineQueryResultCachedSticker;
        - InlineQueryResultCachedVideo;
        - InlineQueryResultCachedVoice;
        - InlineQueryResultArticle;
        - InlineQueryResultAudio;
        - InlineQueryResultContact;
        - InlineQueryResultGame;
        - InlineQueryResultDocument;
        - InlineQueryResultGif;
        - InlineQueryResultLocation;
        - InlineQueryResultMpeg4Gif;
        - InlineQueryResultPhoto;
        - InlineQueryResultVenue;
        - InlineQueryResultVideo.
    Note: All URLs passed in inline query results will be available to end
        users and therefore must be assumed to be public.
    """
    # noinspection PyShadowingBuiltins
    def __init__(self,
                 type: str = 'default',
                 **kwargs):
        if type not in ('InlineQueryResultCachedAudio',
                        'InlineQueryResultCachedDocument',
                        'InlineQueryResultCachedGif',
                        'InlineQueryResultCachedMpeg4Gif',
                        'InlineQueryResultCachedPhoto',
                        'InlineQueryResultCachedSticker',
                        'InlineQueryResultCachedVideo',
                        'InlineQueryResultCachedVoice',
                        'InlineQueryResultArticle',
                        'InlineQueryResultAudio',
                        'InlineQueryResultContact',
                        'InlineQueryResultGame',
                        'InlineQueryResultDocument',
                        'InlineQueryResultGif',
                        'InlineQueryResultLocation',
                        'InlineQueryResultMpeg4Gif',
                        'InlineQueryResultPhoto',
                        'InlineQueryResultVenue',
                        'InlineQueryResultVideo'):
            raise TypeError(f"Unknown InlineQueryResult type: `{type}`.")
        super().__init__(self)
        self['type'] = type
        for key, value in kwargs.items():
            self[key] = value


class MaskPosition(dict):
    """This object describes the position on faces where a mask should be placed by default."""

    def __init__(self, point: str, x_shift: float, y_shift: float, scale: float):
        """This object describes the position on faces where a mask should be placed by default.

        @param point: The part of the face relative to which the mask should
            be placed. One of “forehead”, “eyes”, “mouth”, or “chin”.
        @param x_shift: Shift by X-axis measured in widths of the mask scaled
            to the face size, from left to right. For example, choosing -1.0
            will place mask just to the left of the default mask position.
        @param y_shift: Shift by Y-axis measured in heights of the mask scaled
            to the face size, from top to bottom. For example, 1.0 will place
            the mask just below the default mask position.
        @param scale: Mask scaling coefficient.
            For example, 2.0 means double size.
        """
        super().__init__(self)
        self['point'] = point
        self['x_shift'] = x_shift
        self['y_shift'] = y_shift
        self['scale'] = scale


class InputSticker(dict):
    """This object describes a sticker to be added to a sticker set."""

    def __init__(self, sticker: Union[str, dict, IO], format_: str,
                 emoji_list: List[str],
                 mask_position: Union['MaskPosition', None] = None,
                 keywords: Union[List[str], None] = None):
        """This object describes a sticker to be added to a sticker set.

        @param sticker: The added sticker. Pass a file_id as a String to send
            a file that already exists on the Telegram servers,
            pass an HTTP URL as a String for Telegram to get a file from the
            Internet, upload a new one using multipart/form-data,
            or pass “attach://<file_attach_name>” to upload a new one using
            multipart/form-data under <file_attach_name> name.
            Animated and video stickers can't be uploaded via HTTP URL.
            More information on Sending Files:
            https://core.telegram.org/bots/api#sending-files
        @param format_: Format of the added sticker, must be one of “static”
            for a .WEBP or .PNG image, “animated” for a .TGS animation,
            “video” for a WEBM video
        @param emoji_list: List of 1-20 emoji associated with the sticker
        @param mask_position: Optional. Position where the mask should be
            placed on faces. For “mask” stickers only.
        @param keywords: Optional. List of 0-20 search keywords for the sticker
            with total length of up to 64 characters.
            For “regular” and “custom_emoji” stickers only.
        """
        super().__init__(self)
        self['sticker'] = sticker
        if format_ not in ("static", "animated", "video"):
            logging.error(f"Invalid format `{format_}")
        else:
            self['format'] = format_
        self['emoji_list'] = emoji_list
        self['mask_position'] = mask_position
        self['keywords'] = keywords


class InlineQueryResultsButton(dict):
    """Button to be shown above inline query results."""

    def __init__(self,
                 text: str = None,
                 web_app: 'WebAppInfo' = None,
                 start_parameter: str = None):
        super().__init__(self)
        if sum(1 for e in (text, web_app, start_parameter) if e) != 1:
            logging.error("You must provide exactly one parameter (`text` "
                          "or `web_app` or `start_parameter`).")
            return
        self['text'] = text
        self['web_app'] = web_app
        self['start_parameter'] = start_parameter
        return


class DictToDump(dict):
    def dumps(self):
        parameters = {key: value for key, value in self.items() if value}
        return json.dumps(parameters, separators=(',', ':'))


class ReplyParameters(DictToDump):
    def __init__(self, message_id: int,
                 chat_id: Union[int, str] = None,
                 allow_sending_without_reply: bool = None,
                 quote: str = None,
                 quote_parse_mode: str = None,
                 quote_entities: list = None,
                 quote_position: int = None):
        super().__init__(self)
        self['message_id'] = message_id
        self['chat_id'] = chat_id
        self['allow_sending_without_reply'] = allow_sending_without_reply
        self['quote'] = quote
        self['quote_parse_mode'] = quote_parse_mode
        self['quote_entities'] = quote_entities
        self['quote_position'] = quote_position


class LinkPreviewOptions(DictToDump):
    def __init__(self,
                 is_disabled: bool = None,
                 url: str = None,
                 prefer_small_media: bool = None,
                 prefer_large_media: bool = None,
                 show_above_text: bool = None):
        super().__init__(self)
        self['is_disabled'] = is_disabled
        self['url'] = url
        self['prefer_small_media'] = prefer_small_media
        self['prefer_large_media'] = prefer_large_media
        self['show_above_text'] = show_above_text


class ReactionType(DictToDump):
    def __init__(self,
                 type_: str,
                 emoji: str = None,
                 custom_emoji_id: str = None):
        super().__init__(self)
        if type_ not in ('emoji', 'custom_emoji', 'paid'):
            raise TypeError(
            f"ReactionType must be `emoji`, `custom_emoji` or `paid`.\n"
            f"Unknown type {type_}"
        )
        self['type'] = type_
        if emoji and custom_emoji_id:
            raise TypeError(
                "One and only one of the two fields `emoji` or `custom_emoji` "
                "may be not None."
            )
        elif emoji:
            self['emoji'] = emoji
        elif custom_emoji_id:
            self['custom_emoji_id'] = custom_emoji_id
        elif type_ != 'paid':
            raise TypeError(
                "At least one of the two fields `emoji` or `custom_emoji` "
                "must be provided and not None."
            )


class InputPaidMedia(DictToDump):
    def __init__(self,
                 type_: str,
                 media: str):
        assert type_ in ('photo', 'video'), f"Invalid paid media type `{type_}`"
        super().__init__()
        self['type'] = type_
        self['media'] = media


class InputPaidMediaPhoto(InputPaidMedia):
    def __init__(self,
                 media: str):
        super().__init__('photo', media)


class InputPaidMediaVideo(InputPaidMedia):
    def __init__(self,
                 media: str,
                 thumbnail: str = None,
                 width: int = None,
                 height: int = None,
                 duration: int = None,
                 supports_streaming: bool = None):
        super().__init__('video', media)
        self['thumbnail'] = thumbnail
        self['width'] = width
        self['height'] = height
        self['duration'] = duration
        self['supports_streaming'] = supports_streaming


class MessageEntity(DictToDump):
    def __init__(self,
                 type_: str,
                 offset: int,
                 length: int,
                 url: str,
                 user: 'User',
                 language: str,
                 custom_emoji_id: str):
        super().__init__()
        self['type'] = type_
        self['offset'] = offset
        self['length'] = length
        self['url'] = url
        self['user'] = user
        self['language'] = language
        self['custom_emoji_id'] = custom_emoji_id


class PreparedInlineMessage(DictToDump):
    """Describes an inline message to be sent by a user of a Mini App.
    
    Attributes:
        id (str): Unique identifier of the prepared message
        expiration_date (int): Expiration date of the prepared message,
        in Unix time. Expired prepared messages can no longer be used.
    """
    def __init__(self,
                 id: str,
                 expiration_date: int):
        super().__init__()
        self['id'] = id
        self['expiration_date'] = expiration_date


class StoryAreaPosition(DictToDump):
    """Describes the position of a clickable area within a story.

    @param x_percentage: The abscissa of the area's center, as a percentage of
            the media width
    @param y_percentage: The ordinate of the area's center, as a percentage of
        the media height
    @param width_percentage: The width of the area's rectangle, as a percentage
        of the media width
    @param height_percentage: The height of the area's rectangle, as a
        percentage of the media height
    @param rotation_angle: The clockwise rotation angle of the rectangle, in
        degrees; 0-360
    @param corner_radius_percentage: The radius of the rectangle corner
        rounding, as a percentage of the media width
    """
    def __init__(self,x_percentage: float = None,
                 y_percentage: float = None,
                 width_percentage: float = None,
                 height_percentage: float = None,
                 rotation_angle: float = None,
                 corner_radius_percentage: float = None):
        super().__init__()
        for parameter, value in locals().items():
            if value:
                self[parameter] = value


class StoryAreaType(DictToDump):
    """Describes the type of a clickable area on a story.
    
    Currently, it can be one of:
    - StoryAreaTypeLocation
    - StoryAreaTypeSuggestedReaction
    - StoryAreaTypeLink
    - StoryAreaTypeWeather
    - StoryAreaTypeUniqueGift
    """
    def __init__(self, type_):
        assert type_ in ('location',
                         'suggested_reaction',
                         'link',
                         'weather',
                         'unique_gift'), (
                            f"Invalid StoryAreaType: {type_}"
                         )
        self['type'] = type_
    

class LocationAddress(DictToDump):
    """Describes the physical address of a location.

    @param country_code: the two-letter ISO 3166-1 alpha-2 country code of the
        country where the location is located
    @param state (optional): state of the location
    @param city (optional): city of the location
    @param street(optional): street address of the location
    """
    def __init__(self, country_code: str,
                 state: str = None, 
                 city: str = None, street: str = None):
        assert len(f"{country_code}") == 2, (
            f"Invalid country code: {country_code}"
        )
        super().__init__()
        for parameter, value in locals().items():
            if value:
                self[parameter] = value



class StoryAreaTypeLocation(StoryAreaType):
    """Describes a story area pointing to a location.
    
    Currently, a story can have up to 10 location areas.
    @param latitude: location latitude in degrees
    @param longitude: location longitude in degrees
    @param address: Optional. Address of the location
    """
    def __init__(self, latitude: float, longitude: float,
                 address: 'LocationAddress' = None):
        super().__init__(type_='location')
        for parameter, value in locals().items():
            if value:
                self[parameter] = value


class StoryAreaTypeSuggestedReaction(StoryAreaType):
    """Describes a story area pointing to a suggested reaction.
    
    Currently, a story can have up to 5 suggested reaction areas.
    @param reaction_type: type of the reaction
    @param is_dark: pass True if the reaction area has a dark background
    @param is_flipped: pass True if reaction area corner is flipped
    """
    def __init__(self, reaction_type: 'ReactionType',
                 is_dark: bool = None,
                 is_flipped: bool = None):
        super().__init__(type_='suggested_reaction')
        for parameter, value in locals().items():
            if value is not None:
                self[parameter] = value


class StoryAreaTypeLink(StoryAreaType):
    """Describes a story area pointing to an HTTP or tg:// link.
    
    Currently, a story can have up to 3 link areas.
    @param url: HTTP or tg:// URL to be opened when the area is clicked
    """
    def __init__(self, url: str):
        super().__init__(type_='link')
        self['url'] = url


class StoryAreaTypeWeather(StoryAreaType):
    """Describes a story area containing weather information.
    
    Currently, a story can have up to 3 weather areas.
    Parameters:
    @param temperature: temperature, in degree Celsius
    @param emoji: emoji representing the weather
    @param background_color: a color of the area background in the ARGB format
    """
    def __init__(self, temperature: float, emoji: str, background_color: int):
        super().__init__(type_='weather')
        for parameter, value in locals().items():
            if value:
                self[parameter] = value


class StoryAreaTypeUniqueGift(StoryAreaType):
    """Describes a story area pointing to a unique gift.
    
    Currently, a story can have at most 1 unique gift area.
    @param name: unique name of the gift
    """
    def __init__(self, name):
        super().__init__(type_='unique_gift')
        for parameter, value in locals().items():
            if value:
                self[parameter] = value


class StoryArea(DictToDump):
    """Describes a clickable area on a story media.
    
    @param position: Position of the area
    @param type: Type of the area
    """
    def __init__(self,
                 position: 'StoryAreaPosition',
                 type_: 'StoryAreaType'):
        super().__init__()
        self['position'] = position
        self['type'] = type_


class InputStoryContent(DictToDump):
    """This object describes the content of a story to post.
    
    Currently, it can be one of
    - InputStoryContentPhoto
    - InputStoryContentVideo
    """
    def __init__(self, type_):
        assert type_ in ('photo',
                         'video',), (
                            f"Invalid InputStoryContent type: {type_}"
                         )
        self['type'] = type_


class InputStoryContentPhoto(InputStoryContent):
    """Describes a photo to post as a story.

    @param photo: the photo to post as a story. The photo must be of the size
        1080x1920 and must not exceed 10 MB. The photo can't be reused and can
        only be uploaded as a new file, so you can pass
        attach://<file_attach_name> if the photo was uploaded using
        multipart/form-data under <file_attach_name>.
        
    More information: https://core.telegram.org/bots/api#sending-files
    """
    def __init__(self, photo: str):
        super().__init__(type_='photo')
        for parameter, value in locals().items():
            if value:
                self[parameter] = value


class InputStoryContentVideo(InputStoryContent):
    """Describes a video to post as a story.

    @param video: The video to post as a story. The video must be of the size
        720x1280, streamable, encoded with H.265 codec, with key frames added
        each second in the MPEG4 format, and must not exceed 30 MB. The video
        can't be reused and can only be uploaded as a new file, so you can pass
        “attach://<file_attach_name>” if the video was uploaded using
        multipart/form-data under <file_attach_name>.
        More information: https://core.telegram.org/bots/api#sending-files
    @param duration: Optional. Precise duration of the video in seconds; 0-60
    @param cover_frame_timestamp: Optional. Timestamp in seconds of the frame
        that will be used as the static cover for the story. Defaults to 0.0.
    @param is_animation: Optional. Pass True if the video has no sound
        
    More information: https://core.telegram.org/bots/api#sending-files
    """
    def __init__(self, video: str, duration: float = None,
                 cover_frame_timestamp: float = None,
                 is_animation: bool = None):
        super().__init__(type_='photo')
        for parameter, value in locals().items():
            if value is not None:
                self[parameter] = value


class InputProfilePhoto(DictToDump):
    """This object describes a profile photo to set.
    
    Currently, it can be one of
    - InputProfilePhotoStatic
    - InputProfilePhotoAnimated
    """
    def __init__(self, type_):
        assert type_ in ('InputProfilePhotoStatic',
                         'InputProfilePhotoAnimated',), (
                            f"Invalid InputProfilePhoto type: {type_}"
                         )
        self['type'] = type_


class InputProfilePhotoStatic(InputProfilePhoto):
    """A static profile photo in the .JPG format.

    @param photo: the static profile photo. Profile photos can't be reused and
        can only be uploaded as a new file, so you can pass
        "attach://<file_attach_name>" if the photo was uploaded using
        multipart/form-data under <file_attach_name>.
        More information on Sending Files:
        https://core.telegram.org/bots/api#sending-files
    """
    def __init__(self, photo: str):
        super().__init__(type_='static')
        for parameter, value in locals().items():
            if value:
                self[parameter] = value


class InputProfilePhotoAnimated(InputProfilePhoto):
    """A static profile photo in the MPEG4 format.

    @param animation: The animated profile photo. Profile photos can't be reused
        and can only be uploaded as a new file, so you can pass
        "attach://<file_attach_name>" if the photo was uploaded using
        multipart/form-data under <file_attach_name>.
        More information on Sending Files:
        https://core.telegram.org/bots/api#sending-files
    @param main_frame_timestamp: Optional. Timestamp in seconds of the frame
        that will be used as the static profile photo. Defaults to 0.0.
    """
    def __init__(self, animation: str,
                 main_frame_timestamp: float = None):
        super().__init__(type_='animated')
        for parameter, value in locals().items():
            if value:
                self[parameter] = value


def handle_deprecated_disable_web_page_preview(parameters: dict,
                                               kwargs: dict):
    if 'disable_web_page_preview' in kwargs:
        if parameters['link_preview_options'] is None:
            parameters['link_preview_options'] = LinkPreviewOptions()
        parameters['link_preview_options']['is_disabled'] = True
        logging.error("DEPRECATION WARNING: `disable_web_page_preview` "
                      f"parameter of function `{inspect.stack()[2][3]}` has been "
                      "deprecated since Bot API 7.0. "
                      "Use `link_preview_options` instead.")
    return parameters


def handle_deprecated_reply_parameters(parameters: dict,
                                       kwargs: dict):
    if 'reply_to_message_id' in kwargs and kwargs['reply_to_message_id']:
        if parameters['reply_parameters'] is None:
            parameters['reply_parameters'] = ReplyParameters(
                message_id=kwargs['reply_to_message_id']
            )
        parameters['reply_parameters']['message_id'] = kwargs['reply_to_message_id']
        if 'allow_sending_without_reply' in kwargs:
            parameters['reply_parameters'][
                'allow_sending_without_reply'
            ] = kwargs['allow_sending_without_reply']
        logging.error(f"DEPRECATION WARNING: `reply_to_message_id` and "
                      f"`allow_sending_without_reply` parameters of function "
                      f"`{inspect.stack()[2][3]}` have been deprecated since "
                      f"Bot API 7.0. Use `reply_parameters` instead.")
    return parameters


def handle_forbidden_names_for_parameters(parameters: dict,
                                          kwargs: dict):
    if 'format' in kwargs:
        parameters['format'] = kwargs['format']
    if 'format_' in parameters:
        parameters['format'] = parameters['format_']
        del parameters['format_']
    return parameters


# This class needs to mirror Telegram API, so camelCase method are needed
# noinspection PyPep8Naming
class TelegramBot:
    """Provide python method having the same signature as Telegram API methods.

    All mirrored methods are camelCase.
    """
    _loop = None
    _api_url = "https://api.telegram.org"

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
    _absolute_cooldown_timedelta = datetime.timedelta(seconds=1 / 30)
    _per_chat_cooldown_timedelta = datetime.timedelta(seconds=1)
    _allowed_messages_per_group_per_minute = 20

    def __init__(self, token, api_url: str = None):
        """Set bot token and store HTTP sessions."""
        if self.loop is None:
            self.__class__._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self._token = token
        self._api_url = api_url
        self.sessions = dict()
        self._flood_wait = 0
        # Each `telegram_id` key has a list of `datetime.datetime` as value
        self.last_sending_time = {
            'absolute': (datetime.datetime.now()
                         - self.absolute_cooldown_timedelta),
            0: []
        }

    @property
    def loop(self):
        """Telegram API bot token."""
        return self.__class__._loop

    @property
    def token(self):
        """Telegram API bot token."""
        return self._token

    @property
    def api_url(self):
        """Telegram API bot token."""
        return self._api_url or self.__class__._api_url

    @classmethod
    def set_class_api_url(cls, api_url: str):
        cls._api_url = api_url

    def set_api_url(self, api_url: str):
        self._api_url = api_url

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
        """Build an aiohttp.FormData object from given `parameters`.

        Exclude `self`, empty values and parameters in `exclude` list.
        Cast integers to string to avoid TypeError during json serialization.
        """
        if exclude is None:
            exclude = []
        exclude += ['self', 'kwargs']
        # quote_fields=False, otherwise some file names cause troubles
        data = aiohttp.FormData(quote_fields=False)
        for key, value in parameters.items():
            if not (key in exclude or value is None):
                if (type(value) in (int, list,)
                        or (type(value) is dict and 'file' not in value)):
                    value = json.dumps(value, separators=(',', ':'))
                elif isinstance(value, DictToDump):
                    value = value.dumps()
                data.add_field(key, value)
        return data

    @staticmethod
    def prepare_file_object(file: Union[str, IO, dict, None]
                            ) -> Union[str, Dict[str, IO], None]:
        """If `file` is a valid file path, return a dict for multipart/form-data.

        Other valid file identifiers are URLs and Telegram `file_id`s.
        """
        if type(file) is str and os.path.isfile(file):
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
                    timeout=aiohttp.ClientTimeout(
                        total=cls.sessions_timeouts[api_method]['timeout']
                    )
                )
            session = self.sessions[api_method]
            session_must_be_closed = cls.sessions_timeouts[api_method]['close']
        else:
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=None)
            )
            session_must_be_closed = True
        return session, session_must_be_closed

    def set_flood_wait(self, flood_wait):
        """Wait `flood_wait` seconds before next request."""
        self._flood_wait = flood_wait

    def make_input_sticker(self,
                           sticker: Union[dict, str, IO],
                           emoji_list: Union[List[str], str],
                           mask_position: Union[MaskPosition, None] = None,
                           keywords: Union[List[str], None] = None,
                           format_: str = 'static') -> InputSticker:
        if isinstance(emoji_list, str):
            emoji_list = [c for c in emoji_list]
        if isinstance(keywords, str):
            keywords = [w for w in keywords]
        if isinstance(sticker, str) and os.path.isfile(sticker):
            sticker = self.prepare_file_object(sticker)
        return InputSticker(sticker=sticker, emoji_list=emoji_list,
                            mask_position=mask_position, keywords=keywords,
                            format_=format_)

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
                if sending_datetime >= (now()
                                        - self.longest_cooldown_timedelta)
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
            async with session.post(f"{self.api_url}/bot"
                                    f"{self.token}/{method}",
                                    data=parameters) as response:
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
                            flood_wait = 5 * 60
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
                         drop_pending_updates: bool = None,
                         secret_token: str = None):
        """Set or remove a webhook. Telegram will post to `url` new updates.

        See https://core.telegram.org/bots/api#setwebhook for details.

        Notes:
            1. You will not be able to receive updates using getUpdates for as
                long as an outgoing webhook is set up.
            2. To use a self-signed certificate, you need to upload your public
                key certificate using certificate parameter.
                Please upload as InputFile, sending a String will not work.
            3. Ports currently supported for webhooks: 443, 80, 88, 8443.
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

    async def sendMessage(self, chat_id: Union[int, str],
                          text: str,
                          business_connection_id: str = None,
                          message_thread_id: int = None,
                          parse_mode: str = None,
                          entities: List[dict] = None,
                          link_preview_options: LinkPreviewOptions = None,
                          disable_notification: bool = None,
                          protect_content: bool = None,
                          message_effect_id: str = None,
                          reply_parameters: ReplyParameters = None,
                          reply_markup=None,
                          allow_paid_broadcast: bool = None,
                          **kwargs):
        """Send a text message. On success, return it.

        See https://core.telegram.org/bots/api#sendmessage for details.
        """
        parameters = handle_deprecated_disable_web_page_preview(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        parameters = handle_deprecated_reply_parameters(
            parameters=parameters,
            kwargs=kwargs
        )
        return await self.api_request(
            'sendMessage',
            parameters=parameters
        )

    async def forwardMessage(self, chat_id: Union[int, str],
                             from_chat_id: Union[int, str],
                             message_id: int,
                             message_thread_id: int = None,
                             protect_content: bool = None,
                             disable_notification: bool = None,
                             video_start_timestamp: int = None):
        """Forward a message.

        See https://core.telegram.org/bots/api#forwardmessage for details.
        """
        return await self.api_request(
            'forwardMessage',
            parameters=locals()
        )

    async def sendPhoto(self, chat_id: Union[int, str], photo,
                        business_connection_id: str = None,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        show_caption_above_media: bool = None,
                        message_thread_id: int = None,
                        protect_content: bool = None,
                        disable_notification: bool = None,
                        has_spoiler: bool = None,
                        message_effect_id: str = None,
                        reply_parameters: ReplyParameters = None,
                        reply_markup=None,
                        allow_paid_broadcast: bool = None,
                        **kwargs):
        """Send a photo from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendphoto for details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendPhoto',
            parameters=parameters
        )

    async def sendAudio(self, chat_id: Union[int, str], audio,
                        business_connection_id: str = None,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        duration: int = None,
                        performer: str = None,
                        title: str = None,
                        thumbnail=None,
                        disable_notification: bool = None,
                        message_thread_id: int = None,
                        protect_content: bool = None,
                        message_effect_id: str = None,
                        reply_parameters: ReplyParameters = None,
                        reply_markup=None,
                        allow_paid_broadcast: bool = None,
                        **kwargs):
        """Send an audio file from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendaudio for details.
        """
        if 'thumb' in kwargs:
            thumbnail = kwargs['thumb']
            logging.error("DEPRECATION WARNING: `thumb` parameter of function"
                          "`sendAudio` has been deprecated since Bot API 6.6. "
                          "Use `thumbnail` instead.")
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendAudio',
            parameters=parameters
        )

    async def sendDocument(self, chat_id: Union[int, str], document,
                           business_connection_id: str = None,
                           thumbnail=None,
                           caption: str = None,
                           parse_mode: str = None,
                           caption_entities: List[dict] = None,
                           disable_content_type_detection: bool = None,
                           disable_notification: bool = None,
                           message_thread_id: int = None,
                           protect_content: bool = None,
                           message_effect_id: str = None,
                           reply_parameters: ReplyParameters = None,
                           reply_markup=None,
                           allow_paid_broadcast: bool = None,
                           **kwargs):
        """Send a document from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#senddocument for details.
        """
        if 'thumb' in kwargs:
            thumbnail = kwargs['thumb']
            logging.error("DEPRECATION WARNING: `thumb` parameter of function"
                          "`sendDocument` has been deprecated since Bot API 6.6. "
                          "Use `thumbnail` instead.")
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendDocument',
            parameters=parameters
        )

    async def sendVideo(self, chat_id: Union[int, str], video,
                        business_connection_id: str = None,
                        duration: int = None,
                        width: int = None,
                        height: int = None,
                        thumbnail=None,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        show_caption_above_media: bool = None,
                        supports_streaming: bool = None,
                        disable_notification: bool = None,
                        message_thread_id: int = None,
                        protect_content: bool = None,
                        message_effect_id: str = None,
                        has_spoiler: bool = None,
                        reply_parameters: ReplyParameters = None,
                        reply_markup=None,
                        allow_paid_broadcast: bool = None,
                        start_timestamp: int = None,
                        cover=None,
                        **kwargs):
        """Send a video from file_id, HTTP url or file.

        See https://core.telegram.org/bots/api#sendvideo for details.
        """
        if 'thumb' in kwargs:
            thumbnail = kwargs['thumb']
            logging.error("DEPRECATION WARNING: `thumb` parameter of function"
                          "`sendVideo` has been deprecated since Bot API 6.6. "
                          "Use `thumbnail` instead.")
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendVideo',
            parameters=parameters
        )

    async def sendAnimation(self, chat_id: Union[int, str], animation,
                            business_connection_id: str = None,
                            duration: int = None,
                            width: int = None,
                            height: int = None,
                            thumbnail=None,
                            caption: str = None,
                            parse_mode: str = None,
                            caption_entities: List[dict] = None,
                            show_caption_above_media: bool = None,
                            disable_notification: bool = None,
                            message_thread_id: int = None,
                            protect_content: bool = None,
                            message_effect_id: str = None,
                            has_spoiler: bool = None,
                            reply_parameters: ReplyParameters = None,
                            reply_markup=None,
                            allow_paid_broadcast: bool = None,
                            **kwargs):
        """Send animation files (GIF or H.264/MPEG-4 AVC video without sound).

        See https://core.telegram.org/bots/api#sendanimation for details.
        """
        if 'thumb' in kwargs:
            thumbnail = kwargs['thumb']
            logging.error("DEPRECATION WARNING: `thumb` parameter of function"
                          "`sendAnimation` has been deprecated since Bot API 6.6. "
                          "Use `thumbnail` instead.")
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendAnimation',
            parameters=parameters
        )

    async def sendVoice(self, chat_id: Union[int, str], voice,
                        business_connection_id: str = None,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        duration: int = None,
                        disable_notification: bool = None,
                        message_thread_id: int = None,
                        protect_content: bool = None,
                        message_effect_id: str = None,
                        reply_parameters: ReplyParameters = None,
                        reply_markup=None,
                        allow_paid_broadcast: bool = None,
                        **kwargs):
        """Send an audio file to be displayed as playable voice message.

        `voice` must be in an .ogg file encoded with OPUS.
        See https://core.telegram.org/bots/api#sendvoice for details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendVoice',
            parameters=parameters
        )

    async def sendVideoNote(self, chat_id: Union[int, str], video_note,
                            business_connection_id: str = None,
                            duration: int = None,
                            length: int = None,
                            thumbnail=None,
                            disable_notification: bool = None,
                            message_thread_id: int = None,
                            protect_content: bool = None,
                            message_effect_id: str = None,
                            reply_parameters: ReplyParameters = None,
                            reply_markup=None,
                            allow_paid_broadcast: bool = None,
                            **kwargs):
        """Send a rounded square mp4 video message of up to 1 minute long.

        See https://core.telegram.org/bots/api#sendvideonote for details.
        """
        if 'thumb' in kwargs:
            thumbnail = kwargs['thumb']
            logging.error("DEPRECATION WARNING: `thumb` parameter of function"
                          "`sendVideoNote` has been deprecated since Bot API 6.6. "
                          "Use `thumbnail` instead.")
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendVideoNote',
            parameters=parameters
        )

    async def sendMediaGroup(self, chat_id: Union[int, str], media: list,
                             business_connection_id: str = None,
                             disable_notification: bool = None,
                             message_thread_id: int = None,
                             protect_content: bool = None,
                             message_effect_id: str = None,
                             reply_parameters: ReplyParameters = None,
                             allow_paid_broadcast: bool = None,
                             **kwargs):
        """Send a group of photos or videos as an album.

        `media` must be a list of `InputMediaPhoto` and/or `InputMediaVideo`
            objects.
        See https://core.telegram.org/bots/api#sendmediagroup for details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendMediaGroup',
            parameters=parameters
        )

    async def sendLocation(self, chat_id: Union[int, str],
                           latitude: float, longitude: float,
                           business_connection_id: str = None,
                           horizontal_accuracy: float = None,
                           live_period=None,
                           heading: int = None,
                           proximity_alert_radius: int = None,
                           disable_notification: bool = None,
                           message_thread_id: int = None,
                           protect_content: bool = None,
                           message_effect_id: str = None,
                           reply_parameters: ReplyParameters = None,
                           reply_markup=None,
                           allow_paid_broadcast: bool = None,
                           **kwargs):
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
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendLocation',
            parameters=parameters
        )

    async def editMessageLiveLocation(self, latitude: float, longitude: float,
                                      live_period: int = None,
                                      chat_id: Union[int, str] = None,
                                      business_connection_id: str = None,
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
                                      business_connection_id: str = None,
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
                        business_connection_id: str = None,
                        foursquare_id: str = None,
                        foursquare_type: str = None,
                        google_place_id: str = None,
                        google_place_type: str = None,
                        disable_notification: bool = None,
                        message_thread_id: int = None,
                        protect_content: bool = None,
                        message_effect_id: str = None,
                        reply_parameters: ReplyParameters = None,
                        reply_markup=None,
                        allow_paid_broadcast: bool = None,
                        **kwargs):
        """Send information about a venue.

        Integrated with FourSquare.
        See https://core.telegram.org/bots/api#sendvenue for details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendVenue',
            parameters=parameters
        )

    async def sendContact(self, chat_id: Union[int, str],
                          phone_number: str,
                          first_name: str,
                          business_connection_id: str = None,
                          last_name: str = None,
                          vcard: str = None,
                          disable_notification: bool = None,
                          message_thread_id: int = None,
                          protect_content: bool = None,
                          message_effect_id: str = None,
                          reply_parameters: ReplyParameters = None,
                          reply_markup=None,
                          allow_paid_broadcast: bool = None,
                          **kwargs):
        """Send a phone contact.

        See https://core.telegram.org/bots/api#sendcontact for details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendContact',
            parameters=parameters
        )

    async def sendPoll(self,
                       chat_id: Union[int, str],
                       question: str,
                       options: List[str],
                       question_parse_mode: str = None,
                       question_entities: list = None,
                       business_connection_id: str = None,
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
                       message_thread_id: int = None,
                       protect_content: bool = None,
                       message_effect_id: str = None,
                       reply_parameters: ReplyParameters = None,
                       reply_markup=None,
                       allow_paid_broadcast: bool = None,
                       **kwargs):
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
        parameters = handle_deprecated_reply_parameters(
            parameters=parameters,
            kwargs=kwargs
        )
        return await self.api_request(
            'sendPoll',
            parameters=parameters
        )

    async def sendChatAction(self, chat_id: Union[int, str], action,
                             business_connection_id: str = None,
                             message_thread_id: int = None):
        """Fake a typing status or similar.

        See https://core.telegram.org/bots/api#sendchataction for details.
        """
        return await self.api_request(
            'sendChatAction',
            parameters=locals()
        )

    async def getUserProfilePhotos(self, user_id,
                                   offset=None,
                                   limit=None):
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
            Otherwise, members may only be removed by the group's creator or by
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
                                 use_independent_chat_permissions: bool = None,
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
                                can_promote_members: bool = None,
                                can_manage_topics: bool = None,
                                can_manage_chat: bool = None,
                                can_manage_video_chats: bool = None,
                                can_edit_stories: bool = None,
                                can_delete_stories: bool = None,
                                can_post_stories: bool = None):
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
                             business_connection_id: str = None,
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
                               business_connection_id: str = None,
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
        """Get up-to-date information about the chat.

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
                              business_connection_id: str = None,
                              message_id: int = None,
                              inline_message_id: str = None,
                              parse_mode: str = None,
                              entities: List[dict] = None,
                              link_preview_options: LinkPreviewOptions = None,
                              reply_markup=None,
                              **kwargs):
        """Edit text and game messages.

        On success, if edited message is sent by the bot, the edited Message
            is returned, otherwise True is returned.
        See https://core.telegram.org/bots/api#editmessagetext for details.
        """
        parameters = handle_deprecated_disable_web_page_preview(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'editMessageText',
            parameters=parameters
        )

    async def editMessageCaption(self,
                                 chat_id: Union[int, str] = None,
                                 business_connection_id: str = None,
                                 message_id: int = None,
                                 inline_message_id: str = None,
                                 caption: str = None,
                                 parse_mode: str = None,
                                 caption_entities: List[dict] = None,
                                 show_caption_above_media: bool = None,
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
                               business_connection_id: str = None,
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
                                     business_connection_id: str = None,
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

    async def stopPoll(self,
                       chat_id: Union[int, str],
                       message_id,
                       business_connection_id: str = None,
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

    async def deleteMessages(self, chat_id: Union[int, str],
                             message_ids: List[int]):
        """Delete multiple messages simultaneously.

        If some of the specified messages can't be found, they are skipped.
        Returns True on success.
        See https://core.telegram.org/bots/api#deletemessages for details.
        """
        return await self.api_request(
            'deleteMessages',
            parameters=locals()
        )

    async def sendSticker(self, chat_id: Union[int, str],
                          sticker: Union[str, dict, IO],
                          business_connection_id: str = None,
                          disable_notification: bool = None,
                          message_thread_id: int = None,
                          protect_content: bool = None,
                          emoji: str = None,
                          message_effect_id: str = None,
                          reply_parameters: ReplyParameters = None,
                          reply_markup=None,
                          allow_paid_broadcast: bool = None,
                          **kwargs):
        """Send `.webp` stickers.

        `sticker` must be a file path, a URL, a file handle or a dict
            {"file": io_file_handle}, to allow multipart/form-data encoding.
        On success, the sent Message is returned.
        See https://core.telegram.org/bots/api#sendsticker for details.
        """
        sticker = self.prepare_file_object(sticker)
        if sticker is None:
            logging.error("Invalid sticker provided!")
            return
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        result = await self.api_request(
            'sendSticker',
            parameters=parameters
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

    async def uploadStickerFile(self, user_id: int, sticker: Union[str, dict, IO],
                                sticker_format: str, **kwargs):
        """Upload an image file for later use in sticker packs.

        Use this method to upload a file with a sticker for later use in the
            createNewStickerSet and addStickerToSet methods
            (the file can be used multiple times).
        `sticker` must be a file path, a file handle or a dict
            {"file": io_file_handle}, to allow multipart/form-data encoding.
        Returns the uploaded File on success.
        See https://core.telegram.org/bots/api#uploadstickerfile for details.
        """
        if 'png_sticker' in kwargs:
            sticker = kwargs['png_sticker']
            logging.error("DEPRECATION WARNING: `png_sticker` parameter of function"
                          "`uploadStickerFile` has been deprecated since Bot API 6.6. "
                          "Use `sticker` instead.")
        if sticker_format not in ("static", "animated", "video"):
            logging.error(f"Unknown sticker format `{sticker_format}`.")
        sticker = self.prepare_file_object(sticker)
        if sticker is None:
            logging.error("Invalid sticker provided!")
            return
        result = await self.api_request(
            'uploadStickerFile',
            parameters=locals()
        )
        if type(sticker) is dict:  # Close sticker file, if it was open
            sticker['file'].close()
        return result

    async def createNewStickerSet(self, user_id: int, name: str, title: str,
                                  stickers: List['InputSticker'],
                                  sticker_type: str = 'regular',
                                  needs_repainting: bool = False,
                                  **kwargs):
        """Create new sticker set owned by a user.

        The bot will be able to edit the created sticker set.
        Returns True on success.
        See https://core.telegram.org/bots/api#createnewstickerset for details.
        """
        if stickers is None:
            stickers = []
        if 'sticker_format' in kwargs:
            logging.error("Parameter `sticker_format` of method "
                          "`createNewStickerSet` has been deprecated. "
                          "Use `format` parameter of class `InputSticker` instead.")
        if 'contains_masks' in kwargs:
            logging.error("Parameter `contains_masks` of method "
                          "`createNewStickerSet` has been deprecated. "
                          "Use `sticker_type = 'mask'` instead.")
            sticker_type = 'mask' if kwargs['contains_masks'] else 'regular'
        for old_sticker_format in ('png_sticker', 'tgs_sticker', 'webm_sticker'):
            if old_sticker_format in kwargs:
                if 'emojis' not in kwargs:
                    logging.error(f"No `emojis` provided together with "
                                  f"`{old_sticker_format}`. To create new "
                                  f"sticker set with some stickers in it, use "
                                  f"the new `stickers` parameter.")
                    return
                logging.error(f"Parameter `{old_sticker_format}` of method "
                              "`createNewStickerSet` has been deprecated since"
                              "Bot API 6.6. "
                              "Use `stickers` instead.")
                stickers.append(
                    self.make_input_sticker(
                        sticker=kwargs[old_sticker_format],
                        emoji_list=kwargs['emojis']
                    )
                )
        if sticker_type not in ('regular', 'mask', 'custom_emoji'):
            raise TypeError(f"Unknown sticker type `{sticker_type}`.")
        result = await self.api_request(
            'createNewStickerSet',
            parameters=locals().copy(),
            exclude=['old_sticker_format']
        )
        return result

    async def addStickerToSet(self, user_id: int, name: str,
                              sticker: InputSticker = None,
                              **kwargs):
        """Add a new sticker to a set created by the bot.

        Returns True on success.
        See https://core.telegram.org/bots/api#addstickertoset for details.
        """
        for old_sticker_format in ('png_sticker', 'tgs_sticker', 'webm_sticker'):
            if old_sticker_format in kwargs:
                if 'emojis' not in kwargs:
                    logging.error(f"No `emojis` provided together with "
                                  f"`{old_sticker_format}`.")
                    return
                logging.error(f"Parameter `{old_sticker_format}` of method "
                              "`addStickerToSet` has been deprecated since"
                              "Bot API 6.6. "
                              "Use `sticker` instead.")
                sticker = self.make_input_sticker(
                    sticker=kwargs[old_sticker_format],
                    emoji_list=kwargs['emojis'],
                    mask_position=kwargs['mask_position'] if 'mask_position' in kwargs else None
                )
        if sticker is None:
            logging.error("Must provide a sticker of type `InputSticker` to "
                          "`addStickerToSet` method.")
            return
        result = await self.api_request(
            'addStickerToSet',
            parameters=locals().copy(),
            exclude=['old_sticker_format']
        )
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
                                button: Union['InlineQueryResultsButton', None] = None,
                                **kwargs):
        """Send answers to an inline query.

        On success, True is returned.
        No more than 50 results per query are allowed.
        See https://core.telegram.org/bots/api#answerinlinequery for details.
        """
        if 'switch_pm_text' in kwargs and kwargs['switch_pm_text']:
            button = InlineQueryResultsButton(text=kwargs['switch_pm_text'])
        if 'switch_pm_parameter' in kwargs and kwargs['switch_pm_parameter']:
            button = InlineQueryResultsButton(start_parameter=kwargs['switch_pm_parameter'])
        return await self.api_request(
            'answerInlineQuery',
            parameters=locals()
        )

    async def sendInvoice(self, chat_id: int, title: str, description: str,
                          payload: str, provider_token: str,
                          start_parameter: str,
                          currency: str, prices: List[dict],
                          message_thread_id: int = None,
                          protect_content: bool = None,
                          max_tip_amount: int = None,
                          suggested_tip_amounts: List[int] = None,
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
                          message_effect_id: str = None,
                          reply_parameters: ReplyParameters = None,
                          reply_markup=None,
                          allow_paid_broadcast: bool = None,
                          **kwargs):
        """Send an invoice.

        On success, the sent Message is returned.
        See https://core.telegram.org/bots/api#sendinvoice for details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendInvoice',
            parameters=parameters
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
                       business_connection_id: str = None,
                       message_thread_id: int = None,
                       protect_content: bool = None,
                       disable_notification: bool = None,
                       message_effect_id: str = None,
                       reply_parameters: ReplyParameters = None,
                       reply_markup=None,
                       allow_paid_broadcast: bool = None,
                       **kwargs):
        """Send a game.

        On success, the sent Message is returned.
        See https://core.telegram.org/bots/api#sendgame for
            details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendGame',
            parameters=parameters
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
                       chat_id: Union[int, str],
                       business_connection_id: str = None,
                       emoji: str = None,
                       disable_notification: bool = None,
                       message_thread_id: int = None,
                       protect_content: bool = None,
                       message_effect_id: str = None,
                       reply_parameters: ReplyParameters = None,
                       reply_markup=None,
                       allow_paid_broadcast: bool = None,
                       **kwargs):
        """Send a dice.

        Use this method to send a dice, which will have a random value from 1
            to 6.
        On success, the sent Message is returned.
        (Yes, we're aware of the “proper” singular of die. But it's awkward,
            and we decided to help it change. One dice at a time!)
        See https://core.telegram.org/bots/api#senddice for
            details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'sendDice',
            parameters=parameters
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
                                                    dict] = None,
                                 use_independent_chat_permissions: bool = None):
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

    async def setMyCommands(self,
                            commands: List[Union[Command, dict]],
                            scope: 'BotCommandScope' = None,
                            language_code: str = None):
        """Change the list of the bot's commands.

        Use this method to change the list of the bot's commands.
        Returns True on success.
        See https://core.telegram.org/bots/api#setmycommands for details.
        """
        return await self.api_request(
            'setMyCommands',
            parameters=locals()
        )

    async def getMyCommands(self,
                            scope: 'BotCommandScope' = None,
                            language_code: str = None):
        """Get the current list of the bot's commands.

        Use this method to get the current list of the bot's commands for
            the given scope and user language.
        Returns an Array of BotCommand objects.
        If commands aren't set, an empty list is returned.
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
                          message_thread_id: int = None,
                          protect_content: bool = None,
                          caption: str = None,
                          parse_mode: str = None,
                          caption_entities: list = None,
                          show_caption_above_media: bool = None,
                          disable_notification: bool = None,
                          reply_parameters: ReplyParameters = None,
                          reply_markup=None,
                          allow_paid_broadcast: bool = None,
                          video_start_timestamp: int = None,
                          **kwargs):
        """Use this method to copy messages of any kind.

        The method is analogous to the method forwardMessages, but the copied
        message doesn't have a link to the original message.
        Returns the MessageId of the sent message on success.
        See https://core.telegram.org/bots/api#copymessage for details.
        """
        parameters = handle_deprecated_reply_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'copyMessage',
            parameters=parameters
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

    async def banChatMember(self, chat_id: Union[int, str],
                            user_id: int, until_date: int,
                            revoke_messages: bool):
        """Use this method to ban a user in a group, a supergroup or a channel.

        In the case of supergroups and channels, the user will not be able to
            return to the chat on their own using invite links, etc., unless
            unbanned first.
        The bot must be an administrator in the chat for this to work and must
            have the appropriate administrator rights.
        Returns True on success.
        See https://core.telegram.org/bots/api#banchatmember for details.
        """
        return await self.api_request(
            'banChatMember',
            parameters=locals()
        )

    async def banChatSenderChat(self, chat_id: Union[int, str], sender_chat_id: int):
        """Use this method to ban a channel chat in a supergroup or a channel.

        Until the chat is unbanned, the owner of the banned chat won't be able
            to send messages on behalf of any of their channels.
        The bot must be an administrator in the supergroup or channel for this
            to work and must have the appropriate administrator rights.
        Returns True on success.
        See https://core.telegram.org/bots/api#banchatsenderchat for details.
        """
        return await self.api_request(
            'banChatSenderChat',
            parameters=locals()
        )

    async def unbanChatSenderChat(self, chat_id: Union[int, str], sender_chat_id: int):
        """Use this method to unban a previously banned channel chat in a supergroup or channel.

        The bot must be an administrator for this to work and must have the
            appropriate administrator rights.
        Returns True on success.
        See https://core.telegram.org/bots/api#unbanchatsenderchat for details.
        """
        return await self.api_request(
            'unbanChatSenderChat',
            parameters=locals()
        )

    async def createChatInviteLink(self, chat_id: Union[int, str], name: str,
                                   expire_date: int, member_limit: int,
                                   creates_join_request: bool):
        """Use this method to create an additional invite link for a chat.

        The bot must be an administrator in the chat for this to work and must
            have the appropriate administrator rights.
        The link can be revoked using the method revokeChatInviteLink.
        Returns the new invite link as ChatInviteLink object.
        See https://core.telegram.org/bots/api#createchatinvitelink for details.
        """
        return await self.api_request(
            'createChatInviteLink',
            parameters=locals()
        )

    async def editChatInviteLink(self, chat_id: Union[int, str],
                                 invite_link: str, name: str, expire_date: int,
                                 member_limit: int, creates_join_request: bool):
        """Use this method to edit a non-primary invite link created by the bot.

        The bot must be an administrator in the chat for this to work and must
            have the appropriate administrator rights.
        Returns the edited invite link as a ChatInviteLink object.
        See https://core.telegram.org/bots/api#editchatinvitelink for details.
        """
        return await self.api_request(
            'editChatInviteLink',
            parameters=locals()
        )

    async def revokeChatInviteLink(self, chat_id: Union[int, str], invite_link: str):
        """Use this method to revoke an invite link created by the bot.

        If the primary link is revoked, a new link is automatically generated.
        The bot must be an administrator in the chat for this to work and must
            have the appropriate administrator rights.
        Returns the revoked invite link as ChatInviteLink object.
        See https://core.telegram.org/bots/api#revokechatinvitelink for details.
        """
        return await self.api_request(
            'revokeChatInviteLink',
            parameters=locals()
        )

    async def approveChatJoinRequest(self, chat_id: Union[int, str], user_id: int):
        """Use this method to approve a chat join request.

        The bot must be an administrator in the chat for this to work and must
            have the can_invite_users administrator right.
        Returns True on success.
        See https://core.telegram.org/bots/api#approvechatjoinrequest for details.
        """
        return await self.api_request(
            'approveChatJoinRequest',
            parameters=locals()
        )

    async def declineChatJoinRequest(self, chat_id: Union[int, str], user_id: int):
        """Use this method to decline a chat join request.

        The bot must be an administrator in the chat for this to work and must
            have the can_invite_users administrator right.
        Returns True on success.
        See https://core.telegram.org/bots/api#declinechatjoinrequest for details.
        """
        return await self.api_request(
            'declineChatJoinRequest',
            parameters=locals()
        )

    async def getChatMemberCount(self, chat_id: Union[int, str]):
        """Use this method to get the number of members in a chat. Returns Int on success.
        See https://core.telegram.org/bots/api#getchatmembercount for details.
        """
        return await self.api_request(
            'getChatMemberCount',
            parameters=locals()
        )

    async def getForumTopicIconStickers(self):
        """Use this method to get custom emoji stickers.

        They can be used as a forum topic icon by any user.
        Requires no parameters. Returns an Array of Sticker objects.
        See https://core.telegram.org/bots/api#getforumtopiciconstickers for details.
        """
        return await self.api_request(
            'getForumTopicIconStickers',
            parameters=locals()
        )

    async def createForumTopic(self, chat_id: Union[int, str], name: str,
                               icon_color: int, icon_custom_emoji_id: str):
        """Use this method to create a topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and must
            have the can_manage_topics administrator rights.
        Returns information about the created topic as a ForumTopic object.
        See https://core.telegram.org/bots/api#createforumtopic for details.
        """
        return await self.api_request(
            'createForumTopic',
            parameters=locals()
        )

    async def editForumTopic(self, chat_id: Union[int, str],
                             message_thread_id: int, name: str,
                             icon_custom_emoji_id: str):
        """Use this method to edit name and icon of a topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and must
            have can_manage_topics administrator rights, unless it is the
            creator of the topic.
        Returns True on success.
        See https://core.telegram.org/bots/api#editforumtopic for details.
        """
        return await self.api_request(
            'editForumTopic',
            parameters=locals()
        )

    async def closeForumTopic(self, chat_id: Union[int, str],
                              message_thread_id: int):
        """Use this method to close an open topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and must
            have the can_manage_topics administrator rights, unless it is the
            creator of the topic.
        Returns True on success.
        See https://core.telegram.org/bots/api#closeforumtopic for details.
        """
        return await self.api_request(
            'closeForumTopic',
            parameters=locals()
        )

    async def reopenForumTopic(self, chat_id: Union[int, str],
                               message_thread_id: int):
        """Use this method to reopen a closed topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and must
            have the can_manage_topics administrator rights, unless it is the
            creator of the topic.
        Returns True on success.
        See https://core.telegram.org/bots/api#reopenforumtopic for details.
        """
        return await self.api_request(
            'reopenForumTopic',
            parameters=locals()
        )

    async def deleteForumTopic(self, chat_id: Union[int, str],
                               message_thread_id: int):
        """Use this method to delete a forum topic.

        This method deletes a forum topic along with all its messages in a
            forum supergroup chat.
        The bot must be an administrator in the chat for this to work and must
            have the can_delete_messages administrator rights.
        Returns True on success.
        See https://core.telegram.org/bots/api#deleteforumtopic for details.
        """
        return await self.api_request(
            'deleteForumTopic',
            parameters=locals()
        )

    async def unpinAllForumTopicMessages(self, chat_id: Union[int, str],
                                         message_thread_id: int):
        """Use this method to clear the list of pinned messages in a forum topic.

        The bot must be an administrator in the chat for this to work and must
            have the can_pin_messages administrator right in the supergroup.
        Returns True on success.
        See https://core.telegram.org/bots/api#unpinallforumtopicmessages for details.
        """
        return await self.api_request(
            'unpinAllForumTopicMessages',
            parameters=locals()
        )

    async def deleteMyCommands(self, scope: 'BotCommandScope', language_code: str):
        """Use this method to delete the list of the bot's commands for the given scope and user language.

        After deletion, higher level commands will be shown to affected users.
        Returns True on success.
        See https://core.telegram.org/bots/api#deletemycommands for details.
        """
        return await self.api_request(
            'deleteMyCommands',
            parameters=locals()
        )

    async def setChatMenuButton(self, chat_id: int, menu_button: 'MenuButton'):
        """Use this method to change the bot's menu button in a private chat, or the default menu button.

        Returns True on success.
        See https://core.telegram.org/bots/api#setchatmenubutton for details.
        """
        return await self.api_request(
            'setChatMenuButton',
            parameters=locals()
        )

    async def getChatMenuButton(self, chat_id: int):
        """Use this method to get the current value of the bot's menu button.

        Use this method to get the current value of the bot's menu button in a
            private chat, or the default menu button.
        Returns MenuButton on success.
        See https://core.telegram.org/bots/api#getchatmenubutton for details.
        """
        return await self.api_request(
            'getChatMenuButton',
            parameters=locals()
        )

    async def setMyDefaultAdministratorRights(self,
                                              rights: 'ChatAdministratorRights',
                                              for_channels: bool):
        """Use this method to change the default administrator rights.

        Use this method to change the default administrator rights requested by
            the bot when it's added as an administrator to groups or channels.
        These rights will be suggested to users, but they are free to modify
            the list before adding the bot.
        Returns True on success.
        See https://core.telegram.org/bots/api#setmydefaultadministratorrights for details.
        """
        return await self.api_request(
            'setMyDefaultAdministratorRights',
            parameters=locals()
        )

    async def getMyDefaultAdministratorRights(self, for_channels: bool):
        """Use this method to get the current default administrator rights of
            the bot.
        Returns ChatAdministratorRights on success.
        See https://core.telegram.org/bots/api#getmydefaultadministratorrights for details.
        """
        return await self.api_request(
            'getMyDefaultAdministratorRights',
            parameters=locals()
        )

    async def getCustomEmojiStickers(self, custom_emoji_ids: List[str]):
        """Use this method to get information about custom emoji stickers by their identifiers.

        Returns an Array of Sticker objects.
        See https://core.telegram.org/bots/api#getcustomemojistickers for details.
        """
        return await self.api_request(
            'getCustomEmojiStickers',
            parameters=locals()
        )

    async def answerWebAppQuery(self, web_app_query_id: str,
                                result: 'InlineQueryResult'):
        """Use this method to set the result of an interaction with a Web App.

        Use this method to set the result of an interaction with a Web App and
            send a corresponding message on behalf of the user to the chat from
            which the query originated.
        On success, a SentWebAppMessage object is returned.
        See https://core.telegram.org/bots/api#answerwebappquery for details.
        """
        return await self.api_request(
            'answerWebAppQuery',
            parameters=locals()
        )

    async def createInvoiceLink(self, title: str, description: str,
                                payload: str, provider_token: str,
                                currency: str, prices: List['LabeledPrice'],
                                max_tip_amount: int,
                                suggested_tip_amounts: List[int],
                                provider_data: str, photo_url: str,
                                photo_size: int, photo_width: int,
                                photo_height: int, need_name: bool,
                                need_phone_number: bool, need_email: bool,
                                need_shipping_address: bool,
                                send_phone_number_to_provider: bool,
                                send_email_to_provider: bool,
                                is_flexible: bool,
                                business_connection_id: str = None,
                                subscription_period: int = None
                                ):
        """Use this method to create a link for an invoice.

        Returns the created invoice link as String on success. See
        https://core.telegram.org/bots/api#createinvoicelink for details.

        Attributes:
            business_connection_id (Optional[str]): Unique identifier of the
                business connection on behalf of which the link will be created.
                For payments in Telegram Stars only.
            subscription_period (Optional[int]): The number of seconds the
                subscription will be active for before the next payment. The
                currency must be set to “XTR” (Telegram Stars) if the parameter
                is used. Currently, it must always be 2592000 (30 days) if
                specified. Any number of subscriptions can be active for a given
                bot at the same time, including multiple concurrent
                subscriptions from the same user.
                Subscription price must no exceed 2500 Telegram Stars.
        """
        return await self.api_request(
            'createInvoiceLink',
            parameters=locals()
        )

    async def editGeneralForumTopic(self, chat_id: Union[int, str], name: str):
        """Edit the name of the 'General' topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and must
            have can_manage_topics administrator rights.
        Returns True on success.
        See https://core.telegram.org/bots/api#editgeneralforumtopic for details.
        """
        return await self.api_request(
            'editGeneralForumTopic',
            parameters=locals()
        )

    async def closeGeneralForumTopic(self, chat_id: Union[int, str]):
        """Close an open 'General' topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and must
            have the can_manage_topics administrator rights.
        Returns True on success.
        See https://core.telegram.org/bots/api#closegeneralforumtopic for details.
        """
        return await self.api_request(
            'closeGeneralForumTopic',
            parameters=locals()
        )

    async def reopenGeneralForumTopic(self, chat_id: Union[int, str]):
        """Reopen a closed 'General' topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and must
            have the can_manage_topics administrator rights.
            The topic will be automatically unhidden if it was hidden.
        Returns True on success.
        See https://core.telegram.org/bots/api#reopengeneralforumtopic for details.
        """
        return await self.api_request(
            'reopenGeneralForumTopic',
            parameters=locals()
        )

    async def hideGeneralForumTopic(self, chat_id: Union[int, str]):
        """Hide the 'General' topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and
            must have the can_manage_topics administrator rights.
            The topic will be automatically closed if it was open.
        Returns True on success.
        See https://core.telegram.org/bots/api#hidegeneralforumtopic for details.
        """
        return await self.api_request(
            'hideGeneralForumTopic',
            parameters=locals()
        )

    async def unhideGeneralForumTopic(self, chat_id: Union[int, str]):
        """Unhide the 'General' topic in a forum supergroup chat.

        The bot must be an administrator in the chat for this to work and must
            have the can_manage_topics administrator rights.
        Returns True on success.
        See https://core.telegram.org/bots/api#unhidegeneralforumtopic for details.
        """
        return await self.api_request(
            'unhideGeneralForumTopic',
            parameters=locals()
        )

    async def setMyName(self, name: str, language_code: str):
        """Change the bot's name.

        Returns True on success.
        See https://core.telegram.org/bots/api#setmyname for details.
        """
        return await self.api_request(
            'setMyName',
            parameters=locals()
        )

    async def getMyName(self, language_code: str):
        """Get the current bot name for the given user language.

        Returns BotName on success.
        See https://core.telegram.org/bots/api#getmyname for details.
        """
        return await self.api_request(
            'getMyName',
            parameters=locals()
        )

    async def setMyDescription(self, description: str, language_code: str):
        """Change the bot's description, which is shown in the chat with the bot if
            the chat is empty.

        Returns True on success.
        See https://core.telegram.org/bots/api#setmydescription for details.
        """
        return await self.api_request(
            'setMyDescription',
            parameters=locals()
        )

    async def getMyDescription(self, language_code: str):
        """Get the current bot description for the given user language.

        Returns BotDescription on success.
        See https://core.telegram.org/bots/api#getmydescription for details.
        """
        return await self.api_request(
            'getMyDescription',
            parameters=locals()
        )

    async def setMyShortDescription(self, short_description: str, language_code: str):
        """Change the bot's short description, which is shown on the bot's profile
            page and is sent together with the link when users share the bot.

        Returns True on success.
        See https://core.telegram.org/bots/api#setmyshortdescription for details.
        """
        return await self.api_request(
            'setMyShortDescription',
            parameters=locals()
        )

    async def getMyShortDescription(self, language_code: str):
        """Get the current bot short description for the given user language.

        Returns BotShortDescription on success.
        See https://core.telegram.org/bots/api#getmyshortdescription for details.
        """
        return await self.api_request(
            'getMyShortDescription',
            parameters=locals()
        )

    async def setStickerEmojiList(self, sticker: str, emoji_list: List[str]):
        """Change the list of emoji assigned to a regular or custom emoji sticker.

        The sticker must belong to a sticker set created by the bot.
        Returns True on success.
        See https://core.telegram.org/bots/api#setstickeremojilist for details.
        """
        return await self.api_request(
            'setStickerEmojiList',
            parameters=locals()
        )

    async def setStickerKeywords(self, sticker: str, keywords: List[str]):
        """Change search keywords assigned to a regular or custom emoji sticker.

        The sticker must belong to a sticker set created by the bot.
        Returns True on success.
        See https://core.telegram.org/bots/api#setstickerkeywords for details.
        """
        return await self.api_request(
            'setStickerKeywords',
            parameters=locals()
        )

    async def setStickerMaskPosition(self, sticker: str, mask_position: 'MaskPosition'):
        """Change the mask position of a mask sticker.

        The sticker must belong to a sticker set that was created by the bot.
        Returns True on success.
        See https://core.telegram.org/bots/api#setstickermaskposition for details.
        """
        return await self.api_request(
            'setStickerMaskPosition',
            parameters=locals()
        )

    async def setStickerSetTitle(self, name: str, title: str):
        """Set the title of a created sticker set.

        Returns True on success.
        See https://core.telegram.org/bots/api#setstickersettitle for details.
        """
        return await self.api_request(
            'setStickerSetTitle',
            parameters=locals()
        )

    async def setStickerSetThumbnail(self, name: str, user_id: int,
                                     format_: str,
                                     thumbnail: 'InputFile or String',
                                     **kwargs):
        """Set the thumbnail of a regular or mask sticker set.

        The format of the thumbnail file must match the format of the stickers
            in the set.
        Returns True on success.
        See https://core.telegram.org/bots/api#setstickersetthumbnail for details.
        """
        parameters = handle_forbidden_names_for_parameters(
            parameters=locals().copy(),
            kwargs=kwargs
        )
        return await self.api_request(
            'setStickerSetThumbnail',
            parameters=parameters
        )

    async def setCustomEmojiStickerSetThumbnail(self, name: str, custom_emoji_id: str):
        """Set the thumbnail of a custom emoji sticker set.

        Returns True on success.
        See https://core.telegram.org/bots/api#setcustomemojistickersetthumbnail for details.
        """
        return await self.api_request(
            'setCustomEmojiStickerSetThumbnail',
            parameters=locals()
        )

    async def deleteStickerSet(self, name: str):
        """Delete a sticker set that was created by the bot.

        Returns True on success.
        See https://core.telegram.org/bots/api#deletestickerset for details.
        """
        return await self.api_request(
            'deleteStickerSet',
            parameters=locals()
        )

    async def unpinAllGeneralForumTopicMessages(self, chat_id: Union[int, str]):
        """Clear the list of pinned messages in a General forum topic.

        The bot must be an administrator in the chat for this to work and must
            have the can_pin_messages administrator right in the supergroup.
        Returns True on success.
        See https://core.telegram.org/bots/api#unpinallgeneralforumtopicmessages for details.
        """
        return await self.api_request(
            'unpinAllGeneralForumTopicMessages',
            parameters=locals()
        )

    async def getUserChatBoosts(self, chat_id: Union[int, str], user_id: int):
        """Get the list of boosts added to a chat by a user.

        Requires administrator rights in the chat.
        Returns a UserChatBoosts object.
        See https://core.telegram.org/bots/api#getuserchatboosts for details.
        """
        return await self.api_request(
            'getUserChatBoosts',
            parameters=locals()
        )

    async def forwardMessages(self, chat_id: Union[int, str],
                              from_chat_id: Union[int, str],
                              message_ids: List[int],
                              message_thread_id: int = None,
                              disable_notification: bool = None,
                              protect_content: bool = None):
        """Forward multiple messages of any kind.

        If some of the specified messages can't be found or forwarded, they are
            skipped.
        Service messages and messages with protected content can't be
            forwarded.
        Album grouping is kept for forwarded messages.
        On success, an array of MessageId of the sent messages is returned.
        See https://core.telegram.org/bots/api#forwardmessages for details.
        """
        return await self.api_request(
            'forwardMessages',
            parameters=locals()
        )

    async def copyMessages(self, chat_id: Union[int, str],
                           from_chat_id: Union[int, str],
                           message_ids: List[int],
                           message_thread_id: int = None,
                           disable_notification: bool = None,
                           protect_content: bool = None,
                           remove_caption: bool = None):
        """Copy messages of any kind.

        If some of the specified messages can't be found or copied, they are
            skipped.
        Service messages, giveaway messages, giveaway winners messages, and
            invoice messages can't be copied.
        A quiz poll can be copied only if the value of the field
            correct_option_id is known to the bot.
        The method is analogous to the method forwardMessages, but the copied
            messages don't have a link to the original message.
        Album grouping is kept for copied messages.
        On success, an array of MessageId of the sent messages is returned.
        See https://core.telegram.org/bots/api#copymessages for details.
        """
        return await self.api_request(
            'copyMessages',
            parameters=locals()
        )

    async def setMessageReaction(self, chat_id: Union[int, str],
                                 message_id: int,
                                 reaction: List[ReactionType] = None,
                                 is_big: bool = None):
        """Change the chosen reactions on a message.

        Service messages can't be reacted to.
        Automatically forwarded messages from a channel to its discussion group
            have the same available reactions as messages in the channel.
        Returns True on success.
        See https://core.telegram.org/bots/api#setmessagereaction for details.
        """
        return await self.api_request(
            'setMessageReaction',
            parameters=locals()
        )

    async def getBusinessConnection(self, business_connection_id: str):
        """Get information about the connection of the bot with a business account.

        Returns a BusinessConnection object on success.
        See https://core.telegram.org/bots/api#getbusinessconnection for details.
        """
        return await self.api_request(
            'getBusinessConnection',
            parameters=locals()
        )

    async def replaceStickerInSet(self, user_id: int, name: str,
                                  old_sticker: str, sticker: 'InputSticker'):
        """Replace an existing sticker in a sticker set with a new one.

        The method is equivalent to calling deleteStickerFromSet, then
            addStickerToSet, then setStickerPositionInSet.
        Returns True on success.
        See https://core.telegram.org/bots/api#replacestickerinset for details.
        """
        return await self.api_request(
            'replaceStickerInSet',
            parameters=locals()
        )

    async def sendPaidMedia(self, chat_id: Union[int, str], star_count: int,
                            media: List[InputPaidMedia],
                            payload: str = None,
                            business_connection_id: str = None,
                            caption: str = None, parse_mode: str = None,
                            caption_entities: List[dict] = None,
                            show_caption_above_media: bool = None,
                            disable_notification: bool = None,
                            protect_content: bool = None,
                            reply_parameters: ReplyParameters = None,
                            allow_paid_broadcast: bool = None,
                            reply_markup = None):
        """Send paid media to channel chats.

        On success, the sent Message is returned.
        See https://core.telegram.org/bots/api#sendpaidmedia for details.
        """
        return await self.api_request(
            'sendPaidMedia',
            parameters=locals()
        )

    async def getStarTransactions(self,
                                  offset: int = None,
                                  limit: int = None):
        """Returns the bot's Telegram Star transactions in chronological order.

        On success, returns a StarTransactions object.
        See https://core.telegram.org/bots/api#getstartransactions for details.

        `offset`: number of transactions to skip in the response (defaults to 0)
        `limit`: maximum number of transactions to be retrieved.
            Values between 1-100 are accepted (defaults to 100).
        """
        return await self.api_request(
            'getStarTransactions',
            parameters=locals()
        )

    async def refundStarPayment(self,
                                user_id: int,
                                telegram_payment_charge_id: str):
        """Refunds a successful payment in Telegram Stars.

        Returns True on success.
        See https://core.telegram.org/bots/api#refundstarpayment for details.
        """
        return await self.api_request(
            'refundStarPayment',
            parameters=locals()
        )
    
    async def createChatSubscriptionInviteLink(self, chat_id: Union[int, str],
                                               name: str,
                                               subscription_period: int,
                                               subscription_price: int):
        """Create a subscription invite link for a channel chat.
        
        The bot must have the can_invite_users administrator rights.
        The link can be edited using the method editChatSubscriptionInviteLink
            or revoked using the method revokeChatInviteLink.
        Returns the new invite link as a ChatInviteLink object.
        See https://core.telegram.org/bots/api#createchatsubscriptioninvitelink
        for details.
        """
        return await self.api_request(
            'createChatSubscriptionInviteLink',
            parameters=locals()
        )
    
    async def editChatSubscriptionInviteLink(self, chat_id: Union[int, str],
                                             invite_link: str, name: str):
        """Edit a subscription invite link created by the bot.
        
        The bot must have the can_invite_users administrator rights.
        Returns the edited invite link as a ChatInviteLink object.
        See https://core.telegram.org/bots/api#editchatsubscriptioninvitelink
        for details.
        """
        return await self.api_request(
            'editChatSubscriptionInviteLink',
            parameters=locals()
        )

    async def setUserEmojiStatus(self, user_id: int,
                                 emoji_status_custom_emoji_id: str = None,
                                 emoji_status_expiration_date: int = None):
        """Changes the emoji status for a given user that previously allowed the
            bot to manage their emoji status via the Mini App method
            requestEmojiStatusAccess.
        
        Returns True on success.
        See https://core.telegram.org/bots/api#setuseremojistatus for details.
        """
        if emoji_status_custom_emoji_id is None:
            emoji_status_custom_emoji_id = ''
        return await self.api_request(
            'setUserEmojiStatus',
            parameters=locals()
        )
    
    async def getAvailableGifts(self):
        """Returns the list of gifts that can be sent by the bot to users.
        
        Requires no parameters.
        Returns a Gifts object.
        See https://core.telegram.org/bots/api#getavailablegifts for details.
        """
        return await self.api_request(
            'getAvailableGifts',
            parameters=locals()
        )

    async def sendGift(self, user_id: int, chat_id: Union[int, str],
                       gift_id: str, pay_for_upgrade: bool,
                       text: str, text_parse_mode: str,
                       text_entities: List['MessageEntity']):
        """Sends a gift to the given user.
        
        The gift can't be converted to Telegram Stars by the user.
        Returns True on success.
        See https://core.telegram.org/bots/api#sendgift for details.
        """
        return await self.api_request(
            'sendGift',
            parameters=locals()
        )

    async def verifyUser(self, user_id: int,
                         custom_description: str = None):
        """Verifies a user on behalf of the organization which is represented by
            the bot.
        
        Returns True on success.
        See https://core.telegram.org/bots/api#verifyuser for details.
        """
        if len(custom_description) > 70:
            raise TypeError("Parameter `custom_description` is too long "
                            "(0-70 characters).")
        return await self.api_request(
            'verifyUser',
            parameters=locals()
        )

    async def verifyChat(self, chat_id: Union[int, str],
                         custom_description: str = None):
        """Verifies a chat on behalf of the organization which is represented by
            the bot.
        
        Returns True on success.
        See https://core.telegram.org/bots/api#verifychat for details.
        """
        if isinstance(chat_id, str) and chat_id.isnumeric():
            chat_id = int(chat_id)
        if not (isinstance(chat_id, int) or
            (isinstance(chat_id, str) and chat_id.startswith('@'))):
            raise TypeError(f"Invalid chat_id: `{chat_id}`")
        if len(custom_description) > 70:
            raise TypeError("Parameter `custom_description` is too long "
                            "(0-70 characters).")
        return await self.api_request(
            'verifyChat',
            parameters=locals()
        )

    async def removeUserVerification(self, user_id: int):
        """Removes verification from a user who is currently verified on behalf
        of the organization represented by the bot.
        
        Returns True on success.
        See https://core.telegram.org/bots/api#removeuserverification for
            details.
        """
        return await self.api_request(
            'removeUserVerification',
            parameters=locals()
        )

    async def removeChatVerification(self, chat_id: Union[int, str]):
        """Removes verification from a chat that is currently verified on behalf
        of the organization represented by the bot.
        
        Returns True on success.
        See https://core.telegram.org/bots/api#removechatverification for
            details.
        """
        if not (isinstance(chat_id, int) or
            (isinstance(chat_id, str) and chat_id.startswith('@'))):
            raise TypeError(f"Invalid chat_id: `{chat_id}`")
        return await self.api_request(
            'removeChatVerification',
            parameters=locals()
        )

    async def savePreparedInlineMessage(self,
                                        user_id: int,
                                        result: 'InlineQueryResult',
                                        allow_user_chats: bool = None,
                                        allow_bot_chats: bool = None,
                                        allow_group_chats: bool = None,
                                        allow_channel_chats: bool = None
                                        ) -> 'PreparedInlineMessage':
        """Stores a message that can be sent by a user of a Mini App.
        
        Returns a PreparedInlineMessage object.
        See https://core.telegram.org/bots/api#savepreparedinlinemessage for
            details.
        """
        return await self.api_request(
            'savePreparedInlineMessage',
            parameters=locals()
        )

    async def editUserStarSubscription(self, user_id: int,
                                       telegram_payment_charge_id: str,
                                       is_canceled: bool):
        """Allows the bot to cancel or re-enable extension of a subscription
            paid in Telegram Stars.
        
        Returns True on success.
        See https://core.telegram.org/bots/api#edituserstarsubscription for
            details.
        """
        return await self.api_request(
            'editUserStarSubscription',
            parameters=locals()
        )

    async def giftPremiumSubscription(
        self, user_id: int,
        month_count: int, star_count: int,
        text: str = None,
        text_parse_mode: str = None,
        text_entities: List['MessageEntity'] = None
    ):
        """Gifts a Telegram Premium subscription to the given user.
        
        Returns True on success.
        See https://core.telegram.org/bots/api#giftpremiumsubscription for details.
        """
        if star_count not in (1000, 1500, 2500):
            logging.warning("Star count should be 1000 for three months, 1500 "
                            "for 6 months or 2000 for 12 months")
        return await self.api_request(
            'giftPremiumSubscription',
            parameters=locals()
        )

    async def readBusinessMessage(self,
                                  business_connection_id: str,
                                  chat_id: int,
                                  message_id: int):
        """Marks incoming message as read on behalf of a business account.
        
        Requires the can_read_messages business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#readbusinessmessage for details.
        """
        return await self.api_request(
            'readBusinessMessage',
            parameters=locals()
        )
    
    async def deleteBusinessMessages(self,
                                     business_connection_id: str,
                                     message_ids: List[int]):
        """Delete messages on behalf of a business account.
        
        Requires the can_delete_outgoing_messages business bot right to delete
            messages sent by the bot itself, or the can_delete_all_messages
            business bot right to delete any message.
        Returns True on success.
        See https://core.telegram.org/bots/api#deletebusinessmessages for details.
        """
        return await self.api_request(
            'deleteBusinessMessages',
            parameters=locals()
        )

    async def setBusinessAccountName(self,
                                     business_connection_id: str,
                                     first_name: str,
                                     last_name: str = None):
        """Changes the first and last name of a managed business account.
        
        Requires the can_change_name business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#setbusinessaccountname for details.
        """
        return await self.api_request(
            'setBusinessAccountName',
            parameters=locals()
        )

    async def setBusinessAccountUsername(self,
                                         business_connection_id: str,
                                         username: str = None):
        """Changes the username of a managed business account.
        
        Requires the can_change_username business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#setbusinessaccountusername for details.
        """
        return await self.api_request(
            'setBusinessAccountUsername',
            parameters=locals()
        )

    async def setBusinessAccountBio(self,
                                    business_connection_id: str,
                                    bio: str = None):
        """Changes the bio of a managed business account.
        
        Requires the can_change_bio business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#setbusinessaccountbio for details.
        """
        return await self.api_request(
            'setBusinessAccountBio',
            parameters=locals()
        )

    async def setBusinessAccountProfilePhoto(self,
                                             business_connection_id: str,
                                             photo: 'InputProfilePhoto',
                                             is_public: bool = None):
        """Changes the profile photo of a managed business account.
        
        Requires the can_edit_profile_photo business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#setbusinessaccountprofilephoto for details.
        """
        return await self.api_request(
            'setBusinessAccountProfilePhoto',
            parameters=locals()
        )

    async def removeBusinessAccountProfilePhoto(self, business_connection_id: str, is_public: bool):
        """Removes the current profile photo of a managed business account.
        
        Requires the can_edit_profile_photo business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#removebusinessaccountprofilephoto for details.
        """
        return await self.api_request(
            'removeBusinessAccountProfilePhoto',
            parameters=locals()
        )

    async def setBusinessAccountGiftSettings(self, business_connection_id: str, show_gift_button: bool, accepted_gift_types: 'AcceptedGiftTypes'):
        """Changes the privacy settings pertaining to incoming gifts in a managed
            business account.
        
        Requires the can_change_gift_settings business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#setbusinessaccountgiftsettings for details.
        """
        return await self.api_request(
            'setBusinessAccountGiftSettings',
            parameters=locals()
        )

    async def getBusinessAccountStarBalance(self, business_connection_id: str):
        """Returns the amount of Telegram Stars owned by a managed business
            account.
        
        Requires the can_view_gifts_and_stars business bot right.
        Returns StarAmount on success.
        See https://core.telegram.org/bots/api#getbusinessaccountstarbalance for details.
        """
        return await self.api_request(
            'getBusinessAccountStarBalance',
            parameters=locals()
        )

    async def transferBusinessAccountStars(self, business_connection_id: str, star_count: int):
        """Transfers Telegram Stars from the business account balance to the bot's
            balance.
        
        Requires the can_transfer_stars business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#transferbusinessaccountstars for details.
        """
        return await self.api_request(
            'transferBusinessAccountStars',
            parameters=locals()
        )

    async def getBusinessAccountGifts(self,
                                      business_connection_id: str,
                                      exclude_unsaved: bool = None,
                                      exclude_saved: bool = None,
                                      exclude_unlimited: bool = None,
                                      exclude_limited: bool = None,
                                      exclude_unique: bool = None,
                                      sort_by_price: bool = None,
                                      offset: str = None,
                                      limit: int = None):
        """Returns the gifts received and owned by a managed business account.
        
        Requires the can_view_gifts_and_stars business bot right.
        Returns OwnedGifts on success.
        See https://core.telegram.org/bots/api#getbusinessaccountgifts for details.
        """
        return await self.api_request(
            'getBusinessAccountGifts',
            parameters=locals()
        )

    async def convertGiftToStars(self, business_connection_id: str, owned_gift_id: str):
        """Converts a given regular gift to Telegram Stars.
        
        Requires the can_convert_gifts_to_stars business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#convertgifttostars for details.
        """
        return await self.api_request(
            'convertGiftToStars',
            parameters=locals()
        )

    async def upgradeGift(self, business_connection_id: str,
                          owned_gift_id: str,
                          keep_original_details: bool = None,
                          star_count: int = None):
        """Upgrades a given regular gift to a unique gift.
        
        Requires the can_transfer_and_upgrade_gifts business bot right.
        Additionally requires the can_transfer_stars business bot right if the
            upgrade is paid.
        Returns True on success.
        See https://core.telegram.org/bots/api#upgradegift for details.
        """
        return await self.api_request(
            'upgradeGift',
            parameters=locals()
        )

    async def transferGift(self, business_connection_id: str,
                           owned_gift_id: str,
                           new_owner_chat_id: int,
                           star_count: int = None):
        """Transfers an owned unique gift to another user.
        
        Requires the can_transfer_and_upgrade_gifts business bot right.
        Requires can_transfer_stars business bot right if the transfer is paid.
        Returns True on success.
        See https://core.telegram.org/bots/api#transfergift for details.
        """
        return await self.api_request(
            'transferGift',
            parameters=locals()
        )

    async def postStory(self, business_connection_id: str,
                        content: 'InputStoryContent',
                        active_period: int,
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List['MessageEntity'] = None,
                        areas: List['StoryArea'] = None,
                        post_to_chat_page: bool = None,
                        protect_content: bool = None):
        """Posts a story on behalf of a managed business account.
        
        Requires the can_manage_stories business bot right.
        Returns Story on success.
        See https://core.telegram.org/bots/api#poststory for details.
        """
        return await self.api_request(
            'postStory',
            parameters=locals()
        )

    async def editStory(self, business_connection_id: str,
                        story_id: int,
                        content: 'InputStoryContent',
                        caption: str = None,
                        parse_mode: str = None,
                        caption_entities: List[dict] = None,
                        areas: List['StoryArea'] = None):
        """Edits a story previously posted by the bot on behalf of a managed
            business account.
        
        Requires the can_manage_stories business bot right.
        Returns Story on success.
        See https://core.telegram.org/bots/api#editstory for details.
        """
        return await self.api_request(
            'editStory',
            parameters=locals()
        )

    async def deleteStory(self, business_connection_id: str, story_id: int):
        """Deletes a story previously posted by the bot on behalf of a managed
            business account.
        
        Requires the can_manage_stories business bot right.
        Returns True on success.
        See https://core.telegram.org/bots/api#deletestory for details.
        """
        return await self.api_request(
            'deleteStory',
            parameters=locals()
        )
