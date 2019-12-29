"""This example script shows how to develop a simple bot with davtelepot.

1. Install davtelepot
    ```bash
    # Create a new python virtual environment
    pip -m venv env
    # Activate the virtual environment
    source env/bin/activate
    # Install davtelepot library in this environment
    pip install davtelepot
    # Run the current script within this environment
    python a_simple_bot.py
    ```

2. To run your bot, you will need a bot token. You can get up to 20 bot tokens
    from https://t.me/botfather

3. This script will look for your bot token in a gitignored `secrets.py` file
    in the same folder as the current script. If no `secrets` module is found,
    user will be prompted at runtime for a token, and the entry will be stored
    in `secrets.py` for later use.

4. Standard library, third party and project modules will be imported, and
    `logging` preferences set. You are free to edit these settings, e.g. adding
    one or more file and error loggers or setting different levels.

5. `simple_bot` is an instance of `davtelepot.bot.Bot` class.
    To instantiate a bot you need to provide at least a Telegram bot API token,
    and you may also provide a path to a database (if no path is provided,
    a `./bot.db` SQLite database will be used).

6. `initialize_bot` function is defined and called on `simple_bot`. It assigns
    commands, parsers, callback and inline query handlers to the bot.

7. `Bot.run()` method is called, causing the script to hang while asynchronous
    tasks run checking for updates and routing them to get and send replies.
    Send a KeyboardInterrupt (ctrl+C) to stop the bot.
"""

# Standard library modules
import logging
import os
import sys

# Third party modules
try:
    from davtelepot.bot import Bot
    from davtelepot.utilities import (
        get_cleaned_text, make_inline_keyboard, make_button
    )
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

# Get path of current script
path = os.path.dirname(os.path.abspath(__file__))


def initialize_bot(bot):
    """Take a bot and set commands."""
    bot.set_callback_data_separator('|')

    @bot.command(command='foo', aliases=['Foo'], show_in_keyboard=True,
                 description="Reply 'bar' to 'foo'",
                 authorization_level='everybody')
    async def foo_command(bot, update, user_record):
        return 'Bar!'

    def is_bar_text_message(text):
        return text.startswith('bar')

    @bot.parser(condition=is_bar_text_message,
                description='Reply Foo to users who write Bar',
                authorization_level='everybody',
                argument='text')
    async def bar_parser(bot, update):
        text_except_foo = get_cleaned_text(update, bot, ['bar'])
        return f"Foo!\n{text_except_foo}"

    def get_keyboard(chosen_button=-1):
        return make_inline_keyboard(
            [
                make_button(
                    prefix='button:///',
                    delimiter='|',
                    data=[i],
                    text=f"{'✅' if chosen_button == i else '☑️'} Button #{i}"
                )
                for i in range(1, 13)
            ],
            3
        )

    @bot.command(command='buttons')
    async def buttons_command():
        return dict(
            text="Press a button!",
            reply_markup=get_keyboard()
        )

    @bot.button(prefix='button:///', separator='|',
                authorization_level='everybody')
    async def buttons_button(bot, update, user_record, data):
        button_number = data[0]
        return dict(
            edit=dict(
                text=f"You pressed button #{button_number}",
                reply_markup=get_keyboard(button_number)
            )
        )

    def starts_with_a(text):
        return text.startswith('a')

    @bot.query(
        condition=starts_with_a,
        description='Mirror query text if it starts with letter `a`',
        authorization_level='everybody'
    )
    async def inline_query(bot, update, user_record):
        return dict(
            type='article',
            id=10,
            title="Click here to send your query text as a message.",
            input_message_content=dict(
                message_text=update['query']
            )
        )

    bot.set_default_inline_query_answer(
        dict(
            type='article',
            id=0,
            title="Start query text with `a` to mirror it.",
            input_message_content=dict(
                message_text="This query does not start with `a`."
            )
        )
    )

    bot.set_unknown_command_message(
        "<b>Currently supported features</b>\n\n"
        "- /foo (or text starting with `foo`): replies `Bar!`.\n"
        "- Text starting with `bar`: replies `Foo!` followed by the rest of "
        "text in your bar-starting message.\n"
        "- /buttons demonstrates the use of buttons.\n"
        "- Inline queries starting with letter `a` will be mirrored as text "
        "messages. To use this feature, try writing <code>@{bot.name} "
        "your_text_here</code>"
    )


def _main():
    # Import or prompt user for bot token
    try:
        from secrets import simple_bot_token
    except ImportError:
        simple_bot_token = input("Enter bot token:\t\t")
        with open(
            f'{path}/secrets.py',
            'a'  # Append to file, create it if it does not exist
        ) as secrets_file:
            secrets_file.write(f'simple_bot_token = "{simple_bot_token}"\n')

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

    # Instantiate, initialize and make `simple_bot` run.
    simple_bot = Bot(token=simple_bot_token, database_url=f"{path}/bot.db")
    initialize_bot(simple_bot)
    logging.info("Send a KeyboardInterrupt (ctrl+C) to stop bots.")
    Bot.run()


if __name__ == '__main__':
    _main()
