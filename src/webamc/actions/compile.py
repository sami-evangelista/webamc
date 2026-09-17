import glob
import subprocess
import traceback
import shutil
import hashlib
import uuid
import multiprocessing
import concurrent.futures
import pymupdf
from PIL import Image

from webamc.all import *
from webamc.util import io
from . import tex, output

import re


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
        "iti_num": int,
        "iti_seed": int,
        "png": str,
        "iti_img": bytes
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
        "png": str,
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
        "mdata": list[amc_mdata_t]
    }
)
CTX: ctx_t = {
    "num": 0,
    "headers": list(),
    "stack": list(),
    "mdata": list()
}
WEBAMC_COMMENT = "%webamc "


# task type used for tasks
task_t = tp.TypedDict(
    "task_t",
    {
        "input_tex": str,
        "output_dir": str,
        "item": item_t,
        "mcq_dir": str | None,
        "tex_content": str | None,
        "info": str | None,
        "headers": list[tuple[str, str]],
        "instance_id": int,
        "png_file": str
    },
    total=False
)

# tasks used for multiprocessing
TASKS: list[task_t] = []


def _check_item_mdata(mdata: str) -> None | types.item_mdata_t:
    if mdata in types.literal_type_values(types.item_mdata_t):
        return tp.cast(types.item_mdata_t, mdata)
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


def _ctx_new_item(input_tex: str, read_mdata: bool = True) -> item_t:
    item: item_t = dict()
    item["tex_file"] = input_tex
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


def _item_set_png_file(item: item_t) -> None:
    t = item["itm_type"]
    h: str = {
        types.ITEM_TYPE_CHOICE: "cho",
        types.ITEM_TYPE_EXERCISE: "exe",
        types.ITEM_TYPE_PACK: "pak",
        types.ITEM_TYPE_QUESTION: "qst"
    }[t]
    if t != types.ITEM_TYPE_CHOICE:
        code = item["itm_code"]
    else:
        h = f"{h}[{item['itm_order']}]"
        code, _, _ = CTX["stack"][-1]
    h = f"{h}/{code}"
    hval = hashlib.md5(h.encode()).hexdigest()
    item["png"] = os.path.join("png", hval[0:2], hval[2:] + ".png")


def check_pack(json_file: str) -> str:
    exn_msg = f"{json_file}: invalid pack specification"
    def check(spec: tp.Any) -> bool:
        if isinstance(spec, list):
            return all(check(x) for x in spec)
        if isinstance(spec, dict):
            op = spec.get("op", "all")
            rev = spec.get("rev", False)
            arg = spec.get("arg", None)
            content = spec.get("content")
            if op not in types.literal_type_values(types.pack_op_t):
                return False
            top = tp.cast(types.pack_op_t, op)
            if not isinstance(rev, bool):
                return False
            if content is not None and not check(content):
                return False
            if top == "sort":
                return arg in ("code", "difficulty")
            if top == "head":
                return isinstance(arg, int)
            if top in ("with-code", "with-difficulty", "with-tag"):
                t = int if top == "with-difficulty" else str
                return (
                    isinstance(arg, list)
                    and all(isinstance(a, t) for a in arg)
                )
            return True
        return False
    try:
        result = io.read_file_content(json_file)
        if not check(json.loads(result)):
            raise ValueError(exn_msg)
    except json.decoder.JSONDecodeError as ex:
        raise ValueError(exn_msg) from ex
    return result


def parse_amc_mdata(
        file_path: str,
        file_content: str | None = None
) -> amc_mdata_t:
    if file_content is None:
        file_content = io.read_file_content(file_path)
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


def _pdf_to_png(pdf: str, png: str) -> bool:
    try:
        result = True
        with pymupdf.open(pdf) as pages: # type: ignore[no-untyped-call]
            if len(pages) > 1:
                output.warning(f"{pdf} contains more than 1 page")
            pix = pages[0].get_pixmap(alpha=True, dpi=150)
            pix.save(png)
    except:
        output.error(f"could not convert {pdf} to {png}")
        result = False
    return result


def _crop_png(png: str) -> bool:
    try:
        result = True
        with Image.open(png) as img:
            img.crop(img.getbbox()).save(png)
    except:
        output.error(f"could not crop {png}")
        result = False
    return result


