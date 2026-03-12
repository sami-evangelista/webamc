#!/usr/bin/env python3

import json
import os
import sys
import pathlib
import typing as tp

from webamc.util import termout, io
from . import types


HOME_DIR = pathlib.Path.home()
if sys.platform == "win32":
    ROOT_DIR = os.path.join(HOME_DIR, "AppData", "Roaming", "webamc")
else:
    ROOT_DIR = os.path.join(HOME_DIR, ".local", "share", "webamc")
DEFAULT_CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")


class Config(dict[str, tp.Any]):
    def __getitem__(self, key: str) -> tp.Any:
        if key not in self:
            return CONFIG_DEFAULT[key]  # type: ignore
        return super().__getitem__(key)


def load(cfg_file: str | None = None) -> None:
    if cfg_file is None:
        cfg_file = DEFAULT_CONFIG_FILE
    if os.path.exists(cfg_file):
        with open(cfg_file, encoding="utf-8") as fd:
            try:
                data = json.loads(fd.read())
                if isinstance(data, dict):
                    for key, val in data.items():
                        CONFIG[key] = val  # type: ignore
            except json.decoder.JSONDecodeError:
                termout.warning(f"malformed configuration file {cfg_file}")
    elif cfg_file == DEFAULT_CONFIG_FILE:
        if io.mkdir_of_file(cfg_file):
            with open(cfg_file, "w", encoding="utf-8") as fd:
                fd.write(json.dumps(CONFIG_DEFAULT, indent=2) + "\n")
            load()


CONFIG_DEFAULT: types.conf_t = {
    "base_url": "https://www.example.com",
    "auth_account_creation_enabled": True,
    "auth_cas_enabled": True,
    "auth_local_enabled": True,
    "cas_server": "https://cas.example.com",
    "cas_server_name": "CAS example server",
    "cas_version": 2,
    "date_format": None,
    "date_locale": "fr",
    "datetime_format": None,
    "db_port": 5432,
    "db_host": "localhost",
    "db_name": "webamc",
    "db_password": "webamc_password",
    "db_user": "webamc_user",
    "debug": True,
    "inbox_dir": "/path/to/inbox/dir",
    "icon_size": 24,
    "json_file_pack": "_pack.json",
    "key_qst_next": "d",
    "key_qst_prev": "q",
    "key_switch_mode": "m",
    "lang": "fr",
    "log_file": None,
    "mails_dir": None,
    "password_ticket_validity": 3600,
    "projects_dir": "/path/to/projects/dir",
    "root_path": "/webamc",
    "secret_key": "abcdefghij0123456789",
    "service_name": "Webamc",
    "smtp_auth": True,
    "smtp_eaddr_from": "no-reply@example.com",
    "smtp_host": "mail.example.com",
    "smtp_password": "smtp_password",
    "smtp_port": 465,
    "smtp_user": "smtp_user",
    "tex2pdf_exe": "pdflatex",
    "tex2pdf_exe_args": [
        "-output-directory={out_dir}",
        "{tex_file}"
    ],
    "tex_envs_choices": [
        "choices",
        "choiceshoriz",
        "reponses",
        "reponseshoriz"
    ],
    "tex_envs_question": [
        "question",
        "questionmult"
    ],
    "tex_envs_question_mult": [
        "questionmult"
    ],
    "tex_file_exercise": "_exercise.tex",
    "tex_file_header": "_header.tex",
    "tex_file_mcq": "_mcq.tex",
    "tex_file_question_prefix": "qst-",
    "tex_file_webamc": "_webamc.tex",
    "tex_macros_choice": [
        "bonne",
        "correctchoice",
        "mauvaise",
        "wrongchoice"
    ],
    "tex_macros_choice_correct": [
        "bonne",
        "correctchoice"
    ],
    "tex_macros_lastchoices": [
        "alafin",
        "lastchoices"
    ],
    "ticket_length": 64
}
CONFIG: types.conf_t = tp.cast(types.conf_t, Config(CONFIG_DEFAULT))


