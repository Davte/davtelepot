"""Get and parse Telegram API web page."""

# Standard library modules
import argparse
import asyncio
import inspect
import logging

# Third party modules
import os
from typing import List

import aiohttp
from bs4 import BeautifulSoup

# Project modules
from davtelepot.api import TelegramBot

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
    def parameters_with_types(self) -> List[str]:
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
                            output_file=None,
                            input_file=None):
    """Get information from Telegram bot API web page."""
    if loop is None:
        loop = asyncio.get_event_loop()
    implemented_methods = dir(TelegramBot)
    if input_file is None or not os.path.isfile(input_file):
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
    else:
        with open(input_file, 'r') as local_web_page:
            web_page = BeautifulSoup(
                ''.join(local_web_page.readlines()),
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
    new_methods = []
    edited_methods = []
    for method in methods:
        if print_all or method.name not in implemented_methods:
            new_methods.append(method)
        else:
            parameters = set(parameter['name'] for parameter in method.parameters)
            implemented_parameters = set(
                parameter.strip('_')  # Parameter `type` becomes `type_` in python
                for parameter in inspect.signature(
                    getattr(TelegramBot,
                            method.name)
                ).parameters.keys()
                if parameter != 'self'
            )
            new_parameters = parameters - implemented_parameters
            deprecated_parameters = implemented_parameters - parameters
            if new_parameters or deprecated_parameters:
                edited_methods.append(
                    dict(
                        name=method.name,
                        new_parameters=new_parameters,
                        deprecated_parameters=deprecated_parameters
                    )
                )
    if output_file:
        with open(output_file, 'w') as file:
            if new_methods:
                file.write(
                    "from typing import List, Union\n"
                    "from davtelepot.api import TelegramBot\n\n\n"
                    "# noinspection PyPep8Naming\n"
                    "class Bot(TelegramBot):\n\n"
                )
            file.writelines(
                f"    async def {method.name}("
                f"{', '.join(['self'] + method.parameters_with_types)}"
                f"):\n"
                f"        \"\"\""
                f"    {method.description.replace(new_line, new_line + ' ' * 4)}\n"
                f"        See https://core.telegram.org/bots/api#"
                f"    {method.name.lower()} for details.\n"
                f"        \"\"\"\n"
                f"        return await self.api_request(\n"
                f"            '{method.name}',\n"
                f"            parameters=locals()\n"
                f"        )\n\n"
                for method in new_methods
            )
            if edited_methods:
                file.write('\n# === EDITED METHODS ===\n')
            for method in edited_methods:
                file.write(f'\n"""{method["name"]}\n')
                if method['new_parameters']:
                    file.write("    New parameters: "
                               + ", ".join(method['new_parameters'])
                               + "\n")
                if method['deprecated_parameters']:
                    file.write("    Deprecated parameters: "
                               + ", ".join(method['deprecated_parameters'])
                               + "\n")
                file.write('"""\n')
    else:
        print(
            '\n'.join(
                f"NAME\n\t{method.name}\n"
                f"PARAMETERS\n\t{', '.join(['self'] + method.parameters_with_types)}\n"
                f"DESCRIPTION\n\t{method.description}\n"
                f"TABLE\n\t{method.print_parameters_table()}\n\n"
                for method in new_methods
            )
        )
        for method in edited_methods:
            print(method['name'])
            if method['new_parameters']:
                print("\tNew parameters: " + ", ".join(method['new_parameters']))
            if method['deprecated_parameters']:
                print("\tDeprecated parameters: " + ", ".join(method['deprecated_parameters']))


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
    cli_parser.add_argument('--in', '--input', '-i', type=str,
                            default=None,
                            required=False,
                            help='File path to read Telegram API web page')
    cli_arguments = vars(cli_parser.parse_args())
    filename = cli_arguments['file']
    print_all = cli_arguments['all']
    output_file = cli_arguments['out']
    input_file = cli_arguments['in']
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        print_api_methods(loop=loop,
                          filename=filename,
                          print_all=print_all,
                          output_file=output_file,
                          input_file=input_file)
    )
    logging.info("Done!")


if __name__ == '__main__':
    main()
