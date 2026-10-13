from webamc.all import *
from webamc.www import html_elements as he
from . import util


def tbl_desc(tbl: types.db_tbl_t) -> types.txt_t:
    if isinstance(tbl, sa.Table):
        tbl = util.get_tbl_name(tbl)
    return tp.cast(types.txt_t, f"tbl_desc_{tbl}")


def col_desc(col: types.db_col_t) -> types.txt_t:
    return tp.cast(types.txt_t, f"col_desc_{util.get_col_name(col)}")


def col_txt(col: types.db_col_t) -> he.Txt:
    return he.Txt(col_desc(col))
