#!/usr/bin/env python3

import glob
import tempfile
import shutil
import hashlib
from PIL import Image
import pymupdf 
import concurrent.futures

from webamc.all import *
from webamc.util import log, io
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
        "qst_type": types.question_type_t
    },
    total=False
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
        "headers": list[tuple[str, str]]
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
            # filtering (for now) itm_instances to not be in the final items.json
            if (key == "itm_instances"):
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
            if (directive in ("BEGIN", "END")):
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
        headers: list[tuple[str, str]], # headers added because CTX global variable can't be used in parallelisation
        tex_content: str | None = None,
        info: str | None = None
) -> None:
    # _item_set_png_file(item) # _item_set_png_file is used during the prepartion process
    output_png = os.path.join(output_dir, item["png"])

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

    # # create a temp file for latex content and compute some other file names
    # with tempfile.NamedTemporaryFile(
    #         dir=".", mode="w", suffix=".tex", encoding="utf-8",
    #         delete=False
    # ) as tmp_file:

    #     tmp_file.write(tex_content)
    #     tmp_file.close()

    #     # the output of pdflatex will be written in a temporary directory
    #     with tempfile.TemporaryDirectory() as tmp_dir:

    #         # pdflatexify the file and move back the previous directory
    #         args = [
    #             tex2pdf_exe,
    #             *[arg.format(
    #                 out_dir=tmp_dir,
    #                 tex_file=os.path.abspath(tmp_file.name)
    #             ) for arg in tex2pdf_exe_args]
    #         ]
    #         exec_result = log.log_exec(args, cwd=execution_dir)
            

    #         # check pdflatex terminated correctly and that the
    #         # resulting pdf is not empty and then convert it to png
    #         # and finally crop it
    #         path = Path(tmp_file.name).stem
    #         pdf_file_name = os.path.join(tmp_dir, path + ".pdf")
    #         png_file_name = os.path.join(tmp_dir, path + ".png")
    #         if (
    #                 exec_result
    #                 and os.path.exists(pdf_file_name)
    #                 and os.path.getsize(pdf_file_name) > 0
    #                 and _pdf_to_png(pdf_file_name, png_file_name)
    #                 and _crop_png(png_file_name)
    #                 and io.mkdir_of_file(output_png)
    #         ):
    #             shutil.move(png_file_name, output_png)
    # os.remove(tmp_file.name)

    # create a temporary dir to create pngs, it will delete himself at the end
    with tempfile.TemporaryDirectory() as tmp_dir:
        
        # create a trash temporary directory, it contains tex files, it will delete himself at the end.
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
        
        # the pdflatex commands will run on the "execution_dir" directory
        exec_result = log.log_exec(args, cwd=execution_dir)
        
        pdf_file_name = os.path.join(tmp_dir, "qcm.pdf")
        png_file_name = os.path.join(tmp_dir, "qcm.png")
        
        # create the output_png directory, if exists, the subprocess will not crash.
        os.makedirs(os.path.dirname(output_png), exist_ok=True)
        
        if (
            exec_result
            and os.path.exists(pdf_file_name)
            and os.path.getsize(pdf_file_name) > 0
            and _pdf_to_png(pdf_file_name, png_file_name)
            and _crop_png(png_file_name)
        ):
            shutil.move(png_file_name, output_png)


