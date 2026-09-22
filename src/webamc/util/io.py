import shutil
from pathlib import Path

from webamc.all import *
from . import termout


def get_executable_path(executable_name: Path) -> Path:
    result = shutil.which(executable_name.name)
    if result is None:
        termout.error(f"could not locate {executable_name} in your path")
        sys.exit(1)
    return Path(result)


def get_file_extension(file_path: str) -> str:
    return os.path.splitext(file_path)[1]


def mkdir_of_file(file_path: str) -> bool:
    dir_path = os.path.dirname(os.path.abspath(file_path))
    if os.path.isdir(dir_path):
        return True
    try:
        Path(dir_path).mkdir(parents=True)
        return True
    except NotADirectoryError:
        termout.error(f"{file_path}: not a directory")
    except PermissionError:
        termout.error(f"{file_path}: permission denied to create directory")
    return False


def remove(path: str) -> None:
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
