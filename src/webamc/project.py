#!/usr/bin/env python3

import string
import shutil
import subprocess
import sqlite3
import zipfile
import hashlib
from pathlib import Path

from webamc.all import *
from webamc.util import io
from webamc.db import op, tables, col_types as ct


action_t = tp.Literal[
    "analyse-answer-sheets",
    "annotate",
    "associate-automatic",
    "associate-manual",
    "associate-manual-prepare",
    "clean-files",
    "compile",
    "compute-scores",
    "delete",
    "export-scores",
    "extract-layout-data",
    "extract-scoring-data",
    "extract-answer-sheets",
    "generate-sheets",
    "new",
    "send-annotated-sheets",
    "upload-answer-sheets",
    "upload-project-archive",
    "upload-student-list"
]

data_t = tp_ext.TypedDict(
    "data_t", {
        "code": str,
        "title": str,
        "amc_code": str,
        "id_key": str,
        "threshold": float,
        "copies": int,
        "eaddr": str
    }
)

DEFAULT_DATA: data_t = {
    "code": "",
    "title": "",
    "amc_code": "",
    "id_key": "",
    "threshold": 0.5,
    "copies": 10,
    "eaddr": ""
}

action_params_t = tp_ext.TypedDict(
    "action_params_t", {
        "copy": None | int,
        "student": None | int,
        "id": None | str
    },
    total=False
)

file_id_t = tp.Literal[
    "answer_sheets",
    "project_archive",
    "student_list"
]

status_t = tp_ext.TypedDict(
    "status_t", {
        "actions": dict[action_t, bool],
        "history": list[tuple[action_t, datetime.datetime, bool]]
    }
)

association_t = dict[
    tuple[int, int],  # (student, copy)
    tuple[None | str, None | str, None | str] # (auto, manual, name-file)
]

student_t = tuple[str, str]

CSV_DELIMITER = ";"

CSV_STUDENT_LIST = "students.csv"
DATA_CALAGE = "calage.xy"
DIR_CR = "cr"
DIR_DATA = "data"
DIR_COPIES = "copies"
DIR_OUTBOX = "outbox"
DIR_SCANS = "scans"
DIR_TEX = "tex"
JSON_DATA = "data.json"
JSON_STATUS = "status.json"
LOG_COMPILATION = "compilation.log"
LOG_LAYOUT_DATA_EXTRACTION = "layout-data-extraction.log"
LOG_ANSWER_SHEETS_EXTRACTION = "answer-sheets-extraction.log"
LOG_ANSWER_SHEETS_ANALYSIS = "answer-sheets-analysis.log"
LOG_SCORES_COMPUTATION = "scores-computation.log"
LOG_SCORES_EXPORT = "score-export.log"
LOG_SCORING_DATA_EXTRACTION = "scoring-data-extraction.log"
LOG_AUTOMATIC_SHEETS_ASSOCIATION = "automatic-sheets-association.log"
LOG_ANNOTATION = "annotation.log"
LOG_MANUAL_SHEETS_ASSOCIATION = "manual-sheets-association.log"
LOG_SHEETS_GENERATION = "sheets-generation.log"
ODS_SCORES = "scores.ods"
PDF_CORRECTION = "correction.pdf"
PDF_ANSWER_SHEETS = "answer-sheets.pdf"
PDF_SUBJECT = "subject.pdf"
SQL_ASSOCIATION = "association.sqlite"
TEX_MAIN = "main.tex"
ZIP_ANNOTATED_SHEETS = "annotated-sheets.zip"
ZIP_SHEETS = "sheets.zip"
ZIP_TEX = "tex.zip"

ACTION_FILES: dict[action_t, list[str]] = {
    "annotate": [ZIP_ANNOTATED_SHEETS],
    "compile": [PDF_SUBJECT, PDF_CORRECTION],
    "export-scores": [ODS_SCORES],
    "generate-sheets": [ZIP_SHEETS],
    "upload-answer-sheets": [PDF_ANSWER_SHEETS],
    "upload-project-archive": [ZIP_TEX],
    "upload-student-list": [CSV_STUDENT_LIST]
}

