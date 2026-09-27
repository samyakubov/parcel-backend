import codecs
import logging
import os
from pathlib import Path

import requests
from tqdm import tqdm

from .utility import mkdir


class DownloadFailedError(Exception):
    pass


open_str_kwargs = {"mode": "w", "encoding": "utf-8", "errors": "replace"}
open_byte_kwargs = {"mode": "wb"}


def is_csv(dest):
    return dest[-4:].lower() == ".csv"


def open_kwargs(dest):
    if is_csv(dest):
        return open_str_kwargs
    else:
        return open_byte_kwargs


def is_html_file(path):
    """True when a download saved an HTML error page instead of the data file."""
    try:
        with open(path, "rb") as f:
            sample = f.read(64).lstrip().lower()
    except OSError:
        return False
    return sample.startswith((b"<html", b"<!doctype", b"<head"))


def safe_int(value):
    """
    Attempt to convert the given value to an integer,
    returning None on failure.
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def download_file(url, dest, hide_progress=False):
    """
    Downloads a url and saves the result to the destination path

    It will creates parent directory of the destination path,
    if they they don't exist.

    If the destination file exists and is not empty, it assumes the file has
    already been downloaded and will skip downloading the file accordingly.
    """
    mkdir(dest)

    if Path(dest).exists() and os.stat(dest).st_size > 0 and not is_html_file(dest):
        logging.info(f"{url} has already been downloaded, skipping")
        return True

    try:
        logging.info(f"Downloading {url} to {dest}")
        is_csv_file = is_csv(dest)
        # nyc.gov answers the default requests user agent with an Access Denied HTML page.
        r = requests.get(
            url,
            stream=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; nycdb/0.4)"},
        )
        total_bytes = safe_int(r.headers.get("content-length"))
        pbar = tqdm(total=total_bytes, unit="B", unit_scale=True, unit_divisor=1024, disable=hide_progress)
        with open(dest, **open_kwargs(dest)) as f:
            for chunk in r.iter_content(chunk_size=(512 * 1024)):
                if chunk:
                    pbar.update(len(chunk))
                    if is_csv_file:
                        f.write(codecs.decode(chunk, encoding="utf-8", errors="replace"))
                    else:
                        f.write(chunk)
        pbar.close()
        if is_html_file(dest):
            os.remove(dest)
            raise DownloadFailedError(
                f"Download of {url} returned an HTML error page instead of the data file"
            )
        return True
    except DownloadFailedError:
        raise
    except Exception as err:
        raise DownloadFailedError(f"Could not download: {url}") from err


class File:
    """Wrapper around a file"""

    def __init__(self, file_dict, root_dir="./data", folder=""):
        self.root_dir = root_dir
        self.url = file_dict["url"]
        self.dest = self._dest(file_dict)

    def download(self, hide_progress=False):
        download_file(self.url, self.dest, hide_progress=hide_progress)
        return self

    def _dest(self, file_dict):
        if "dest" in file_dict:
            file_path = file_dict["dest"]
        else:
            file_path = file_dict["url"].split("/")[-1]
        return os.path.abspath(os.path.join(self.root_dir, file_path))
