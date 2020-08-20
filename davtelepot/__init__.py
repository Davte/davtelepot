"""Information about this package.

See `bot.py` for information about Bot class.
    ```python3.5+
    from davtelepot.bot import Bot
    help(Bot)
    ```
"""

__author__ = "Davide Testa"
__email__ = "davide@davte.it"
__credits__ = ["Marco Origlia", "Nick Lee @Nickoala"]
__license__ = "GNU General Public License v3.0"
__version__ = "2.6.12"
__maintainer__ = "Davide Testa"
__contact__ = "t.me/davte"

from . import (administration_tools, authorization, bot, helper, languages,
               suggestions, useful_tools, utilities)

__all__ = [administration_tools, authorization, bot, helper, languages,
           suggestions, useful_tools, utilities]
