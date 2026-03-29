#!/usr/bin/env python3

import subprocess

from webamc.all import *
from . import termout


log_fd: None | tp.TextIO = None


def log_open(mode: tp.Literal["a", "w"] = "w") -> None:
    global log_fd
    log_file = config.CONFIG["log_file"]
    if log_fd is None and log_file is not None:
        log_fd = open(log_file, mode, encoding="UTF-8")


def log_close() -> None:
    if log_fd is not None:
        log_fd.close()


def log(msg: str) -> None:
    log_open()
    if log_fd is not None:
        log_fd.write(msg + "\n")

def log_exec(
        args: list[str],
        stdout: None | tp.TextIO | tp.BinaryIO = None,
        stderr: None | tp.TextIO | tp.BinaryIO = None,
        cwd: str | None = None
) -> bool:
    log_open()
    if log_fd is None:
        stdout = sys.stdout
        stderr = sys.stderr
    else:
        stdout = log_fd
        stderr = log_fd
    cmd = " ".join(args)
    cmt = (62 + len(cmd)) * "*" + "\n"
    stdout.write(cmt)
    stdout.write(30 * "*" + " " + cmd + " " + 30 * "*" + "\n")
    stdout.write(cmt)
    stdout.flush()
    proc_result = subprocess.run(
        args,
        check=False,
        input="",
        stdout=stdout,
        stderr=stderr,
        cwd=cwd
    )
    if proc_result.returncode != 0:
        termout.error(f"there was an error with command {cmd}")
        return False
    return True