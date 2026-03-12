#!/usr/bin/env python3

from webamc.all import *
from . import col_types as ct, util


clusters = {
    "auth": (
        "Authentication",
        "lightblue",
        [
            "admin", "cas_auth", "usr", "local_auth", "tbl", "ticket"
        ]
    ),
    "mcq": (
        "MCQ elements",
        "lightgreen",
        [
            "choice", "exercise", "item", "question", "mcq", "pack"
        ]
    ),
    "submission": (
        "Exams and Submission",
        "coral", [
            "answer", "exam", "submission", "exam_submission",
            "registration", "review_submission"
        ]
    ),
    "tags": (
        "Tagging",
        "bisque",
        [
            "tag", "item_tag"
        ]
    ),
    "groups": (
        "Groups",
        "gold",
        [
            "grp", "mcq_grp", "usr_grp"
        ]
    )
}


def gen_dot() -> str:
    def col_fmt(col: sa.Column[tp.Any]) -> str:
        try:
            color = tp.cast(ct.ColType, col.type).doc_color
        except:
            color = "black"
        name = col.name
        if col.foreign_keys != set():
            name = f"#{name}"
        flags = list()
        if col.unique:
            flags.append("U")
        if col.nullable:
            flags.append("N")
        if flags != list():
            name = f"{name} ({','.join(flags)})"
        if col.primary_key:
            name = f"<u>{name}</u>"
        return f"<font color=\"{color}\">{name}</font>"
    indent = 4 * " "
    result = f"""digraph WebamcDB {{
{indent}graph [
{indent}{indent}labelloc="t"
{indent}{indent}fontname="Helvetica,Arial,sans-serif"
{indent}]
{indent}node [
{indent}{indent}fontname="Helvetica,Arial,sans-serif"
{indent}{indent}shape=record
{indent}{indent}style=filled
{indent}{indent}fillcolor=gray75
{indent}]
"""
    result += "\n".join(
        f"{indent}subgraph cluster_{cluster} {{"
        + "\n" + f"label=\"{label}\""
        + "\n" + f"bgcolor={bgcolor}"
        + "\n".join(f"{indent}{indent}{tbl_name};" for tbl_name in tbl_names)
        + "\n" + indent + "}"
        for cluster, (label, bgcolor, tbl_names) in clusters.items()
    )
    for tbl_name in sorted(util.get_all_tbl_names()):
        tbl = util.get_tbl(tbl_name)
        fkeys = util.get_tbl_fkeys(tbl)
        label = (
            f"<b><font point-size=\"18\">{tbl_name}</font></b> |" +
            "|".join(col_fmt(col) for col in util.get_tbl_cols(tbl))
        )
        result += f"{indent}{tbl_name} [label=<{{{label}}}>]\n"
        for fkey, cols in fkeys.items():
            inheritance = fkey.primary_key
            ahead = "normal" if inheritance else "none"
            for col in cols:
                ref_tbl = util.get_col_tbl(col)
                result += f"{indent}{tbl_name} -> {ref_tbl.name}"
                result += f" [label={fkey.name},arrowhead={ahead}]"
                result += "\n"
    result = "\n" + result + "}"
    return result
