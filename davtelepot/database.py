"""Provide any inheriting object with a dataset-powered database management."""

# Standard library modules
import logging
from typing import Tuple

# Third party modules
import dataset


class ObjectWithDatabase(object):
    """Objects inheriting from this class will have a `.db` method.

    Using `subclass_instance.db` will open a SQL transaction.
    To perform multiple SQL queries in a single transaction use a with
        statement as in this simple example:
        ```
        with my_object.db as db:
            if db['my_table'].find_one(id=14):
                db['fourteen_exists'].insert(
                    {'exists': True}
                )
        ```
    """

    def __init__(self, database_url: str = None):
        """Instantiate object and open connection with database."""
        if database_url is None:
            database_url = 'database.db'
        if '://' not in database_url:
            # Default database engine is sqlite, which operates on a
            # single-file database having `.db` extension
            if not database_url.endswith('.db'):
                database_url += '.db'
            database_url = f'sqlite:///{database_url}'
        self._database_url = database_url
        try:
            self._database = dataset.connect(self.db_url)
        except Exception as e:
            self._database_url = None
            self._database = None
            logging.error(f"{e}")

    @property
    def db_url(self) -> str:
        """Return complete path to database."""
        return self._database_url

    @property
    def db(self) -> dataset.Database:
        """Return the dataset.Database instance related to `self`."""
        return self._database

    def create_views(self, views, overwrite=False):
        """Take a list of `views` and add them to bot database.

        Overwrite existing views if `overwrite` is set to True.
        Each element of this list should have
        - a `name` field
        - a `query field`
        """
        with self.db as db:
            for view in views:
                try:
                    if overwrite:
                        db.query(
                            f"DROP VIEW IF EXISTS {view['name']}"
                        )
                    db.query(
                        f"CREATE VIEW IF NOT EXISTS {view['name']} "
                        f"AS {view['query']}"
                    )
                except Exception as e:
                    logging.error(f"{e}")

    def add_table_and_columns_if_not_existent(self,
                                              table_name: str,
                                              columns: Tuple[
                                                  Tuple[str,
                                                        dataset.database.Types],
                                                  ...] = None):
        """Create table (if it does not exist) and add given columns (if missing).

        @param table_name: Table name (string)
        @param columns: Table columns as tuples of column name and type
        @return: None
        """
        if table_name not in self.db.tables:
            table = self.db.create_table(table_name=table_name)
            logging.info(f"Created table `{table_name}`")
        else:
            table = self.db[table_name]
        if columns is None:
            columns = []
        for column_name, column_type in columns:
            if not table.has_column(column_name):
                table.create_column(
                    column_name,
                    column_type
                )
                logging.info(f"Added column `{column_name}` "
                             f"(type `{column_type}`) "
                             f"to table `{table_name}`")
