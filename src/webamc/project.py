#!/usr/bin/env python3

import string
import shutil
import subprocess
import sqlite3
import zipfile
import hashlib
from pathlib import Path
from sqlalchemy.orm.session import Session as ORMSession

from webamc.all import *
from webamc.util import io, fmt
from webamc.db import col_types as ct, tables


action_t = tp.Literal[
    "analyse",
    "associate-automatic",
    "associate-manual-prepare",
    "associate-manual",
    "clean-associations",
    "compile",
    "delete",
    "export-scores",
    "new",
    "upload-answer-sheets",
    "upload-project-archive",
    "send-annotated-sheets"
]

cmd_t = tp.Literal[
    "analyse-answer-sheets",
    "annotate",
    "associate-automatic",
    "associate-manual",
    "clean-associations",
    "compile",
    "compute-scores",
    "export-scores",
    "extract-layout-data",
    "extract-scoring-data",
    "extract-answer-sheets",
    "generate-sheets",
    "send-annotated-sheets"
]
data_t = tp_ext.TypedDict(
    "data_t", {
        "assoc_attr": int,
        "code": str,
        "title": str,
        "amc_code": str,
        "threshold": float,
        "copies": int,
        "groups": list[int]
    }
)
action_params_t = tp_ext.TypedDict(
    "action_params_t", {
        "copy": None | int,
        "student": None | int,
        "id": None | str
    },
    total=False
)
association_t = dict[
    tuple[int, int],  # (student, copy)
    tuple[None | str, None | str, None | str] # (auto, manual, name-file)
]
dir_t = tp.Literal[
    "copies",
    "cr",
    "data",
    "outbox",
    "scans",
    "tex"
]
file_t = tp.Literal[
    "csv-list",
    "json-status",
    "log-webamc",
    "ods-scores",
    "pdf-answer-sheets",
    "pdf-correction",
    "pdf-subject",
    "sqlite-association",
    "sqlite-capture",
    "tex-main",
    "xy-calage",
    "zip-annotated-sheets",
    "zip-sheets",
    "zip-tex"
]
file_status_t = tp.TypedDict(
    "file_status_t", {
        "exists": bool,
        "size": None | int,
        "date": None | datetime.datetime
    }
)
status_t = tp_ext.TypedDict(
    "status_t", {
        "done": dict[action_t, bool],
        "doable": dict[action_t, tuple[bool, list[tuple[str, str]]]],
        "history": list[tuple[action_t, datetime.datetime, bool]],
        "data": data_t,
        "files": dict[file_t, file_status_t]
    }
)
mail_data_t = tp.TypedDict(
    "mail_data_t", {
        "title": str,
        "date": datetime.datetime,
        "sender": str,
        "project": str
    }
)

