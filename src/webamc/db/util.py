from sqlalchemy import Column, Table
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm.attributes import InstrumentedAttribute

from webamc.all import *
from . import tables


def get_tbl_name(tbl: Table) -> str:
    return tbl.name


def get_tbl_pkey(tbl: str | Table) -> Column[tp.Any]:
    if isinstance(tbl, Table):
        tbl = get_tbl_name(tbl)
    return struct["tbls"][tbl]["pkey"]


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


def get_tbl_meta(tbl: str | DeclarativeMeta | Table) -> DeclarativeMeta:
    if isinstance(tbl, str):
        return struct["tbls"][tbl]["meta"]
    if isinstance(tbl, Table):
        return get_tbl_meta(get_tbl_name(tbl))
    return tbl


def get_tbl_doc(tbl: str | DeclarativeMeta | Table) -> str | None:
    return getattr(get_tbl_meta(tbl), "__doc__", None)


def get_col(col: str | InstrumentedAttribute[tp.Any]) -> Column[tp.Any]:
    if isinstance(col, InstrumentedAttribute):
        col_name = col.name
    else:
        col_name = col
    return struct["cols"][col_name]["def"]


def get_col_name(col: Column[tp.Any]) -> str:
    return col.name


def get_col_tbl(col: str | Column[tp.Any]) -> Table:
    if isinstance(col, Column):
        col = col.name
    return struct["cols"][col]["tbl"]


def get_tbl_code(tbl: str | DeclarativeMeta | Table) -> Column[tp.Any] | None:
    return getattr(get_tbl_meta(tbl), "__code__", None)


def get_all_tbl_names() -> list[str]:
    return list(struct["tbls"])


db_struct_tbl_t = tp.TypedDict(
    "db_struct_tbl_t",
    {
        "meta": DeclarativeMeta,
        "def": Table,
        "cols": list[Column[tp.Any]],
        "pkey": Column[tp.Any],
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


def _init(base: tp.Any) -> None:
    global struct
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
            "pkey": next(col for col in tbl.columns if col.primary_key),
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

    # only one column forms the primary key
    for tbl, tbl_def in struct["tbls"].items():
        assert 1 == len(
            [col for col in tbl_def["def"].columns if col.primary_key]
        )

    # a foreign or a primary key can only be an integer
    for tbl, tbl_def in struct["tbls"].items():
        assert isinstance(tbl_def["pkey"].type, sa.Integer)
        for fkey in tbl_def["fkeys"]:
            assert isinstance(fkey.type, sa.Integer)

    # a code column can only be an integer or a string
    for tbl, tbl_def in struct["tbls"].items():
        col = get_tbl_code(tbl)
        if col is not None:
            assert isinstance(col.type, (sa.String, sa.Integer))


_init(tables.Base)
