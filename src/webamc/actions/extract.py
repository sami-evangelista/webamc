import os
import pathlib
import TexSoup  # type: ignore

from webamc.all import *
from webamc.util import termout, io
from webamc.config import CONFIG as cfg


def _extract(tex: pathlib.Path, odir: pathlib.Path) -> None:
    with open(tex) as fd:
        soup = TexSoup.TexSoup(fd.read())
        for qst in soup.find_all(cfg["tex_envs_question"]):
            odir.mkdir(parents=True, exist_ok=True)
            qst_code = qst.args[0].string
            qst_file = (
                cfg["tex_file_question_prefix"]
                + qst_code.replace("/", "-")
                + ".tex"
            )
            with open(pathlib.Path(odir / qst_file), "w") as fd:
                fd.write(str(qst))


def _traverse(idir: pathlib.Path, odir: pathlib.Path) -> None:
    for entry in sorted(idir.iterdir()):
        ext = io.get_file_extension(entry.name)
        if entry.is_file() and ext == ".tex":
            _extract(entry, odir)
    for entry in sorted(idir.iterdir()):
        if entry.is_dir():
            _traverse(entry, odir / entry.name)


def action(input: str, output: str) -> None:
    try:
        idir = pathlib.Path(input)
        odir = pathlib.Path(output)
        odir.mkdir(parents=True)
        _traverse(idir, odir)
    except FileExistsError as ex:
        termout.error(f"{ex.filename} already exists")
    except PermissionError as ex:
        termout.error(f"no permission to write directory {ex.filename}")