CONFIG_DESC_MD = {
    "base_url":
    (False, True,
     "base URL of your web site"),
    ###
    "auth_account_creation_enabled":
    (False, True,
     "true if account creation is allowed via the web UI"),
    ###
    "auth_cas_enabled":
    (False, True,
     "true if authentication through the CAS server is enabled"),
    ###
    "auth_local_enabled":
    (False, True,
     "true if local system authentication is enabled"),
    ###
    "cas_server":
    (False, True,
     "URL of the CAS server"),
    ###
    "cas_server_name":
    (False, True,
     "a description of the CAS server (e.g. Arkham university CAS server)"),
    ###
    "cas_version":
    (False, True,
     "version of the CAS server (2 or 3)"),
    ###
    "date_format":
    (False, True,
     "date format (null for default format) in the babel package syntax"),
    ###
    "date_locale":
    (False, True,
     "date locale in the babel package syntax"),
    ###
    "datetime_format":
    (False, True,
     "datetime format (null for default format) in the babel package syntax"),
    ###
    "db_host":
    (True, True,
     "name/IP of the host hosting the database server"),
    ###
    "db_name":
    (True, True,
     "name of the database"),
    ###
    "db_password":
    (True, True,
     "password of the database user"),
    ###
    "db_port":
    (True, True,
     "network port used by the database server"),
    ###
    "db_user":
    (False, True,
     "database user"),
    ###
    "debug":
    (False, True,
     "if true exception tracebacks will be displayed in web browser"),
    ###
    "icon_size":
    (False, True,
     "size of icons in the web interface (24, 32, 48, or 64)"),
    ###
    "inbox_dir":
    (False, True,
     "directory in which user PDF annotated sheets will be stored"),
    ###
    "json_file_pack":
    (True, False,
     "json file of a question pack in an MCQ or exercise directory"),
    ###
    "key_qst_next":
    (False, True,
     "key used in the web interface to move to the next question"),
    ###
    "key_qst_prev":
    (False, True,
     "key used in the web interface to move to the previous question"),
    ###
    "key_switch_mode":
    (False, True,
     "key used in the web interface for switching fillin mode"),
    ###
    "lang":
    (False, True,
     "language of the web interface"),
    ###
    "log_file":
    (True, False,
     "path of the log file used to store compilation result"),
    ###
    "mails_dir":
    (False, True,
     "directory in which mails are stored"),
    ###
    "projects_dir":
    (False, True,
     "directory in which user projects will be stored"),
    ###
    "password_ticket_validity":
    (False, True,
     "lifespan of a password regeneration ticket, in seconds"),
    ###
    "root_path":
    (False, True,
     "root path of webamc on the webserver"),
    ###
    "secret_key":
    (False, True,
     "secret key of webamc service"),
    ###
    "service_name":
    (False, True,
     "human readable name of the service that will appear in the UI"),
    ###
    "smtp_auth":
    (False, True,
     "true if the SMTP server requires authentication"),
    ###
    "smtp_eaddr_from":
    (False, True,
     "email address that will be appear in the Form field of mails sent"),
    ###
    "smtp_host":
    (False, True,
     "name/IP of the host hosting the SMTP server"),
    ###
    "smtp_password":
    (False, True,
     "password used to connect to the SMTP server"),
    ###
    "smtp_port":
    (False, True,
     "port the SMTP server listens to"),
    ###
    "smtp_user":
    (False, True,
     "user account used to connect to the SMTP server"),
    ###
    "tex2pdf_exe":
    (True, False,
     "name or absolute path of the tex-to-pdf compiler"),
    ###
    "tex2pdf_exe_args":
    (True, False,
     "list of arguments that must be passed to tex2pdf_exe"),
    ###
    "tex_envs_choices":
    (True, False,
     "tex environments for choice lists"),
    ###
    "tex_envs_question":
    (True, False,
     "tex environments for questions"),
    ###
    "tex_envs_question_mult":
    (True, False,
     "tex environments for question with multiple correct choices"),
    ###
    "tex_file_exercise":
    (True, False,
     "tex file of an exercise directory"),
    ###
    "tex_file_header":
    (True, False,
     "tex file with headers to be used for all tex files of a directory"),
    ###
    "tex_file_mcq":
    (True, False,
     "tex file of an MCQ directory"),
    ###
    "tex_file_question_prefix":
    (True, False,
     "prefix (possibly empty) of tex files containing questions"),
    ###
    "tex_file_webamc":
    (True, False,
     "tex file in a directory containing webamc meta-data"),
    ###
    "tex_macros_choice":
    (True, False,
     "tex macros for choices"),
    ###
    "tex_macros_choice_correct":
    (True, False,
     "tex macros for correct choices"),
    ###
    "tex_macros_lastchoices":
    (True, False,
     "tex macros for last choices"),
    ###
    "ticket_length":
    (False, True,
     "length of tickets (e.g., password change ticket) generated"),
}
