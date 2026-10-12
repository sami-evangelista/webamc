from webamc.all import *
from webamc.db import op, util, tables, errors
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

    def load_row(num: int, row: dict[str, tp.Any]) -> bool:

        # save the initial row in case we have to display it on error
        row_init = dict(row)

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
                    col_code = util.get_tbl_code(ref_tbl)
                    assert col_code is not None
                    db_row = dbs.query(ref_col).where(col_code == val).first()
                    if db_row is None:
                        output.error(
                            f"{file_path}:{num}: invalid value "
                            f"for {col}: {val}"
                        )
                        return False
                    row[col_name] = int(db_row[0])

        try:
            obj = tbl_meta(**row)
            dbs.add(obj)
            dbs.commit()
            output.info(f"{file_path}:{num}: inserted successfuly")
            return True
        except errors.DBDuplicateValue as ex:
            if isinstance(ex.col, str):
                val = row_init.get(ex.col)
            else:
                val = [row_init.get(c) for c in ex.col]
            msg = (
                f"{file_path}:{num}: duplicate value for column(s) "
                f"{ex.col}: {json.dumps(val)}"
            )
            output.warning(msg)
            return False
        except errors.DBInvalidValue as ex:
            msg = (
                f"{file_path}:{num}: invalid value for column "
                f"{ex.col}: {json.dumps(row_init.get(ex.col))}"
            )
            output.warning(msg)
            return False
        except errors.DBInvalidNullValue as ex:
            msg = (
                f"{file_path}:{num}: invalid null value for column {ex.col}"
            )
            output.warning(msg)
            return False
        except:
            output.warning(f"{file_path}:{num}: integrity error on row {row}")
            return False

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
        no_inserts = 0
        for num, row in enumerate(reader):
            with op.Session() as dbs, dbs.begin():
                if load_row(num + 2, row):
                    no_inserts += 1
        output.info(f"{file_path}: {no_inserts} insert(s) in table {tbl_name}")
