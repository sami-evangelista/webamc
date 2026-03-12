#!/usr/bin/env python3

import csv
import os
import posixpath
from importlib import resources

from webamc.util import io


texts: dict[str, str]
texts_loaded: bool = False


def load_texts() -> None:
    from webamc import config
    global texts_loaded, texts
    if not texts_loaded:
        texts_loaded = True
        texts = dict()
        dir_path = (
            resources.files("webamc") / "data" / "lang" / config.CONFIG["lang"]
        )
        csv_files = [
            x
            for x in dir_path.iterdir()
            if x.is_file() and io.get_file_extension(x.name) == ".csv"
        ]
        for entry in csv_files:
            with (
                    resources.as_file(entry) as path,
                    path.open(encoding="utf-8") as fd
            ):
                reader = csv.DictReader(fd, delimiter=";")
                texts = dict({
                    txt["id"]: txt["text"] for txt in reader
                }, **texts)


def txt(id_: str) -> str:
    load_texts()
    return texts.get(id_, id_)
