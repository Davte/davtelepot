# davtelepot
This project conveniently mirrors the Telegram bot API with the class `Bot`.

Please note that you need Python3.5+ to run async code.

Check requirements.txt for third party dependencies.

Check out `help(Bot)` for detailed information.

## Project folders

### data folder
* `*.db`: databases used by bots
* `*.log`: log files (store log_file_name and errors_file_name in `data/config.py` module)
* `passwords.py`: contains secret information to be git-ignored (e.g. bot tokens)

```
my_token = 'token_of_bot1'
my_other_token = 'token_of_bot2'
...
```

## Usage
```
import sys
from davtelepot.bot import Bot
from data.passwords import my_token, my_other_token

long_polling_bot = Bot(token=my_token, database_url='my_db')
webhook_bot = Bot(token=my_other_token, hostname='example.com',
                  certificate='path/to/certificate.pem',
                  database_url='my_other_db')

@long_polling_bot.command('/foo')
async def foo_command(bot, update, user_record):
  return "Bar!"

@webhook_bot.command('/bar')
async def bar_command(bot, update, user_record):
  return "Foo!"

exit_state = Bot.run()
sys.exit(exit_state)
```
Check out `help(Bot)` for detailed information.
