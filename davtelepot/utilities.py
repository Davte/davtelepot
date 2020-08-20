"""Useful functions used by Davte when programming in python."""

# Standard library modules
import asyncio
import collections
import csv
import datetime
import inspect
import io
import json
import logging
import os
import random
import re
import string
import time

from difflib import SequenceMatcher

# Third party modules
from typing import Tuple, Union

import aiohttp
from aiohttp import web
from bs4 import BeautifulSoup


weekdays = collections.OrderedDict()
weekdays[0] = {
    'en': "Monday",
    'it': "Lunedì",
}
weekdays[1] = {
    'en': "Tuesday",
    'it': "Martedì",
}
weekdays[2] = {
    'en': "Wednesday",
    'it': "Mercoledì",
}
weekdays[3] = {
    'en': "Thursday",
    'it': "Giovedì",
}
weekdays[4] = {
    'en': "Friday",
    'it': "Venerdì",
}
weekdays[5] = {
    'en': "Saturday",
    'it': "Sabato",
}
weekdays[6] = {
    'en': "Sunday",
    'it': "Domenica",
}


def sumif(iterable, condition):
    """Sum all `iterable` items matching `condition`."""
    return sum(
        filter(
            condition,
            iterable
        )
    )


def markdown_check(text, symbols):
    """Check that  all `symbols` occur an even number of times in `text`."""
    for s in symbols:
        if (len(text.replace(s, "")) - len(text)) % 2 != 0:
            return False
    return True


def shorten_text(text, limit, symbol="[...]"):
    """Return a given text truncated at limit if longer than limit.

    On truncation, add symbol.
    """
    assert type(text) is str and type(symbol) is str and type(limit) is int
    if len(text) <= limit:
        return text
    return text[:limit-len(symbol)] + symbol


def extract(text, starter=None, ender=None):
    """Return string in text between starter and ender.

    If starter is None, truncate at ender.
    """
    if starter and starter in text:
        text = text.partition(starter)[2]
    if ender:
        return text.partition(ender)[0]
    return text


def make_button(text=None, callback_data='',
                prefix='', delimiter='|', data=None):
    """Return a Telegram bot API-compliant button.

    callback_data can be either a ready-to-use string or a
        prefix + delimiter-joined data.
    If callback_data exceeds Telegram limits (currently 60 characters),
        it gets truncated at the last delimiter before that limit.
    If absent, text is the same as callback_data.
    """
    if data is None:
        data = []
    if len(data):
        callback_data += delimiter.join(map(str, data))
    callback_data = "{p}{c}".format(
        p=prefix,
        c=callback_data
    )
    if len(callback_data) > 60:
        callback_data = callback_data[:61]
        callback_data = callback_data[:-1-callback_data[::-1].find(delimiter)]
    if text is None:
        text = callback_data
    return dict(
        text=text,
        callback_data=callback_data
    )


def mkbtn(x, y):
    """Backward compatibility.

    Warning: this function will be deprecated sooner or later,
        stop using it and migrate to make_button.
    """
    return make_button(text=x, callback_data=y)


def make_lines_of_buttons(buttons, row_len=1):
    """Split `buttons` list in a list of lists having length = `row_len`."""
    return [
        buttons[i:i + row_len]
        for i in range(
            0,
            len(buttons),
            row_len
        )
    ]


def make_inline_keyboard(buttons, row_len=1):
    """Make a Telegram API compliant inline keyboard."""
    return dict(
        inline_keyboard=make_lines_of_buttons(
            buttons,
            row_len
        )
    )


async def async_get(url, mode='json', **kwargs):
    """Make an async get request.

    `mode`s allowed:
        * html
        * json
        * string

    Additional **kwargs may be passed.
    """
    if 'mode' in kwargs:
        mode = kwargs['mode']
        del kwargs['mode']
    return await async_request(
        url,
        method='get',
        mode=mode,
        **kwargs
    )


async def async_post(url, mode='html', **kwargs):
    """Make an async post request.

    `mode`s allowed:
        * html
        * json
        * string

    Additional **kwargs may be passed (will be converted to `data`).
    """
    return await async_request(
        url,
        method='post',
        mode=mode,
        **kwargs
    )


async def async_request(url, method='get', mode='json', encoding=None, errors='strict',
                        **kwargs):
    """Make an async html request.

    `types` allowed
        * get
        * post

    `mode`s allowed:
        * html
        * json
        * string
        * picture

    Additional **kwargs may be passed.
    """
    try:
        async with aiohttp.ClientSession() as s:
            async with (
                s.get(url, timeout=30)
                if method == 'get'
                else s.post(url, timeout=30, data=kwargs)
            ) as r:
                if mode in ['html', 'json', 'string']:
                    result = await r.text(encoding=encoding, errors=errors)
                else:
                    result = await r.read()
                    if encoding is not None:
                        result = result.decode(encoding)
    except Exception as e:
        logging.error(
            'Error making async request to {}:\n{}'.format(
                url,
                e
            ),
            exc_info=False
        )  # Set exc_info=True to debug
        return e
    if mode == 'json':
        try:
            result = json.loads(
                result
            )
        except json.decoder.JSONDecodeError:
            result = {}
    elif mode == 'html':
        result = BeautifulSoup(result, "html.parser")
    elif mode == 'string':
        result = result
    return result


def json_read(file_, default=None, encoding='utf-8', **kwargs):
    """Return json parsing of `file_`, or `default` if file does not exist.

    `encoding` refers to how the file should be read.
    `kwargs` will be passed to json.load()
    """
    if default is None:
        default = {}
    if not os.path.isfile(file_):
        return default
    with open(file_, "r", encoding=encoding) as f:
        return json.load(f, **kwargs)


