# Standard library modules
import aiohttp
import asyncio
import collections
import csv
import datetime
import io
import json
import logging
import os
import random
import string
import sys
import time

# Third party modules
from bs4 import BeautifulSoup
import telepot, telepot.aio

def sumif(it, cond):
    return sum(filter(cond, it))

def markdown_check(text, symbols):
    #Dato un testo text e una lista symbols di simboli, restituisce vero solo se TUTTI i simboli della lista sono presenti in numero pari di volte nel testo.
    for s in symbols:
        if (len(text.replace(s,"")) - len(text))%2 != 0:
            return False
    return True

def shorten_text(text, limit, symbol="[...]"):
    """Return a given text truncated at limit if longer than limit. On truncation, add symbol.
    """
    assert type(text) is str and type(symbol) is str and type(limit) is int
    if len(text) <= limit:
        return text
    return text[:limit-len(symbol)] + symbol

def extract(text, starter=None, ender=None):
    """Return string in text between starter and ender.
    If starter is None, truncates at ender.
    """
    if starter and starter in text:
        text = text.partition(starter)[2]
    if ender:
        return text.partition(ender)[0]
    return text

def mkbtn(x, y):
    if len(y) > 60:#If callback_data exceeeds 60 characters (max is 64), it gets trunkated at the last comma
        y = y[:61]
        y = y[:- y[::-1].find(",")-1]
    return {'text': x, 'callback_data': y}

def make_lines_of_buttons(btns, row_len=1):
    return [btns[i:i + row_len] for i in range(0, len(btns), row_len)]

def make_inline_keyboard(btns, row_len=1):
    return dict(inline_keyboard=make_lines_of_buttons(btns, row_len))

async def async_get(url, mode='json', **kwargs):
    if 'mode' in kwargs:
        mode = kwargs['mode']
        del kwargs['mode']
    return await async_request(url, type='get', mode=mode, **kwargs)

async def async_post(url, mode='html', **kwargs):
    return await async_request(url, type='post', mode=mode, **kwargs)

async def async_request(url, type='get', mode='json', **kwargs):
    try:
        async with aiohttp.ClientSession() as s:
                async with (s.get(url, timeout=30) if type=='get' else s.post(url, timeout=30, data=kwargs)) as r:
                    result = await r.read()
    except Exception as e:
        logging.error('Error making async request to {}:\n{}'.format(url, e), exc_info=False) # Set exc_info=True to debug
        return e
    if mode=='json':
        if not result:
            return {}
        return json.loads(result.decode('utf-8'))
    if mode=='html':
        return BeautifulSoup(result.decode('utf-8'), "html.parser")
    if mode=='string':
        return result.decode('utf-8')
    return result

def json_read(file, default={}):
    if not os.path.isfile(file):
        return default
    with open(file, "r", encoding='utf-8') as f:
        return json.load(f)

def json_write(what, file):
    with open(file, "w") as f:
        return json.dump(what, f, indent=4)

