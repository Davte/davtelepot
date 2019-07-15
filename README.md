# davtelepot
This project conveniently mirrors the Telegram bot API with the class `Bot`.

Please note that Python3.5+ is needed to run async code.

Check requirements.txt for third party dependencies.

Check out `help(Bot)` for detailed information.

## Project folders

### `davtelepot/data` folder
* `config.py` contains configuration settings (e.g. certificate path, local_host, port etc.)
* `passwords.py` contains secret information to be git-ignored (e.g. bot tokens)
* `*.db` files are SQLite databases used by bots
* `*.log`: log files (store log_file_name and errors_file_name in `data/config.py` module)

### `examples` folder
This folder contains full-commented and ready-to-run examples for simple davtelepot.bot Telegram bots.

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

exit_state = Bot.run(
    local_host='127.0.0.5',
    port=8552
)
sys.exit(exit_state)
```
Check out `help(Bot)` for detailed information.

## Webhook additional information
To run a bot in webhook modality, you have to provide a `hostname` and `certificate` at bot instantiation and a `local_host` and `port` when calling `Bot.run` method.
* Telegram will send POST requests at `https://{hostname}/webhook/{tokens}/` using `certificate` for encryption
* `aiohttp.web.Application` server will listen on `http://{local_host}:{port}` for updates

It is therefore required a reverse proxy passing incoming requests to local_host.

**Example of nginx reverse proxy serving this purpose**
```nginx
server {
  listen 8553 ssl;
  listen [::]:8553 ssl;

  server_name example.com www.example.com;

  location /telegram/ {
     proxy_pass http://127.0.0.5:8552/;
  }

  ssl_certificate /path/to/fullchain.pem;
  ssl_certificate_key /path/to/privkey.pem;
}

```

**Example of python configuration file in this situation**
```python
# File data/config.py, gitignored and imported in main script
hostname = "https://www.example.com:8553/telegram"
certificate = "/path/to/fullchain.pem"
local_host = "127.0.0.5"
port = 8552

# Main script
from data.config import hostname, certificate, local_host, port
from data.passwords import bot_token
from davtelepot.bot import Bot

my_bot = Bot(
  token=bot_token,
  hostname=hostname,
  certificate=certificate
)

# ...

Bot.run(
  local_host=local_host,
  port=port
)
```