ACTION_DEP: dict[
    action_t, list[tuple[tp.Literal["action", "file", "data"], str]]
] = {
    "analyse-answer-sheets": [
        ("action", "extract-answer-sheets")
    ],
    "annotate": [
        ("action", "export-scores"),
        ("data", "id_key")
    ],
    "associate-automatic": [
        ("action", "compute-scores"),
        ("file", CSV_STUDENT_LIST),
        ("data", "amc_code"),
        ("data", "id_key")
    ],
    "associate-manual-prepare": [
        ("action", "compute-scores"),
        ("file", CSV_STUDENT_LIST),
        ("data", "id_key")
    ],
    "compile": [
        ("file", ZIP_TEX)
    ],
    "compute-scores": [
        ("action", "extract-scoring-data")
    ],
    "export-scores": [
        ("action", "compute-scores"),
        ("file", CSV_STUDENT_LIST)
    ],
    "extract-answer-sheets": [
        ("action", "extract-layout-data"),
        ("file", PDF_ANSWER_SHEETS)
    ],
    "extract-layout-data": [
        ("action", "compile")
    ],
    "extract-scoring-data": [
        ("action", "analyse-answer-sheets")
    ],
    "generate-sheets": [
        ("action", "extract-layout-data")
    ],
    "send-annotated-sheets": [
        ("action", "annotate"),
        ("data", "eaddr")
    ]
}

NOT_CLEANABLE = [
    CSV_STUDENT_LIST,
    DATA_CALAGE,
    JSON_DATA,
    JSON_STATUS,
    ODS_SCORES,
    PDF_CORRECTION,
    PDF_ANSWER_SHEETS,
    PDF_SUBJECT,
    DIR_TEX,
    DIR_OUTBOX,
    ZIP_TEX,
    ZIP_SHEETS,
    ZIP_ANNOTATED_SHEETS
]

mail_data_t = tp.TypedDict(
    "mail_data_t", {
        "title": str,
        "date": datetime.datetime,
        "sender": str,
        "project": str
    }
)
MAIL_DATA_FILE = "data.json"
MAIL_PDF_FILE = "sheet.pdf"


def get_usr_inbox_dir(usr_eaddr: str) -> str:
    h = hashlib.sha1(usr_eaddr.encode()).hexdigest()
    d1 = h[0:2]
    d2 = h[2:4]
    return os.path.join(config.CONFIG["inbox_dir"], d1, d2, usr_eaddr)


def inbox_empty(usr_eaddr: str) -> bool:
    idir = get_usr_inbox_dir(usr_eaddr)
    return not os.path.isdir(idir) or os.listdir(idir) == list()


def check_pcode(pcode: str) -> bool:
    allowed = string.ascii_letters + string.digits + "-_"
    return (
        pcode != ""
        and all(c in allowed for c in pcode)
    )


def check_project_title(project_title: str) -> bool:
    return any(x != " " for x in project_title)


def get_path(ucode: str, pcode: str = "", *name: str) -> str:
    join = os.path.join
    if pcode == "":
        return join(config.CONFIG["projects_dir"], ucode)
    return join(get_path(ucode), pcode, *name)


def list_projects(ucode: str) -> list[tuple[str, str]]:
    try:
        result = list()
        udir = get_path(ucode)
        for p in sorted(os.listdir(udir)):
            pdir = os.path.join(udir, p)
            status_file = os.path.join(pdir, JSON_STATUS)
            if os.path.isfile(status_file):
                result.append((p, pdir))
        return result
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return list()


def run_cmd(
        args: list[str],
        exec_dir: str,
        log_file: str
) -> types.oper_code_t:
    exec_path = shutil.which("auto-multiple-choice")
    if exec_path is None:
        return "err_amc_not_installed"
    args.insert(0, exec_path)
    cur_dir = os.getcwd()
    os.chdir(exec_dir)
    with open(log_file, "a") as fd:
        fd.write(79 * "#" + "\n")
        fd.write("# date:\n")
        fd.write(f"#    {str(datetime.datetime.now())}\n")
        fd.write("# execution dir:\n")
        fd.write(f"#    {os.getcwd()}\n")
        fd.write("# command:\n")
        fd.write(f"#    {' '.join(args)}\n")
        fd.write(79 * "#" + "\n\n")
    with open(log_file, "a") as fd:
        proc_result = subprocess.run(
            args,
            input="",
            stdout=fd,
            stderr=fd
        )
        fd.write("\n\n\n")
    os.chdir(cur_dir)
    if proc_result.returncode == 0:
        return "succ"
    return "err_check_log_file"