def csv_read(file_, default=[]):
    if not os.path.isfile(file_):
        return default
    result = []
    keys = []
    with open(file_, newline='', encoding='utf8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        for row in csv_reader:
            if not keys:
                keys = row
                continue
            item = collections.OrderedDict()
            for key, val in zip(keys, row):
                item[key] = val
            result.append(item)
    return result

def csv_write(info=[], file_='output.csv'):
    assert type(info) is list and len(info)>0, "info must be a non-empty list"
    assert all(isinstance(row, dict) for row in info), "Rows must be dictionaries!"
    with open(file_, 'w', newline='', encoding='utf8') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"')
        csv_writer.writerow(info[0].keys())
        for row in info:
            csv_writer.writerow(row.values())
    return

class MyOD(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._anti_list_casesensitive = None
        self._anti_list_caseinsensitive = None

    @property
    def anti_list_casesensitive(self):
        if not self._anti_list_casesensitive:
            self._anti_list_casesensitive = {self[x]:x for x in self}
        return self._anti_list_casesensitive

    @property
    def anti_list_caseinsensitive(self):
        if not self._anti_list_caseinsensitive:
            self._anti_list_caseinsensitive = {self[x].lower() if type(self[x]) is str else self[x] :x for x in self}
        return self._anti_list_caseinsensitive

    #MyOD[key] = val <-- MyOD.get(key) = val <--> MyOD.get_by_val(val) = key
    def get_by_val(self, val, case_sensitive=True):
        return (self.anti_list_casesensitive if case_sensitive else self.anti_list_caseinsensitive)[val]

    def get_by_key_val(self, key, val, case_sensitive=True, return_value=False):
        for x, y in self.items():
            if (y[key] == val and case_sensitive) or (y[key].lower() == val.lower() and not case_sensitive):
                return y if return_value else x
        return None

def line_drawing_unordered_list(l):
    result = ""
    if l:
        for x in l[:-1]:
            result += "├ {}\n".format(x)
        result += "└ {}".format(l[-1])
    return result

def str_to_datetime(d):
    if isinstance(d, datetime.datetime):
        return d
    return datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S.%f')

def datetime_to_str(d):
    if not isinstance(d, datetime.datetime):
        raise TypeError('Input of datetime_to_str function must be a datetime.datetime object. Output is a str')
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(d)

class MyCounter():
    def __init__(self):
        self.n = 0
        return

    def lvl(self):
        self.n += 1
        return self.n

    def reset(self):
        self.n = 0
        return self.n

def wrapper(func, *args, **kwargs):
    def wrapped(update):
        return func(update, *args, **kwargs)
    return wrapped

async def async_wrapper(func, *args, **kwargs):
    async def wrapped(update):
        return await func(update, *args, **kwargs)
    return wrapped

#Decorator: such decorated functions have effect only if update is forwarded from someone (you can specify *by* whom)
def forwarded(by=None):
    def isforwardedby(update, by):
        if 'forward_from' not in update:
            return False
        if by:
            if update['forward_from']['id']!=by:
                return False
        return True
    def decorator(view_func):
        if asyncio.iscoroutinefunction(view_func):
            async def decorated(update):
                if isforwardedby(update, by):
                    return await view_func(update)
        else:
            def decorated(update):
                if isforwardedby(update, by):
                    return view_func(update)
        return decorated
    return decorator

#Decorator: such decorated functions have effect only if update comes from specific chat.
def chat_selective(chat_id=None):
    def check_function(update, chat_id):
        if 'chat' not in update:
            return False
        if chat_id:
            if update['chat']['id']!=chat_id:
                return False
        return True
    def decorator(view_func):
        if asyncio.iscoroutinefunction(view_func):
            async def decorated(update):
                if check_function(update, chat_id):
                    return await view_func(update)
        else:
            def decorated(update):
                if check_function(update, chat_id):
                    return view_func(update)
        return decorated
    return decorator

async def sleep_until(when):
    if not isinstance(when, datetime.datetime):
        raise TypeError("sleep_until takes a datetime.datetime object as argument!")
    delta = when - datetime.datetime.now()
    if delta.days>=0:
        await asyncio.sleep(max(1, delta.seconds//2))
    return

async def wait_and_do(when, what, *args, **kwargs):
    while when >= datetime.datetime.now():
        await sleep_until(when)
    return await what(*args, **kwargs)

def get_csv_string(l):
    return ','.join(
    str(x) if type(x) is not str
    else '"{}"'.format(x)
    for x in l
    )

def case_accent_insensitive_sql(field):
    """Given a field, return a part of SQL string necessary to perform a case- and accent-insensitive query."""
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

class Gettable():
    """Gettable objects can be retrieved from memory without being duplicated.
    Key is the primary key.
    Use classmethod get to instanciate (or retrieve) Gettable objects.
    Assign SubClass.instances = {} or Gettable.instances will contain SubClass objects.
    """
    instances = {}

    @classmethod
    def get(cls, key, *args, **kwargs):
        if key not in cls.instances:
            cls.instances[key] = cls(key, *args, **kwargs)
        return cls.instances[key]

class Confirmable():
    """Confirmable objects are provided with a confirm instance method.
    It evaluates True if it was called within self._confirm_timedelta, False otherwise.
    When it returns True, timer is reset.
    """
    CONFIRM_TIMEDELTA = datetime.timedelta(seconds=10)

    def __init__(self, confirm_timedelta=None):
        if confirm_timedelta is None:
            confirm_timedelta = self.__class__.CONFIRM_TIMEDELTA
        self.set_confirm_timedelta(confirm_timedelta)
        self._confirm_datetimes = {}

    @property
    def confirm_timedelta(self):
        return self._confirm_timedelta

    def confirm_datetime(self, who='unique'):
        if who not in self._confirm_datetimes:
            self._confirm_datetimes[who] = datetime.datetime.now() - 2*self.confirm_timedelta
        confirm_datetime = self._confirm_datetimes[who]
        return confirm_datetime

    def set_confirm_timedelta(self, confirm_timedelta):
        if type(confirm_timedelta) is int:
            confirm_timedelta = datetime.timedelta(seconds=confirm_timedelta)
        assert isinstance(confirm_timedelta, datetime.timedelta), "confirm_timedelta must be a datetime.timedelta instance!"
        self._confirm_timedelta = confirm_timedelta

    def confirm(self, who='unique'):
        now = datetime.datetime.now()
        if now >= self.confirm_datetime(who) + self.confirm_timedelta:
            self._confirm_datetimes[who] = now
            return False
        self._confirm_datetimes[who] = now - 2*self.confirm_timedelta
        return True

class HasBot():
    """HasBot objects have a class method which sets the class attribute bot (set_bot)\
    and an instance property which returns it (bot).
    """
    bot = None

    @property
    def bot(self):
        return self.__class__.bot

    @property
    def db(self):
        return self.bot.db

    @classmethod
    def set_bot(cls, bot):
        cls.bot = bot

class CachedPage(Gettable):
    """Store a webpage in this object, return cached webpage during CACHE_TIME, otherwise refresh.

    Usage:
    cached_page = CachedPage.get('https://www.google.com', datetime.timedelta(seconds=30), **kwargs)
    page = await cached_page.get_page()

    __init__ arguments
        url: the URL to be cached
        cache_time: timedelta from last_update during which page is not refreshed
        **kwargs will be passed to async_get function
    """
    CACHE_TIME = datetime.timedelta(minutes=5)
    instances = {}

    def __init__(self, url, cache_time=None, **async_get_kwargs):
        self._url = url
        if type(cache_time) is int:
            cache_time = datetime.timedelta(seconds=cache_time)
        if cache_time is None:
            cache_time = self.__class__.CACHE_TIME
        assert type(cache_time) is datetime.timedelta, "Cache time must be a datetime.timedelta object!"
        self._cache_time = cache_time
        self._page = None
        self._last_update = datetime.datetime.now() - self.cache_time
        self._async_get_kwargs = async_get_kwargs

    @property
    def url(self):
        return self._url

    @property
    def cache_time(self):
        return self._cache_time

    @property
    def page(self):
        return self._page

    @property
    def last_update(self):
        return self._last_update

    @property
    def async_get_kwargs(self):
        return self._async_get_kwargs

    @property
    def is_old(self):
        return datetime.datetime.now() > self.last_update + self.cache_time

    async def refresh(self):
        try:
            self._page = await async_get(self.url, **self.async_get_kwargs)
            self._last_update = datetime.datetime.now()
            return 0
        except Exception as e:
            self._page = None
            logging.error(''.format(e), exc_info=True)
            return 1
        return 1

    async def get_page(self):
        if self.is_old:
            await self.refresh()
        return self.page

class Confirmator(Gettable, Confirmable):
    instances = {}
    def __init__(self, key, *args, confirm_timedelta=None):
        Confirmable.__init__(self, confirm_timedelta)

def get_cleaned_text(update, bot=None, replace=[], strip='/ @'):
    if bot is not None:
        replace.append(
            '@{.name}'.format(
                bot
            )
        )
    text = update['text'].strip(strip)
    for s in replace:
        while s and text.lower().startswith(s.lower()):
            text = text[len(s):]
    return text.strip(strip)

def get_user(record):
    if not record:
        return
    from_ = {key: val for key, val in record.items()}
    first_name, last_name, username, id_ = None, None, None, None
    result = ''
    if 'telegram_id' in from_:
        from_['id'] = from_['telegram_id']
    if 'id' in from_:
        result = '<a href="tg://user?id={}">{{name}}</a>'.format(from_['id'])
    if 'username' in from_ and from_['username']:
        result = result.format(
            name=from_['username']
        )
    elif 'first_name' in from_ and from_['first_name'] and 'last_name' in from_ and from_['last_name']:
        result = result.format(
            name='{} {}'.format(
                from_['first_name'],
                from_['last_name']
            )
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
    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
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
    if len(result)==0 or result[-1]['ok']:
        text_part = ''
        _text = text # I need to iterate through _text modifying text
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
    elif len(result)>0 and not result[-1]['ok']:
        text_part = ''
        _text = text # I need to iterate through _text modifying text
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
    if 3 <= len(text) <= 10 and text.count('/')>=1:
        if 3 <= len(text) <= 5 and text.count('/')==1:
            text += '/{:%y}'.format(datetime.datetime.now())
        if 6 <= len(text) <= 10 and text.count('/')==2:
            day, month, year = [
                int(n) for n in [
                    ''.join(char)
                    for char in text.split('/')
                    if char.isnumeric()
                ]
            ]
            if year < 100: year += 2000
            if result is None: result = []
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
        text = text.replace('.', ':')
        if len(text) <= 2:
            text = '{:02d}:00:00'.format(int(text))
        elif len(text) == 4 and ':' not in text:
            text = '{:02d}:{:02d}:00'.format(*[int(x) for x in (text[:2], text[2:])])
        elif text.count(':')==1:
            text = '{:02d}:{:02d}:00'.format(*[int(x) for x in text.split(':')])
        if text.count(':')==2:
            hour, minute, second = (int(x) for x in text.split(':'))
            if (0 <= hour <= 24) and (0 <= minute <= 60) and (0 <= second <= 60):
                if result is None: result = []
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

WEEKDAY_NAMES_ITA = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
WEEKDAY_NAMES_ENG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def _period_parser(text, result):
    succeeded = False
    if text in ('every', 'ogni',):
        succeeded = True
    if text.title() in WEEKDAY_NAMES_ITA + WEEKDAY_NAMES_ENG:
        day_code = (WEEKDAY_NAMES_ITA + WEEKDAY_NAMES_ENG).index(text.title())
        if day_code > 6: day_code -= 7
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
    parsers = []
    result_text, result_datetime, result_timedelta = [], None, None
    is_quoted_text = False
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
            succeeded, result = parsers[-1]['parser'](word, parsers[-1]['result'])
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
            if len(result_text)>0 and result_text[-1].lower() in TIME_WORDS:
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
            if not result['ok']:
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
        if result_datetime is None: result_datetime = _now
        if recurring_event:
            result_timedelta = _timedelta
            if weekly:
                result_timedelta = datetime.timedelta(days=7)
        else:
            result_datetime += _timedelta
    while result_datetime and result_datetime < datetime.datetime.now():
        result_datetime += (result_timedelta if result_timedelta else datetime.timedelta(days=1))
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
    result = ''
    if type(td) is int:
        td = datetime.timedelta(seconds=td)
    assert isinstance(td, datetime.timedelta), "td must be a datetime.timedelta object!"
    mtd = datetime.timedelta
    if td < mtd(minutes=1):
        result = "{:.0f} secondi".format(
            td.total_seconds()
        )
    elif td < mtd(minutes=10):
        result = "{:.0f} min{}".format(
            td.total_seconds()//60,
            (
                " {:.0f} s".format(
                    td.total_seconds()%60
                )
            ) if td.total_seconds()%60 else ''
        )
    elif td < mtd(days=1):
        result = "{:.0f} h{}".format(
            td.total_seconds()//3600,
            (
                " {:.0f} min".format(
                (td.total_seconds()%3600)//60)
            ) if td.total_seconds()%3600 else ''
        )
    elif td < mtd(days=30):
        result = "{} giorni{}".format(
            td.days,
            (
                " {:.0f} h".format(
                    td.total_seconds()%(3600*24)//3600
                )
            ) if td.total_seconds()%(3600*24) else ''
        )
    return result

def beautydt(dt):
    """Format a datetime in a smart way
    """
    if type(dt) is str:
        dt = str_to_datetime(dt)
    assert isinstance(dt, datetime.datetime), "dt must be a datetime.datetime object!"
    now = datetime.datetime.now()
    gap = dt - now
    gap_days = (dt.date() - now.date()).days
    result = "{dt:alle %H:%M}".format(
        dt=dt
    )
    if abs(gap) < datetime.timedelta(minutes=30):
        result += "{dt::%S}".format(dt=dt)
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
    for tag in HTML_TAGS:
        if tag is None:
            continue
        text = text.replace(tag, '')
    return text

def escape_html_chars(text):
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
    to_be_replaced = ('à', 'è', 'é', 'ì', 'ò', 'ù')
    if lower:
        text = text.lower()
    else:
        to_be_replaced += tuple(s.upper() for s in to_be_replaced)
    for s in to_be_replaced:
        text = text.replace(s, '_')
    return text.replace("'", "''")

def get_secure_key(allowed_chars=None, length=6):
    if allowed_chars is None:
        allowed_chars = string.ascii_uppercase + string.digits
    return ''.join(
        random.SystemRandom().choice(
            allowed_chars
        )
        for _ in range(length)
    )

def round_to_minute(datetime_):
    return (
        datetime_ + datetime.timedelta(seconds=30)
    ).replace(second=0, microsecond=0)

def get_line_by_content(text, key):
    for line in text.split('\n'):
        if key in line:
            return line
    return

def str_to_int(string):
    string = ''.join(
        char
        for char in string
        if char.isnumeric()
    )
    if len(string) == 0:
        string = '0'
    return int(string)
