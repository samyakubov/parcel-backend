import itertools
import logging
from collections.abc import Generator

from tqdm import tqdm

from . import dataset_transformations, sql
from .database import Database
from .datasets import datasets
from .file import File
from .typecast import Typecast
from .utility import colorize, list_wrap

BATCH_SIZE = 1000


class Dataset:
    """
    Most CLI actions correspond to a method in this class.
    It is initialized with the name of a dataset:

        pluto_latest = Dataset('pluto_latest')

    To download the files:

        pluto_latest.download_files()

    To load the files into DuckDB:

        pluto_latest.db_import()
    """

    def __init__(self, dataset_name, args=None):
        self.name = dataset_name
        self.args = args
        self.db = None

        if self.args:
            self.root_dir = self.args.root_dir
        else:
            self.root_dir = "./data"

        self.dataset = datasets()[dataset_name]
        self.files = self._files()
        self.schemas = list_wrap(self.dataset["schema"])
        self.dependencies = list_wrap(self.dataset["dependencies"]) if "dependencies" in self.dataset else []

    def _files(self):
        if "files" not in self.dataset:
            return []
        return [File(file_dict, folder=self.name, root_dir=self.root_dir) for file_dict in self.dataset["files"]]

    def download_files(self):
        """
        Downloads all files for the dataset.

        See ./file.py for more details.
        """
        for f in self.files:
            f.download(hide_progress=self.args.hide_progress)

    def db_import(self, limit=None):
        """
        Inserts the dataset into DuckDB.

        Optionally, provide a list of table names to limit the import
        to certain schemas in the dataset

        Output:  True | Throws
        """
        self.setup_db()
        self.create_schema()

        if self.dependencies:
            for dep_dataset_name in self.dependencies:
                dep_dataset = Dataset(dep_dataset_name)
                for dep_schema in dep_dataset.schemas:
                    if not self.db.table_exists(dep_schema["table_name"]):
                        raise Exception(
                            f"Missing dataset dependency. {','.join(self.dependencies)} datasets must be loaded first."
                        )

        for schema in self.schemas:
            if limit is None or schema["table_name"] in limit:
                if "fields" not in schema:
                    # Tables without fields are created via SQL and have no data
                    # file to import
                    continue
                elif self.db.table_exists(schema["table_name"]) and self.db.row_count(schema["table_name"]) > 0:
                    # A previous load already inserted rows. Importing again would
                    # duplicate them. SQL files still run below.
                    logging.info(f"{schema['table_name']} already has rows, skipping import")
                    continue
                else:
                    self.import_schema(schema)

        self.sql_files()

    def index(self):
        """
        Some datasets contains additional indices (notably, full-text-search indices)
        that are not automatically created.

        This method creates those indices.
        It does nothing if the dataset has no additional indexes
        """
        if "index" in self.dataset:
            for sql_file in self.dataset["index"]:
                self.db.execute_sql_file(sql_file)
        else:
            logging.debug("no index files exist for this dataset")

    def transform(self, schema: dict) -> Generator:
        """
        Calls the function in dataset_transformation with the same name
        as the schema.

        If no function exists with the same name as the schema table, it tries
        to call the function with the same name as the dataset
        """
        tc = Typecast(schema)

        try:
            rows = getattr(dataset_transformations, schema["table_name"])(self)
        except AttributeError:
            rows = getattr(dataset_transformations, self.name)(self, schema)

        # raise error if headers don't match dataset schema
        forked_rows, rows = itertools.tee(rows, 2)
        tc.check_headers(next(forked_rows))

        return tc.cast_rows(rows)

    def import_schema(self, schema):
        """
        Imports the schema (table) into DuckDB in batches.
        """
        rows = self.transform(schema)

        pbar = tqdm(unit="rows", disable=self.args.hide_progress)
        while True:
            batch = list(itertools.islice(rows, 0, BATCH_SIZE))
            if len(batch) == 0:
                break
            else:
                pbar.update(len(batch))
                self.db.insert_rows(batch, table_name=schema["table_name"])
        pbar.close()

    def create_schema(self):
        """
        Issues CREATE TABLE statements for all tables in the dataset.
        """
        for s in self.schemas:
            # Tables without fields are created via the sql script and don't
            # have a data file associated with them.
            if "fields" not in s:
                continue

            if self.db.table_exists(s["table_name"]):
                logging.info(f"{s['table_name']} already exists, skipping CREATE TABLE")
                continue

            self.db.sql(sql.create_table(s["table_name"], s["fields"]))

    def sql_files(self):
        """
        Executes all sql files for the dataset.
        """
        if "sql" in self.dataset:
            for f in self.dataset["sql"]:
                self.db.execute_sql_file(f)

    def setup_db(self):
        """
        Establishes the Database object. Used to lazy-load self.db.
        """
        if self.db is None:
            self.db = Database(self.args, table_name=self.name)

    def verify(self):
        """
        Verifies if the tables for this dataset exists and
        if it contains approximately the right number of rows.
        """
        self.setup_db()
        exit_state = True

        for schema in self.schemas:
            table_name = schema["table_name"]

            if not self.db.table_exists(table_name):
                exit_state = False
                print(colorize("fail", table_name + " is missing!"))
                continue

            cnt = self.db.row_count(table_name)
            if not schema.get("verify_count"):
                exit_state = False
                print(
                    colorize(
                        "fail",
                        table_name + " is missing verify_count. It has " + format(cnt, ",") + " rows",
                    )
                )
            elif cnt >= schema["verify_count"]:
                print(colorize("green", table_name + " has " + format(cnt, ",") + " rows "))
            else:
                exit_state = False
                if cnt == 0:
                    print(colorize("fail", table_name + " has no rows!"))
                else:
                    print(
                        colorize("fail", table_name + " has ")
                        + format(cnt, ",")
                        + colorize("fail", " rows, ")
                        + colorize("fail", "expecting at least ")
                        + colorize("blue", format(schema["verify_count"], ","))
                        + colorize("fail", " rows")
                    )

        return exit_state

    def drop(self):
        """
        Drops the dataset from DuckDB.
        """
        self.setup_db()

        for s in self.schemas:
            self.db.sql(sql.drop_table(s["table_name"]))
