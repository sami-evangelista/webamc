from pathlib import Path

from webamc.all import *
from . import compile as comp, output


def _check_dir_traversal(dir_path: Path) -> bool:
    result = True
    cfg = config.CONFIG
    for entry in dir_path.iterdir():
        if entry.name in {cfg["tex_file_exercise"], cfg["tex_file_mcq"]}:
            mdata = comp.parse_amc_mdata(entry)
            for (key, attr) in [
                    ("itm_code", "CODE"),
                    ("itm_title", "TITLE")
            ]:
                if key not in mdata:
                    output.error(f"{entry}: missing {attr} attribute")
                    result = False
        if entry.is_dir():
            result = _check_dir_traversal(entry) and result
    return result


def action(dir_path: str) -> bool:
    path = Path(dir_path)
    if not path.is_dir():
        output.error(f"directory not found: {dir_path}")
        return False
    result = _check_dir_traversal(path)
    if result:
        output.info(f"{dir_path}: no error found")
    return result
