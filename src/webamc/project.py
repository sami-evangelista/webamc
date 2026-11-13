import io
import shutil
import subprocess
import sqlite3
import zipfile
from sqlalchemy.orm.session import Session as ORMSession

from webamc.all import *
from webamc import mailing
from webamc.db import tables, queries
from webamc.util import fmt
from webamc.www import base


association_t = dict[
    tuple[int, int],  # (student, copy)
    tuple[  # (auto, manual, name-file)
        tp.Optional[str],
        tp.Optional[str],
        tp.Optional[Path]
    ]
]
doable_t = dict[types.action_t, tuple[bool, list[tuple[str, str]]]]
ACTION_FILES: dict[types.action_t, list[types.file_t]] = {
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
    types.action_t,
    list[
        tuple[tp.Literal["action"], types.action_t]
        | tuple[tp.Literal["file"], types.file_t]
    ]
] = {
    "analyse": [
        ("action", "upload_answer_sheets"),
        ("file", "pdf_answer_sheets")
    ],
    "associate_automatic": [
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
        ("file", "source")
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
    "publish_annotated_sheets": [
        ("action", "export_scores")
    ],
    "send_notification_mail": [
        ("action", "publish_annotated_sheets")
    ]
}
ACTION_COMMANDS: dict[types.action_t, list[types.cmd_t]] = {
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
AMC_COMMANDS: dict[types.cmd_t, list[str]] = {
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
CANCELLED: dict[types.action_t, list[types.action_t]] = {
    "compile": [
        "analyse",
        "associate_automatic",
        "associate_manual_prepare",
        "associate_manual",
        "clean_associations",
        "upload_answer_sheets",
        "publish_annotated_sheets",
        "export_scores"
    ],
    "upload_answer_sheets": [
        "analyse",
        "associate_automatic",
        "associate_manual_prepare",
        "associate_manual",
        "clean_associations",
        "publish_annotated_sheets",
        "export_scores"
    ]
}
CLEAN: dict[types.action_t, list[types.file_t]] = {
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


def file_name(f: types.file_t) -> str:
    idx = f.find("_")
    if idx < 0:
        return f
    return f[idx + 1:] + "." + f[:idx]


def file_txt(f: types.file_t) -> types.txt_t:
    result = tp.cast(types.txt_t, f"project_file_{f}")
    assert result in types.literal_type_values(types.txt_t)
    return result


def json_serialise(obj: object) -> str:
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError


def list_action_files(act: types.action_t) -> list[types.file_t]:
    return list(ACTION_FILES.get(act, list()))


def root_path(prj: tables.Project) -> Path:
    return Path(config.CONFIG["projects_dir"]) / prj.dir_path()


def joinpath(prj: tables.Project, *name: str) -> Path:
    return root_path(prj).joinpath(*name)


def file_path(prj: tables.Project, f: types.file_t) -> Path:
    return root_path(prj) / file_name(f)


def create_files(prj: tables.Project) -> types.oper_code_t:
    try:
        path = root_path(prj)
        path.mkdir(parents=True)
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
            Path(path.joinpath(*d)).mkdir(parents=True)
        return "succ_project_created"
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return "err_io"


def delete_files(prj: tables.Project) -> types.oper_code_t:
    try:
        shutil.rmtree(root_path(prj))
        return "succ"
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return "err_io"


def list_files(prj: tables.Project) -> dict[types.file_t, types.file_status_t]:
    result: dict[types.file_t, types.file_status_t] = dict()
    for f in types.literal_type_values(types.file_t):
        fpath = file_path(prj, f)
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


def get_file(prj: tables.Project, f: str) -> None | tuple[Path, str]:
    path = joinpath(prj, f)
    if not path.is_file():
        return None
    return path, f"{prj.prj_code}_{f}"


def warning(prj: tables.Project) -> dict[types.action_t, bool]:
    done = types.check_project_actions_done(prj.prj_done)
    result = {
        act: False
        for act in types.literal_type_values(types.action_t)
    }
    result["compile"] = done["compile"]
    result["delete"] = True
    result["associate_automatic"] = (
        done["associate_automatic"]
        or done["associate_manual"]
    )
    return result


def doable(dbs: ORMSession, prj: tables.Project) -> doable_t:
    files = list_files(prj)
    result: doable_t = dict()
    done = types.check_project_actions_done(prj.prj_done)
    for act in types.literal_type_values(types.action_t):
        act_doable = True
        missing = list()
        for dep_type, dep in ACTION_DEP[act]:
            ok = True
            if dep_type == "file":
                ok = files[tp.cast(types.file_t, dep)]["exists"]
            elif dep_type == "action":
                ok = done[tp.cast(types.action_t, dep)]
            elif dep_type == "data":
                ok = getattr(prj, dep) is not None
            act_doable = act_doable and ok
            if not ok:
                missing.append((str(dep_type), str(dep)))
        result[act] = (act_doable, missing)

    # special cases
    if result["compile"] == (False, [("data", "copies")]):
        projects = queries.list_project_groups(dbs, prj.prj_id)
        if next(projects, None) is not None:
            result["compile"] = (True, list())

    return result


def upload_source(
        prj: tables.Project,
        fname: str,
        fcontent: bytes
) -> types.oper_code_t:
    ext = Path(fname).suffix
    if ext == ".tex":
        src = joinpath(prj, "tex", file_name("tex_main"))
        with open(src, "w", encoding="utf-8") as fds:
            fds.write(fcontent.decode("utf-8"))
        prj.prj_src_type = "tex"
    elif ext == ".txt":
        src = joinpath(prj, "tex", file_name("txt_main"))
        with open(src, "w", encoding="utf-8") as fds:
            fds.write(fcontent.decode("utf-8"))
        prj.prj_src_type = "txt"
    elif ext == ".zip":
        try:
            src = file_path(prj, "zip_tex")
            with zipfile.ZipFile(io.BytesIO(fcontent)) as zf:
                path = Path("tex") / file_name("tex_main")
                if str(path) not in zf.namelist():
                    return "err_project_invalid_tex_archive"
                for x in sorted(
                        x for x in zf.namelist()
                        if x.startswith("tex" + os.path.sep)
                ):
                    zf.extract(member=x, path=root_path(prj))
        except zipfile.BadZipFile:
            return "err_project_not_a_zip_file"
        with open(file_path(prj, "zip_tex"), "wb") as fdb:
            fdb.write(fcontent)
        prj.prj_src_type = "tex"
    else:
        return "err_project_invalid_source"

    path_source = Path(file_path(prj, "source"))
    if path_source.is_file() or path_source.is_symlink():
        path_source.unlink()
    os.symlink(src, file_path(prj, "source"))
    return "succ"


def exec_cmd(
        dbs: ORMSession,
        prj: tables.Project,
        cmd: types.cmd_t,
        exec_dir: Path,
        *args: str,
        **kwargs: tp.Any
) -> types.oper_code_t:
    exec_path = shutil.which("auto-multiple-choice")
    if exec_path is None:
        return "err_project_amc_not_installed"

    if prj.prj_src_type == "txt":
        flt = "plain"
        src = "main.txt"
    else:
        flt = "latex"
        src = "main.tex"

    threshold = prj.prj_threshold
    copies = max(prj.prj_copies, len(list_usrs(dbs, prj)))

    # replace parameter in command arguments
    cmd_args = [
        arg.format(
            dir_cr=joinpath(prj, "cr"),
            dir_data=joinpath(prj, "data"),
            dir_outbox=joinpath(prj, "outbox"),
            dir_project=joinpath(prj, ),
            dir_scans=joinpath(prj, "scans"),
            dir_tex=joinpath(prj, "tex"),
            file_csv_students=file_path(prj, "csv_list"),
            file_ods_scores=file_path(prj, "ods_scores"),
            file_pdf_answer_sheets=file_path(prj, "pdf_answer_sheets"),
            file_pdf_copy=joinpath(prj, "copies", "copy_%e.pdf"),
            file_pdf_correction=file_path(prj, "pdf_correction"),
            file_pdf_subject=file_path(prj, "pdf_subject"),
            file_source=src,
            file_tex_main=file_name("tex_main"),
            file_xy_calage=file_path(prj, "xy_calage"),
            var_amc_code=prj.prj_amc_code,
            var_copies=str(copies),
            var_copy=str(kwargs.get("copy")),
            var_filter=flt,
            var_project_title=prj.title(),
            var_student=str(kwargs.get("student")),
            var_threshold=str(threshold)
        )
        for arg in AMC_COMMANDS[cmd]
    ] + list(args)
    cmd_args.insert(0, exec_path)
    cur_dir = os.getcwd()
    os.chdir(exec_dir)
    with open(file_path(prj, "log_webamc"), "a", encoding="utf-8") as fd:
        fd.write(79 * "#" + "\n")
        fd.write(f"# date:\n#   {str(datetime.datetime.now())}\n")
        fd.write(f"# execution dir:\n#   {os.getcwd()}\n")
        fd.write(f"# command:\n#   {' '.join(cmd_args)}\n")
        fd.write(79 * "#" + "\n\n")
    with open(file_path(prj, "log_webamc"), "a", encoding="utf-8") as fd:
        proc_result = subprocess.run(
            cmd_args,
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


def action(
        dbs: ORMSession,
        usr_id: int,
        prj: tables.Project,
        act: types.action_t,
        fname: tp.Optional[str] = None,
        fcontent: tp.Optional[bytes] = None,
        **kwargs: tp.Any
) -> types.oper_code_t:

    def dump_json(data: tp.Any) -> str:
        return json.dumps(data, indent=3, default=json_serialise)

    def clean_files(files: list[types.file_t]) -> None:
        for f in files:
            if f.startswith("sqlite"):
                path = joinpath(prj, "data", file_name(f))
            else:
                path = file_path(prj, f)
            if path.is_file():
                path.unlink()

    def clean_dir(dir_path: Path) -> None:
        for entry in dir_path.iterdir():
            if entry.is_file():
                entry.unlink()

    def pre_analyse() -> None:
        clean_dir(joinpath(prj, "scans"))
        clean_dir(joinpath(prj, "cr"))

    def pre_export_scores() -> None:
        clean_dir(joinpath(prj, "outbox"))
        clean_dir(joinpath(prj, "cr", "corrections", "pdf"))
        db_assoc = joinpath(prj, "data", file_name("sqlite_association"))
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
        zip_pdfs(prj, "zip_sheets", joinpath(prj, "copies"))

    def post_export_scores() -> None:
        pdf_dir = joinpath(prj, "cr", "corrections", "pdf")
        zip_pdfs(prj, "zip_annotated_sheets", pdf_dir)

    def publish_annotated_sheets() -> types.oper_code_t:

        # delete old messages
        dbs.query(
            tables.Message
        ).where(
            (tables.Message.msg_from == usr_id)
            & (tables.Message.msg_file_project == prj.prj_id)
        ).delete()
        dbs.commit()

        # add new messages
        for f in joinpath(prj, "outbox").iterdir():
            m = re.match(r".\d+_\d+-(.+).pdf", f.name)
            if m is None:
                continue
            usr_code = m.groups()[0]
            dest_usr = dbs.query(
                tables.Usr
            ).where(
                tables.Usr.usr_code == usr_code
            ).first()
            if dest_usr is None:
                continue
            name = fmt.fmt_name(dest_usr.usr_fst_name, dest_usr.usr_name)
            filename = f"{prj.prj_code}_{name.replace(' ', '')}.pdf"
            msg = tables.Message(
                msg_type=types.MESSAGE_TYPE_FILE,
                msg_title=prj.fmt(),
                msg_from=usr_id,
                msg_to=dest_usr.usr_id,
                msg_file_content=f.read_bytes(),
                msg_file_name=filename,
                msg_file_project=prj.prj_id
            )
            dbs.add(msg)
        return "succ"

    def send_notification_mail() -> types.oper_code_t:
        usr = queries.get_usr(dbs, usr_id)
        if usr is None:
            return "err"
        rec = queries.list_recipients(dbs, usr_id, prj.prj_id)
        bcc = [usr.usr_eaddr for usr in rec]
        mail = mailing.find_mail("notification-email")
        cc = [usr.usr_eaddr]
        if mail is None:
            return "err_mail_file_not_found"
        fields = {
            "sender": fmt.fmt_name(usr.usr_fst_name, usr.usr_name),
            "exam": prj.title(),
            "url": config.CONFIG["base_url"] + base.mkuri("/")
        }
        if not mailing.send_mail(list(), mail, fields, bcc=bcc, cc=cc):
            return "err_mail_file_not_found"
        return "succ"

    done = types.check_project_actions_done(prj.prj_done)
    history = types.check_project_history(prj.prj_history)
    generate_csv(dbs, prj)

    if act == "delete":
        dbs.delete(prj)
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
    for a in CANCELLED.get(act, list()):
        done[a] = False
    if act in CLEAN:
        clean_files(CLEAN[act])
    if act in pre:
        pre[act]()

    # execute all commands of the action
    result: types.oper_code_t = "succ"
    for sub in ACTION_COMMANDS.get(act, list()):
        run_dir = joinpath(prj, )
        args = list()
        if sub == "analyse":
            scan_dir = joinpath(prj, "scans")
            args = sorted(
                str(x)
                for x in scan_dir.iterdir()
                if x.suffix == ".jpg" and x.is_file()
            )
        elif sub == "association":
            id_ = kwargs.get("id_")
            if id_ != "" and id_ is not None:
                args = [
                    "--id", str(id_)
                ]
        elif sub == "prepare_s":
            run_dir = joinpath(prj, "tex")
        elif sub == "prepare_bk":
            run_dir = joinpath(prj, "tex")
        code = exec_cmd(dbs, prj, sub, run_dir, *args, **kwargs)
        if not types.is_success(code):
            result = code
            break

    # some actions handled specifically
    if act == "clean_associations":
        result = "succ"
    elif act == "upload_answer_sheets":
        assert fname is not None and fcontent is not None
        with open(file_path(prj, "pdf_answer_sheets"), "wb") as fd:
            fd.write(fcontent)
        result = "succ"
    elif act == "upload_source":
        assert fname is not None and fcontent is not None
        result = upload_source(prj, fname, fcontent)
    elif act == "publish_annotated_sheets":
        result = publish_annotated_sheets()
    elif act == "send_notification_mail":
        result = send_notification_mail()

    # post-treatment
    success = types.is_success(result)
    if success and act in post:
        post[act]()

    # update the status and regenerate the csv file
    done[act] = success
    history.append((act, datetime.datetime.now(), success))
    prj.prj_done = dump_json(done)
    prj.prj_history = dump_json(history)

    return result


def zip_pdfs(
        prj: tables.Project,
        zip_file: types.file_t,
        pdf_dir: Path
) -> None:
    path = file_path(prj, zip_file)
    with zipfile.ZipFile(path, "w") as zf:
        for entry in pdf_dir.iterdir():
            if entry.is_file() and entry.suffix == ".pdf":
                arcname = Path(prj.prj_code) / entry.name
                zf.write(entry, arcname=arcname)


def list_associations(prj: tables.Project) -> association_t:
    assoc_file = joinpath(prj, "data", file_name("sqlite_association"))
    result = dict()
    if assoc_file.is_file():
        conn = sqlite3.Connection(assoc_file)
        cur = conn.cursor()
        q = "select student, copy, manual, auto from association_association"
        for student, copy, manual, auto in cur.execute(q):
            try:
                st = int(student)
                co = int(copy)
            except ValueError:
                continue
            fpath = joinpath(prj, "cr", f"name-{st}-{co}.jpg")
            exists = fpath.is_file()
            name_file = Path("cr") / f"name-{st}-{co}.jpg"
            result[st, co] = (manual, auto, name_file if exists else None)
        conn.close()
    for x in joinpath(prj, "cr").iterdir():
        m = re.match(r"name-(\d+)-(\d+).jpg", x.name)
        if m:
            student = int(m.group(1))
            copy = int(m.group(2))
            if (student, copy) not in result:
                path = Path("cr") / x.name
                result[student, copy] = (None, None, path)
    return result


def generate_csv(dbs: ORMSession, prj: tables.Project) -> None:
    with open(file_path(prj, "csv_list"), "w", encoding="utf-8") as fd:
        fd.write("id;code;name\n")
        for usr_attr, usr in list_usrs(dbs, prj):
            if usr_attr is None:
                attr = usr.usr_code
            else:
                attr = usr_attr.uat_value
            fd.write(f"{attr};{usr.usr_code};{usr.fmt()}\n")


def list_usrs(
        dbs: ORMSession,
        prj: tables.Project
) -> list[tuple[None | tables.UsrAttr, tables.Usr]]:

    # get groups and all their sub-groups
    groups: set[int] = set()
    for grp in queries.list_project_groups(dbs, prj.prj_id):
        groups = groups.union(groups, queries.get_grp_tree(dbs, grp.grp_id))

    # first get all users
    query_all = dbs.query(
        tables.Usr
    ).where(
        (tables.Usr.usr_id == tables.UsrGrp.ugp_usr)
        & (tables.UsrGrp.ugp_grp.in_(groups))
    )
    usrs: dict[int, tuple[None | tables.UsrAttr, tables.Usr]] = {
        usr.usr_id: (None, usr)
        for usr in query_all
    }

    # then those that have their attribute set
    if prj.prj_auto_assoc_attr is not None:
        query = dbs.query(
            tables.UsrAttr,
            tables.Usr
        ).where(
            (tables.Usr.usr_id == tables.UsrGrp.ugp_usr)
            & (tables.UsrGrp.ugp_grp.in_(groups))
            & (tables.UsrAttr.uat_usr == tables.Usr.usr_id)
            & (tables.UsrAttr.uat_attr == prj.prj_auto_assoc_attr)
        )
        for row in query:
            usr_attr, usr = row.tuple()
            usrs[usr.usr_id] = (usr_attr, usr)
    return sorted(
        (tup for tup in usrs.values()),
        key=lambda s: (s[1].usr_name, s[1].usr_fst_name)
    )
