#!/usr/bin/env python3

import csv
import os
import posixpath
import typing as tp
from importlib import resources

from webamc.util import io
from webamc import types


texts: dict[types.txt_t, str]
texts_loaded: bool = False


def reset() -> None:
    global texts_loaded, texts
    texts_loaded = False
    texts = dict()

    
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
                for txt in reader:
                    texts[tp.cast(types.txt_t, txt["id"])] = txt["text"]


def txt(id_: types.txt_t, args: None | tuple[str] = None) -> str:
    load_texts()
    if id_ not in texts:
        return id_
    txt = texts[id_]
    if args is None:
        return txt
    return txt % args


def exists(id_: types.txt_t) -> bool:
    load_texts()
    return id_ in texts


def all_texts() -> list[str]:
    return sorted(texts)