def get_status(ucode: str, pcode: str) -> status_t:
    json_file = get_path(ucode, pcode, JSON_STATUS)
    with open(json_file) as fd:
        return tp.cast(status_t, json.loads(fd.read()))


def get_status_and_files(
        ucode: str,
        pcode: str
) -> tuple[status_t, list[file_id_t]]:
    files: list[file_id_t] = list()
    file_list: list[tuple[file_id_t, str]] = [
            ("answer_sheets", PDF_ANSWER_SHEETS),
            ("project_archive", os.path.join(DIR_TEX, TEX_MAIN)),
            ("student_list", CSV_STUDENT_LIST)
    ]
    for file_id, file_name in file_list:
        if os.path.isfile(get_path(ucode, pcode, file_name)):
            files.append(file_id)
    json_file = get_path(ucode, pcode, JSON_STATUS)
    return get_status(ucode, pcode), files


def json_serialise(obj: object) -> str:
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError


def update_status(ucode: str, pcode: str, status: status_t) -> None:
    to_write = json.dumps(status, indent=3, default=json_serialise)
    with open(get_path(ucode, pcode, JSON_STATUS), "w") as fd:
        fd.write(to_write)


def prerequisites(
        ucode: str,
        pcode: str,
        action: action_t
) -> tuple[data_t, status_t, list[action_t], set[str], set[str]]:
    status = get_status_and_files(ucode, pcode)[0]
    data = get_data(ucode, pcode)
    pre_actions: list[action_t] = [action]
    pre_files: set[str] = set()
    pre_data: set[str] = set()
    todo = [action]
    while todo != list():
        next_todo = todo[0]
        del todo[0]
        new_pre_actions = list()
        for t, dep in ACTION_DEP.get(next_todo, list()):
            if t == "action":
                act = tp.cast(action_t, dep)
                if not status["actions"][act]:
                    new_pre_actions.append(act)
            elif t == "file":
                if not os.path.isfile(get_path(ucode, pcode, dep)):
                    pre_files.add(dep)
            elif t == "data":
                val = data[dep]  # type: ignore
                if val == "" or val is None:
                    pre_data.add(dep)
        pre_actions = new_pre_actions + pre_actions
        todo = todo + list(new_pre_actions)
    return data, status, pre_actions, pre_files, pre_data


def check_action_dependency(
        ucode: str,
        pcode: str,
        action: action_t
) -> tuple[
    data_t,
    status_t,
    list[action_t],
    None | tuple[list[types.oper_code_t], list[str]]
]:
    data, status, pre_actions, pre_files, pre_data = prerequisites(
        ucode,
        pcode,
        action
    )
    errs: list[types.oper_code_t] = list()
    ids = list()
    for f in pre_files:
        errs.append("err_missing_file")
        label_id = "label-file-" + f.replace(".", "-")
        ids.append(label_id)
    for p in pre_data:
        errs.append("err_missing_or_invalid_parameter")
        ids.append(p)
    if errs != list():
        return data, status, pre_actions, (errs, ids)
    return data, status, pre_actions, None


