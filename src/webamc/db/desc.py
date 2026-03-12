#!/usr/bin/env python3

from webamc.all import *
from webamc.www import html_elements as he
from . import util


def tbl_desc(tbl: str | sa.Table) -> str:
    if isinstance(tbl, sa.Table):
        tbl = util.get_tbl_name(tbl)
    return f"tbl_desc_{tbl}"


def col_desc(col: str | sa.Column[tp.Any]) -> str:
    if isinstance(col, sa.Column):
        col = util.get_col_name(col)
    return f"col_desc_{col}"


def col_txt(col: str) -> he.Txt:
    return he.Txt(col_desc(col))
