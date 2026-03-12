#!/usr/bin/env python3

from webamc.all import *
from webamc.db import op, util, tables, row_op
from . import output


def get_tbl_name(
        csv_file: str,
        delimiter: str,
        reader: None | csv.DictReader = None  # type: ignore
) -> str | None:
    fd = None
    if reader is None:
        fd = open(csv_file, encoding="utf-8")
        reader = csv.DictReader(fd, delimiter=delimiter)
    try:
        if reader.fieldnames is None:
            return None
    except UnicodeDecodeError:
        return None

    # look for the tbl in which we have to insert rows. return if not
    # found
    result = next(
        (tbl.__table__.name  # type: ignore
         for tbl in tables.Base.__subclasses__()
         if all(hasattr(tbl, col) for col in reader.fieldnames)),
        None
    )
    if fd is not None:
        fd.close()
    return result


def action(file_path: str, delimiter: str) -> None:
    load_result_t = tp.Literal[0, 1, 2]

    def load_row(num: int, row: dict[str, tp.Any]) -> load_result_t:

        # replace foreign keys
        ref_col: sa.Column[tp.Any]
        assert tbl is not None
        for col_name, val in row.items():
            col = util.get_col(col_name)
            if col in fkeys:
                if val == "":
                    row[col_name] = None
                else:
                    ref_col = fkeys[col][0]
                    ref_tbl = util.get_col_tbl(ref_col)
                    col_code = util.get_tbl_code(ref_tbl)[0]
                    db_row = dbs.query(ref_col).where(col_code == val).first()
                    if db_row is None:
                        output.error(
                            f"{file_path}:{num}: invalid value "
                            f"for {col}: {val}"
                        )
                        return 0
                    row[col_name] = int(db_row[0])

        # if the table has a code column we check if the table already
        # contains a record with this code in which case we have to do
        # an update. otherwise we have to do an insert
        result: load_result_t
        op_descr: str
        col_codes = util.get_tbl_code(tbl)
        cond = [
            col_code == row[util.get_col_name(col_code)]
            for col_code in col_codes
        ]
        if cond == list():
            result = 1
        elif dbs.query(tbl).where(sa.and_(*cond)).first() is None:
            result = 1
        else:
            result = 2
        try:
            req_type: types.db_query_type_t
            if result == 1:
                op_descr, req_type = "inserted", "insert"
            else:
                op_descr, req_type = "updated", "update"
            ok, err, row = row_op.check_tbl_values(
                dbs, tbl, row, req_type, check_unicity=False
            )
            if not ok:
                msg = err[0] if err is not None and err != list() else "error"
                output.warning(f"{file_path}:{num}: {msg}")
                return 0
            row = row_op.transform_tbl_values(tbl, row)
            if req_type == "insert":
                obj = tbl_meta(**row)
                dbs.add(obj)
            else:
                dbs.query(tbl).where(*cond).update(row)  # type: ignore
            dbs.commit()
            output.info(f"{file_path}:{num}: {op_descr} successfuly")
            return result
        except:
            output.warning(f"{file_path}:{num}: integrity error for {row}")
            return 0

    # open the file or read from stdin
    with open(file_path, encoding="utf-8") as fd:
        reader = csv.DictReader(fd, delimiter=delimiter)
        tbl_name = get_tbl_name(file_path, delimiter, reader)
        if tbl_name is None:
            output.error(f"{file_path}: could not determine destination table")
            return

        tbl = util.get_tbl(tbl_name)
        tbl_meta = util.get_tbl_meta(tbl_name)
        fkeys = util.get_tbl_fkeys(tbl)

        # load the file content
        no_op = {x: 0 for x in range(3)}
        for num, row in enumerate(reader):
            with op.Session() as dbs, dbs.begin():
                no_op[load_row(num + 2, row)] += 1
        output.info(
            f"{file_path}: {no_op[1]} insert(s), {no_op[2]} update(s), "
            f"{no_op[0]} error(s) in table {tbl_name}"
        )
