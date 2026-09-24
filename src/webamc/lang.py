import csv
import typing as tp
from importlib import resources
from pathlib import Path

from webamc.types import all as types


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
        path = (
            Path(str(resources.files("webamc")))
            / "data" / "lang" / config.CONFIG["lang"]
        )
        csv_files = [
            x for x in path.iterdir() if x.is_file() and x.suffix == ".csv"
        ]
        for entry in csv_files:
            with (
                    resources.as_file(entry) as path,
                    path.open(encoding="utf-8") as fd
            ):
                reader = csv.DictReader(fd, delimiter=";")
                for t in reader:
                    texts[tp.cast(types.txt_t, t["id"])] = t["text"]


def txt(id_: types.txt_t, args: None | tuple[str] = None) -> str:
    load_texts()
    if id_ not in texts:
        return id_
    if args is None:
        result = texts[id_]
    else:
        result = texts[id_] % args
    return result


def exists(id_: types.txt_t) -> bool:
    load_texts()
    return id_ in texts


def all_texts() -> list[str]:
    return sorted(texts)
