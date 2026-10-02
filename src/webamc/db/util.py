from sqlalchemy import Column, Table
from sqlalchemy.orm.decl_api import DeclarativeMeta

from webamc.all import *
from . import tables


def get_tbl_name(tbl: Table) -> str:
    return tbl.name


def get_tbl_pkey(tbl: str | Table) -> Column[tp.Any]:
    if isinstance(tbl, Table):
        tbl = get_tbl_name(tbl)
    pkeys = struct["tbls"][tbl]["pkeys"]
    assert len(pkeys) == 1
    return pkeys[0]


def get_tbl_fkeys(
        tbl: str | Table
) -> dict[Column[tp.Any], list[Column[tp.Any]]]:
    if isinstance(tbl, Table):
        tbl = get_tbl_name(tbl)
    return struct["tbls"][tbl]["fkeys"]


def get_tbl_cols(tbl: str | Table) -> list[Column[tp.Any]]:
    if isinstance(tbl, Table):
        tbl = get_tbl_name(tbl)
    return struct["tbls"][tbl]["cols"]


def get_tbl(tbl: str) -> Table:
    return struct["tbls"][tbl]["def"]


def get_tbl_meta(tbl: str) -> DeclarativeMeta:
    return struct["tbls"][tbl]["meta"]


def get_col(col: str) -> Column[tp.Any]:
    return struct["cols"][col]["def"]


def get_col_name(col: Column[tp.Any]) -> str:
    return col.name


def get_col_tbl(col: str | Column[tp.Any]) -> Table:
    if isinstance(col, Column):
        col = col.name
    return struct["cols"][col]["tbl"]


def get_tbl_code(tbl: str | Table) -> list[Column[tp.Any]]:
    if isinstance(tbl, Table):
        tbl = get_tbl_name(tbl)
    try:
        return list(get_col(col_name) for col_name in codes.get(tbl, list()))
    except ValueError:
        return list()


def get_all_tbl_names() -> list[str]:
    return list(struct["tbls"])


db_struct_tbl_t = tp.TypedDict(
    "db_struct_tbl_t",
    {
        "meta": DeclarativeMeta,
        "def": Table,
        "cols": list[Column[tp.Any]],
        "pkeys": list[Column[tp.Any]],
        "fkeys": dict[Column[tp.Any], list[Column[tp.Any]]]
    },
    total=True
)
db_struct_col_t = tp.TypedDict(
    "db_struct_col_t",
    {
        "def": Column[tp.Any],
        "tbl": Table
    },
    total=True
)
db_struct_t = tp.TypedDict(
    "db_struct_t",
    {
        "tbls": dict[str, db_struct_tbl_t],
        "cols": dict[str, db_struct_col_t]
    }
)


struct: db_struct_t
codes: dict[str, list[str]]


def _init(base: tp.Any, codes_: dict[str, list[str]]) -> None:
    global struct
    global codes
    codes = dict(codes_)
    struct = {
        "tbls": dict(),
        "cols": dict()
    }
    todo = list(base.__subclasses__())
    done: set[tp.Type[base]] = set()
    while todo != list():
        tbl_cls = todo.pop()
        tbl = tbl_cls.__table__
        struct["tbls"][tbl.name] = {
            "meta": tbl_cls,
            "def": tbl,
            "cols": list(tbl.columns),
            "pkeys": [col for col in tbl.columns if col.primary_key],
            "fkeys": {
                col: [fkey.column for fkey in col.foreign_keys]
                for col in tbl.columns
                if len(col.foreign_keys) > 0
            }
        }
        for col in tbl.columns:
            struct["cols"][col.name] = {
                "def": col,
                "tbl": tbl
            }
        done.add(tbl_cls)
        todo += tbl_cls.__subclasses__()

    # perform some checks

    # a foreign key can only be an integer
    for tbl, tbl_def in struct["tbls"].items():
        for fkey in tbl_def["fkeys"]:
            assert isinstance(fkey.type, sa.Integer)

    # a code column can only be an integer or a string
    for tbl, tbl_def in struct["tbls"].items():
        for col in get_tbl_code(tbl):
            assert isinstance(col.type, (sa.String, sa.Integer))


_init(tables.Base, tables.TBL_CODES)