def action(
        ucode: str,
        pcode: str,
        action: action_t,
        params: action_params_t
) -> tuple[list[types.oper_code_t], tp.Any]:
    def path(name: str = "", *args: str) -> str:
        return get_path(ucode, pcode, name, *args)

    def pre_annotate() -> None:
        pdir = get_path(ucode, pcode)
        pdf_dir = os.path.join(pdir, DIR_CR, "corrections", "pdf")
        for entry in os.listdir(pdf_dir):
            entry_abs = os.path.join(pdf_dir, entry)
            if os.path.isfile(entry_abs) and entry_abs.endswith(".pdf"):
                os.remove(entry_abs)

    def pre_export_scores() -> None:
        assoc_file = get_path(ucode, pcode, DIR_DATA, SQL_ASSOCIATION)
        if os.path.isfile(assoc_file):
            conn = sqlite3.Connection(assoc_file)
            cur = conn.cursor()
            q = "delete from association_variables where name = 'key_in_list'"
            cur.execute(q)
            q = "insert into association_variables values ('key_in_list', ?)"
            cur.execute(q, (data["id_key"], ))
            conn.commit()
            conn.close()

    def post_generate_sheets() -> None:
        zip_pdfs(ucode, pcode, ZIP_SHEETS, DIR_COPIES)

    def post_annotate() -> None:
        pdf_dir = os.path.join(DIR_CR, "corrections", "pdf")
        zip_pdfs(ucode, pcode, ZIP_ANNOTATED_SHEETS, pdf_dir)

    def post_send_annotated_sheets() -> None:
        assert status is not None
        for f in os.listdir(path(DIR_OUTBOX)):
            m = re.match(r".\d+_\d+-(.+).pdf", f)
            if m is None or m.groups()[0] not in eaddrs:
                continue
            eaddr = eaddrs[m.groups()[0]]
            try:
                ct.Eaddr.val_chk(eaddr)
            except ValueError:
                continue
            mdir = os.path.join(get_usr_inbox_dir(eaddr), ucode, pcode)
            Path(mdir).mkdir(parents=True, exist_ok=True)
            pdf_file = os.path.join(mdir, MAIL_PDF_FILE)
            data_file = os.path.join(mdir, MAIL_DATA_FILE)
            if os.path.isfile(pdf_file):
                os.remove(pdf_file)
            os.link(os.path.join(path(DIR_OUTBOX), f), pdf_file)
            with open(data_file, "w") as fd:
                mail_data: mail_data_t = {
                    "title": get_project_title(data),
                    "date": datetime.datetime.now(),
                    "sender": ucode,
                    "project": pcode
                }
                to_write = json.dumps(
                    mail_data,
                    indent=3,
                    default=json_serialise
                )
                fd.write(to_write)

    def clean_files() -> types.oper_code_t:
        root = path()
        to_keep = [os.path.join(root, x) for x in NOT_CLEANABLE]
        for dir_name, sub_dir_names, file_names in os.walk(root):
            if any(dir_name.startswith(x) for x in to_keep):
                continue
            for file_name in file_names:
                abs_path = os.path.join(dir_name, file_name)
                if abs_path not in to_keep:
                    os.remove(abs_path)
        status, _ = get_status_and_files(ucode, pcode)
        status["actions"] = {
            act: st if act in {"compile", "new"} else False
            for act, st in status["actions"].items()
        }
        update_status(ucode, pcode, status)
        return "succ"

    def delete() -> types.oper_code_t:
        shutil.rmtree(path())
        return "succ"

    def new() -> types.oper_code_t:
        if not check_pcode(pcode):
            return "err_invalid_project_code"
        udir = get_path(ucode)
        pdir = get_path(ucode, pcode)
        try:
            Path(udir).mkdir(parents=True, exist_ok=True)
            dirs = [
                pdir,
                os.path.join(pdir, DIR_COPIES),
                os.path.join(pdir, DIR_CR),
                os.path.join(pdir, DIR_CR, "corrections"),
                os.path.join(pdir, DIR_CR, "corrections", "jpg"),
                os.path.join(pdir, DIR_CR, "corrections", "pdf"),
                os.path.join(pdir, DIR_CR, "diagnostic"),
                os.path.join(pdir, DIR_CR, "zooms"),
                os.path.join(pdir, DIR_DATA),
                os.path.join(pdir, DIR_OUTBOX),
                os.path.join(pdir, "exports"),
                os.path.join(pdir, DIR_SCANS)
            ]
            for d in dirs:
                if os.path.exists(d):
                    return "err_project_already_exists"
                print(d)
                Path(d).mkdir(parents=True)
            actions: dict[action_t, bool] = {
                a: False for a in types.literal_type_values(action_t)
            }
            actions["new"] = True
            status: status_t = {
                "actions": actions,
                "history": []
            }
            update_status(ucode, pcode, status)
            data = DEFAULT_DATA
            data["code"] = pcode
            update_data(ucode, tp.cast(dict[str, str], data))
            return "succ_project_created"
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            return "err_io"

    # some actions handled specifically
    funs = {
        "new": new,
        "clean-files": clean_files,
        "delete": delete
    }
    if action in funs:
        return [funs[action]()], list()

    # check dependencies
    data, status, pre_actions, check_result = check_action_dependency(
        ucode,
        pcode,
        action
    )
    if check_result is not None:
        return check_result

    action = pre_actions[0]
    next_action = None if len(pre_actions) < 2 else pre_actions[1]

    action_pre = {
        "annotate": pre_annotate,
        "export-scores": pre_export_scores
    }
    action_post = {
        "annotate": post_annotate,
        "generate-sheets": post_generate_sheets,
        "send-annotated-sheets": post_send_annotated_sheets
    }

    # pre-treatment
    if action in action_pre:
        action_pre[action]()

    assert status is not None
    if action == "analyse-answer-sheets":
        scan_dir = path(DIR_SCANS)
        args = [
            "analyse",
            "--project", path(),
        ] + [
            os.path.join(scan_dir, x)
            for x in sorted(os.listdir(scan_dir))
            if x.endswith(".jpg")
        ]
        run_dir = path()
        log_file = path(LOG_ANSWER_SHEETS_ANALYSIS)

    elif action == "annotate":
        args = [
            "annotate",
            "--project", path(),
            "--names-file", path(CSV_STUDENT_LIST),
            "--association-key", data["id_key"],
            "--corrected", path(PDF_CORRECTION),
            "--subject", path(PDF_SUBJECT),
            "--compose", "1"
        ]
        run_dir = path()
        log_file = path(LOG_ANNOTATION)

    elif action == "associate-automatic":
        args = [
            "association-auto",
            "--data", path(DIR_DATA),
            "--notes-id", data["amc_code"],
            "--liste", path(CSV_STUDENT_LIST),
            "--liste-key", data["id_key"]
        ]
        run_dir = path()
        log_file = path(LOG_AUTOMATIC_SHEETS_ASSOCIATION)

    elif action == "associate-manual":        
        args = [
            "association",
            "--data", path(DIR_DATA),
            "--set",
            "--student", str(params.get("student")),
            "--copy", str(params.get("copy"))
        ]
        id_ = params.get("id")
        if id_ != "" and id_ is not None:
            args += [
                "--id", str(id_)
            ]
        run_dir = path()
        log_file = path(LOG_MANUAL_SHEETS_ASSOCIATION)

    elif action == "compile":
        args = [
            "prepare",
            "--mode", "s",
            "--prefix", path(),
            "--data", path(DIR_DATA),
            "--out-sujet", path(PDF_SUBJECT),
            "--out-corrige", path(PDF_CORRECTION),
            "--out-calage", path(DATA_CALAGE),
            "--n-copies", str(data["copies"]),
            TEX_MAIN
        ]
        run_dir = path(DIR_TEX)
        log_file = path(LOG_COMPILATION)

    elif action == "compute-scores":
        args = [
            "note",
            "--seuil", str(data["threshold"]),
            "--data", path(DIR_DATA),
        ]
        run_dir = path()
        log_file = path(LOG_SCORES_COMPUTATION)

    elif action == "export-scores":
        args = [
            "export",
            "--data", path(DIR_DATA),
            "--fich-noms", path(CSV_STUDENT_LIST),
            "--module", "ods",
            "--option", "stats=true",
            "--option", f"nom={get_project_title(data)}",
            "-o", path(ODS_SCORES)
        ]
        run_dir = path()
        log_file = path(LOG_SCORES_EXPORT)

    elif action == "extract-scoring-data":
        args = [
            "prepare",
            "--mode", "b",
            "--prefix", path(),
            "--data", path(DIR_DATA),
            TEX_MAIN
        ]
        run_dir = path(DIR_TEX)
        log_file = path(LOG_SCORING_DATA_EXTRACTION)

    elif action == "extract-layout-data":
        args = [
            "meptex",
            "--src", path(DATA_CALAGE),
            "--data", path(DIR_DATA)
        ]
        run_dir = path()
        log_file = path(LOG_LAYOUT_DATA_EXTRACTION)

    elif action == "extract-answer-sheets":
        args = [
            "getimages",
            "--copy-to", path(DIR_SCANS),
            path(PDF_ANSWER_SHEETS)
        ]
        run_dir = path()
        log_file = path(LOG_ANSWER_SHEETS_EXTRACTION)

    elif action == "generate-sheets":
        name, _ = os.path.splitext(PDF_SUBJECT)
        args = [
            "imprime",
            "--sujet", path(PDF_SUBJECT),
            "--data", path(DIR_DATA),
            "--method", "file",
            "--output", path(DIR_COPIES, f"{name}-%e.pdf")
        ]
        run_dir = path()
        log_file = path(LOG_SHEETS_GENERATION)

    elif action == "send-annotated-sheets":
        col_id_key = data["id_key"]
        col_eaddr = data["eaddr"]
        with open(path(CSV_STUDENT_LIST)) as fd:
            try:
                eaddrs = {
                    row[col_eaddr].replace("@", "_"): row[col_eaddr]
                    for row in csv.DictReader(fd, delimiter=CSV_DELIMITER)
                }
            except KeyError:
                return ["err_invalid_csv_file"], list()
        args = [
            "annotate",
            "--project", path(),
            "--names-file", path(CSV_STUDENT_LIST),
            "--association-key", str(col_id_key),
            "--corrected", path(PDF_CORRECTION),
            "--subject", path(PDF_SUBJECT),
            "--compose", "1",
            "--csv-build-name", f"({col_eaddr})",
            "--pdf-dir", path(DIR_OUTBOX)
        ]
        run_dir = path()
        log_file = os.devnull

    code = run_cmd(args, run_dir, log_file)
    success = code.startswith("succ")
    status["actions"][action] = success
    status["history"].append((action, datetime.datetime.now(), success))
    update_status(ucode, pcode, status)

    # post-treatment
    if success and action in action_post:
        action_post[action]()

    return [code], { "next_action": next_action }