def json_write(what, file_, encoding='utf-8', **kwargs):
    """Store `what` in json `file_`.

    `encoding` refers to how the file should be written.
    `kwargs` will be passed to json.dump()
    """
    with open(file_, "w", encoding=encoding) as f:
        return json.dump(what, f, indent=4, **kwargs)


def csv_read(file_, default=None, encoding='utf-8',
             delimiter=',', quotechar='"', **kwargs):
    """Return csv parsing of `file_`, or `default` if file does not exist.

    `encoding` refers to how the file should be read.
    `delimiter` is the separator of fields.
    `quotechar` is the string delimiter.
    `kwargs` will be passed to csv.reader()
    """
    if default is None:
        default = []
    if not os.path.isfile(file_):
        return default
    result = []
    keys = []
    with open(file_, newline='', encoding=encoding) as csv_file:
        csv_reader = csv.reader(
            csv_file,
            delimiter=delimiter,
            quotechar=quotechar,
            **kwargs
        )
        for row in csv_reader:
            if not keys:
                keys = row
                continue
            item = collections.OrderedDict()
            for key, val in zip(keys, row):
                item[key] = val
            result.append(item)
    return result


def csv_write(info=None, file_='output.csv', encoding='utf-8',
              delimiter=',', quotechar='"', **kwargs):
    """Store `info` in CSV `file_`.

    `encoding` refers to how the file should be read.
    `delimiter` is the separator of fields.
    `quotechar` is the string delimiter.
    `encoding` refers to how the file should be written.
    `kwargs` will be passed to csv.writer()
    """
    if info is None:
        info = []
    assert (
        type(info) is list
        and len(info) > 0
    ), "info must be a non-empty list"
    assert all(
        isinstance(row, dict)
        for row in info
    ), "Rows must be dictionaries!"
    with open(file_, 'w', newline='', encoding=encoding) as csv_file:
        csv_writer = csv.writer(
            csv_file,
            delimiter=delimiter,
            quotechar=quotechar,
            **kwargs
        )
        csv_writer.writerow(info[0].keys())
        for row in info:
            csv_writer.writerow(row.values())
    return


class MyOD(collections.OrderedDict):
    """Subclass of OrderedDict.

    It features `get_by_val` and `get_by_key_val` methods.
    """

    def __init__(self, *args, **kwargs):
        """Return a MyOD instance."""
        super().__init__(*args, **kwargs)
        self._anti_list_casesensitive = None
        self._anti_list_caseinsensitive = None

    @property
    def anti_list_casesensitive(self):
        """Case-sensitive reverse dictionary.

        Keys and values are swapped.
        """
        if not self._anti_list_casesensitive:
            self._anti_list_casesensitive = {
                val: key
                for key, val in self.items()
            }
        return self._anti_list_casesensitive

    @property
    def anti_list_caseinsensitive(self):
        """Case-sensitive reverse dictionary.

        Keys and values are swapped and lowered.
        """
        if not self._anti_list_caseinsensitive:
            self._anti_list_caseinsensitive = {
                (val.lower() if type(val) is str else val): key
                for key, val in self.items()
            }
        return self._anti_list_caseinsensitive

    def get_by_val(self, val, case_sensitive=True):
        """Get key pointing to given val.

        Can be case-sensitive or insensitive.
        MyOD[key] = val <-- MyOD.get(key) = val <--> MyOD.get_by_val(val) = key
        """
        return (
            self.anti_list_casesensitive
            if case_sensitive
            else self.anti_list_caseinsensitive
        )[val]

    def get_by_key_val(self, key, val,
                       case_sensitive=True, return_value=False):
        """Get key (or val) of a dict-like object having key == val.

        Perform case-sensitive or insensitive search.
        """
        for x, y in self.items():
            if (
                (
                    y[key] == val
                    and case_sensitive
                ) or (
                    y[key].lower() == val.lower()
                    and not case_sensitive
                )
            ):
                return (
                    y if return_value
                    else x
                )
        return None


def line_drawing_unordered_list(list_):
    """Draw an old-fashioned unordered list.

    Unordered list example
    ├ An element
    ├ Another element
    └Last element
    """
    result = ""
    if list_:
        for x in list_[:-1]:
            result += "├ {}\n".format(x)
        result += "└ {}".format(list_[-1])
    return result


def str_to_datetime(d):
    """Convert string to datetime.

    Dataset library often casts datetimes to str, this is a workaround.
    """
    if isinstance(d, datetime.datetime):
        return d
    return datetime.datetime.strptime(
        d,
        '%Y-%m-%d %H:%M:%S.%f'
    )


def datetime_to_str(d):
    """Cast datetime to string."""
    if isinstance(d, str):
        d = str_to_datetime(d)
    if not isinstance(d, datetime.datetime):
        raise TypeError(
            'Input of datetime_to_str function must be a datetime.datetime '
            'object. Output is a str'
        )
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(d)


class MyCounter:
    """Counter object, with a `lvl` method incrementing `n` property."""

    def __init__(self):
        """Initialize and get MyCounter instance."""
        self._n = 0
        return

    def lvl(self):
        """Increments and return self.n."""
        self._n += 1
        return self.n

    def reset(self):
        """Set self.n = 0."""
        self._n = 0
        return self.n

    def n(self):
        """Counter's value."""
        return self._n


def wrapper(func, *args, **kwargs):
    """Wrap a function so that it can be later called with one argument."""
    def wrapped(update):
        return func(update, *args, **kwargs)
    return wrapped