ACTION_FILES: dict[action_t, list[file_t]] = {
    "compile": [
        "pdf-subject",
        "pdf-correction",
        "zip-sheets"
    ],
    "export-scores": [
        "ods-scores",
        "zip-annotated-sheets"
    ],
    "upload-answer-sheets": [
        "pdf-answer-sheets"
    ],
    "upload-project-archive": [
        "zip-tex"
    ]
}
ACTION_DEP: dict[
    action_t,
    list[
        tuple[tp.Literal["action"], action_t]
        | tuple[tp.Literal["file"], file_t]
        | tuple[tp.Literal["data"], str]
    ]
] = {
    "analyse": [
        ("action", "upload-answer-sheets"),
        ("file", "pdf-answer-sheets")
    ],
    "associate-automatic": [
        ("data", "amc_code"),
        ("action", "analyse")
    ],
    "associate-manual-prepare": [
        ("action", "analyse")
    ],
    "associate-manual": [
        ("action", "analyse")
    ],
    "clean-associations": [
        ("action", "analyse")
    ],
    "compile": [
        ("action", "upload-project-archive"),
        ("file", "zip-tex"),
        ("data", "copies")
    ],
    "delete": [
        ("action", "new")
    ],
    "export-scores": [
        ("action", "analyse")
    ],
    "new": [
    ],
    "upload-answer-sheets": [
        ("action", "compile")
    ],
    "upload-project-archive": [
        ("action", "new")
    ],
    "send-annotated-sheets": [
        ("action", "export-scores")
    ]
}
ACTION_COMMANDS: dict[action_t, list[cmd_t]] = {
    "analyse": [
        "extract-answer-sheets",
        "extract-scoring-data",
        "analyse-answer-sheets",
        "compute-scores"
    ],
    "associate-automatic": [
        "associate-automatic"
    ],
    "associate-manual": [
        "associate-manual"
    ],
    "compile": [
        "compile",
        "extract-layout-data",
        "generate-sheets",
    ],
    "delete": [
    ],
    "export-scores": [
        "export-scores",
        "annotate"
    ],
    "new": [
    ],
    "send-annotated-sheets": [
        "send-annotated-sheets"
    ]
}
AMC_COMMANDS: dict[cmd_t, list[str]] = {
    "analyse-answer-sheets": [
        "analyse",
        "--data", "{dir_data}",
        "--cr", "{dir_cr}",
        "--project", "{dir_project}"
    ],
    "annotate": [
        "annotate",
        "--project", "{dir_project}",
        "--names-file", "{file_csv_students}",
        "--association-key", "code",
        "--corrected", "{file_pdf_correction}",
        "--subject", "{file_pdf_subject}",
        "--compose", "1"
    ],
    "associate-manual": [
        "association",
        "--data", "{dir_data}",
        "--set",
        "--student", "{var_student}",
        "--copy", "{var_copy}"
    ],
    "associate-automatic": [
        "association-auto",
        "--data", "{dir_data}",
        "--notes-id", "{var_amc_code}",
        "--liste", "{file_csv_students}",
        "--liste-key", "code"
    ],
    "compile": [
        "prepare",
        "--mode", "s",
        "--prefix", "{dir_project}",
        "--data", "{dir_data}",
        "--out-sujet", "{file_pdf_subject}",
        "--out-corrige", "{file_pdf_correction}",
        "--out-calage", "{file_xy_calage}",
        "--n-copies", "{var_copies}",
        "{file_tex_main}"
    ],
    "compute-scores": [
        "note",
        "--seuil", "{var_threshold}",
        "--data", "{dir_data}"
    ],
    "export-scores": [
        "export",
        "--data", "{dir_data}",
        "--fich-noms", "{file_csv_students}",
        "--module", "ods",
        "--option", "stats=true",
        "--option", "nom={var_project_title}",
        "-o", "{file_ods_scores}"
    ],
    "extract-answer-sheets": [
        "getimages",
        "--copy-to", "{dir_scans}",
        "{file_pdf_answer_sheets}"
    ],
    "extract-layout-data": [
        "meptex",
        "--src", "{file_xy_calage}",
        "--data", "{dir_data}"
    ],
    "extract-scoring-data": [
        "prepare",
        "--mode", "b",
        "--out-sujet", "{file_pdf_subject}",
        "--out-corrige", "{file_pdf_correction}",
        "--out-calage", "{file_xy_calage}",
        "--prefix", "{dir_project}",
        "--data", "{dir_data}",
        "{file_tex_main}"
    ],
    "generate-sheets": [
        "imprime",
        "--sujet", "{file_pdf_subject}",
        "--data", "{dir_data}",
        "--method", "file",
        "--output", "{file_pdf_copy}"
    ],
    "send-annotated-sheets": [
        "annotate",
        "--project", "{dir_project}",
        "--names-file", "{file_csv_students}",
        "--association-key", "code",
        "--corrected", "{file_pdf_correction}",
        "--subject", "{file_pdf_subject}",
        "--compose", "1",
        "--csv-build-name", f"(key)",
        "--pdf-dir", "{dir_outbox}"
    ]
}
MAIL_DATA_FILE = "data.json"
MAIL_PDF_FILE = "sheet.pdf"


def file_name(f: file_t) -> str:
    idx = f.find("-")
    return f[idx + 1:] + "." + f[:idx]


def default_data() -> data_t:
    return {
        "assoc_attr": 0,
        "code": "",
        "title": "",
        "amc_code": "",
        "threshold": 0.5,
        "copies": 10,
        "groups": list()
    }


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


def json_serialise(obj: object) -> str:
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError


