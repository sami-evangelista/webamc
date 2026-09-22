from pathlib import Path
import subprocess
import traceback
import shutil
import uuid
import multiprocessing
from concurrent import futures
import typeguard
import pymupdf
from PIL import Image

from webamc.all import *
from webamc.util import io
from . import tex, output


JSON_SPEC = "items.json"

amc_mdata_t = tp.TypedDict(
    "amc_mdata_t",
    {
        "itm_code": str,
        "itm_difficulty": int,
        "itm_rnd": bool,
        "itm_standalone": bool,
        "itm_tags": list[str],
        "itm_title": str,
        "itm_visible": bool,
        "itm_instances": int
    },
    total=False
)

instance_t = tp.TypedDict(
    "instance_t",
    {
        "iti_img": bytes,
        "iti_num": int,
        "iti_seed": int,
        "png": str
    },
    total=False
)

item_t = tp.TypedDict(
    "item_t",
    {
        "num": int,
        "tags": list[str],
        "is_mcq": bool,
        "tex_file": str,
        "cho_correct": bool,
        "cho_last": bool,
        "itm_code": str,
        "itm_difficulty": int,
        "itm_img": bytes,
        "itm_order": int,
        "itm_parent": int,
        "itm_rnd": bool,
        "itm_standalone": bool,
        "itm_title": str,
        "itm_type": types.item_type_t,
        "itm_usr": int,
        "itm_visible": bool,
        "pak_spec": str,
        "qst_type": types.question_type_t,
        "instances": list[instance_t]
    },
    total=False
)


qst_template_t = tp.TypedDict(
    "qst_template_t",
    {
        "item": item_t,
        "qst_data": tp.Any,
        "choices": list[tuple[item_t, str, int]]
    }
)

ctx_t = tp.TypedDict(
    "ctx_t",
    {
        "num": int,
        "headers": list[tuple[str, str]],
        "stack": list[tuple[str, int, int]],
        "mdata": list[amc_mdata_t],
        "log_dir": Path | None
    }
)
CTX: ctx_t = {
    "num": 0,
    "headers": list(),
    "stack": list(),
    "mdata": list(),
    "log_dir": None
}
WEBAMC_COMMENT = "%webamc "


# task type used for tasks
task_t = tp.TypedDict(
    "task_t",
    {
        "input_tex": Path,
        "output_dir": Path,
        "item": item_t,
        "mcq_dir": Path | None,
        "tex_content": str | None,
        "info": str | None,
        "headers": list[tuple[str, str]],
        "instance_id": int,
        "png_file": Path,
        "seed": int,
        "dyn_code": str | None,
        "dyn_vars": dict[str, str]
    },
    total=False
)

# tasks used for multiprocessing
TASKS: list[task_t] = []


def _check_item_mdata(mdata: str) -> None | types.item_mdata_t:
    try:
        result = typeguard.check_type(mdata, types.item_mdata_t)
        return tp.cast(types.item_mdata_t, result)
    except typeguard.TypeCheckError:
        return None


def _ctx_push_item(item: item_t) -> None:
    CTX["stack"].append((item["itm_code"], item["num"], 0))


def _ctx_pop_item() -> None:
    CTX["stack"].pop()


def _ctx_push_mdata(mdata: amc_mdata_t) -> None:
    CTX["mdata"].append(mdata)


def _ctx_pop_mdata() -> None:
    CTX["mdata"].pop()


def _ctx_push_header(header: tuple[str, str]) -> None:
    CTX["headers"].append(header)


def _ctx_pop_header() -> None:
    CTX["headers"].pop()


def _ctx_new_item(input_tex: Path, read_mdata: bool = True) -> item_t:
    item: item_t = dict()
    item["tex_file"] = str(input_tex)
    if read_mdata:
        _ctx_push_mdata(parse_amc_mdata(input_tex))
    for mdata in CTX["mdata"][::-1]:
        for key, val in mdata.items():
            # filtering (for now) itm_instances to not be in the final
            # items.json
            if key == "itm_instances":
                continue
            if key == "itm_tags":
                if "tags" not in item:
                    item["tags"] = list()
                item["tags"] = sorted(
                    list(set(item["tags"] + list(mdata["itm_tags"])))
                )
            elif key not in item:
                item[key] = val  # type: ignore
    CTX["num"] += 1
    item["num"] = CTX["num"]
    try:
        code, parent, order = CTX["stack"].pop()
        item["itm_parent"] = parent
        item["itm_order"] = order + 1
        CTX["stack"].append((code, parent, order + 1))
    except IndexError:
        pass
    if read_mdata:
        _ctx_pop_mdata()
    return item


