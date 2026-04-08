import os
import pathlib
import TexSoup  # type: ignore

from webamc.all import *
from webamc.util import io
from webamc.config import CONFIG as cfg
from . import output


def _extract(tex: pathlib.Path, odir: pathlib.Path) -> None:
    with open(tex) as fd:
        output.info(f"parse {tex}")
        try:
            soup = TexSoup.TexSoup(fd.read())
        except:
            output.warning(f"parse error !")
            return
        for qst in soup.find_all(cfg["tex_envs_question"]):
            odir.mkdir(parents=True, exist_ok=True)
            qst_code = qst.args[0].string
            qst_file = (
                cfg["tex_file_question_prefix"]
                + qst_code.replace("/", "-")
                + ".tex"
            )
            output.info(f"extract {tex} -> {qst_file}")
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


def action(idir: str, odir: str) -> None:
    try:
        pathlib.Path(odir).mkdir(parents=True)
        _traverse(pathlib.Path(idir), pathlib.Path(odir))
    except FileExistsError as ex:
        output.error(f"{ex.filename} already exists")
    except PermissionError as ex:
        output.error(f"no permission to write directory {ex.filename}")
