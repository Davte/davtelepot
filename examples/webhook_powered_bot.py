"""Example showing how to use webhooks with davtelepot."""

# Standard library modules
import logging
import os
import sys

# Third party modules
try:
    from davtelepot.bot import Bot
except ImportError:
    logging.error(
        "Please install davtelepot library.\n"
        "Using a python virtual environment is advised.\n\n"
        "```bash\n"
        "pip -m venv env\n"
        "env/bin/pip install davtelepot\n"
        "env/bin/python davtelepot/examples/a_simple_bot.py"
        "```"
    )
    sys.exit(1)

# Project modules
from a_simple_bot import initialize_bot

# Get path of current script
os.path.dirname(os.path.abspath(__file__))


def _main():
    # Import or prompt user for bot token
    try:
        from secrets import webhook_bot_token
    except ImportError:
        webhook_bot_token = input("Enter bot token:\t\t")
        with open(
            f'{path}/secrets.py',
            'a'  # Append to file, create it if it does not exist
        ) as secrets_file:
            secrets_file.write(f'webhook_bot_token = "{webhook_bot_token}"\n')
    try:
        from secrets import hostname
    except ImportError:
        hostname = input("Enter host name:\t\t")
        with open(
            f'{path}/secrets.py',
            'a'  # Append to file, create it if it does not exist
        ) as secrets_file:
            secrets_file.write(f'hostname = "{hostname}"\n')
    try:
        from secrets import certificate
    except ImportError:
        certificate = input("Enter ssl certificate:\t\t")
        with open(
            f'{path}/secrets.py',
            'a'  # Append to file, create it if it does not exist
        ) as secrets_file:
            secrets_file.write(f'certificate = "{certificate}"\n')
    try:
        from secrets import local_host
    except ImportError:
        local_host = input("Enter local host:\t\t")
        with open(
            f'{path}/secrets.py',
            'a'  # Append to file, create it if it does not exist
        ) as secrets_file:
            secrets_file.write(f'local_host = "{local_host}"\n')
    try:
        from secrets import port
    except ImportError:
        port = input("Enter local port:\t\t")
        with open(
            f'{path}/secrets.py',
            'a'  # Append to file, create it if it does not exist
        ) as secrets_file:
            secrets_file.write(f'port = "{port}"\n')

    # Set logging preferences
    log_formatter = logging.Formatter(
        "%(asctime)s [%(module)-15s %(levelname)-8s]     %(message)s",
        style='%'
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(log_formatter)
    consoleHandler.setLevel(logging.DEBUG)
    root_logger.addHandler(consoleHandler)

    # Instantiate, initialize and make `webhook_bot` run.
    webhook_bot = Bot(
        token=webhook_bot_token,
        database_url=f"{path}/webhook_bot.db",
        hostname=hostname,
        certificate=certificate
    )
    initialize_bot(webhook_bot)
    logging.info("Send a KeyboardInterrupt (ctrl+C) to stop bots.")
    Bot.run(
        local_host=local_host,
        port=port
    )


if __name__ == '__main__':
    _main()