async def async_wrapper(coroutine, *args1, **kwargs1):
    """Wrap a `coroutine` so that it can be later awaited with more arguments.

    Set some of the arguments, let the coroutine be awaited with the rest of
        them later.
    The wrapped coroutine will always pass only supported parameters to
        `coroutine`.
    Example:
    ```
        import asyncio
        from davtelepot.utilities import async_wrapper
        async def printer(a, b, c, d):
            print(a, a+b, b+c, c+d)
            return

        async def main():
            my_coroutine = await async_wrapper(
                printer,
                c=3, d=2
            )
            await my_coroutine(a=1, b=5)

        asyncio.get_event_loop().run_until_complete(main())
    ```
    """
    async def wrapped_coroutine(*args2, bot=None, update=None, user_record=None, **kwargs2):
        # Update keyword arguments
        kwargs1.update(kwargs2)
        kwargs1['bot'] = bot
        kwargs1['update'] = update
        kwargs1['user_record'] = user_record
        # Pass only supported arguments
        kwargs = {
            name: argument
            for name, argument in kwargs1.items()
            if name in inspect.signature(
                coroutine
            ).parameters
        }
        return await coroutine(*args1, *args2, **kwargs)
    return wrapped_coroutine


def forwarded(by=None):
    """Check that update is forwarded, optionally `by` someone in particular.

    Decorator: such decorated functions have effect only if update
        is forwarded from someone (you can specify `by` whom).
    """
    def is_forwarded_by(update):
        if 'forward_from' not in update:
            return False
        if by and update['forward_from']['id'] != by:
            return False
        return True

    def decorator(view_func):
        if asyncio.iscoroutinefunction(view_func):
            async def decorated(update):
                if is_forwarded_by(update):
                    return await view_func(update)
        else:
            def decorated(update):
                if is_forwarded_by(update):
                    return view_func(update)
        return decorated
    return decorator


def chat_selective(chat_id=None):
    """Check that update comes from a chat, optionally having `chat_id`.

    Such decorated functions have effect only if update comes from
        a specific (if `chat_id` is given) or generic chat.
    """
    def check_function(update):
        if 'chat' not in update:
            return False
        if chat_id:
            if update['chat']['id'] != chat_id:
                return False
        return True

    def decorator(view_func):
        if asyncio.iscoroutinefunction(view_func):
            async def decorated(update):
                if check_function(update):
                    return await view_func(update)
        else:
            def decorated(update):
                if check_function(update):
                    return view_func(update)
        return decorated
    return decorator


async def sleep_until(when: Union[datetime.datetime, datetime.timedelta]):
    """Sleep until now > `when`.

    `when` could be a datetime.datetime or a datetime.timedelta instance.
    """
    if not (
        isinstance(when, datetime.datetime)
        or isinstance(when, datetime.timedelta)
    ):
        raise TypeError(
            "sleep_until takes a datetime.datetime or datetime.timedelta "
            "object as argument!"
        )
    if isinstance(when, datetime.datetime):
        delta = when - datetime.datetime.now()
    elif isinstance(when, datetime.timedelta):
        delta = when
    else:
        delta = datetime.timedelta(seconds=1)
    if delta.days >= 0:
        await asyncio.sleep(
            delta.seconds
        )
    return


async def wait_and_do(when, what, *args, **kwargs):
    """Sleep until `when`, then call `what` passing `args` and `kwargs`."""
    await sleep_until(when)
    return await what(*args, **kwargs)


def get_csv_string(list_, delimiter=',', quotechar='"'):
    """Return a `delimiter`-delimited string of `list_` items.

    Wrap strings in `quotechar`s.
    """
    return delimiter.join(
        str(item) if type(item) is not str
        else '{q}{i}{q}'.format(
            i=item,
            q=quotechar
        )
        for item in list_
    )


def case_accent_insensitive_sql(field):
    """Get a SQL string to perform a case- and accent-insensitive query.

    Given a `field`, return a part of SQL string necessary to perform
        a case- and accent-insensitive query.
    """
    replacements = [
        (' ', ''),
        ('à', 'a'),
        ('è', 'e'),
        ('é', 'e'),
        ('ì', 'i'),
        ('ò', 'o'),
        ('ù', 'u'),
    ]
    return "{r}LOWER({f}){w}".format(
        r="replace(".upper()*len(replacements),
        f=field,
        w=''.join(
            ", '{w[0]}', '{w[1]}')".format(w=w)
            for w in replacements
        )
    )


# Italian definite articles.
ARTICOLI = MyOD()
ARTICOLI[1] = {
    'ind': 'un',
    'dets': 'il',
    'detp': 'i',
    'dess': 'l',
    'desp': 'i'
}
ARTICOLI[2] = {
    'ind': 'una',
    'dets': 'la',
    'detp': 'le',
    'dess': 'lla',
    'desp': 'lle'
}
ARTICOLI[3] = {
    'ind': 'uno',
    'dets': 'lo',
    'detp': 'gli',
    'dess': 'llo',
    'desp': 'gli'
}
ARTICOLI[4] = {
    'ind': 'un',
    'dets': 'l\'',
    'detp': 'gli',
    'dess': 'll\'',
    'desp': 'gli'
}


class Gettable:
    """Gettable objects can be retrieved from memory without being duplicated.

    Key is the primary key.
    Use class method get to instantiate (or retrieve) Gettable objects.
    Assign SubClass.instances = {}, otherwise Gettable.instances will
        contain SubClass objects.
    """

    instances = {}

    def __init__(self, *args, key=None, **kwargs):
        if key is None:
            key = args[0]
        if key not in self.__class__.instances:
            self.__class__.instances[key] = self

    @classmethod
    def get(cls, *args, key=None, **kwargs):
        """Instantiate and/or retrieve Gettable object.

        SubClass.instances is searched if exists.
        Gettable.instances is searched otherwise.
        """
        if key is None:
            key = args[0]
        else:
            kwargs['key'] = key
        if key not in cls.instances:
            cls.instances[key] = cls(*args, **kwargs)
        return cls.instances[key]


