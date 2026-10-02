import io
import re
import shutil
import subprocess
import sqlite3
import zipfile
from pathlib import Path
from sqlalchemy.orm.session import Session as ORMSession

from webamc.all import *
from webamc import mailing
from webamc.db import tables, queries
from webamc.util import fmt
from webamc.www import base


action_t = tp.Literal[
    "analyse",
    "associate_automatic",
    "associate_manual_prepare",
    "associate_manual",
    "clean_associations",
    "compile",
    "delete",
    "export_scores",
    "new",
    "upload_answer_sheets",
    "upload_source",
    "send_annotated_sheets",
    "send_notification_mail"
]
source_type_t = tp.Literal[
    "tex",
    "txt"
]
cmd_t = tp.Literal[
    "decode",
    "analyse",
    "annotate",
    "association",
    "association-auto",
    "clean_associations",
    "prepare_s",
    "note",
    "export",
    "meptex",
    "prepare_bk",
    "getimages",
    "imprime",
    "read-pdfform"
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
    },
    total=False
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
    tuple[None | str, None | str, None | Path]  # (auto, manual, name-file)
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
    "csv_list",
    "json_status",
    "log_webamc",
    "ods_scores",
    "pdf_answer_sheets",
    "pdf_correction",
    "pdf_subject",
    "sqlite_association",
    "sqlite_capture",
    "source",
    "tex_main",
    "txt_main",
    "xy_calage",
    "zip_annotated_sheets",
    "zip_sheets",
    "zip_tex"
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
        "source_type": source_type_t,
        "done": dict[action_t, bool],
        "doable": dict[action_t, tuple[bool, list[tuple[str, str]]]],
        "history": list[tuple[action_t, datetime.datetime, bool]],
        "data": data_t,
        "files": dict[file_t, file_status_t],
        "warning": dict[action_t, bool]
    }
)
doable_t = dict[action_t, tuple[bool, list[tuple[str, str]]]]
ACTION_FILES: dict[action_t, list[file_t]] = {
    "compile": [
        "pdf_subject",
        "zip_sheets",
        "pdf_correction"
    ],
    "export_scores": [
        "ods_scores",
        "zip_annotated_sheets"
    ],
    "upload_answer_sheets": [
        "pdf_answer_sheets"
    ],
    "upload_source": [
        "source"
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
        ("action", "upload_answer_sheets"),
        ("file", "pdf_answer_sheets")
    ],
    "associate_automatic": [
        ("data", "amc_code"),
        ("data", "assoc_attr"),
        ("action", "analyse")
    ],
    "associate_manual_prepare": [
        ("action", "analyse")
    ],
    "associate_manual": [
        ("action", "analyse")
    ],
    "clean_associations": [
        ("action", "analyse")
    ],
    "compile": [
        ("action", "upload_source"),
        ("file", "source"),
        ("data", "copies")
    ],
    "delete": [
        ("action", "new")
    ],
    "export_scores": [
        ("action", "analyse")
    ],
    "new": [
    ],
    "upload_answer_sheets": [
        ("action", "compile")
    ],
    "upload_source": [
        ("action", "new")
    ],
    "send_annotated_sheets": [
        ("action", "export_scores")
    ],
    "send_notification_mail": [
        ("action", "send_annotated_sheets")
    ]
}
ACTION_COMMANDS: dict[action_t, list[cmd_t]] = {
    "analyse": [
        "read-pdfform",
        "getimages",
        "analyse",
        "decode",
        "prepare_bk",
        "note"
    ],
    "associate_automatic": [
        "association-auto"
    ],
    "associate_manual": [
        "association"
    ],
    "compile": [
        "prepare_s",
        "meptex",
        "imprime",
    ],
    "export_scores": [
        "export",
        "annotate"
    ]
}
AMC_COMMANDS: dict[cmd_t, list[str]] = {
    "analyse": [
        "analyse",
        "--data", "{dir_data}",
        "--cr", "{dir_cr}",
        "--project-dir", "{dir_project}",
        "--unlink-on-global-err"
    ],
    "association": [
        "association",
        "--data", "{dir_data}",
        "--set",
        "--student", "{var_student}",
        "--copy", "{var_copy}"
    ],
    "association-auto": [
        "association-auto",
        "--data", "{dir_data}",
        "--notes-id", "{var_amc_code}",
        "--liste", "{file_csv_students}",
        "--liste-key", "id"
    ],
    "decode": [
        "decode",
        "--project-dir", "{dir_project}",
        "--no-all"
    ],
    "prepare_s": [
        "prepare",
        "--mode", "s[sc]k",
        "--project-dir", "{dir_project}",
        "--data", "{dir_data}",
        "--n-copies", "{var_copies}",
        "--filter", "{var_filter}",
        "--latex-stdout",
        "--builddir", "{dir_tex}",
        "--out-sujet", "{file_pdf_subject}",
        "--out-corrige", "{file_pdf_correction}",
        "--out-calage", "{file_xy_calage}",
        "--source", "{file_source}"
    ],
    "note": [
        "note",
        "--seuil", "{var_threshold}",
        "--data", "{dir_data}"
    ],
    "export": [
        "export",
        "--data", "{dir_data}",
        "--fich-noms", "{file_csv_students}",
        "--module", "ods",
        "--option", "stats=true",
        "--option", "nom={var_project_title}",
        "-o", "{file_ods_scores}"
    ],
    "getimages": [
        "getimages",
        "--copy-to", "{dir_scans}",
        "{file_pdf_answer_sheets}"
    ],
    "meptex": [
        "meptex",
        "--src", "{file_xy_calage}",
        "--data", "{dir_data}"
    ],
    "prepare_bk": [
        "prepare",
        "--mode", "bk",
        "--out-sujet", "{file_pdf_subject}",
        "--out-corrige", "{file_pdf_correction}",
        "--out-calage", "{file_xy_calage}",
        "--data", "{dir_data}",
        "--filter", "{var_filter}",
        "--n-copies", "{var_copies}",
        "{file_source}"
    ],
    "imprime": [
        "imprime",
        "--sujet", "{file_pdf_subject}",
        "--data", "{dir_data}",
        "--method", "file",
        "--output", "{file_pdf_copy}"
    ],
    "read-pdfform": [
        "read-pdfform",
        "--project-dir", "{dir_project}"
    ],
    "annotate": [
        "annotate",
        "--project", "{dir_project}",
        "--names-file", "{file_csv_students}",
        "--association-key", "id",
        "--corrected", "{file_pdf_correction}",
        "--subject", "{file_pdf_subject}",
        "--compose", "1",
        "--csv-build-name", "(code)",
        "--pdf-dir", "{dir_outbox}"
    ]
}
CANCELLED: dict[action_t, list[action_t]] = {
    "compile": [
        "analyse",
        "associate_automatic",
        "associate_manual_prepare",
        "associate_manual",
        "clean_associations",
        "upload_answer_sheets",
        "send_annotated_sheets",
        "export_scores"
    ],
    "upload_answer_sheets": [
        "analyse",
        "associate_automatic",
        "associate_manual_prepare",
        "associate_manual",
        "clean_associations",
        "send_annotated_sheets",
        "export_scores"
    ]
}
CLEAN: dict[action_t, list[file_t]] = {
    "compile": [
        "ods_scores",
        "pdf_answer_sheets",
        "pdf_correction",
        "pdf_subject",
        "sqlite_association",
        "zip_annotated_sheets",
        "zip_sheets"
    ],
    "analyse": [
        "sqlite_capture"
    ],
    "upload_answer_sheets": [
        "ods_scores",
        "pdf_answer_sheets",
        "sqlite_association",
        "zip_annotated_sheets"
    ],
    "associate_automatic": [
        "sqlite_association"
    ]
}
MAIL_PDF_FILE = "sheet.pdf"
DEFAULT_THRESHOLD = 0.5
DEFAULT_COPIES = 10
DEFAULT_AMC_CODE = "code"
PCODE_REGEXP = r'[a-zA-Z][a-zA-Z0-9_\-]*'