def check_pack(json_file: Path) -> str:
    exn_msg = f"{json_file}: invalid pack specification"
    try:
        result = json_file.read_text()
        typeguard.check_type(json.loads(result), types.pack_spec_t)
    except typeguard.TypeCheckError as ex:
        raise ValueError(exn_msg) from ex
    except json.decoder.JSONDecodeError as ex:
        raise ValueError(exn_msg) from ex
    return result


def parse_amc_mdata(
        file_path: Path,
        file_content: str | None = None
) -> amc_mdata_t:
    if file_content is None:
        file_content = file_path.read_text()
    result: amc_mdata_t = dict()
    lg = len(WEBAMC_COMMENT)
    for line in file_content.split("\n"):
        if line.startswith(WEBAMC_COMMENT):
            directive = line[lg:].strip()
            if directive in ("BEGIN", "END"):
                continue
            try:
                var, val = (d.strip() for d in directive.split("="))
                mdata = _check_item_mdata(var)

                if var is None:
                    output.warning(f"{file_path}: unknown field {mdata}")
                elif var == "INSTANCES":
                    result["itm_instances"] = int(val)
                elif mdata == "TAG":
                    if "itm_tags" not in result:
                        result["itm_tags"] = [val]
                    else:
                        result["itm_tags"].append(val)
                elif mdata == "DIFFICULTY":
                    result["itm_difficulty"] = int(val)
                elif mdata == "CODE":
                    result["itm_code"] = val
                elif mdata == "TITLE":
                    result["itm_title"] = val
                elif mdata == "RND":
                    result["itm_rnd"] = bool(int(val))
                elif mdata == "STANDALONE":
                    result["itm_standalone"] = bool(int(val))
                elif mdata == "VISIBLE":
                    result["itm_visible"] = bool(int(val))
            except ValueError:
                output.warning(f"{file_path}: skipped comment {directive}")
    return result


def _pdf_to_png(pdf: Path, png: Path) -> bool:
    try:
        result = True
        with pymupdf.open(pdf) as pages:  # type: ignore[no-untyped-call]
            if len(pages) > 1:
                output.warning(f"{pdf} contains more than 1 page")
            pix = pages[0].get_pixmap(alpha=True, dpi=150)
            pix.save(png)
    except:
        output.error(f"could not convert {pdf} to {png}")
        result = False
    return result


def _crop_png(png: Path) -> bool:
    try:
        result = True
        with Image.open(png) as img:
            img.crop(img.getbbox()).save(png)
    except:
        output.error(f"could not crop {png}")
        result = False
    return result


def _exec_and_log(
        args: list[str],
        cwd: Path | None = None
) -> bool:

    cmd = " ".join(args)

    # running the process
    proc_result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        cwd=cwd,
        input=""
    )

    result = proc_result.returncode == 0

    if not result:
        output.error(f"there was an error with command {cmd}")

    # log output
    if config.CONFIG["log_file"] is None:

        # if log_file is none, it will write in the console
        if proc_result.stdout:
            sys.stdout.write(proc_result.stdout)
        if proc_result.stderr:
            sys.stderr.write(proc_result.stderr)

    else:

        assert CTX["log_dir"] is not None

        # getting process number
        p_name = multiprocessing.current_process().name

        # extracting process number from str (process-1 => 1)
        worker_id = "".join(filter(str.isdigit, p_name))
        if not worker_id:
            worker_id = str(os.getpid())

        log_file = CTX["log_dir"] / f"{worker_id}.log"

        with open(log_file, "a", encoding="UTF-8") as f:
            cmt = 79 * "*" + "\n"
            f.write(cmt)
            f.write("* " + " " + cmd + "\n")
            f.write(cmt)
            if proc_result.stdout:
                f.write(proc_result.stdout)
            if proc_result.stderr:
                f.write("\n" + proc_result.stderr)
            f.write("\n")

    return result


def _merge_logs() -> None:
    assert CTX["log_dir"] is not None
    assert config.CONFIG["log_file"] is not None
    log = "\n".join(
        log.read_text()
        for log in CTX["log_dir"].iterdir()
        if log.is_file()
    )
    Path(config.CONFIG["log_file"]).write_text(log, encoding="utf-8")