class Confirmable:
    """Confirmable objects are provided with a confirm instance method.

    It evaluates True if it was called within self._confirm_timedelta,
        False otherwise.
    When it returns True, timer is reset.
    """

    CONFIRM_TIMEDELTA = datetime.timedelta(seconds=10)

    def __init__(self, confirm_timedelta: Union[datetime.timedelta, int] = None):
        """Instantiate Confirmable instance.

        If `confirm_timedelta` is not passed,
            `self.__class__.CONFIRM_TIMEDELTA` is used as default.
        """
        if confirm_timedelta is None:
            confirm_timedelta = self.__class__.CONFIRM_TIMEDELTA
        elif type(confirm_timedelta) is int:
            confirm_timedelta = datetime.timedelta(seconds=confirm_timedelta)
        self._confirm_timedelta = None
        self.set_confirm_timedelta(confirm_timedelta)
        self._confirm_datetimes = {}

    @property
    def confirm_timedelta(self):
        """Maximum timedelta between two calls of `confirm`."""
        return self._confirm_timedelta

    def confirm_datetime(self, who='unique'):
        """Get datetime of `who`'s last confirm.

        If `who` never called `confirm`, fake an expired call.
        """
        if who not in self._confirm_datetimes:
            self._confirm_datetimes[who] = (
                datetime.datetime.now()
                - 2*self.confirm_timedelta
            )
        return self._confirm_datetimes[who]

    def set_confirm_timedelta(self, confirm_timedelta):
        """Change self._confirm_timedelta."""
        if type(confirm_timedelta) is int:
            confirm_timedelta = datetime.timedelta(
                seconds=confirm_timedelta
            )
        assert isinstance(
            confirm_timedelta, datetime.timedelta
        ), "confirm_timedelta must be a datetime.timedelta instance!"
        self._confirm_timedelta = confirm_timedelta

    def confirm(self, who='unique'):
        """Return True if `confirm` was called by `who` recetly enough."""
        now = datetime.datetime.now()
        if now >= self.confirm_datetime(who) + self.confirm_timedelta:
            self._confirm_datetimes[who] = now
            return False
        self._confirm_datetimes[who] = now - 2*self.confirm_timedelta
        return True


class HasBot:
    """Objects having a Bot subclass object as `.bot` attribute.

    HasBot objects have a .bot and .db properties for faster access.
    """

    _bot = None

    @property
    def bot(self):
        """Class bot."""
        return self.__class__._bot

    @property
    def db(self):
        """Class bot db."""
        return self.bot.db

    @classmethod
    def set_bot(cls, bot):
        """Change class bot."""
        cls._bot = bot


class CachedPage(Gettable):
    """Cache a web page and return it during CACHE_TIME, otherwise refresh.

    Usage:
    cached_page = CachedPage.get(
        'https://www.google.com',
        datetime.timedelta(seconds=30),
        **kwargs
    )
    page = await cached_page.get_page()
    """

    CACHE_TIME = datetime.timedelta(minutes=5)
    instances = {}

    def __init__(self, url, cache_time=None, **async_get_kwargs):
        """Instantiate CachedPage object.

        `url`: the URL to be cached
        `cache_time`: timedelta from last_update during which
            page will be cached
        `**kwargs` will be passed to async_get function
        """
        self._url = url
        if type(cache_time) is int:
            cache_time = datetime.timedelta(seconds=cache_time)
        if cache_time is None:
            cache_time = self.__class__.CACHE_TIME
        assert type(cache_time) is datetime.timedelta, (
            "Cache time must be a datetime.timedelta object!"
        )
        self._cache_time = cache_time
        self._page = None
        self._last_update = datetime.datetime.now() - self.cache_time
        self._async_get_kwargs = async_get_kwargs
        super().__init__(key=url)

    @property
    def url(self):
        """Get cached page url."""
        return self._url

    @property
    def cache_time(self):
        """Get cache time."""
        return self._cache_time

    @property
    def page(self):
        """Get webpage."""
        return self._page

    @property
    def last_update(self):
        """Get datetime of last update."""
        return self._last_update

    @property
    def async_get_kwargs(self):
        """Get async get request keyword arguments."""
        return self._async_get_kwargs

    @property
    def is_old(self):
        """Evaluate True if `chache_time` has passed since last update."""
        return datetime.datetime.now() > self.last_update + self.cache_time

    async def refresh(self):
        """Update cached web page."""
        try:
            self._page = await async_get(self.url, **self.async_get_kwargs)
            self._last_update = datetime.datetime.now()
            return 0
        except Exception as e:
            self._page = None
            logging.error(
                '{e}'.format(
                    e=e
                ),
                exc_info=False
            )  # Set exc_info=True to debug
        return 1

    async def get_page(self):
        """Refresh if necessary and return web page."""
        if self.is_old:
            await self.refresh()
        return self.page


class Confirmator(Gettable, Confirmable):
    """Gettable Confirmable object."""

    instances = {}

    def __init__(self, key, *args, confirm_timedelta=None):
        """Call Confirmable.__init__ passing `confirm_timedelta`."""
        Confirmable.__init__(self, confirm_timedelta)
        Gettable.__init__(self, key=key, *args)


def get_cleaned_text(update, bot=None, replace=None, strip='/ @'):
    """Clean `update`['text'] and return it.

    Strip `bot`.name and items to be `replace`d from the beginning of text.
    Strip `strip` characters from both ends.
    """
    if replace is None:
        replace = []
    if bot is not None:
        replace.append(
            '@{.name}'.format(
                bot
            )
        )
    text = update['text'].strip(strip)
    # Replace longer strings first
    for s in sorted(replace, key=len, reverse=True):
        while s and text.lower().startswith(s.lower()):
            text = text[len(s):]
    return text.strip(strip)