def _tex_to_png(
        input_tex: str,
        output_dir: str,
        item: item_t,
        mcq_dir: str | None,
        # headers added because CTX global
        # variable can't be used in parallelisation
        headers: list[tuple[str, str]],
        tex_content: str | None = None,
        info: str | None = None,
        instance_id: int = 1,
        png_file: str = ""
) -> None:

    # use png_file from task directly instead of looking for item["png"]
    output_png = os.path.join(output_dir, png_file)

    msg = f"compile {input_tex}"
    if info is not None:
        msg = f"{msg} {info}"
    msg = f"{msg} to {output_png}"
    output.info(msg)

    # check that pdflatex executable can be found
    tex2pdf_exe = config.CONFIG["tex2pdf_exe"]
    tex2pdf_exe_args = config.CONFIG["tex2pdf_exe_args"]
    if not os.path.isabs(tex2pdf_exe):
        tex2pdf_exe = io.get_executable_path(tex2pdf_exe)

    dir_path = os.path.dirname(input_tex)

    # the directory when pdflatex will execute
    execution_dir = mcq_dir if mcq_dir is not None else dir_path

    if tex_content is None:
        tex_content = io.read_file_content(input_tex)

    # create the content of the tex file to compile
    sep = "\n%\n"
    tex_headers = sep.join(
        f"%%%%% header from {header_file} %%%%%{sep}{header_content}"
        for header_file, header_content in headers
    )
    tex_content = (
        r"\documentclass{article}" + sep
        + r"\def\WEBAMC{1}" + sep + tex_headers
        + r"\begin{document}" + sep
        + r"\pagestyle{empty}" + sep
        + f"%%%%% tex content from {input_tex} %%%%%{sep}"
        + r"\noindent{" + tex_content + "}" + sep
        + r"\end{document}" + sep
    )

    # create a temporary dir to create pngs, it will delete himself at the end
    with tempfile.TemporaryDirectory() as tmp_dir:

        # create a trash temporary directory, it contains tex files,
        # it will delete himself at the end.
        tex_file_path = os.path.join(tmp_dir, "qcm.tex")
        with open(tex_file_path, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(tex_content)

        args = [
            tex2pdf_exe,
            *[arg.format(
                out_dir=tmp_dir,
                tex_file=tex_file_path
            ) for arg in tex2pdf_exe_args]
        ]

        # the pdflatex commands will run on the "execution_dir"
        # directory
        exec_result = exec_and_log(args, cwd=execution_dir)

        pdf_file_name = os.path.join(tmp_dir, "qcm.pdf")
        png_file_name = os.path.join(tmp_dir, "qcm.png")

        # create the output_png directory, if exists, the subprocess
        # will not crash.
        os.makedirs(os.path.dirname(output_png), exist_ok=True)

        if (
            exec_result
            and os.path.exists(pdf_file_name)
            and os.path.getsize(pdf_file_name) > 0
            and _pdf_to_png(pdf_file_name, png_file_name)
            and _crop_png(png_file_name)
        ):
            shutil.move(png_file_name, output_png)


def _generate_png_path() -> str:
    h = uuid.uuid4().hex
    return f"png/{h[:2]}/{h}.png"


def _compile_question(
        input_tex: str,
        output_dir: str,
        mcq_dir: None | str
) -> list[item_t]:

    # extract tex content and custom latex variables block (%webamc
    # BEGIN / END)
    content = io.read_file_content(input_tex)
    var_block = ""
    begin_tag = "%webamc BEGIN"
    end_tag = "%webamc END"

    if begin_tag in content and end_tag in content:
        start_idx = content.find(begin_tag) + len(begin_tag)
        end_idx = content.find(end_tag)
        var_block = content[start_idx:end_idx].strip()
        content = (
            content[:content.find(begin_tag)]
            + content[end_idx + len(end_tag):]
        )

    # check if an external python script exists for this question
    py_file_path = os.path.splitext(input_tex)[0] + ".py"
    has_py_script = os.path.isfile(py_file_path)
    py_code = ""
    if has_py_script:
        output.info(f"Extern python filed founded : {py_file_path}")
        py_code = io.read_file_content(py_file_path)

    # parse tex file to find questions and clean the preamble
    code, qsts = tex.extract_qst(content)
    raw_preamble = re.split(r"\\begin\{question(?:mult)?\}", content, maxsplit=1)[0]


    clean_preamble = re.sub(
        r"\\documentclass(\[.*?\])?\{.*?\}",
        "",
        raw_preamble
    )

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
        root_mcq_dir = os.path.dirname(input_tex)

    # read webamc metadata (instances, random, tags...)
    mdata = parse_amc_mdata(input_tex, content)
    num_instances = mdata.get("itm_instances", 1)
    is_dynamic = num_instances > 1 or var_block != ""

    # prepare templates (mother items)
    qst_templates: list[qst_template_t] = []
    for qst in qsts:
        # setup the main question template
        item = _ctx_new_item(input_tex)
        item["itm_code"] = qst["itm_code"]
        item["itm_type"] = types.ITEM_TYPE_QUESTION
        item["qst_type"] = qst["qst_type"]
        item["instances"] = []

        _ctx_push_item(item)

        # setup the choices linked to this specific question
        choices_templates = []
        iterator = tex.iter_on_choices(qst)
        for num, (correct, last, cho_tex) in enumerate(iterator):
            cho_item = _ctx_new_item(input_tex, False)
            cho_item["itm_type"] = types.ITEM_TYPE_CHOICE
            cho_item["cho_correct"] = correct
            cho_item["cho_last"] = last
            cho_item["instances"] = []
            choices_templates.append((cho_item, cho_tex, num))

        _ctx_pop_item()

        qst_templates.append({
            "item": item,
            "qst_data": qst,
            "choices": choices_templates
        })

    # generate children (instances loop)
    for instance_id in range(1, num_instances + 1):

        # prevent amc watermark from appearing
        anti_brouillon = (
            r"\makeatletter\ifdefined\AMC@watermarkfalse" +
            r"\AMC@watermarkfalse\fi\makeatother"
        )

        if not is_dynamic:
            seed_val = 0
            dynamic_header = f"{clean_preamble}\n{anti_brouillon}\n"

        else:
            # creating a unique and reproducible
            # seed value for this specific instance
            # seed_val = (instance_id * 123456789) % 2147483647
            # seed_magic = f"\\ifdefined\\FPseed\\FPseed={seed_val}\\fi\n\\" + \
            # f"ifdefined\\pgfmathsetseed\\pgfmathsetseed{{{seed_val}}}\\fi"
            # custom_vars_latex = ""

            seed_val = (instance_id * 123456789) % 2147483647

            # We expose the seed via \WEBAMCseed for any custom random package.
            # We also try to auto-seed the most common ones (fp and pgfmath)
            # if they are defined, without forcing them.
            seed_magic = (
                f"\\def\\WEBAMCseed{{{seed_val}}}\n"
                f"\\ifdefined\\FPseed\\FPseed={seed_val}\\fi\n"
                f"\\ifdefined\\pgfmathsetseed\\pgfmathsetseed{{{seed_val}}}\\fi\n"
            )
            custom_vars_latex = ""

            # execute external python script
            # and translate its VAR dict into latex definitions
            if has_py_script:
                env: dict[str,tp.Any] = {}
                try:
                    import random
                    random.seed(seed_val)
                    exec(py_code, env)

                    if "VAR" in env and isinstance(env["VAR"], dict):
                        for key, value in env["VAR"].items():
                            var_latex = f"\\def\\VAR{key}{{{value}}}\n"
                            custom_vars_latex += var_latex

                except Exception as e:
                    output.error(
                        f"Exception catched in '{py_file_path}' : {e}"
                    )

            if var_block != "":
                custom_vars_latex += f"{var_block}\n"

            # build the final dynamic latex header for this instance
            dynamic_header = (
                f"{clean_preamble}\n{anti_brouillon}\n{seed_magic}\n"
                f"{custom_vars_latex}\n\\def\\thecopy{{{instance_id}}}\n"
            )

        headers_for_instance = list(CTX["headers"])
        headers_for_instance.append(("variables_fp", dynamic_header))

        # create tasks for multiprocessing
        for qst_entry in qst_templates:
            main_item = qst_entry["item"]
            qst = qst_entry["qst_data"]

            # tasks for the main question
            png_file = _generate_png_path()

            main_item["instances"].append({
                "iti_num": instance_id,
                "iti_seed": seed_val,
                "png": png_file
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
                "png_file": png_file
            })

            # tasks for the choices
            for cho_item, cho_tex, num in qst_entry["choices"]:
                png_cho = _generate_png_path()

                cho_item["instances"].append({
                    "iti_num": instance_id,
                    "iti_seed": seed_val,
                    "png": png_cho
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
                    "png_file": png_cho
                })

    # flatten the list to return all items (questions and choices)
    for qst_entry in qst_templates:
        result.append(qst_entry["item"])
        for cho_item, _, _ in qst_entry["choices"]:
            result.append(cho_item)

    return result


def _compile_dir_traversal(
        input_dir: str,
        output_dir: str,
        mcq_dir: None | str
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
        {sf: os.path.join(input_dir, cfg[sf])  # type: ignore
         for sf in special_files}.items()
        if os.path.isfile(path)
    }

    # header file
    if "tex_file_header" in files:
        path = files["tex_file_header"]
        _ctx_push_header((path, io.read_file_content(path)))

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
                "png": png_file
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
                "png_file": png_file
            })

            _ctx_push_item(item)
            result.append(item)
            if f == "tex_file_mcq":
                mcq_dir = os.path.abspath(input_dir)
            break

    # traverse the directory recursively
    for entry in sorted(os.listdir(input_dir)):
        input_path = os.path.join(input_dir, entry)
        if os.path.isdir(input_path):
            result += _compile_dir_traversal(input_path, output_dir, mcq_dir)
        elif os.path.isfile(input_path):
            if (
                    io.get_file_extension(entry) == ".tex"
                    and entry.startswith(cfg["tex_file_question_prefix"])
            ):
                result += _compile_question(input_path, output_dir, mcq_dir)

    # post treatment
    if "tex_file_header" in files:
        _ctx_pop_header()
    if "tex_file_webamc" in files:
        _ctx_pop_mdata()
    if in_exe:
        _ctx_pop_item()

    return result


