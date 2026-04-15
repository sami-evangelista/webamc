#!/usr/bin/env python3

import multiprocessing
import subprocess

from webamc.all import *
from . import termout
import glob

log_fd: None | tp.TextIO = None

def log_open(mode: tp.Literal["a", "w"] = "w") -> None:
    """
        Remove old log_files
    """
    base_log_file = config.CONFIG["log_file"]
    if base_log_file:
        filename, ext = os.path.splitext(base_log_file)
        for old_log in glob.glob(f"{filename}-*{ext}"):
            try: 
                os.remove(old_log)
            except OSError:
                pass

def log_close() -> None:
    pass

def log(msg: str) -> None:
    base_log_file = config.CONFIG.get("log_file")
    if base_log_file:
        # getting process number
        p_name = multiprocessing.current_process().name
        # extracting process number from str (process-1 => 1)
        worker_id = ''.join(filter(str.isdigit, p_name))
        
        if not worker_id:
            worker_id = str(os.getpid())
            
        filename, ext = os.path.splitext(base_log_file)
        worker_log_file = f"{filename}-{worker_id}{ext}"
        # ----------------------------------------------------------

        with open(worker_log_file, "a", encoding="UTF-8") as f:
            f.write(msg + "\n")


def log_exec(
        args: list[str],
        stdout: None | tp.TextIO | tp.BinaryIO = None,
        stderr: None | tp.TextIO | tp.BinaryIO = None,
        cwd: str | None = None
) -> bool:
    """
    Execute commande, then catch and write the output to the default log file
    """
    cmd = " ".join(args)
    
    # running the process
    proc_result = subprocess.run(
        args,
        check=False,
        capture_output=True, 
        text=True,
        cwd=cwd
    )

    success = (proc_result.returncode == 0)

    if not success:
        termout.error(f"there was an error with command {cmd}")

    # log file
    base_log_file = config.CONFIG.get("log_file")
    
    if base_log_file:
        # getting process number
        p_name = multiprocessing.current_process().name
        # extracting process number from str (process-1 => 1)
        worker_id = ''.join(filter(str.isdigit, p_name))
        
        # Sécurité : si on lance le script sans multi-processus, on garde le PID
        if not worker_id:
            worker_id = str(os.getpid())
            
        filename, ext = os.path.splitext(base_log_file)
        worker_log_file = f"{filename}-{worker_id}{ext}"
        # ----------------------------------------------------------

        with open(worker_log_file, "a", encoding="UTF-8") as f:
            cmt = (62 + len(cmd)) * "*" + "\n"
            f.write(cmt)
            f.write(30 * "*" + " " + cmd + " " + 30 * "*" + "\n")
            f.write(cmt)
            
            if proc_result.stdout:
                f.write(proc_result.stdout)
            if proc_result.stderr:
                f.write("\n" + proc_result.stderr)
            f.write("\n")
            
    else:
        # if log_file is none, it will write in the console
        if proc_result.stdout:
            sys.stdout.write(proc_result.stdout)
        if proc_result.stderr:
            sys.stderr.write(proc_result.stderr)

    return success