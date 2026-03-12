#!/usr/bin/env python3

import tempfile
import shutil
import hashlib
from pathlib import Path
from PIL import Image
import pymupdf  # type: ignore

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
        "itm_visible": bool
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
            try:
                var, val = (d.strip() for d in directive.split("="))
                mdata = _check_item_mdata(var)
                if var is None:
                    output.warning(f"{file_path}: unknown field {mdata}")
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
        with pymupdf.open(pdf) as pages:
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
        tex_content: str | None = None,
        info: str | None = None
) -> None:
    _item_set_png_file(item)
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
    cur_dir_path = os.getcwd()
    if tex_content is None:
        tex_content = io.read_file_content(input_tex)

    # if we are in an mcq, the file is compiled from the mcq
    # directory. otherwise we move to the file directory
    if mcq_dir is not None:
        os.chdir(mcq_dir)
    else:
        os.chdir(dir_path)

    # create the content of the tex file to compile
    sep = "\n%\n"
    tex_headers = sep.join(
        f"%%%%% header from {header_file} %%%%%{sep}{header_content}"
        for header_file, header_content in CTX["headers"]
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

    # create a temp file for latex content and compute some other file names
    with tempfile.NamedTemporaryFile(
            dir=".", mode="w", suffix=".tex", encoding="utf-8",
            delete=False
    ) as tmp_file:

        tmp_file.write(tex_content)
        tmp_file.close()

        # the output of pdflatex will be written in a temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:

            # pdflatexify the file and move back the previous directory
            args = [
                tex2pdf_exe,
                *[arg.format(
                    out_dir=tmp_dir,
                    tex_file=tmp_file.name
                ) for arg in tex2pdf_exe_args]
            ]
            exec_result = log.log_exec(args)
            os.chdir(cur_dir_path)

            # check pdflatex terminated correctly and that the
            # resulting pdf is not empty and then convert it to png
            # and finally crop it
            path = Path(tmp_file.name).stem
            pdf_file_name = os.path.join(tmp_dir, path + ".pdf")
            png_file_name = os.path.join(tmp_dir, path + ".png")
            if (
                    exec_result
                    and os.path.exists(pdf_file_name)
                    and os.path.getsize(pdf_file_name) > 0
                    and _pdf_to_png(pdf_file_name, png_file_name)
                    and _crop_png(png_file_name)
                    and io.mkdir_of_file(output_png)
            ):
                shutil.move(png_file_name, output_png)
    os.remove(tmp_file.name)


def _compile_question(
        input_tex: str,
        output_dir: str,
        mcq_dir: None | str
) -> list[item_t]:

    # parse tex
    content = io.read_file_content(input_tex)
    code, qsts = tex.extract_qst(content)

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

    # extraction successful => convert questions and choices to png
    # files and create json files
    for qst in qsts:
        item = _ctx_new_item(input_tex)
        tex_content = tex.qst_tex_header(qst)
        item["itm_code"] = qst["itm_code"]
        item["itm_type"] = types.ITEM_TYPE_QUESTION
        item["qst_type"] = qst["qst_type"]
        _tex_to_png(input_tex, output_dir, item, mcq_dir, tex_content)
        _ctx_push_item(item)
        result.append(item)
        iterator = tex.iter_on_choices(qst)
        for num, (correct, last, cho_tex) in enumerate(iterator):
            item = _ctx_new_item(input_tex, False)
            item["itm_type"] = types.ITEM_TYPE_CHOICE
            item["cho_correct"] = correct
            item["cho_last"] = last
            info = f"(choice {num})"
            _tex_to_png(input_tex, output_dir, item, mcq_dir, cho_tex, info)
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
            _tex_to_png(files[f], output_dir, item, mcq_dir)
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


def action(input_dir: str, prefix: str) -> None:

    # everything will be written in a temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:

        # traverse input_dir to generate json and png files
        log.log_open()
        items = _compile_dir_traversal(input_dir, tmp_dir, None)
        log.log_close()

        json_path = os.path.join(tmp_dir, JSON_SPEC)
        with open(json_path, "w", encoding="utf-8") as fd:
            fd.write(json.dumps(items, indent=2))

        # zip the the temporary directory and remove it
        shutil.make_archive(prefix, "zip", root_dir=tmp_dir)