def clean_logs() -> None:
    base_log_file = config.CONFIG["log_file"]
    if base_log_file:
        filename, ext = os.path.splitext(base_log_file)
        for old_log in glob.glob(f"{filename}-*{ext}"):
            try:
                os.remove(old_log)
            except OSError:
                pass


def exec_and_log(args: list[str], cwd: str | None = None) -> bool:
    cmd = " ".join(args)

    # running the process
    proc_result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        cwd=cwd
    )

    success = proc_result.returncode == 0

    if not success:
        output.error(f"there was an error with command {cmd}")

    # log file
    base_log_file = config.CONFIG.get("log_file")

    if not base_log_file:

        # if log_file is none, it will write in the console
        if proc_result.stdout:
            sys.stdout.write(proc_result.stdout)
        if proc_result.stderr:
            sys.stderr.write(proc_result.stderr)

    else:

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
            cmt = (62 + len(cmd)) * "*" + "\n"
            f.write(cmt)
            f.write(30 * "*" + " " + cmd + " " + 30 * "*" + "\n")
            f.write(cmt)

            if proc_result.stdout:
                f.write(proc_result.stdout)
            if proc_result.stderr:
                f.write("\n" + proc_result.stderr)
            f.write("\n")

    return success


def action(input_dir: str, prefix: str, max_threads: int = 4) -> None:
    global TASKS
    TASKS = [] # TASKS is empty when the compilation starts

    print(f"Compilation starts with {max_threads} threads")
    # everything will be written in a temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:

        # traverse input_dir to generate json
        clean_logs()
        items = _compile_dir_traversal(input_dir, tmp_dir, None)

        # generate png with items and TASKS
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=max_threads
        ) as executor:
            futures = [executor.submit(_tex_to_png, **task) for task in TASKS]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    output.error(f"An error happened in worker {exc}")
                    traceback.print_exc()
                    raise SystemExit(1)

        json_path = os.path.join(tmp_dir, JSON_SPEC)
        with open(json_path, "w", encoding="utf-8") as fd:
            fd.write(json.dumps(items, indent=2))

        # zip the the temporary directory and remove it
        shutil.make_archive(prefix, "zip", root_dir=tmp_dir)
