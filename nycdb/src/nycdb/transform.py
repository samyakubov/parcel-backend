import csv
import io
import re
import types
from zipfile import ZipFile

from .bbl import bbl
from .utility import merge

invalid_header_chars = ["\n", "\r", " ", "-", "#", ".", "'", '"', "_", "/", "(", ")", ":", "+"]
replace_header_chars = [("%", "pct")]
starts_with_numbers = re.compile(r"^(\d+)(.*)$")
only_numbers = re.compile(r"^\d+$")


def flip_numbers(header):
    """
    str -> str
    If the header starts with numbers, it places
    those numbers at the end of the string.

    Columns in SQL cannot start with a number. This function will change
    a header named '2017values' to 'values2017'
    """
    match = starts_with_numbers.match(header)
    if match:
        if only_numbers.match(header):
            raise ValueError("Column names cannot be composed of all numbers")
        else:
            return match.group(2) + match.group(1)
    else:
        return header


def clean_headers(headers):
    """
    parses header csv line and fixes some common issues with column names

    String --> [String]
    """
    s = headers.lower()
    for char in invalid_header_chars:
        s = s.replace(char, "")
    for old, new in replace_header_chars:
        s = s.replace(old, new)
    return [flip_numbers(x) for x in s.split(",")]


def stream_files_from_zip(file_path, extension="csv", common_header=True):
    """
    Extracts data from all files of a single type (default = csv) from the zip file.
    It uses the header from the first file and skips the headers from other files

    String --> Generator
    """
    with ZipFile(file_path, "r") as zip_f:
        csv_files = [f for f in zip_f.namelist() if f[-3:].lower() == extension]
        for idx, csv_file in enumerate(csv_files):
            with zip_f.open(csv_file) as f:
                firstline = f.readline().decode("UTF-8", "ignore")
                if idx == 0:
                    yield firstline
                for line in f:
                    yield line.decode("UTF-8", "ignore")


# String (filepath) -> String
def extract_csvs_from_zip(file_path):
    """
    Combines all content in all CSVs (.csv) in the zip file.

    Uses the header from the first csv file and
    excludes the header from the rest of the csvs.
    """
    return stream_files_from_zip(file_path)


def extract_csv_from_zip(file_path, csv_file_path):
    """
    Returns a generator that iterates through all the rows
    in the given CSV file in the given ZIP file, including
    the header row.
    """

    with ZipFile(file_path, "r") as zip_f:
        with zip_f.open(csv_file_path) as f:
            for line in f:
                yield line.decode("UTF-8", "ignore")


def to_csv(file_path_or_generator, header_replacements=None):
    """
    Reads firstline as the headers and converts input into a stream of dicts

    String | Generator --> Generator
    """
    if header_replacements is None:
        header_replacements = {}

    if isinstance(file_path_or_generator, types.GeneratorType):
        f = io.StringIO("".join(list(file_path_or_generator)))
    elif isinstance(file_path_or_generator, str):
        f = open(file_path_or_generator, encoding="utf-8", errors="replace")
    else:
        raise ValueError("to_csv accepts Strings or Generators")

    with f:
        headers = clean_headers(f.readline())
        headers = [header_replacements[h] if header_replacements.get(h) else h for h in headers]
        yield from csv.DictReader(f, fieldnames=headers)


def with_bbl(table, borough="borough", block="block", lot="lot"):
    for row in table:
        yield merge(row, {"bbl": bbl(row[borough], row[block], row[lot])})


def skip_fields(table, fields_to_skip):
    for row in table:
        for f in fields_to_skip:
            if f in row:
                del row[f]
        yield row
