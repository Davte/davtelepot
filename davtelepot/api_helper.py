"""Get and parse Telegram API webpage."""

# Standard library modules
import asyncio
import logging

# Third party modules
import aiohttp
from bs4 import BeautifulSoup

api_url = "https://core.telegram.org/bots/api"


class TelegramApiMethod(object):
    """Telegram bot API method."""

    def __init__(self, name, description, table):
        """Initialize object with name, description and table data."""
        self._name = name
        self._description = description
        self._table = table

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

    def get_parameters_from_table(self):
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


async def main(loop=None, filename=None):
    """Get information from Telegram bot API webpage."""
    if loop is None:
        loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession(
        loop=loop,
        timeout=aiohttp.ClientTimeout(
            total=100
        )
    ) as session:
            async with session.get(
                api_url
            ) as response:
                webpage = BeautifulSoup(
                    await response.text(),
                    "html.parser"
                )
    if filename is not None:
        with open(filename, 'w') as _file:
            _file.write(webpage.decode())
    for method in webpage.find_all("h4"):
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
        if method_name and method_name[0] == method_name[0].lower():
            method = TelegramApiMethod(
                method_name, description, parameters_table
            )
            print(
                "NAME\n\t{m.name}\n"
                "DESCRIPTION\n\t{m.description}\n"
                f"TABLE\n\t{method.get_parameters_from_table()}\n\n".format(
                    m=method
                )
            )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop=loop, filename='prova.txt'))
    logging.info("Done!")
