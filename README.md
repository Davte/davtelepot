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
from davtelepot import Bot
from data.passwords import my_token, my_other_token

my_bot = Bot.get(token=my_token, db_name='my_db')
my_other_bot = Bot.get(token=my_other_token, db_name='my_other_db')

@my_bot.command('/foo')
async def foo_command(update):
  return "Bar!"

@my_other_bot.command('/bar')
async def bar_command(update):
  return "Foo!"

Bot.run()
```
Check out `help(Bot)` for detailed information.
