import os

from webamc.all import *
from . import compile as comp, output


def _check_dir_traversal(dir_path: str) -> bool:
    result = True
    cfg = config.CONFIG
    for entry in os.listdir(dir_path):
        entry_path = os.path.join(dir_path, entry)
        if entry in {cfg["tex_file_exercise"], cfg["tex_file_mcq"]}:
            mdata = comp.parse_amc_mdata(entry_path)
            for (key, attr) in [
                    ("itm_code", "CODE"),
                    ("itm_title", "TITLE")
            ]:
                if key not in mdata:
                    output.error(f"{entry_path}: missing {attr} attribute")
                    result = False
        if os.path.isdir(entry_path):
            result = _check_dir_traversal(entry_path) and result
    return result


def action(dir_path: str) -> bool:
    if not os.path.isdir(dir_path):
        output.error(f"directory not found: {dir_path}")
        return False
    result = _check_dir_traversal(dir_path)
    if result:
        output.info(f"{dir_path}: no error found")
    return result