def zip_pdfs(
        ucode: str,
        pcode: str,
        zip_file: str,
        pdf_dir: str
) -> None:
    with zipfile.ZipFile(get_path(ucode, pcode, zip_file), "w") as zf:
        pdf_dir = get_path(ucode, pcode, pdf_dir)
        for entry in os.listdir(pdf_dir):
            entry_abs = os.path.join(pdf_dir, entry)
            if os.path.isfile(entry_abs) and entry_abs.endswith(".pdf"):
                zf.write(entry_abs, arcname=os.path.join(pcode, entry))


def action_upload(
        ucode: str,
        pcode: str,
        action: action_t,
        file_name: str
) -> types.oper_code_t:
    if action == "upload-answer-sheets":
        dst = PDF_ANSWER_SHEETS
    elif action == "upload-student-list":
        with open(file_name) as fd:
            try:
                read = csv.DictReader(fd, delimiter=CSV_DELIMITER)
                if read.fieldnames is None or "name" not in read.fieldnames:
                    return "err_invalid_csv_file"
            except UnicodeDecodeError:
                return "err_invalid_csv_file"
        dst = CSV_STUDENT_LIST
    elif action == "upload-project-archive":
        try:
            with zipfile.ZipFile(file_name) as zf:
                if os.path.join(DIR_TEX, TEX_MAIN) not in zf.namelist():
                    return "err_invalid_tex_archive"
                in_tex_dir = sorted(
                    x for x in sorted(zf.namelist())
                    if x.startswith(DIR_TEX + "/")
                )
                for x in in_tex_dir:
                    zf.extract(
                        member=x,
                        path=get_path(ucode, pcode)
                    )
        except zipfile.BadZipFile:
            return "err_not_a_zip_file"
        dst = ZIP_TEX
    shutil.copyfile(file_name, get_path(ucode, pcode, dst))
    status = get_status(ucode, pcode)
    status["actions"][action] = True
    status["history"].append((action, datetime.datetime.now(), True))
    update_status(ucode, pcode, status)
    return "succ"
    

