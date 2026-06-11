from sqlalchemy.orm.session import Session

from webamc.all import *
from . import desc, util, col_types as ct


def check_col_value(
        dbs: Session,
        col: sa.Column[tp.Any],
        val: None | types.db_base_val_t,
        req_type: types.db_query_type_t,
        check_unicity: bool = True
) -> tuple[bool, None | str, None | types.db_base_val_t]:
    result: tuple[bool, None | str, None | types.db_base_val_t]
    if val is None or val == "":
        if not col.nullable:
            col_desc = lang.txt(desc.col_desc(col))
            msg = lang.txt("param_err_invalid_null_value") % col_desc
            return False, msg, None
        return True, None, None
    val_chk = tp.cast(tp.Type[ct.ColType], col.type).val_chk
    try:
        result = True, None, val_chk(val, dbs=dbs)
    except ValueError:
        col_desc = lang.txt(desc.col_desc(col))
        msg = lang.txt("param_err_invalid_value") % col_desc
        return False, msg, None
    if col.unique and check_unicity:
        row = dbs.query(col).where(col == result[2]).first()
        if row is not None:
            col_desc = lang.txt(desc.col_desc(col))
            msg = lang.txt("param_err_invalid_duplicate_value") % col_desc
            result = False, msg, None
    return result


def check_tbl_values(
        dbs: Session,
        tbl: str | sa.Table,
        val: types.db_map_t,
        req_type: types.db_query_type_t,
        check_unicity: bool = True
) -> tuple[bool, list[str], types.db_map_t]:
    ok = True
    err: list[str] = list()
    new_val: types.db_map_t = dict()
    for col in util.get_tbl_cols(tbl):
        if col.name in val:
            cok, cerr, cval = check_col_value(
                dbs, col, val[col.name], req_type, check_unicity=check_unicity
            )
            ok = ok and cok
            if cok:
                new_val[col.name] = cval
            elif cerr is not None:
                err.append(cerr)
        else:
            if (req_type, col.nullable) == ("insert", True):
                col_desc = lang.txt(desc.col_desc(col))
                msg = lang.txt("param_err_invalid_null_value") % col_desc
                ok = False
                err.append(msg)
    return ok, err, new_val


def transform_tbl_values(
        tbl: str | sa.Table,
        val: types.db_map_t
) -> types.db_map_t:
    return {
        col.name: tp.cast(
            tp.Type[ct.ColType], col.type
        ).val_transform(
            val[col.name]
        )
        for col in util.get_tbl_cols(tbl)
        if col.name in val
    }