def file_name(f: file_t) -> str:
    idx = f.find("_")
    if idx < 0:
        return f
    return f[idx + 1:] + "." + f[:idx]


def file_txt(f: file_t) -> types.txt_t:
    result = tp.cast(types.txt_t, f"seq_project_file_{f}")
    assert result in types.literal_type_values(types.txt_t)
    return result


def check_pcode(pcode: str) -> bool:
    return bool(re.fullmatch(PCODE_REGEXP, pcode, re.ASCII))


def json_serialise(obj: object) -> str:
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError


def list_files(action: action_t) -> list[file_t]:
    return list(ACTION_FILES.get(action, list()))


class Project:

    def __init__(
            self,
            ucode: str,
            uname: str,
            pcode: str,
            read: bool = True,
            dbs: ORMSession | None = None):
        self.ucode = ucode
        self.uname = uname
        self.pcode = pcode
        self.done = {a: False for a in types.literal_type_values(action_t)}
        self.history = list()
        self.data: data_t = {}
        self.dbs = dbs
        self.source_type: source_type_t = "tex"
        if read:
            json_file = self.fpath("json_status")
            with open(json_file, encoding="utf-8") as fd:
                status = tp.cast(status_t, json.loads(fd.read()))
                try:
                    self.source_type = status["source_type"]
                    self.done = status["done"]
                    self.history = status["history"]
                    self.data = status["data"]
                except KeyError:
                    pass

    def path(self, *name: str) -> Path:
        return Project.user_dir(self.ucode).joinpath(self.pcode, *name)

    def fpath(self, f: file_t) -> Path:
        return self.path() / file_name(f)

    @staticmethod
    def user_dir(ucode: str) -> Path:
        return Path(config.CONFIG["projects_dir"]) / ucode

    def usr(self) -> tables.Usr:
        assert self.dbs is not None
        result = self.dbs.query(
            tables.Usr
        ).where(
            tables.Usr.usr_code == self.ucode
        ).first()
        assert result is not None
        return result

    def files(self) -> dict[file_t, file_status_t]:
        result: dict[file_t, file_status_t] = dict()
        for f in types.literal_type_values(file_t):
            fpath = self.fpath(f)
            exists = fpath.is_file()
            date: datetime.datetime | None = None
            size: int | None = None
            if exists:
                stat = fpath.stat()
                date = datetime.datetime.fromtimestamp(stat.st_mtime)
                size = stat.st_size
            result[f] = {
                "exists": exists,
                "date": date,
                "size": size
            }
        return result

    def doable(self) -> doable_t:
        files = self.files()
        result: doable_t = dict()
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

        # special cases
        if result["compile"] == (False, [("data", "copies")]):
            if self.has_groups():
                result["compile"] = (True, list())
        return result

    def status(self) -> status_t:
        return {
            "source_type": self.source_type,
            "done": self.done,
            "doable": self.doable(),
            "history": self.history,
            "data": self.data,
            "files": self.files(),
            "warning": self.warning()
        }

    def warning(self) -> dict[action_t, bool]:
        result = {act: False for act in types.literal_type_values(action_t)}
        result["compile"] = self.done["compile"]
        result["delete"] = True
        result["associate_automatic"] = (
            self.done["associate_automatic"]
            or self.done["associate_manual"]
        )
        return result

    def update(self) -> None:
        with open(self.fpath("json_status"), "w", encoding="utf-8") as fd:
            status = {
                "source_type": self.source_type,
                "done": self.done,
                "history": self.history,
                "data": self.data
            }
            fd.write(json.dumps(status, indent=3, default=json_serialise))

    def get_title(self) -> str:
        if self.data.get("title", None) in ("", None):
            return self.pcode
        return self.data["title"]

    @staticmethod
    def new(ucode: str, uname: str, pcode: str) -> types.oper_code_t:
        if not check_pcode(pcode):
            return "err_project_invalid_code"
        proj = Project(ucode, uname, pcode, False)
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
                ("scans", ),
                ("tex", )
            ]
            for d in dirs:
                path = pdir.joinpath(*d)
                if path.exists():
                    return "err_project_already_exists"
                Path(path).mkdir(parents=True)
            proj.done["new"] = True
            proj.update()
            return "succ_project_created"
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            return "err_io"

    @staticmethod
    def list_projects(ucode: str) -> list[tuple[str, Path]]:
        try:
            result = list()
            udir = Project.user_dir(ucode)
            for p in sorted(os.listdir(udir)):
                pdir = udir.joinpath(p)
                status_file = pdir / file_name("json_status")
                if status_file.is_file():
                    result.append((str(p), pdir))
            return result
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            return list()

    def has_groups(self) -> bool:
        return self.data.get("groups") not in (None, list())

    def exec(
            self,
            cmd: cmd_t,
            exec_dir: Path,
            params: action_params_t,
            additional_args: list[str]
    ) -> types.oper_code_t:
        exec_path = shutil.which("auto-multiple-choice")
        if exec_path is None:
            return "err_project_amc_not_installed"

        if self.source_type == "txt":
            flt = "plain"
            src = "main.txt"
        else:
            flt = "latex"
            src = "main.tex"

        threshold = self.data.get("threshold", DEFAULT_THRESHOLD)
        amc_code = self.data.get("amc_code", DEFAULT_AMC_CODE)

        # to determine the number of copies we take first the value in
        # data then, if present, the number of students in groups and
        # finally DEFAULT_COPIES
        if "copies" in self.data:
            copies = self.data["copies"]
        elif self.has_groups():
            copies = len(self.list_students())
        else:
            copies = DEFAULT_COPIES

        # replace parameter in command arguments
        args = [
            arg.format(
                dir_cr=self.path("cr"),
                dir_data=self.path("data"),
                dir_outbox=self.path("outbox"),
                dir_project=self.path(),
                dir_scans=self.path("scans"),
                dir_tex=self.path("tex"),
                file_csv_students=self.fpath("csv_list"),
                file_ods_scores=self.fpath("ods_scores"),
                file_pdf_answer_sheets=self.fpath("pdf_answer_sheets"),
                file_pdf_copy=self.path("copies", "copy_%e.pdf"),
                file_pdf_correction=self.fpath("pdf_correction"),
                file_pdf_subject=self.fpath("pdf_subject"),
                file_source=src,
                file_tex_main=file_name("tex_main"),
                file_xy_calage=self.fpath("xy_calage"),
                var_amc_code=amc_code,
                var_copies=str(copies),
                var_copy=str(params.get("copy")),
                var_filter=flt,
                var_project_title=self.get_title(),
                var_student=str(params.get("student")),
                var_threshold=str(threshold)
            )
            for arg in AMC_COMMANDS[cmd]
        ] + additional_args
        args.insert(0, exec_path)
        cur_dir = os.getcwd()
        os.chdir(exec_dir)
        with open(self.fpath("log_webamc"), "a", encoding="utf-8") as fd:
            fd.write(79 * "#" + "\n")
            fd.write(f"# date:\n#   {str(datetime.datetime.now())}\n")
            fd.write(f"# execution dir:\n#   {os.getcwd()}\n")
            fd.write(f"# command:\n#   {' '.join(args)}\n")
            fd.write(79 * "#" + "\n\n")
        with open(self.fpath("log_webamc"), "a", encoding="utf-8") as fd:
            proc_result = subprocess.run(
                args,
                input="",
                stdout=fd,
                stderr=fd,
                check=False
            )
            fd.write("\n\n\n")
        os.chdir(cur_dir)
        if proc_result.returncode == 0:
            return "succ"
        return "err_project_check_log_file"

    def set_data(
            self,
            data: dict[str, str]
    ) -> tuple[types.oper_code_t, list[str]]:
        ids = list()
        for key, val in data.items():
            if val == "" or val is None:
                if key in self.data:
                    del self.data[key]  # type: ignore
            else:
                typ = tp.get_type_hints(data_t)[key]
                try:
                    self.data[key] = typ(data[key])  # type: ignore
                except (ValueError, TypeError):
                    ids.append(key)
        if ids != list():
            return "err_project_missing_or_invalid_parameter", ids
        self.update()
        self.generate_csv()
        return "succ", list()

    def zip_pdfs(self, zip_file: file_t, pdf_dir: Path) -> None:
        path = self.fpath(zip_file)
        with zipfile.ZipFile(path, "w") as zf:
            for entry in pdf_dir.iterdir():
                if entry.is_file() and entry.suffix == ".pdf":
                    zf.write(entry, arcname=self.pcode / entry)

    def get_file(self, f: str) -> None | tuple[Path, str]:
        path = self.path(f)
        if not path.is_file():
            return None
        return path, f"{self.pcode}_{f}"

    def list_associations(self) -> association_t:
        assoc_file = self.path("data", file_name("sqlite_association"))
        result = dict()
        if assoc_file.is_file():
            conn = sqlite3.Connection(assoc_file)
            cur = conn.cursor()
            q = "select student,copy,manual,auto from association_association"
            for student, copy, manual, auto in cur.execute(q):
                try:
                    st = int(student)
                    co = int(copy)
                except ValueError:
                    continue
                name_file = self.path("cr", f"name-{st}-{co}.jpg")
                exists = name_file.is_file()
                result[st, co] = (manual, auto, name_file if exists else None)
            conn.close()
        for x in self.path("cr").iterdir():
            m = re.match(r"name-(\d+)-(\d+).jpg", x.name)
            if m:
                student = int(m.group(1))
                copy = int(m.group(2))
                if (student, copy) not in result:
                    path = self.path("cr", x.name)
                    result[student, copy] = (None, None, path)
        return result

    def list_students(self) -> list[tuple[None | tables.UsrAttr, tables.Usr]]:
        assert self.dbs is not None
        if not self.has_groups():
            return list()

        # get groups and all their sub-groups
        groups: set[int] = set()
        for gid in self.data["groups"]:
            groups = groups.union(groups, queries.get_grp_tree(self.dbs, gid))

        # first get all students
        query_all = self.dbs.query(
            tables.Usr
        ).where(
            (tables.Usr.usr_id == tables.UsrGrp.ugp_usr)
            & (tables.UsrGrp.ugp_grp.in_(groups))
        )
        students: dict[int, tuple[None | tables.UsrAttr, tables.Usr]] = {
            usr.usr_id: (None, usr)
            for usr in query_all
        }

        # then those that have their attribute set
        if "assoc_attr" in self.data:
            query = self.dbs.query(
                tables.UsrAttr,
                tables.Usr
            ).where(
                (tables.Usr.usr_id == tables.UsrGrp.ugp_usr)
                & (tables.UsrGrp.ugp_grp.in_(groups))
                & (tables.UsrAttr.uat_usr == tables.Usr.usr_id)
                & (tables.UsrAttr.uat_attr == (self.data["assoc_attr"]))
            )
            for row in query:
                usr_attr, usr = row.tuple()
                students[usr.usr_id] = (usr_attr, usr)
        return sorted(
            (tup for tup in students.values()),
            key=lambda s: (s[1].usr_name, s[1].usr_fst_name)
        )

    def generate_csv(self) -> None:
        with open(self.fpath("csv_list"), "w", encoding="utf-8") as fd:
            fd.write("id;code;name\n")
            for usr_attr, usr in self.list_students():
                if usr_attr is None:
                    attr = usr.usr_code
                else:
                    attr = usr_attr.uat_value
                row = (
                    f"{attr};"
                    f"{usr.usr_code};"
                    f"{usr.usr_name.upper()} {usr.usr_fst_name.title()}\n"
                )
                fd.write(row)

    def action(
            self,
            action: action_t,
            params: action_params_t,
            fname: str | None = None,
            fcontent: bytes | None = None
    ) -> types.oper_code_t:
        def clean_files(files: list[file_t]) -> None:
            for f in files:
                if f.startswith("sqlite"):
                    path = self.path("data", file_name(f))
                else:
                    path = self.fpath(f)
                if path.is_file():
                    path.unlink()
        def clean_dir(dir_path: Path) -> None:
            for entry in dir_path.iterdir():
                if entry.is_file():
                    entry.unlink()
        def pre_analyse() -> None:
            clean_dir(self.path("scans"))
            clean_dir(self.path("cr"))
        def pre_export_scores() -> None:
            clean_dir(self.path("outbox"))
            clean_dir(self.path("cr", "corrections", "pdf"))
            db_assoc = self.path("data", file_name("sqlite_association"))
            if db_assoc.is_file():
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
                cur.execute(q, ("id", ))
                conn.commit()
                conn.close()
        def post_compile() -> None:
            self.zip_pdfs("zip_sheets", self.path("copies"))
        def post_export_scores() -> None:
            pdf_dir = self.path("cr", "corrections", "pdf")
            self.zip_pdfs("zip_annotated_sheets", pdf_dir)
        def send_annotated_sheets() -> types.oper_code_t:
            assert self.dbs is not None
            from_usr = self.usr()

            # delete old messages
            self.dbs.query(
                tables.Message
            ).where(
                (tables.Message.msg_from == from_usr.usr_id)
                & (tables.Message.msg_code == self.pcode)
            ).delete()

            # add new messages
            for f in self.path("outbox").iterdir():
                m = re.match(r".\d+_\d+-(.+).pdf", f.name)
                if m is None:
                    continue
                usr_code = m.groups()[0]
                dest_usr = self.dbs.query(
                    tables.Usr
                ).where(
                    tables.Usr.usr_code == usr_code
                ).first()
                if dest_usr is None:
                    continue
                name = fmt.fmt_name(dest_usr.usr_fst_name, dest_usr.usr_name)
                filename = f"{self.pcode}_{name.replace(' ', '')}.pdf"
                msg = tables.Message(
                    msg_title=self.get_title(),
                    msg_code=self.pcode,
                    msg_from=from_usr.usr_id,
                    msg_to=dest_usr.usr_id,
                    msg_file=f.read_bytes(),
                    msg_filename=filename
                )
                self.dbs.add(msg)
            return "succ"
        def send_notification_mail() -> types.oper_code_t:
            assert self.dbs is not None
            usr = self.usr()
            rec = queries.list_recipients(self.dbs, usr.usr_id, self.pcode)
            bcc = [usr.usr_eaddr for usr in rec]
            mail = mailing.find_mail("project-notification-mail")
            cc = [usr.usr_eaddr]
            if mail is None:
                return "err_mail_file_not_found"
            fields = {
                "sender": fmt.fmt_name(usr.usr_fst_name, usr.usr_name),
                "exam": self.get_title(),
                "url": config.CONFIG["base_url"] + base.mkuri("/")
            }
            if not mailing.send_mail(list(), mail, fields, bcc=bcc, cc=cc):
                return "err_mail_file_not_found"
            return "succ"

        if action == "delete":
            shutil.rmtree(self.path())
            return "succ"

        pre = {
            "analyse": pre_analyse,
            "export_scores": pre_export_scores
        }
        post = {
            "compile": post_compile,
            "export_scores": post_export_scores
        }

        # pre-treatment
        for act in CANCELLED.get(action, list()):
            self.done[act] = False
        if action in CLEAN:
            clean_files(CLEAN[action])
        if action in pre:
            pre[action]()

        # execute all commands of the action
        result: types.oper_code_t = "succ"
        for sub in ACTION_COMMANDS.get(action, list()):
            run_dir = self.path()
            args = list()
            if sub == "analyse":
                scan_dir = self.path("scans")
                args = sorted(
                    str(x)
                    for x in scan_dir.iterdir()
                    if x.suffix == ".jpg" and x.is_file()
                )
            elif sub == "association":
                id_ = params.get("id")
                if id_ != "" and id_ is not None:
                    args = [
                        "--id", str(id_)
                    ]
            elif sub == "prepare_s":
                run_dir = self.path("tex")
            elif sub == "prepare_bk":
                run_dir = self.path("tex")
            code = self.exec(sub, run_dir, params, args)
            if not code.startswith("succ"):
                result = code
                break

        # some actions handled specifically
        if action == "clean_associations":
            result = "succ"
        elif action == "upload_answer_sheets":
            assert fname is not None and fcontent is not None
            with open(self.fpath("pdf_answer_sheets"), "wb") as fd:
                fd.write(fcontent)
            result = "succ"
        elif action == "upload_source":
            assert fname is not None and fcontent is not None
            result = self.upload_source(fname, fcontent)
        elif action == "send_annotated_sheets":
            result = send_annotated_sheets()
        elif action == "send_notification_mail":
            result = send_notification_mail()

        # post-treatment
        success = result.startswith("succ")
        if success and action in post:
            post[action]()

        # update the status
        self.done[action] = success
        self.history.append((action, datetime.datetime.now(), success))
        self.update()

        return result

    def upload_source(self, fname: str, fcontent: bytes) -> types.oper_code_t:
        ext = Path(fname).suffix
        if ext == ".tex":
            src = self.path("tex", file_name("tex_main"))
            with open(src, "w", encoding="utf-8") as fds:
                fds.write(fcontent.decode("utf-8"))
            self.source_type = "tex"
        elif ext == ".txt":
            src = self.path("tex", file_name("txt_main"))
            with open(src, "w", encoding="utf-8") as fds:
                fds.write(fcontent.decode("utf-8"))
            self.source_type = "txt"
        elif ext == ".zip":
            try:
                src = self.fpath("zip_tex")
                with zipfile.ZipFile(io.BytesIO(fcontent)) as zf:
                    path = Path("tex") / file_name("tex_main")
                    if str(path) not in zf.namelist():
                        return "err_project_invalid_tex_archive"
                    for x in sorted(
                            x for x in zf.namelist()
                            if x.startswith("tex" + os.path.sep)
                    ):
                        zf.extract(member=x, path=self.path())
            except zipfile.BadZipFile:
                return "err_project_not_a_zip_file"
            with open(self.fpath("zip_tex"), "wb") as fdb:
                fdb.write(fcontent)
            self.source_type = "tex"
        else:
            return "err_project_invalid_source"
        if Path(self.fpath("source")).is_file():
            shutil.rmtree(self.fpath("source"))
        os.link(src, self.fpath("source"))
        return "succ"