class Project:

    def __init__(self, ucode: str, pcode: str, read: bool = True):
        self.ucode = ucode
        self.pcode = pcode
        self.done = {a: False for a in types.literal_type_values(action_t)}
        self.history = list()
        self.data = default_data()
        if read:
            json_file = self.fpath("json-status")
            with open(json_file) as fd:
                status = tp.cast(status_t, json.loads(fd.read()))
                try:
                    self.done = status["done"]
                    self.history = status["history"]
                    self.data = status["data"]
                except KeyError:
                    pass

    def path(self, *name: str) -> str:
        return os.path.join(Project.user_dir(self.ucode), self.pcode, *name)

    def fpath(self, f: file_t) -> str:
        return os.path.join(self.path(), file_name(f))
    
    @staticmethod
    def user_dir(ucode: str) -> str:
        return os.path.join(config.CONFIG["projects_dir"], ucode)

    def files(self) -> dict[file_t, file_status_t]:
        result: dict[file_t, file_status_t] = dict()
        for f in types.literal_type_values(file_t):
            fpath = self.fpath(f)
            exists = os.path.isfile(fpath)
            date: datetime.datetime | None
            size: int | None
            if exists:
                date = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
                size = os.path.getsize(fpath)
            else:
                date = None
                size = None
            result[f] = {
                "exists": exists,
                "date": date,
                "size": size
            }
        return result

    def doable(self) -> dict[action_t, tuple[bool, list[tuple[str, str]]]]:
        files = self.files()
        result = dict()
        for act in types.literal_type_values(action_t):
            doable = True
            missing = list()
            for dep_type, dep in ACTION_DEP[act]:
                ok = True
                if dep_type == "file":
                    ok = files[tp.cast(file_t, dep)]["exists"]
                elif dep_type == "action":
                    ok = self.done[dep]
                elif dep_type == "data":
                    ok = self.data.get(dep) not in (None, "")
                doable = doable and ok
                if not ok:
                    missing.append((str(dep_type), str(dep)))
            result[act] = (doable, missing)
        return result

    def status(self) -> status_t:
        return {
            "done": self.done,
            "doable": self.doable(),
            "history": self.history,
            "data": self.data,
            "files": self.files()
        }

    def update(self) -> None:
        with open(self.fpath("json-status"), "w") as fd:
            status = {
                "done": self.done,
                "history": self.history,
                "data": self.data
            }
            fd.write(json.dumps(status, indent=3, default=json_serialise))

    def get_title(self) -> str:
        if self.data["title"] == "":
            return self.pcode
        return self.data["title"]

    @staticmethod
    def new(ucode: str, pcode: str) -> types.oper_code_t:
        if not check_pcode(pcode):
            return "err_invalid_project_code"
        proj = Project(ucode, pcode, False)
        pdir = proj.path()
        try:
            Path(pdir).mkdir(parents=True, exist_ok=True)
            dirs = [
                ("copies", ),
                ("cr", ),
                ("cr", "corrections"),
                ("cr", "corrections", "jpg"),
                ("cr", "corrections", "pdf"),
                ("cr", "diagnostic"),
                ("cr", "zooms"),
                ("data", ),
                ("outbox", ),
                ("exports", ),
                ("scans", )
            ]
            for d in dirs:
                path = os.path.join(pdir, *d)
                if os.path.exists(path):
                    return "err_project_already_exists"
                Path(path).mkdir(parents=True)
            proj.done["new"] = True
            proj.update()
            return "succ_project_created"
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            return "err_io"

    @staticmethod
    def list_projects(ucode: str) -> list[tuple[str, str]]:
        try:
            result = list()
            udir = Project.user_dir(ucode)
            for p in sorted(os.listdir(udir)):
                pdir = os.path.join(udir, p)
                status_file = os.path.join(pdir, file_name("json-status"))
                if os.path.isfile(status_file):
                    result.append((p, pdir))
            return result
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            return list()

    def exec(
            self,
            cmd: cmd_t,
            exec_dir: str,
            params: action_params_t,
            additional_args: list[str]
    ) -> types.oper_code_t:
        exec_path = shutil.which("auto-multiple-choice")
        if exec_path is None:
            return "err_amc_not_installed"

        # replace parameter in command arguments
        args = [
            arg.format(
                dir_cr=self.path("cr"),
                dir_data=self.path("data"),
                dir_outbox=self.path("outbox"),
                dir_project=self.path(),
                dir_scans=self.path("scans"),
                file_csv_students=self.fpath("csv-list"),
                file_ods_scores=self.fpath("ods-scores"),
                file_pdf_answer_sheets=self.fpath("pdf-answer-sheets"),
                file_pdf_copy=self.path("copies", f"copy-%e.pdf"),
                file_pdf_correction=self.fpath("pdf-correction"),
                file_pdf_subject=self.fpath("pdf-subject"),
                file_tex_main=file_name("tex-main"),
                file_xy_calage=self.fpath("xy-calage"),
                var_amc_code=self.data["amc_code"],
                var_copies=str(self.data["copies"]),
                var_copy=str(params.get("copy")),
                var_project_title=self.get_title(),
                var_student=str(params.get("student")),
                var_threshold=str(self.data["threshold"])
            )
            for arg in AMC_COMMANDS[cmd]
        ] + additional_args
        args.insert(0, exec_path)
        cur_dir = os.getcwd()
        os.chdir(exec_dir)
        with open(self.fpath("log-webamc"), "a") as fd:
            fd.write(79 * "#" + "\n")
            fd.write(f"# date:\n#   {str(datetime.datetime.now())}\n")
            fd.write(f"# execution dir:\n#   {os.getcwd()}\n")
            fd.write(f"# command:\n#   {' '.join(args)}\n")
            fd.write(79 * "#" + "\n\n")
        with open(self.fpath("log-webamc"), "a") as fd:
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

    def update_data_untyped(
            self,
            data: dict[str, str]
    ) -> tuple[types.oper_code_t, list[str]]:
        ids = list()
        for key, val in self.data.items():
            if key in data:
                typ = tp.get_type_hints(data_t)[key]
                try:
                    self.data[key] = typ(data[key])  # type: ignore
                except (ValueError, TypeError):
                    ids.append(key)
            if ids != list():
                return "err_missing_or_invalid_parameter", ids
        self.update()
        return "succ", list()

    def zip_pdfs(self, zip_file: file_t, pdf_dir: str) -> None:
        path = self.fpath(zip_file)
        with zipfile.ZipFile(path, "w") as zf:
            for entry in os.listdir(pdf_dir):
                entry_abs = os.path.join(pdf_dir, entry)
                if os.path.isfile(entry_abs) and entry_abs.endswith(".pdf"):
                    zf.write(
                        entry_abs,
                        arcname=os.path.join(self.pcode, entry)
                    )

    def get_file(self, file_name: str) -> None | tuple[str, str]:
        path = self.path(file_name)
        if not os.path.isfile(path):
            return None
        return path, f"{self.pcode}-{file_name}"

    def list_associations(self) -> association_t:
        assoc_file = self.path("data", file_name("sqlite-association"))
        result = dict()
        if os.path.isfile(assoc_file):
            conn = sqlite3.Connection(assoc_file)
            cur = conn.cursor()
            q = "select student,copy,manual,auto from association_association"
            for student, copy, manual, auto in cur.execute(q):
                try:
                    st = int(student)
                    co = int(copy)
                except ValueError:
                    continue
                name = os.path.join("cr", f"name-{st}-{co}.jpg")
                name_file = self.path(name)
                exists = os.path.isfile(name_file)
                result[st, co] = (manual, auto, name if exists else None)
            conn.close()
        for x in os.listdir(self.path("cr")):
            m = re.match(r"name-(\d+)-(\d+).jpg", x)
            if m:
                student = int(m.group(1))
                copy = int(m.group(2))
                if (student, copy) not in result:
                    result[student, copy] = (
                        None,
                        None,
                        os.path.join("cr", x)
                    )
        return result

    def list_students(
            self,
            dbs: ORMSession
    ) -> list[tuple[tables.Usr, tables.UsrAttr]]:
        query = dbs.query(
            tables.Usr,
            tables.UsrAttr
        ).where(
            (tables.Usr.usr_id == tables.UsrGrp.ugp_usr)
            & (tables.UsrGrp.ugp_grp.in_(self.data["groups"]))
            & (tables.UsrAttr.uat_usr == tables.Usr.usr_id)
            & (tables.UsrAttr.uat_attr == (self.data["assoc_attr"]))
        ).distinct()
        return [row.tuple() for row in query]

    def action(
            self,
            action: action_t,
            params: action_params_t,
            dbs: ORMSession
    ) -> types.oper_code_t:
        def clean_dir(dir_path: str) -> None:
            for entry in os.listdir(dir_path):
                entry_abs = os.path.join(dir_path, entry)
                if os.path.isfile(entry_abs):
                    os.remove(entry_abs)
        def pre_analyse() -> None:
            clean_dir(self.path("scans"))
            clean_dir(self.path("cr"))
            db_capture = self.path("data", file_name("sqlite-capture"))
            if os.path.isfile(db_capture):
                os.remove(db_capture)
        def pre_export_scores() -> None:
            clean_dir(self.path("cr", "corrections", "pdf"))
            db_assoc = self.path("data", file_name("sqlite-association"))
            if os.path.isfile(db_assoc):
                conn = sqlite3.Connection(db_assoc)
                cur = conn.cursor()
                q = (
                    "delete from association_variables "
                    "where name = 'key_in_list'"
                )
                cur.execute(q)
                q = (
                    "insert into association_variables "
                    "values ('key_in_list', ?)"
                )
                cur.execute(q, ("code", ))
                conn.commit()
                conn.close()
        def post_compile() -> None:
            self.zip_pdfs("zip-sheets", self.path("copies"))
        def post_export_scores() -> None:
            pdf_dir = self.path("cr", "corrections", "pdf")
            self.zip_pdfs("zip-annotated-sheets", pdf_dir)
        def post_send_annotated_sheets() -> None:
            """
        for f in os.listdir(path("outbox")):
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
            os.link(os.path.join(path("outbox"), f), pdf_file)
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
            """
        def generate_csv() -> None:
            with open(self.fpath("csv-list"), "w", encoding="utf-8") as fd:
                fd.write("code;eaddr;name\n")
                for usr, usr_attr in self.list_students(dbs):
                    row = (
                        f"{usr_attr.uat_value};"
                        f"{usr.usr_eaddr};"
                        f"{usr.usr_name.upper()} {usr.usr_fst_name.title()}\n"
                    )
                    fd.write(row)
        def clean_associations() -> types.oper_code_t:
            fpath = self.path("data", file_name("sqlite-association"))
            if os.path.exists(fpath):
                os.remove(fpath)
            return "succ"
        def delete() -> types.oper_code_t:
            shutil.rmtree(self.path())
            return "succ"

        # some actions handled specifically
        funs: dict[action_t, tp.Callable[[], types.oper_code_t]] = {
            "clean-associations": clean_associations,
            "delete": delete
        }
        if action in funs:
            return funs[action]()

        # check dependencies
        #pre_actions, check_result = self.check_action_dependency(action)
        #if check_result is not None:
        #    return check_result

        pre_post_action = dict[action_t, tp.Callable[[], None]]
        action_pre: pre_post_action = {
            "analyse": pre_analyse,
            "export-scores": pre_export_scores,
        }
        action_post: pre_post_action = {
            "compile": post_compile,
            "export-scores": post_export_scores,
            "send-annotated-sheets": post_send_annotated_sheets
        }

        # generate CSV file if required by the command
        if action in {
                "annotate",
                "associate-automatic",
                "export-scores",
                "send-annotated-sheets"
        }:
            generate_csv()
        
        # pre-treatment
        if action in action_pre:
            action_pre[action]()

        success = True
        result: types.oper_code_t = "succ"
        for sub in ACTION_COMMANDS[action]:

            run_dir = self.path()
            args = list()

            if sub == "analyse-answer-sheets":
                scan_dir = self.path("scans")
                args = [
                    os.path.join(scan_dir, x)
                    for x in sorted(os.listdir(scan_dir))
                    if x.endswith(".jpg")
                ]
            elif sub == "associate-manual":
                id_ = params.get("id")
                if id_ != "" and id_ is not None:
                    args = [
                        "--id", str(id_)
                    ]
            elif sub == "compile":
                run_dir = self.path("tex")
            elif sub == "extract-scoring-data":
                run_dir = self.path("tex")
            code = self.exec(sub, run_dir, params, args)
            if not code.startswith("succ"):
                success = False
                result = code
                break
        
        # post-treatment
        if success and action in action_post:
            action_post[action]()

        self.done[action] = success
        self.history.append(
            (action, datetime.datetime.now(), success)
        )
        self.update()
        return result

    def action_upload(
            self,
            action: action_t,
            file_path: str
    ) -> types.oper_code_t:
        dst: file_t
        if action == "upload-answer-sheets":
            dst = "pdf-answer-sheets"
        elif action == "upload-project-archive":
            try:
                with zipfile.ZipFile(file_path) as zf:
                    path = os.path.join("tex", file_name("tex-main"))
                    if path not in zf.namelist():
                        return "err_invalid_tex_archive"
                    in_tex_dir = sorted(
                        x for x in sorted(zf.namelist())
                        if x.startswith("tex" + os.path.sep)
                    )
                    for x in in_tex_dir:
                        zf.extract(member=x, path=self.path())
            except zipfile.BadZipFile:
                return "err_not_a_zip_file"
            dst = "zip-tex"
        shutil.copyfile(file_path, self.fpath(dst))
        self.done[action] = True
        self.history.append((action, datetime.datetime.now(), True))
        self.update()
        return "succ"
    

def list_files(action: action_t) -> list[file_t]:
    return [f for f in ACTION_FILES.get(action, list())]


def get_mail_pdf(eaddr: str, ucode: str, pcode: str) -> None | tuple[str, str]:
    path = os.path.join(get_usr_inbox_dir(eaddr), ucode, pcode, MAIL_PDF_FILE)
    if not os.path.isfile(path):
        return None
    return path, pcode


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