def _tex_to_png(
        input_tex: Path,
        output_dir: Path,
        item: item_t,
        mcq_dir: Path | None,
        headers: list[tuple[str, str]],
        tex_content: str | None,
        info: str | None,
        instance_id: int,
        png_file: Path,
        seed: int,
        dyn_vars: dict[str, str],
        dyn_code: str | None,
) -> None:

    # use png_file from task directly instead of looking for item["png"]
    output_png = output_dir / png_file

    msg = f"compile {input_tex}"
    if info is not None:
        msg = f"{msg} {info}"
    msg = f"{msg} to {output_png}"
    output.info(msg)

    # check that pdflatex executable can be found
    tex2pdf_exe = Path(config.CONFIG["tex2pdf_exe"])
    tex2pdf_exe_args = config.CONFIG["tex2pdf_exe_args"]
    if not tex2pdf_exe.is_absolute():
        tex2pdf_exe = io.get_executable_path(tex2pdf_exe)

    dir_path = input_tex.parent

    # the directory when pdflatex will execute
    execution_dir = mcq_dir if mcq_dir is not None else dir_path

    if tex_content is None:
        tex_content = input_tex.read_text()

    # create the content of the tex file to compile
    tex_headers = "\n%\n".join(
        f"% header from {header_file}\n{header_content}"
        for header_file, header_content in headers
    )

    # dynamic code
    tex_dyn = "\n".join(
        (rf"\def\WEBAMCVAR{var}{{{val}}}" + "\n")
        for var, val in dyn_vars.items()
    )
    if tex_dyn != "":
        tex_dyn = (
            "%%%%%%%%%%\n"
            + "% python generated variables\n"
            + tex_dyn
        )
    if dyn_code is not None:
        tex_dyn = (
            tex_dyn
            + "%%%%%%%%%%\n"
            + "% dynamic code provided by the user\n"
            + dyn_code
        )

    tex_content = (
        r"\documentclass{article}" + "\n"
        + "%%%%%%%%%%\n"
        + "% variables generated by webamc\n"
        + r"\def\WEBAMC{1}" + "\n"
        + rf"\def\WEBAMCinstance{{{instance_id}}}  % instance number" + "\n"
        + rf"\def\WEBAMCseed{{{seed}}} % seed of the instance" + "\n"
        + "%%%%%%%%%%\n"
        + tex_headers + "\n"
        + "%%%%%%%%%%\n"
        + "% try to auto-seed some common latex packages (fp and pgfmath)\n"
        + r"\ifdefined\FPseed\FPseed=\WEBAMCseed\fi" + "\n"
        + r"\ifdefined\pgfmathsetseed\pgfmathsetseed\WEBAMCseed\fi" + "\n"
        + "%%%%%%%%%%\n"
        + tex_dyn + "\n"
        + r"\begin{document}" + "\n"
        + r"\pagestyle{empty}" + "\n"
        + "%%%%%%%%%%\n"
        + f"% tex code from {input_tex}" + "\n"
        + rf"\noindent {tex_content}" + "\n"
        + r"\end{document}" + "\n"
    )

    # create a temporary dir to create pngs, it will delete himself at the end
    with tempfile.TemporaryDirectory() as tmp_dir:

        tmp_path = Path(tmp_dir)
        tex_file_path = tmp_path / "main.tex"
        with open(tex_file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(tex_content)

        args = [
            str(tex2pdf_exe),
            *[arg.format(
                out_dir=str(tmp_dir),
                tex_file=str(tex_file_path)
            ) for arg in tex2pdf_exe_args]
        ]

        # the pdflatex commands will run on the "execution_dir"
        # directory
        exec_result = _exec_and_log(args, cwd=execution_dir)

        pdf_file_name = tmp_path / "main.pdf"
        png_file_name = tmp_path / "main.png"

        # create the output_png directory, if exists, the subprocess
        # will not crash.
        output_png.parent.mkdir(parents=True, exist_ok=True)

        if (
            exec_result
            and pdf_file_name.exists()
            and pdf_file_name.stat().st_size > 0
            and _pdf_to_png(pdf_file_name, png_file_name)
            and _crop_png(png_file_name)
        ):
            png_file_name.rename(output_png)


def _generate_png_path() -> Path:
    h = uuid.uuid4().hex
    return Path("png") / str(h[:2]) / f"{h}.png"


def _extract_code(content: str) -> tuple[str, str]:
    comment_begin = "%webamc BEGIN"
    comment_end = "%webamc END"
    lines = content.split("\n")
    in_block = False
    new_content = list()
    code = list()
    for line in lines:
        if in_block:
            if line.strip() == comment_end:
                in_block = False
            else:
                code.append(line)
        else:
            if line.strip() == comment_begin:
                in_block = True
            else:
                new_content.append(line)
    return "\n".join(new_content), "\n".join(code)


def _compile_question(
        input_tex: Path,
        output_dir: Path,
        mcq_dir: None | Path
) -> list[item_t]:

    content = input_tex.read_text()
    content, dyn_code = _extract_code(content)

    # check if an external python script exists for this question
    py_file_path = input_tex.parent / (input_tex.stem + ".py")
    has_py_script = py_file_path.exists() and py_file_path.is_file()
    py_code = ""
    if has_py_script:
        output.info(f"external python file found: {py_file_path}")
        py_code = py_file_path.read_text()

    # parse tex file to find questions
    code, qsts = tex.extract_qst(content)

    # if no question is found, display an error and abort
    if qsts == list():
        msg = tex.tex_error_msg[code]
        funcs = {
            "error_": output.error,
            "info_": output.info,
            "warning_": output.warning
        }
        for prefix, func in funcs.items():
            if code.startswith(prefix):
                func(f"{input_tex}: {msg}")
        return list()

    result: list[item_t] = list()
    if mcq_dir is not None:
        root_mcq_dir = mcq_dir
    else:
        root_mcq_dir = input_tex.parent

    # read webamc metadata (instances, random, tags...)
    mdata = parse_amc_mdata(input_tex, content)
    num_instances = mdata.get("itm_instances", 1)
    is_dynamic = num_instances > 1 or dyn_code != ""

    # prepare templates (mother items)
    qst_templates: list[qst_template_t] = []
    for qst in qsts:

        # setup the main question template
        item = _ctx_new_item(input_tex)
        item["itm_code"] = qst["itm_code"]
        item["itm_type"] = types.ITEM_TYPE_QUESTION
        item["qst_type"] = qst["qst_type"]
        item["instances"] = list()

        _ctx_push_item(item)

        # setup the choices linked to this specific question
        choices_templates = []
        iterator = tex.iter_on_choices(qst)
        for num, (correct, last, cho_tex) in enumerate(iterator):
            cho_item = _ctx_new_item(input_tex, False)
            cho_item["itm_type"] = types.ITEM_TYPE_CHOICE
            cho_item["cho_correct"] = correct
            cho_item["cho_last"] = last
            cho_item["instances"] = list()
            choices_templates.append((cho_item, cho_tex, num))

        _ctx_pop_item()

        qst_templates.append({
            "item": item,
            "qst_data": qst,
            "choices": choices_templates
        })

    # generate children (instances loop)
    for instance_id in range(1, num_instances + 1):

        if not is_dynamic:
            seed_val = 0
            dyn_vars: dict[str, str] = dict()

        else:
            # creating a unique and reproducible seed value for this
            # specific instance
            seed_val = (instance_id * 123456789) % 2147483647
            dyn_vars = dict()

            # execute external python script and fetch its VAR dict
            if has_py_script:
                env: dict[str, tp.Any] = {}
                try:
                    exec(py_code, env)
                    if "VAR" in env and isinstance(env["VAR"], dict):
                        dyn_vars = {**dyn_vars, **env["VAR"]}
                except Exception as ex:  # pylint: disable=W0718
                    output.error(
                        f"Exception catched in {py_file_path}: {ex}"
                    )

        headers_for_instance = list(CTX["headers"])

        # create tasks for multiprocessing
        for qst_entry in qst_templates:
            main_item = qst_entry["item"]
            qst = qst_entry["qst_data"]

            # tasks for the main question
            png_file = _generate_png_path()

            main_item["instances"].append({
                "iti_num": instance_id,
                "iti_seed": seed_val,
                "png": str(png_file)
            })

            info_qst = f"(instance {instance_id})" if is_dynamic else None

            TASKS.append({
                "input_tex": input_tex,
                "output_dir": output_dir,
                "item": main_item,
                "mcq_dir": root_mcq_dir,
                "tex_content": tex.qst_tex_header(qst),
                "info": info_qst,
                "headers": headers_for_instance,
                "instance_id": instance_id,
                "png_file": png_file,
                "seed": seed_val,
                "dyn_vars": dyn_vars,
                "dyn_code": dyn_code
            })

            # tasks for the choices
            for cho_item, cho_tex, num in qst_entry["choices"]:
                png_cho = _generate_png_path()

                cho_item["instances"].append({
                    "iti_num": instance_id,
                    "iti_seed": seed_val,
                    "png": str(png_cho)
                })

                if is_dynamic:
                    info_cho = f"(instance {instance_id} - choice {num})"
                else:
                    info_cho = f"(choice {num})"

                TASKS.append({
                    "input_tex": input_tex,
                    "output_dir": output_dir,
                    "item": cho_item,
                    "mcq_dir": root_mcq_dir,
                    "tex_content": cho_tex,
                    "info": info_cho,
                    "headers": headers_for_instance,
                    "instance_id": instance_id,
                    "png_file": png_cho,
                    "seed": seed_val,
                    "dyn_vars": dyn_vars,
                    "dyn_code": dyn_code
                })

    # flatten the list to return all items (questions and choices)
    for qst_entry in qst_templates:
        result.append(qst_entry["item"])
        for cho_item, _, _ in qst_entry["choices"]:
            result.append(cho_item)

    return result


def _compile_dir_traversal(
        input_dir: Path,
        output_dir: Path,
        mcq_dir: None | Path
) -> list[item_t]:

    result: list[item_t] = list()

    cfg = config.CONFIG
    special_files = [
        "json_file_pack",
        "tex_file_exercise",
        "tex_file_header",
        "tex_file_mcq",
        "tex_file_webamc"
    ]

    # check which special files are in the directory
    files = {
        f: path
        for f, path in
        {sf: input_dir / cfg[sf]  # type: ignore
         for sf in special_files}.items()
        if path.is_file()
    }

    # header file
    if "tex_file_header" in files:
        path = files["tex_file_header"]
        _ctx_push_header((path, path.read_text()))

    # meta-data file
    if "tex_file_webamc" in files:
        _ctx_push_mdata(parse_amc_mdata(files["tex_file_webamc"]))

    # pack file
    pack: str | None = None
    if "json_file_pack" in files:
        pack = check_pack(files["json_file_pack"])

    # mcq or exercise tex file
    in_exe = False
    for f in ["tex_file_mcq", "tex_file_exercise"]:
        if f in files:
            in_exe = True
            item = _ctx_new_item(files[f])
            item["is_mcq"] = f == "tex_file_mcq"
            if pack is None:
                item["itm_type"] = types.ITEM_TYPE_EXERCISE
            else:
                item["itm_type"] = types.ITEM_TYPE_PACK
                item["pak_spec"] = pack

            png_file = _generate_png_path()
            item["instances"] = [{
                "iti_num": 1,
                "iti_seed": 0,
                "png": str(png_file)
            }]

            TASKS.append({
                "input_tex": files[f],
                "output_dir": output_dir,
                "item": item,
                "mcq_dir": mcq_dir,
                "tex_content": None,
                "info": None,
                "headers": list(CTX["headers"]),
                "instance_id": 1,
                "png_file": png_file,
                "seed": 0,
                "dyn_vars": dict(),
                "dyn_code": None
            })

            _ctx_push_item(item)
            result.append(item)
            if f == "tex_file_mcq":
                mcq_dir = input_dir.absolute()
            break

    # traverse the directory recursively
    for entry in input_dir.iterdir():
        if entry.is_dir():
            result += _compile_dir_traversal(entry, output_dir, mcq_dir)
        elif entry.is_file():
            if (
                    io.get_file_extension(entry.name) == ".tex"
                    and entry.name.startswith(cfg["tex_file_question_prefix"])
            ):
                result += _compile_question(entry, output_dir, mcq_dir)

    # post treatment
    if "tex_file_header" in files:
        _ctx_pop_header()
    if "tex_file_webamc" in files:
        _ctx_pop_mdata()
    if in_exe:
        _ctx_pop_item()

    return result


def action(input_dir: str, prefix: str, max_threads: int = 4) -> None:
    global TASKS
    TASKS = list()
    output.info(f"Compilation starts with {max_threads} threads")

    # everything will be written in a temporary directory
    with (
            tempfile.TemporaryDirectory() as tmp_dir,
            tempfile.TemporaryDirectory() as log_dir
    ):
        CTX["log_dir"] = Path(log_dir)

        # traverse input_dir to generate json
        items = _compile_dir_traversal(Path(input_dir), Path(tmp_dir), None)

        # generate png with items and TASKS
        with futures.ProcessPoolExecutor(max_workers=max_threads) as executor:
            results = [executor.submit(_tex_to_png, **task) for task in TASKS]
            for future in futures.as_completed(results):
                try:
                    future.result()
                except Exception as ex:
                    output.error(f"An error happened in worker {ex}")
                    traceback.print_exc()
                    raise SystemExit(1) from ex

        json_path = Path(tmp_dir) / JSON_SPEC
        with open(json_path, "w", encoding="utf-8") as fd:
            fd.write(json.dumps(items, indent=2))

        # zip the the temporary directory and remove it
        shutil.make_archive(prefix, "zip", root_dir=tmp_dir)

        # merge logs
        if config.CONFIG["log_file"] is not None:
            _merge_logs()
