import argparse
import asyncio
import logging
import os.path
import sys
from typing import Any, Dict, Union

import davtelepot.authorization as authorization
import davtelepot.administration_tools as administration_tools
import davtelepot.helper as helper
from davtelepot.bot import Bot
from davtelepot.utilities import (get_cleaned_text, get_secure_key,
                                  get_user, join_path, json_read, json_write,
                                  line_drawing_unordered_list)


def dir_path(path):
    if os.path.isdir(path) and os.access(path, os.W_OK):
        return path
    else:
        raise argparse.ArgumentTypeError(f"`{path}` is not a valid path")


def get_cli_arguments() -> Dict[str, Any]:
    default_path = join_path(os.path.dirname(__file__), 'data')
    cli_parser = argparse.ArgumentParser(
        description='Run a davtelepot-powered Telegram bot from command line.',
        allow_abbrev=False,
    )
    cli_parser.add_argument('-a', '--action', type=str,
                            default='run',
                            required=False,
                            help='Action to perform (currently supported: run).')
    cli_parser.add_argument('-p', '--path', type=dir_path,
                            default=default_path,
                            required=False,
                            help='Folder to store secrets, data and log files.')
    cli_parser.add_argument('-l', '--log_file', type=argparse.FileType('a'),
                            default=None,
                            required=False,
                            help='File path to store full log')
    cli_parser.add_argument('-e', '--error_log_file', type=argparse.FileType('a'),
                            default=None,
                            required=False,
                            help='File path to store only error log')
    cli_parser.add_argument('-t', '--token', type=str,
                            required=False,
                            help='Telegram bot token (you may get one from t.me/botfather)')
    cli_parsed_arguments = vars(cli_parser.parse_args())
    for key in cli_parsed_arguments:
        if key.endswith('_file') and cli_parsed_arguments[key]:
            cli_parsed_arguments[key] = cli_parsed_arguments[key].name
    for key, default in {'error_log_file': "davtelepot.errors",
                         'log_file': "davtelepot.log"}.items():
        if cli_parsed_arguments[key] is None:
            cli_parsed_arguments[key] = join_path(cli_parsed_arguments['path'], default)
    return cli_parsed_arguments


def set_loggers(log_file: str = 'davtelepot.log',
                error_log_file: str = 'davtelepot.errors'):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(module)-10s %(levelname)-8s]     %(message)s",
        style='%'
    )

    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    file_handler = logging.FileHandler(error_log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.ERROR)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)


async def elevate_to_admin(bot: Bot, update: dict, user_record: dict,
                           secret: str) -> Union[str, None]:
    text = get_cleaned_text(update=update, bot=bot,
                            replace=['00elevate_', 'elevate '])
    if text == secret:
        bot.db['users'].upsert(dict(id=user_record['id'], privileges=1), ['id'])
        return "👑 You have been granted full powers! 👑"
    else:
        print(f"The secret entered (`{text}`) is wrong. Enter `{secret}` instead.")


def allow_elevation_to_admin(telegram_bot: Bot) -> None:
    secret = get_secure_key(length=15)

    @telegram_bot.additional_task('BEFORE')
    async def print_secret():
        await telegram_bot.get_me()
        logging.info(f"To get administration privileges, enter code {secret} "
                     f"or click here: https://t.me/{telegram_bot.name}?start=00elevate_{secret}")

    @telegram_bot.command(command='/elevate', aliases=['00elevate_'], show_in_keyboard=False,
                          authorization_level='anybody')
    async def _elevate_to_admin(bot, update, user_record):
        return await elevate_to_admin(bot=bot, update=update,
                                      user_record=user_record,
                                      secret=secret)
    return


def send_single_message(telegram_bot: Bot):
    records = []
    text, last_text = '', ''
    offset = 0
    max_shown = 3
    while True:
        if text == '+' and len(records) > max_shown:
            offset += 1
        elif offset > 0 and text == '-':
            offset -= 1
        else:
            offset = 0
        if text in ('+', '-'):
            text = last_text
        condition = (f"WHERE username LIKE '%{text}%' "
                     f"OR first_name LIKE '%{text}%' "
                     f"OR last_name LIKE '%{text}%' ")
        records = list(telegram_bot.db.query("SELECT username, first_name, "
                                             "last_name, telegram_id "
                                             "FROM users "
                                             f"{condition} "
                                             f"LIMIT {max_shown+1} "
                                             f"OFFSET {offset*max_shown} "))
        if len(records) == 1 and offset == 0:
            break
        last_text = text
        print("=== Users ===",
              line_drawing_unordered_list(
                  list(map(lambda x: get_user(x, False),
                           records[:max_shown]))
                  + (['...'] if len(records) >= max_shown else [])
              ),
              sep='\n')
        text = input("Select a recipient: write part of their name.\t\t")
    while True:
        text = input(f"Write a message for {get_user(records[0], False)}\t\t")
        if input("Should I send it? Y to send, anything else cancel\t\t").lower() == "y":
            break

    async def send_and_print_message():
        sent_message = await telegram_bot.send_one_message(chat_id=records[0]['telegram_id'], text=text)
        print(sent_message)

    asyncio.run(send_and_print_message())
    return


def run_from_command_line():
    arguments = get_cli_arguments()
    stored_arguments_file = os.path.join(arguments['path'],
                                         'cli_args.json')
    for key, value in json_read(file_=stored_arguments_file,
                                default={}).items():
        if key not in arguments or not arguments[key]:
            arguments[key] = value
    set_loggers(**{k: v
                   for k, v in arguments.items()
                   if k in ('log_file', 'error_log_file')})
    if 'error_log_file' in arguments:
        Bot.set_class_errors_file_path(file_path=arguments['error_log_file'])
    if 'log_file' in arguments:
        Bot.set_class_log_file_path(file_path=arguments['log_file'])
    if 'path' in arguments:
        Bot.set_class_path(arguments['path'])
    if 'token' in arguments and arguments['token']:
        token = arguments['token']
    else:
        token = input("Enter bot Token:\t\t")
        arguments['token'] = token
    json_write(arguments, stored_arguments_file)
    bot = Bot(token=token, database_url=join_path(arguments['path'], 'bot.db'))
    action = arguments['action'] if 'action' in arguments else 'run'
    if action == 'run':
        administration_tools.init(telegram_bot=bot)
        authorization.init(telegram_bot=bot)
        allow_elevation_to_admin(telegram_bot=bot)
        helper.init(telegram_bot=bot)
        exit_state = Bot.run(**{k: v
                                for k, v in arguments.items()
                                if k in ('local_host', 'port')})
        sys.exit(exit_state)
    if action == 'send':
        try:
            send_single_message(telegram_bot=bot)
        except KeyboardInterrupt:
            print("\nExiting...")
