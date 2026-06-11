import sys
import typing as tp


VERBOSE = False

COL_FG_BLACK = "\033[30m"
COL_FG_RED = "\033[31m"
COL_FG_GREEN = "\033[32m"
COL_FG_ORANGE = "\033[33m"
COL_FG_BLUE = "\033[34m"
COL_FG_PURPLE = "\033[35m"
COL_FG_CYAN = "\033[36m"
COL_FG_LIGHTGREY = "\033[37m"
COL_FG_DARKGREY = "\033[90m"
COL_FG_LIGHTRED = "\033[91m"
COL_FG_LIGHTGREEN = "\033[92m"
COL_FG_YELLOW = "\033[93m"
COL_FG_LIGHTBLUE = "\033[94m"
COL_FG_PINK = "\033[95m"
COL_FG_LIGHTCYAN = "\033[96m"

COL_BG_BLACK = "\033[40m"
COL_BG_RED = "\033[41m"
COL_BG_GREEN = "\033[42m"
COL_BG_ORANGE = "\033[43m"
COL_BG_BLUE = "\033[44m"
COL_BG_PURPLE = "\033[45m"
COL_BG_CYAN = "\033[46m"
COL_BG_LIGHTGREY = "\033[47m"

settings_t = tp.TypedDict("settings_t", {
    "fg_color": None | str,
    "bg_color": None | str,
    "prefix": None | str,
    "file": tp.TextIO
})

SETTINGS: tp.Dict[str, settings_t] = {
    "msg": {
        "fg_color": COL_FG_YELLOW,
        "bg_color": None,
        "prefix": "# ",
        "file": sys.stdout
    },
    "info": {
        "fg_color": COL_FG_CYAN,
        "bg_color": None,
        "prefix": None,
        "file": sys.stdout
    },
    "warning": {
        "fg_color": COL_FG_ORANGE,
        "bg_color": None,
        "prefix": "[WARNING] ",
        "file": sys.stdout
    },
    "error": {
        "fg_color": COL_FG_RED,
        "bg_color": None,
        "prefix": "[ERROR] ",
        "file": sys.stderr
    }
}


def output_string(
        st: str,
        setting: None | str = None,
        fg_color: None | str = None,
        bg_color: None | str = None,
        prefix: None | str = None,
        file: tp.TextIO = sys.stdout
) -> None:
    """Print st to file using settings."""
    if setting is not None:
        if setting in SETTINGS:
            output_string(st, **SETTINGS[setting])
        else:
            output_string(f"termout: setting {setting} not found", "warning")
            output_string(st)
    else:
        if prefix is not None:
            st = f"{prefix}{st}"
        if fg_color is not None:
            st = f"\033[{fg_color}{st}"
        if bg_color is not None:
            st = f"\033[{bg_color}{st}"
        if fg_color is not None or bg_color is not None:
            st = f"{st}\033[00m"
        print(st, file=file)


def msg(m: str) -> None:
    """Print m using the "msg" settings and only if VERBOSE == True."""
    if VERBOSE:
        output_string(m, "msg")


def warning(warn: str) -> None:
    """Print warn using the "warning" settings."""
    output_string(warn, "warning")


def error(err: str) -> None:
    """Print err using the "error" settings."""
    output_string(err, "error")


def info(inf: str) -> None:
    """Print msg using the "info" settings."""
    output_string(inf, "info")