def list_files(
        ucode: str,
        pcode: str,
        action: action_t
) -> list[tuple[str, None | datetime.datetime]]:
    result = list()
    pdir = get_path(ucode, pcode)
    for f in ACTION_FILES.get(action, list()):
        path = get_path(ucode, pcode, f)
        if not os.path.isfile(path):
            fdata: None | datetime.datetime = None
        else:
            fdata = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        result.append((f, fdata))
    return result


def get_file(ucode: str, pcode: str, name: str) -> None | tuple[str, str]:
    path = get_path(ucode, pcode, name)
    if not os.path.isfile(path):
        return None
    return path, f"{pcode}-{name}"


def get_mail_pdf(eaddr: str, ucode: str, pcode: str) -> None | tuple[str, str]:
    path = os.path.join(get_usr_inbox_dir(eaddr), ucode, pcode, MAIL_PDF_FILE)
    if not os.path.isfile(path):
        return None
    return path, pcode


def list_associations(ucode: str, pcode: str) -> association_t:
    assoc_file = get_path(ucode, pcode, DIR_DATA, SQL_ASSOCIATION)
    result = dict()
    if os.path.isfile(assoc_file):
        conn = sqlite3.Connection(assoc_file)
        cur = conn.cursor()
        q = "select student, copy, manual, auto from association_association"
        for student, copy, manual, auto in cur.execute(q):
            name = os.path.join(DIR_CR, f"name-{student}-{copy}.jpg")
            name_file = get_path(ucode, pcode, name)
            exists = os.path.isfile(name_file)
            result[int(student), int(copy)] = (
                manual, auto, name if exists else None
            )
        conn.close()
    for x in os.listdir(get_path(ucode, pcode, DIR_CR)):
        m = re.match(r"name-(\d+)-(\d+).jpg", x)
        if m:
            student = int(m.group(1))
            copy = int(m.group(2))
            if (student, copy) not in result:
                result[student, copy] = (
                    None,
                    None,
                    os.path.join(DIR_CR, x)
                )
    return result