def get_user(record, link_profile=True):
    """Get an HTML Telegram tag for user `record`."""
    if not record:
        return
    from_ = {key: val for key, val in record.items()}
    result = '{name}'
    if 'telegram_id' in from_:
        from_['id'] = from_['telegram_id']
    if (
        'id' in from_
        and from_['id'] is not None
        and link_profile
    ):
        result = f"""<a href="tg://user?id={from_['id']}">{{name}}</a>"""
    if 'username' in from_ and from_['username']:
        result = result.format(
            name=from_['username']
        )
    elif (
        'first_name' in from_
        and from_['first_name']
        and 'last_name' in from_
        and from_['last_name']
    ):
        result = result.format(
            name=f"{from_['first_name']} {from_['last_name']}"
        )
    elif 'first_name' in from_ and from_['first_name']:
        result = result.format(
            name=from_['first_name']
        )
    elif 'last_name' in from_ and from_['last_name']:
        result = result.format(
            name=from_['last_name']
        )
    else:
        result = result.format(
            name="Utente anonimo"
        )
    return result


def datetime_from_utc_to_local(utc_datetime):
    """Convert `utc_datetime` to local datetime."""
    now_timestamp = time.time()
    offset = (
        datetime.datetime.fromtimestamp(now_timestamp)
        - datetime.datetime.utcfromtimestamp(now_timestamp)
    )
    return utc_datetime + offset


# TIME_SYMBOLS from more specific to less specific (avoid false positives!)
TIME_SYMBOLS = MyOD()
TIME_SYMBOLS["'"] = 'minutes'
TIME_SYMBOLS["settimana"] = 'weeks'
TIME_SYMBOLS["settimane"] = 'weeks'
TIME_SYMBOLS["weeks"] = 'weeks'
TIME_SYMBOLS["week"] = 'weeks'
TIME_SYMBOLS["giorno"] = 'days'
TIME_SYMBOLS["giorni"] = 'days'
TIME_SYMBOLS["secondi"] = 'seconds'
TIME_SYMBOLS["seconds"] = 'seconds'
TIME_SYMBOLS["secondo"] = 'seconds'
TIME_SYMBOLS["minuti"] = 'minutes'
TIME_SYMBOLS["minuto"] = 'minutes'
TIME_SYMBOLS["minute"] = 'minutes'
TIME_SYMBOLS["minutes"] = 'minutes'
TIME_SYMBOLS["day"] = 'days'
TIME_SYMBOLS["days"] = 'days'
TIME_SYMBOLS["ore"] = 'hours'
TIME_SYMBOLS["ora"] = 'hours'
TIME_SYMBOLS["sec"] = 'seconds'
TIME_SYMBOLS["min"] = 'minutes'
TIME_SYMBOLS["m"] = 'minutes'
TIME_SYMBOLS["h"] = 'hours'
TIME_SYMBOLS["d"] = 'days'
TIME_SYMBOLS["s"] = 'seconds'


def _interval_parser(text, result):
    text = text.lower()
    succeeded = False
    if result is None:
        result = []
    if len(result) == 0 or result[-1]['ok']:
        text_part = ''
        _text = text  # I need to iterate through _text modifying text
        for char in _text:
            if not char.isnumeric():
                break
            else:
                text_part += char
                text = text[1:]
        if text_part.isnumeric():
            result.append(
                dict(
                    unit=None,
                    value=int(text_part),
                    ok=False
                )
            )
            succeeded = True, True
            if text:
                dummy, result = _interval_parser(text, result)
    elif len(result) > 0 and not result[-1]['ok']:
        text_part = ''
        _text = text  # I need to iterate through _text modifying text
        for char in _text:
            if char.isnumeric():
                break
            else:
                text_part += char
                text = text[1:]
        for time_symbol, unit in TIME_SYMBOLS.items():
            if time_symbol in text_part:
                result[-1]['unit'] = unit
                result[-1]['ok'] = True
                succeeded = True, True
                break
        else:
            result.pop()
        if text:
            dummy, result = _interval_parser(text, result)
    return succeeded, result


def _date_parser(text, result):
    succeeded = False
    if 3 <= len(text) <= 10 and text.count('/') >= 1:
        if 3 <= len(text) <= 5 and text.count('/') == 1:
            text += '/{:%y}'.format(datetime.datetime.now())
        if 6 <= len(text) <= 10 and text.count('/') == 2:
            day, month, year = [
                int(n) for n in [
                    ''.join(char)
                    for char in text.split('/')
                    if char.isnumeric()
                ]
            ]
            if year < 100:
                year += 2000
            if result is None:
                result = []
            result += [
                dict(
                    unit='day',
                    value=day,
                    ok=True
                ),
                dict(
                    unit='month',
                    value=month,
                    ok=True
                ),
                dict(
                    unit='year',
                    value=year,
                    ok=True
                )
            ]
            succeeded = True, True
    return succeeded, result


