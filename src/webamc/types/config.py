import json
import typing as tp
import typing_extensions as tp_ext
from pydantic import TypeAdapter, ValidationError


lang_t = tp.Literal[
    "en",
    "fr"
]

class config_t(tp_ext.TypedDict):
    base_url: str
    auth_account_creation_enabled: bool
    auth_cas_enabled: bool
    auth_local_enabled: bool
    cas_server: str
    cas_server_name: str
    cas_version: int
    date_format: None | str
    date_locale: str
    datetime_format: None | str
    db_host: str
    db_name: str
    db_password: str
    db_port: None | int
    db_user: str
    debug: bool
    dev: bool
    exam_autosave_period: int
    icon_size: int
    json_file_pack: str
    key_qst_next: str
    key_qst_prev: str
    key_switch_mode: str
    lang: lang_t
    log_file: None | str
    mails_dir: None | str
    password_ticket_validity: int
    projects_dir: str
    root_path: str
    secret_key: str
    service_name: str
    smtp_auth: bool
    smtp_eaddr_from: str
    smtp_host: str
    smtp_password: str
    smtp_port: int
    smtp_ssl: bool
    smtp_user: str
    tex2pdf_exe: str
    tex2pdf_exe_args: list[str]
    tex_envs_choices: list[str]
    tex_envs_question: list[str]
    tex_envs_question_mult: list[str]
    tex_file_exercise: str
    tex_file_header: str
    tex_file_mcq: str
    tex_file_question_prefix: str
    tex_file_webamc: str
    tex_macros_choice: list[str]
    tex_macros_choice_correct: list[str]
    tex_macros_lastchoices: list[str]
    ticket_length: int


def check_config(conf: str) -> config_t:
    try:
        parsed = json.loads(conf)
        TypeAdapter(config_t).validate_python(parsed)
    except (ValidationError, json.decoder.JSONDecodeError) as ex:
        raise ValueError from ex
    return tp.cast(config_t, parsed)
