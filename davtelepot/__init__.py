"""Information about this package.

See `bot.py` for information about Bot class.
    ```python3.5+
    from davtelepot.bot import Bot
    help(Bot)
    ```

Legacy `custombot.py` is kept for backward compatibility but will finally
    be deprecated.
"""

__author__ = "Davide Testa"
__email__ = "davide@davte.it"
__credits__ = ["Marco Origlia", "Nick Lee @Nickoala"]
__license__ = "GNU General Public License v3.0"
__version__ = "2.4.15"
__maintainer__ = "Davide Testa"
__contact__ = "t.me/davte"

# Legacy module; please use `from davtelepot.bot import Bot` from now on
from .custombot import Bot
from . import administration_tools, authorization, bot, helper, languages, suggestions, utilities

__all__ = [administration_tools, authorization, Bot, bot, helper, languages, suggestions, utilities]