def _time_parser(text, result):
    succeeded = False
    if (1 <= len(text) <= 8) and any(char.isnumeric() for char in text):
        text = ''.join(
            ':' if char == '.' else char
            for char in text
            if char.isnumeric() or char in (':', '.')
        )
        if len(text) <= 2:
            text = '{:02d}:00:00'.format(int(text))
        elif len(text) == 4 and ':' not in text:
            text = '{:02d}:{:02d}:00'.format(
                *[int(x) for x in (text[:2], text[2:])]
            )
        elif text.count(':') == 1:
            text = '{:02d}:{:02d}:00'.format(
                *[int(x) for x in text.split(':')]
            )
        if text.count(':') == 2:
            hour, minute, second = (int(x) for x in text.split(':'))
            if (
                0 <= hour <= 24
                and 0 <= minute <= 60
                and 0 <= second <= 60
            ):
                if result is None:
                    result = []
                result += [
                    dict(
                        unit='hour',
                        value=hour,
                        ok=True
                    ),
                    dict(
                        unit='minute',
                        value=minute,
                        ok=True
                    ),
                    dict(
                        unit='second',
                        value=second,
                        ok=True
                    )
                ]
                succeeded = True
    return succeeded, result


WEEKDAY_NAMES_ITA = ["Lunedì", "Martedì", "Mercoledì", "Giovedì",
                     "Venerdì", "Sabato", "Domenica"]
WEEKDAY_NAMES_ENG = ["Monday", "Tuesday", "Wednesday", "Thursday",
                     "Friday", "Saturday", "Sunday"]


def _period_parser(text, result):
    if text.title() in WEEKDAY_NAMES_ITA + WEEKDAY_NAMES_ENG:
        day_code = (WEEKDAY_NAMES_ITA + WEEKDAY_NAMES_ENG).index(text.title())
        if day_code > 6:
            day_code -= 7
        today = datetime.date.today()
        days = 1
        while (today + datetime.timedelta(days=days)).weekday() != day_code:
            days += 1
        if result is None:
            result = []
        result.append(
            dict(
                unit='days',
                value=days,
                ok=True,
                weekly=True
            )
        )
        succeeded = True
    else:
        succeeded, result = _interval_parser(text, result)
    return succeeded, result


TIME_WORDS = {
    'tra': dict(
        parser=_interval_parser,
        recurring=False,
        type_='delta'
    ),
    'in': dict(
        parser=_interval_parser,
        recurring=False,
        type_='delta'
    ),
    'at': dict(
        parser=_time_parser,
        recurring=False,
        type_='set'
    ),
    'on': dict(
        parser=_date_parser,
        recurring=False,
        type_='set'
    ),
    'alle': dict(
        parser=_time_parser,
        recurring=False,
        type_='set'
    ),
    'il': dict(
        parser=_date_parser,
        recurring=False,
        type_='set'
    ),
    'every': dict(
        parser=_period_parser,
        recurring=True,
        type_='delta'
    ),
    'ogni': dict(
        parser=_period_parser,
        recurring=True,
        type_='delta'
    ),
}


def parse_datetime_interval_string(text):
    """Parse `text` and return text, datetime and timedelta."""
    parsers = []
    result_text, result_datetime, result_timedelta = [], None, None
    is_quoted_text = False
    # Replace multiple spaces with single space character
    text = re.sub(r'\s\s+', ' ', text)
    for word in text.split(' '):
        if word.count('"') % 2:
            is_quoted_text = not is_quoted_text
        if is_quoted_text or '"' in word:
            result_text.append(
                word.replace('"', '') if 'href=' not in word else word
            )
            continue
        result_text.append(word)
        word = word.lower()
        succeeded = False
        if len(parsers) > 0:
            succeeded, result = parsers[-1]['parser'](
                word,
                parsers[-1]['result']
            )
            if succeeded:
                parsers[-1]['result'] = result
        if not succeeded and word in TIME_WORDS:
            parsers.append(
                dict(
                    result=None,
                    parser=TIME_WORDS[word]['parser'],
                    recurring=TIME_WORDS[word]['recurring'],
                    type_=TIME_WORDS[word]['type_']
                )
            )
        if succeeded:
            result_text.pop()
            if len(result_text) > 0 and result_text[-1].lower() in TIME_WORDS:
                result_text.pop()
    result_text = escape_html_chars(
        ' '.join(result_text)
    )
    parsers = list(
        filter(
            lambda x: 'result' in x and x['result'],
            parsers
        )
    )
    recurring_event = False
    weekly = False
    _timedelta = datetime.timedelta()
    _datetime = None
    _now = datetime.datetime.now()
    for parser in parsers:
        if parser['recurring']:
            recurring_event = True
        type_ = parser['type_']
        for result in parser['result']:
            if not isinstance(result, dict) or not result['ok']:
                continue
            if recurring_event and 'weekly' in result and result['weekly']:
                weekly = True
            if type_ == 'set':
                if _datetime is None:
                    _datetime = _now
                _datetime = _datetime.replace(
                    **{
                        result['unit']: result['value']
                    }
                )
            elif type_ == 'delta':
                _timedelta += datetime.timedelta(
                    **{
                        result['unit']: result['value']
                    }
                )
    if _datetime:
        result_datetime = _datetime
    if _timedelta:
        if result_datetime is None:
            result_datetime = _now
        if recurring_event:
            result_timedelta = _timedelta
            if weekly:
                result_timedelta = datetime.timedelta(days=7)
        else:
            result_datetime += _timedelta
    while result_datetime and result_datetime < datetime.datetime.now():
        result_datetime += (
            result_timedelta
            if result_timedelta
            else datetime.timedelta(days=1)
        )
    return result_text, result_datetime, result_timedelta


DAY_GAPS = {
    -1: 'ieri',
    -2: 'avantieri',
    0: 'oggi',
    1: 'domani',
    2: 'dopodomani'
}

