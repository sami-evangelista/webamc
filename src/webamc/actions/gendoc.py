"""Implement action gendoc that generate some documentation files.

Init some files according to src/webamc/config.py:
- doc/config.tex - tex file listing configuration parameters
- doc/tool-settings.tex - tex file defining some setting constants
- doc/csv-desc.tex - tex file containing database table descriptions
- doc/db.dot - database relational schema
- examples/cfg/default.json - default configuration file

Action must be executed from the package repository.

"""

import types as _types

import webamc
from webamc.all import *
from webamc.db import util, doc, dotify
from webamc.util import termout


def _type_desc(t: type) -> str:
    if t == str:
        return "string"
    if t == bool:
        return "bool"
    if t == int:
        return "int"
    if t is None:
        return "null"
    if tp.get_origin(t) == list:
        return f"list of ({_type_desc(tp.get_args(t)[0])})"
    if tp.get_origin(t) == dict:
        return (
            f"dict from ({_type_desc(tp.get_args(t)[0])}) to "
            f"({_type_desc(tp.get_args(t)[1])})"
        )
    lit = tp.Literal
    if tp.get_origin(t) == lit:  # pylint: disable=comparison-with-callable
        return " | ".join(json.dumps(u) for u in tp.get_args(t))
    if isinstance(t, _types.UnionType):
        return " | ".join(_type_desc(u) for u in tp.get_args(t))
    print(t)
    assert 0


def _texify(s: str) -> str:
    str_map = {"_": "\\_", "{": r"\{", "}": r"\}"}
    result = str(s)
    for fr, to in str_map.items():
        result = result.replace(fr, to)
    return result


def action() -> None:
    """Generate the documentation."""
    cfg = config.CONFIG_DEFAULT

    # examples/cfg/default.json
    f = "examples/cfg/default.json"
    termout.info(f"generate {f}")
    with open(f, "w", encoding="utf-8") as fd:
        fd.write(json.dumps(cfg, indent=2) + "\n")

    # doc/version.tex
    f = "doc/tool-settings.tex"
    termout.info(f"generate {f}")
    with open(f, "w", encoding="utf-8") as fd:
        fd.write("\\def\\TOOLVERSION{" + webamc.VERSION + "}\n")
        fd.write("\\def\\TOOLURLGIT{" + webamc.URL_GIT + "}\n")
        fd.write("\\def\\TOOLURLRELEASE{" + webamc.URL_RELEASE + "}\n")

    # doc/config.tex
    f = "doc/config-parameters.tex"
    termout.info(f"generate {f}")
    sep = "[itemsep=0pt,parsep=0pt,topsep=0pt,partopsep=0pt]"
    with open(f, "w", encoding="utf-8") as fd:
        w = fd.write
        w("{\\newcommand{\\cmark}{\\ding{51}}%\n")
        w("\\newcommand{\\xmark}{\\ding{55}}%\n")
        w("\\begin{itemize}" + sep + "\n")
        for param, typ in sorted(types.conf_t.__annotations__.items()):
            cli, web, desc = config.CONFIG_DESC_MD[param]
            w("\\item{\\tt{" + _texify(param) + "}}")
            where = {
                x: "\\cmark" if y else "\\xmark"
                for x, y in [("cli", cli), ("web", web)]
            }
            w("~~~" + "~".join(f"{x}: {y}" for x, y in where.items()))
            w("\n  \\begin{itemize}" + sep + "\n")
            default = json.dumps(cfg[param])  # type: ignore
            fields = {
                "Description: ": _texify(desc),
                "Type: ": "{\\tt{" + str(_type_desc(typ)) + "}}",
                "Default value: ": "{\\tt{" + str(_texify(default)) + "}}"
            }
            w("\n".join("  \\item " + label + f" {val}"
                        for label, val in fields.items()))
            w("\n  \\end{itemize}\n")
        w("\\end{itemize}}\n")

    # doc/csv-tables.tex
    f = "doc/csv-tables.tex"
    termout.info(f"generate {f}")
    with open(f, "w", encoding="utf-8") as fd:
        w = fd.write
        for tbl_name, tbl_doc in doc.tbls.items():
            tbl = util.get_tbl(tbl_name)
            w("\\subsection{Table \\texttt{" + _texify(tbl_name) + "}}\n")
            w("\\begin{itemize}" + sep + "\n")
            w("\\item Description: " + tbl_doc + "\n")
            w("\\item Columns:\n")
            w("\\begin{itemize}" + sep + "\n")
            for col_name, col_doc in doc.cols.items():
                if util.get_col(col_name) in util.get_tbl_cols(tbl):
                    w(
                        "\\item\\texttt{" + _texify(col_name) + "} --- "
                        + col_doc + "\n"
                )
            w("\\end{itemize}\n")
            w("\\end{itemize}\n")

    # doc/db.dot
    f = "doc/db.dot"
    termout.info(f"generate {f}")
    with open(f, "w", encoding="utf-8") as fd:
        fd.write(dotify.gen_dot() + "\n")
