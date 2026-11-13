from webamc.all import *
from webamc.www import html_elements as he


def tbl_desc(tbl: types.db_tbl_t) -> types.txt_t:
    from . import util
    if isinstance(tbl, sa.Table):
        tbl = util.get_tbl_name(tbl)
    return tp.cast(types.txt_t, f"db_tbl_{tbl}")


def col_desc(col: types.db_col_t) -> types.txt_t:
    from . import util
    return tp.cast(types.txt_t, f"db_col_{util.get_col_name(col)}")


def col_txt(col: types.db_col_t) -> he.Txt:
    return he.Txt(col_desc(col))