MONTH_NAMES_ITA = MyOD()
MONTH_NAMES_ITA[1] = "gennaio"
MONTH_NAMES_ITA[2] = "febbraio"
MONTH_NAMES_ITA[3] = "marzo"
MONTH_NAMES_ITA[4] = "aprile"
MONTH_NAMES_ITA[5] = "maggio"
MONTH_NAMES_ITA[6] = "giugno"
MONTH_NAMES_ITA[7] = "luglio"
MONTH_NAMES_ITA[8] = "agosto"
MONTH_NAMES_ITA[9] = "settembre"
MONTH_NAMES_ITA[10] = "ottobre"
MONTH_NAMES_ITA[11] = "novembre"
MONTH_NAMES_ITA[12] = "dicembre"


def beautytd(td):
    """Format properly timedeltas."""
    result = ''
    if type(td) is int:
        td = datetime.timedelta(seconds=td)
    assert isinstance(
        td,
        datetime.timedelta
    ), "td must be a datetime.timedelta object!"
    mtd = datetime.timedelta
    if td < mtd(minutes=1):
        result = "{:.0f} secondi".format(
            td.total_seconds()
        )
    elif td < mtd(minutes=60):
        result = "{:.0f} min{}".format(
            td.total_seconds()//60,
            (
                " {:.0f} s".format(
                    td.total_seconds() % 60
                )
            ) if td.total_seconds() % 60 else ''
        )
    elif td < mtd(days=1):
        result = "{:.0f} h{}".format(
            td.total_seconds()//3600,
            (
                " {:.0f} min".format(
                    (td.total_seconds() % 3600) // 60
                )
            ) if td.total_seconds() % 3600 else ''
        )
    elif td < mtd(days=30):
        result = "{} giorni{}".format(
            td.days,
            (
                " {:.0f} h".format(
                    td.total_seconds() % (3600*24) // 3600
                )
            ) if td.total_seconds() % (3600*24) else ''
        )
    return result


def beautydt(dt):
    """Format a datetime in a smart way."""
    if type(dt) is str:
        dt = str_to_datetime(dt)
    assert isinstance(
        dt,
        datetime.datetime
    ), "dt must be a datetime.datetime object!"
    now = datetime.datetime.now()
    gap = dt - now
    gap_days = (dt.date() - now.date()).days
    result = "alle {dt:%H:%M}".format(
        dt=dt
    )
    if abs(gap) < datetime.timedelta(minutes=30):
        result += ":{dt:%S}".format(dt=dt)
    if -2 <= gap_days <= 2:
        result += " di {dg}".format(
            dg=DAY_GAPS[gap_days]
        )
    elif gap.days not in (-1, 0):
        result += " del {d}{m}".format(
            d=dt.day,
            m=(
                "" if now.year == dt.year and now.month == dt.month
                else " {m}{y}".format(
                    m=MONTH_NAMES_ITA[dt.month].title(),
                    y="" if now.year == dt.year
                    else " {}".format(dt.year)
                )
            )
        )
    return result


HTML_SYMBOLS = MyOD()
HTML_SYMBOLS["&"] = "&amp;"
HTML_SYMBOLS["<"] = "&lt;"
HTML_SYMBOLS[">"] = "&gt;"
HTML_SYMBOLS["\""] = "&quot;"
HTML_SYMBOLS["&lt;b&gt;"] = "<b>"
HTML_SYMBOLS["&lt;/b&gt;"] = "</b>"
HTML_SYMBOLS["&lt;i&gt;"] = "<i>"
HTML_SYMBOLS["&lt;/i&gt;"] = "</i>"
HTML_SYMBOLS["&lt;code&gt;"] = "<code>"
HTML_SYMBOLS["&lt;/code&gt;"] = "</code>"
HTML_SYMBOLS["&lt;pre&gt;"] = "<pre>"
HTML_SYMBOLS["&lt;/pre&gt;"] = "</pre>"
HTML_SYMBOLS["&lt;a href=&quot;"] = "<a href=\""
HTML_SYMBOLS["&quot;&gt;"] = "\">"
HTML_SYMBOLS["&lt;/a&gt;"] = "</a>"

HTML_TAGS = [
    None, "<b>", "</b>",
    None, "<i>", "</i>",
    None, "<code>", "</code>",
    None, "<pre>", "</pre>",
    None, "<a href=\"", "\">", "</a>",
    None
]


def remove_html_tags(text):
    """Remove HTML tags from `text`."""
    for tag in HTML_TAGS:
        if tag is None:
            continue
        text = text.replace(tag, '')
    return text


def escape_html_chars(text):
    """Escape HTML chars if not part of a tag."""
    for s, r in HTML_SYMBOLS.items():
        text = text.replace(s, r)
    copy = text
    expected_tag = None
    while copy:
        min_ = min(
            (
                dict(
                    position=copy.find(tag) if tag in copy else len(copy),
                    tag=tag
                )
                for tag in HTML_TAGS
                if tag
            ),
            key=lambda x: x['position'],
            default=0
        )
        if min_['position'] == len(copy):
            break
        if expected_tag and min_['tag'] != expected_tag:
            return text.replace('<', '_').replace('>', '_')
        expected_tag = HTML_TAGS[HTML_TAGS.index(min_['tag'])+1]
        copy = extract(copy, min_['tag'])
    return text


def accents_to_jolly(text, lower=True):
    """Replace letters with Italian accents with SQL jolly character."""
    to_be_replaced = ('à', 'è', 'é', 'ì', 'ò', 'ù')
    if lower:
        text = text.lower()
    else:
        to_be_replaced += tuple(s.upper() for s in to_be_replaced)
    for s in to_be_replaced:
        text = text.replace(s, '_')
    return text.replace("'", "''")


def get_secure_key(allowed_chars=None, length=6):
    """Get a randomly-generate secure key.

    You can specify a set of `allowed_chars` and a `length`.
    """
    if allowed_chars is None:
        allowed_chars = string.ascii_uppercase + string.digits
    return ''.join(
        random.SystemRandom().choice(
            allowed_chars
        )
        for _ in range(length)
    )


