"""Useful functions to patch third part libraries until they are fixed."""

import aiohttp
from urllib.parse import quote


def hacked_content_disposition_header(disptype, quote_fields=True, **params):
    """Prevent aiohttp from encoding file names as URLs.

    Thanks @Nickoala (Nick Lee) for this hack from his archived `telepot` repo.
    See https://github.com/nickoala/telepot/blob/master/telepot/aio/hack.py
        for details.
    """
    if not disptype or not (aiohttp.helpers.TOKEN > set(disptype)):
        raise ValueError('bad content disposition type {!r}'
                         ''.format(disptype))

    value = disptype
    if params:
        lparams = []
        for key, val in params.items():
            if not key or not (aiohttp.helpers.TOKEN > set(key)):
                raise ValueError('bad content disposition parameter'
                                 ' {!r}={!r}'.format(key, val))

            if key == 'filename':
                qval = val
            else:
                qval = quote(val, '') if quote_fields else val

            lparams.append((key, '"%s"' % qval))

        sparams = '; '.join('='.join(pair) for pair in lparams)
        value = '; '.join((value, sparams))
    return value
