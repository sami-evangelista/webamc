import shutil

from webamc.all import *


def get_file_extension(file_path: str) -> str:
    return os.path.splitext(file_path)[1]


def remove(path: str) -> None:
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