def _compile_question(
        input_tex: str,
        output_dir: str,
        mcq_dir: None | str
) -> list[item_t]:

    # parse tex
    content = io.read_file_content(input_tex)
    var_block = ""
    begin_tag = "%webamc BEGIN"
    end_tag = "%webamc END"
    if (begin_tag in content and end_tag in content):
        start_idx = content.find(begin_tag) + len(begin_tag)
        end_idx = content.find(end_tag)
        var_block = content[start_idx:end_idx].strip()
        content = content[:content.find(begin_tag)] + content[end_idx + len(end_tag):]


    code, qsts = tex.extract_qst(content)
    envs = config.CONFIG["tex_envs_question"]
    envs_pattern = "|".join(envs)
    match = re.search(
        r"\\begin\{(" + envs_pattern + r")\}", 
        content
    )
    if match:
        raw_preamble = content[:match.start()]
    else:
        raw_preamble = content

    clean_preamble = re.sub(
        r"\\documentclass(\[.*?\])?\{.*?\}", 
        "", 
        raw_preamble
    )
    #clean_preamble = clean_preamble.replace(r"\begin{document}", "")
    #raw_preamble = content.split(r"\begin{question}")[0]
    #clean_preamble = re.sub(r"\\documentclass(\[.*?\])?\{.*?\}", "", raw_preamble)
    clean_preamble = clean_preamble.replace(r"\begin{document}", "")

    # no question found => exit
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
    root_mcq_dir = mcq_dir if mcq_dir is not None else os.path.dirname(input_tex)

    mdata = parse_amc_mdata(input_tex, content)
    num_instances = mdata.get("itm_instances", 1)
    is_dynamic = num_instances > 1 or var_block != ""

    for instance_id in range(1, num_instances + 1):
        anti_brouillon = ( r"\makeatletter\ifdefined\AMC@watermarkfalse"
        r"\AMC@watermarkfalse\fi\makeatother")
        if is_dynamic:
            seed_val = instance_id * 1234567
            seed_magic = (f"\\ifdefined\\FPseed\\FPseed={seed_val}\\fi\n"
            f"\\ifdefined\\pgfmathsetseed\\pgfmathsetseed{{{seed_val}}}\\fi")
            dynamic_header = (
                 f"{clean_preamble}\n{anti_brouillon}\n{seed_magic}\n"
                 f"{var_block}\n\\def\\thecopy{{{instance_id}}}\n")
        else:
            dynamic_header = f"{clean_preamble}\n{anti_brouillon}\n"
        
        headers_for_instance = list(CTX["headers"])
        headers_for_instance.append(("variables_fp", dynamic_header))

        # extraction successful => convert questions and ch oices to png
        # files and create json files
        for qst in qsts:
            item = _ctx_new_item(input_tex)
            tex_content = tex.qst_tex_header(qst)
            item["itm_code"] = f"{qst['itm_code']}_{instance_id}" if is_dynamic else qst['itm_code']
            item["itm_type"] = types.ITEM_TYPE_QUESTION
            item["qst_type"] = qst["qst_type"]
            # _tex_to_png(input_tex, output_dir, item, mcq_dir, tex_content)
            _item_set_png_file(item)
            TASKS.append({
                "input_tex": input_tex,
                "output_dir": output_dir,
                "item": item,
                "mcq_dir": mcq_dir,
                "tex_content": tex_content,
                "info": f"(instance {instance_id})" if is_dynamic else None,
                "headers": headers_for_instance
            })
            _ctx_push_item(item)
            result.append(item)
            iterator = tex.iter_on_choices(qst)
            for num, (correct, last, cho_tex) in enumerate(iterator):
                item = _ctx_new_item(input_tex, False)
                item["itm_type"] = types.ITEM_TYPE_CHOICE
                item["cho_correct"] = correct
                item["cho_last"] = last
                info = f"(instance {instance_id} - choice {num})" if is_dynamic else f"(choice {num})"
                # _tex_to_png(input_tex, output_dir, item, mcq_dir, cho_tex, info)
                
                # creating png file name used later for _tex_to_png
                _item_set_png_file(item)
                # adding new task
                TASKS.append({
                    "input_tex": input_tex,
                    "output_dir": output_dir,
                    "item": item,
                    "mcq_dir": mcq_dir,
                    "tex_content": cho_tex,
                    "info": info,
                    "headers": headers_for_instance
                })
                result.append(item)
            _ctx_pop_item()

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
            # _tex_to_png(files[f], output_dir, item, mcq_dir)
            _item_set_png_file(item)
            TASKS.append({
                "input_tex": files[f],
                "output_dir": output_dir,
                "item": item,
                "mcq_dir": mcq_dir,
                "tex_content": None,
                "info": None,
                "headers": list(CTX["headers"])
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


def action(input_dir: str, prefix: str, max_threads: int = 4) -> None:
    global TASKS
    TASKS = [] # TASKS is empty when the compilation starts

    print(f"Compilation starts with {max_threads} threads")
    # everything will be written in a temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:

        # traverse input_dir to generate json
        log.log_open()
        items = _compile_dir_traversal(input_dir, tmp_dir, None)
        log.log_close()

        # generate png with items and TASKS
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(_tex_to_png, **task) for task in TASKS]
            concurrent.futures.wait(futures)


        json_path = os.path.join(tmp_dir, JSON_SPEC)
        with open(json_path, "w", encoding="utf-8") as fd:
            fd.write(json.dumps(items, indent=2))

        # zip the the temporary directory and remove it
        shutil.make_archive(prefix, "zip", root_dir=tmp_dir)


    # output.info("Removing temporary variable files")
    # # removing all variables files created before with pdflatex
    # for var_file in glob.glob(os.path.join(input_dir, "**", "vars_*.tex"), recursive=True):
    #     try:
    #         os.remove(var_file)
    #     except OSError:
    #         output.error("OSError")
    
    # # removing junk files (aux, log) created by pdflatex
    # for junk_file in glob.glob(os.path.join(input_dir, "**", "variables.aux"), recursive=True) + \
    #                  glob.glob(os.path.join(input_dir, "**", "variables.log"), recursive=True):
    #     try:
    #         os.remove(junk_file)
    #     except OSError:
    #         pass
    