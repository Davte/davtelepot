"""Get and parse Telegram API web page."""

# Standard library modules
import argparse
import asyncio
import logging

# Third party modules
import aiohttp
from bs4 import BeautifulSoup

# Project modules
from . import api

api_url = "https://core.telegram.org/bots/api"


class TelegramApiMethod(object):
    types = {
        'Array of String': "List[str]",
        'Boolean': "bool",
        'Integer': "int",
        'Integer or String': "Union[int, str]",
        'String': "str",
    }
    """Telegram bot API method."""

    def __init__(self, name, description, table):
        """Initialize object with name, description and table data."""
        self._name = name
        self._description = description
        self._table = table
        self._parameters = self.get_parameters_from_table()

    @property
    def name(self):
        """Return method name."""
        return self._name

    @property
    def description(self):
        """Return method description."""
        return self._description

    @property
    def table(self):
        """Return method parameters table."""
        return self._table

    @property
    def parameters(self):
        return self._parameters

    @property
    def parameters_with_types(self):
        return [
            f"{parameter['name']}: {parameter['type']}"
            for parameter in self._parameters
        ]

    def print_parameters_table(self):
        """Extract parameters from API table."""
        result = ''
        if self.table is None:
            return "No parameters"
        rows = self.table.tbody.find_all('tr')
        if rows is None:
            rows = []
        for row in rows:
            result += '------\n'
            columns = row.find_all('td')
            if columns is None:
                columns = []
            for column in columns:
                result += f'| {column.text.strip()} |'
            result += '\n'
        result += '\n'
        return result

    def get_parameters_from_table(self):
        if self.table is None:
            return []
        parameters = []
        rows = self.table.tbody.find_all('tr') or []
        for row in rows:
            columns = row.find_all('td') or []
            name, type_, *_ = map(lambda column: column.text.strip(), columns)
            if type_ in self.types:
                type_ = self.types[type_]
            else:
                type_ = f"'{type_}'"
            parameters.append(
                dict(
                    name=name,
                    type=type_
                )
            )
        return parameters


async def print_api_methods(loop=None,
                            filename=None,
                            print_all=False,
                            output_file=None):
    """Get information from Telegram bot API web page."""
    if loop is None:
        loop = asyncio.get_event_loop()
    implemented_methods = dir(api.TelegramBot)
    async with aiohttp.ClientSession(
        loop=loop,
        timeout=aiohttp.ClientTimeout(
            total=100
        )
    ) as session:
        async with session.get(
                api_url
        ) as response:
            web_page = BeautifulSoup(
                await response.text(),
                "html.parser"
            )
    if filename is not None:
        with open(filename, 'w') as _file:
            _file.write(web_page.decode())
    methods = []
    for method in web_page.find_all("h4"):
        method_name = method.text
        description = ''
        parameters_table = None
        for tag in method.next_siblings:
            if tag.name is None:
                continue
            if tag.name == 'h4':
                break  # Stop searching in siblings if <h4> is found
            if tag.name == 'table':
                parameters_table = tag
                break  # Stop searching in siblings if <table> is found
            description += tag.get_text()
        # Methods start with a lowercase letter
        if method_name and method_name[0] == method_name[0].lower():
            methods.append(
                TelegramApiMethod(
                    method_name,
                    description,
                    parameters_table
                )
            )
    new_line = '\n'
    if output_file:
        with open(output_file, 'w') as file:
            file.write(
                "from typing import List, Union\n"
                "from davtelepot.api import TelegramBot\n"
                "self = TelegramBot('fake_token')\n\n\n"
            )
            file.writelines(
                f"async def {method.name}("
                f"{', '.join(method.parameters_with_types)}"
                "):\n"
                "    \"\"\""
                f"{method.description.replace(new_line, new_line + ' ' * 4)}\n"
                "    See https://core.telegram.org/bots/api#"
                f"{method.name.lower()} for details.\n"
                "    \"\"\"\n"
                "    return await self.api_request(\n"
                f"        '{method.name}',\n"
                "        parameters=locals()\n"
                "    )\n\n\n"
                for method in methods
                if print_all or method.name not in implemented_methods
            )
    else:
        print(
            '\n'.join(
                f"NAME\n\t{method.name}\n"
                f"PARAMETERS\n\t{', '.join(method.parameters_with_types)}\n"
                f"DESCRIPTION\n\t{method.description}\n"
                f"TABLE\n\t{method.print_parameters_table()}\n\n"
                for method in methods
                if print_all or method.name not in implemented_methods
            )
        )


def main():
    cli_parser = argparse.ArgumentParser(
        description='Get Telegram API methods information from telegram '
                    'website.\n'
                    'Implement missing (or --all) methods in --out file, '
                    'or print methods information.',
        allow_abbrev=False,
    )
    cli_parser.add_argument('--file', '-f', '--filename', type=str,
                            default=None,
                            required=False,
                            help='File path to store Telegram API web page')
    cli_parser.add_argument('--all', '-a',
                            action='store_true',
                            help='Print all methods (default: print missing '
                                 'methods only)')
    cli_parser.add_argument('--out', '--output', '-o', type=str,
                            default=None,
                            required=False,
                            help='File path to store methods implementation')
    cli_arguments = vars(cli_parser.parse_args())
    filename = cli_arguments['file']
    print_all = cli_arguments['all']
    output_file = cli_arguments['out']
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        print_api_methods(loop=loop,
                          filename=filename,
                          print_all=print_all,
                          output_file=output_file)
    )
    logging.info("Done!")


if __name__ == '__main__':
    main()