def list_students_from_csv(ucode: str, pcode: str) -> list[student_t]:
    data = get_data(ucode, pcode)
    student_file = get_path(ucode, pcode, CSV_STUDENT_LIST)
    if not os.path.isfile(student_file):
        return list()
    with open(student_file) as fd:
        id_key = data["id_key"]
        try:
            result = [
                (row[id_key], row["name"])
                for row in csv.DictReader(fd, delimiter=CSV_DELIMITER)
            ]
        except KeyError:
            return list()
        result.sort(key=lambda id_name: id_name[1])
    return result


def list_inbox(eaddr: str) -> list[mail_data_t]:
    idir = get_usr_inbox_dir(eaddr)
    result = list()
    for udir in os.listdir(idir):
        udir_path = os.path.join(idir, udir)
        if not os.path.isdir(udir_path):
            continue
        for pdir in os.listdir(udir_path):
            pdir_path = os.path.join(udir_path, pdir)
            if not os.path.isdir(pdir_path):
                continue
            data_file = os.path.join(pdir_path, MAIL_DATA_FILE)
            pdf_file = os.path.join(pdir_path, MAIL_PDF_FILE)
            if os.path.isfile(data_file) and os.path.isfile(pdf_file):
                with open(data_file) as fd:
                    mapper = {
                        "date": datetime.datetime.fromisoformat
                    }
                    data: mail_data_t = tp.cast(mail_data_t, {
                        k: mapper[k](v) if k in mapper else v
                        for k, v in json.loads(fd.read()).items()
                    })
                    result.append(data)
    return result


def get_data(ucode: str, pcode: str) -> data_t:
    with open(get_path(ucode, pcode, JSON_DATA)) as fd:
        return tp.cast(data_t, json.loads(fd.read()))


def update_data(
        ucode: str,
        data: dict[str, str]
) -> tuple[types.oper_code_t, list[str]]:
    data_typed: data_t = tp.cast(data_t, dict(DEFAULT_DATA))
    ids = list()
    for k in data_typed.keys():
        if k in data:
            typ = tp.get_type_hints(data_t)[k]
            try:
                data_typed[k] = typ(data[k])  # type: ignore
            except ValueError:
                ids.append(k)
    if ids != list():
        return "err_missing_or_invalid_parameter", ids
    with open(get_path(ucode, data_typed["code"], JSON_DATA), "w") as fd:
        fd.write(json.dumps(data_typed, indent=3))
    return "succ", list()


def get_project_title(data: data_t) -> str:
    if data["title"] == "":
        return data["code"]
    return data["title"]