def round_to_minute(datetime_):
    """Round `datetime_` to closest minute."""
    return (
        datetime_ + datetime.timedelta(seconds=30)
    ).replace(second=0, microsecond=0)


def get_line_by_content(text, key):
    """Get line of `text` containing `key`."""
    for line in text.split('\n'):
        if key in line:
            return line
    return


def str_to_int(string_):
    """Cast str to int, ignoring non-numeric characters."""
    string_ = ''.join(
        char
        for char in string_
        if char.isnumeric()
    )
    if len(string_) == 0:
        string_ = '0'
    return int(string_)


def starting_with_or_similar_to(a, b):
    """Return similarity between two strings.

    Least similar equals 0, most similar evaluates 1.
    If similarity is less than 0.75, return 1 if one string starts with
        the other and return 0.5 if one string is contained in the other.
    """
    a = a.lower()
    b = b.lower()
    similarity = SequenceMatcher(None, a, b).ratio()
    if similarity < 0.75:
        if b.startswith(a) or a.startswith(b):
            return 1
        if b in a or a in b:
            return 0.5
    return similarity


def pick_most_similar_from_list(list_, item):
    """Return element from `list_` which is most similar to `item`.

    Similarity is evaluated using `starting_with_or_similar_to`.
    """
    return max(
        list_,
        key=lambda element: starting_with_or_similar_to(
            item,
            element
        )
    )


def run_aiohttp_server(app, *args, **kwargs):
    """Run an aiohttp web app, with its positional and keyword arguments.

    Useful to run apps in dedicated threads.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    web.run_app(app, *args, **kwargs)


def custom_join(_list, joiner, final=None):
    """Join elements of `_list` using `joiner` (`final` as last joiner)."""
    _list = list(map(str, _list))
    if final is None:
        final = joiner
    if len(_list) == 0:
        return ''
    if len(_list) == 1:
        return _list[0]
    if len(_list) == 2:
        return final.join(_list)
    return joiner.join(_list[:-1]) + final + _list[-1]


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


# noinspection PyUnusedLocal
async def dummy_coroutine(*args, **kwargs):
    """Accept everything as argument and do nothing."""
    return


async def send_csv_file(bot, chat_id: int, query: str, caption: str = None,
                        file_name: str = 'File.csv', language: str = None,
                        user_record=None, update=None):
    """Run a query on `bot` database and send result as CSV file to `chat_id`.

    Optional parameters `caption` and `file_name` may be passed to this
        function.
    """
    if update is None:
        update = dict()
    if language is None:
        language = bot.get_language(update=update,
                                    user_record=user_record)
    try:
        with bot.db as db:
            record = db.query(
                query
            )
        header_line = []
        body_lines = []
        for row in record:
            if not header_line:
                header_line.append(get_csv_string(row.keys()))
            body_lines.append(get_csv_string(row.values()))
        text = '\n'.join(header_line + body_lines)
    except Exception as e:
        text = "{message}\n{e}".format(
            message=bot.get_message('admin', 'query_button', 'error',
                                    language=language),
            e=e
        )
    for x, y in {'&lt;': '<', '\n': '\r\n'}.items():
        text = text.replace(x, y)
    if len(text) == 0:
        text = bot.get_message('admin', 'query_button', 'empty_file',
                               language=language)
    with io.BytesIO(text.encode('utf-8')) as f:
        f.name = file_name
        return await bot.send_document(
            chat_id=chat_id,
            document=f,
            caption=caption
        )


async def send_part_of_text_file(bot, chat_id, file_path, caption=None,
                                 file_name='File.txt', user_record=None,
                                 update=None,
                                 reversed_=True,
                                 limit=None):
    """Send `lines` lines of text file via `bot` in `chat_id`.

    If `reversed`, read the file from last line.
    TODO: do not load whole file in RAM. At the moment this is the easiest
        way to allow `reversed` files, but it is inefficient and requires a lot
        of memory.
    """
    if update is None:
        update = dict()
    try:
        with open(file_path, 'r') as log_file:
            lines = log_file.readlines()
            if reversed_:
                lines = lines[::-1]
            if limit:
                lines = lines[:limit]
            with io.BytesIO(
                ''.join(lines).encode('utf-8')
            ) as document:
                document.name = file_name
                return await bot.send_document(
                    chat_id=chat_id,
                    document=document,
                    caption=caption
                )
    except Exception as e:
        return e


def recursive_dictionary_update(one: dict, other: dict) -> dict:
    """Extension of `dict.update()` method.

    For each key of `other`, if key is not in `one` or the values differ, set
        `one[key]` to `other[key]`. If the value is a dict, apply this function
        recursively.
    """
    for key, val in other.items():
        if key not in one:
            one[key] = val
        elif one[key] != val:
            if isinstance(val, dict):
                one[key] = recursive_dictionary_update(one[key], val)
            else:
                one[key] = val
    return one


async def aio_subprocess_shell(command: str) -> Tuple[str, str]:
    """Run `command` in a subprocess shell.

    Await for the subprocess to end and return standard error and output.
    On error, log errors.
    """
    stdout, stderr = None, None
    try:
        _subprocess = await asyncio.create_subprocess_shell(
            command
        )
        stdout, stderr = await _subprocess.communicate()
        if stdout:
            stdout = stdout.decode().strip()
        if stderr:
            stderr = stderr.decode().strip()
    except Exception as e:
        logging.error(
            "Exception {e}:\n{o}\n{er}".format(
                e=e,
                o=(stdout.decode().strip() if stdout else ''),
                er=(stderr.decode().strip() if stderr else '')
            )
        )
    return stdout, stderr
